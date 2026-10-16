"""Typed temporal repositories over the controlled relational boundary."""

from __future__ import annotations

import builtins
import json
import types
from collections.abc import Iterable, Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any, Union, cast, get_args, get_origin, get_type_hints

from ada.config import AdaConfig
from ada.domain import (
    Absence,
    AdministrativeAction,
    CanonicalEntity,
    DocumentRecord,
    DueOut,
    DueOutAssignment,
    Organization,
    OrganizationRelationship,
    Personnel,
    PersonnelAssignment,
    PersonnelContact,
    TrainingCompletion,
    TrainingCourse,
    TrainingRequirement,
    validate_field_policy,
)
from ada.domain.common import EncryptedNationalIdentifier, ValidationSeverity
from ada.platform.db import execute, get_connection, init_db

ENTITY_MODELS: tuple[type[CanonicalEntity], ...] = (
    Personnel,
    Organization,
    OrganizationRelationship,
    PersonnelAssignment,
    PersonnelContact,
    TrainingCourse,
    TrainingRequirement,
    TrainingCompletion,
    DueOut,
    DueOutAssignment,
    AdministrativeAction,
    Absence,
    DocumentRecord,
)
ENTITY_MODELS_BY_TYPE = {model.ENTITY_TYPE: model for model in ENTITY_MODELS}


class RepositoryError(RuntimeError):
    """Base canonical persistence failure."""


class EntityNotFoundError(RepositoryError):
    """The requested canonical entity does not exist."""


class ConcurrencyConflictError(RepositoryError):
    """A mutation used a stale expected version."""

    def __init__(self, entity_type: str, entity_id: str, expected: int, actual: int):
        super().__init__(
            f"{entity_type} {entity_id} expected version {expected}, current version is {actual}"
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.expected = expected
        self.actual = actual


class EntityValidationError(RepositoryError):
    """A canonical entity violates its governed field policy."""


class DeletedEntityError(RepositoryError):
    """A tombstoned entity cannot be changed."""


def _columns(model: type[CanonicalEntity]) -> tuple[str, ...]:
    resolved: list[str] = []
    for item in fields(model):
        if item.name == "national_identifier":
            resolved.extend(
                (
                    "national_id_ciphertext",
                    "national_id_last4",
                    "national_id_key_id",
                    "national_id_algorithm",
                )
            )
        elif item.name == "metadata":
            resolved.append("metadata_json")
        else:
            resolved.append(item.name)
    return tuple(resolved)


def _scalar(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return int(value)
    return value


def _entity_values(entity: CanonicalEntity) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in fields(entity):
        value = getattr(entity, item.name)
        if item.name == "national_identifier":
            encrypted = cast(EncryptedNationalIdentifier | None, value)
            values.update(
                {
                    "national_id_ciphertext": encrypted.ciphertext if encrypted else None,
                    "national_id_last4": encrypted.last4 if encrypted else None,
                    "national_id_key_id": encrypted.key_id if encrypted else None,
                    "national_id_algorithm": encrypted.algorithm if encrypted else None,
                }
            )
        elif item.name == "metadata":
            values["metadata_json"] = json.dumps(dict(value), sort_keys=True)
        else:
            values[item.name] = _scalar(value)
    return values


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _history_payload(entity: CanonicalEntity) -> str:
    payload = {item.name: _json_value(getattr(entity, item.name)) for item in fields(entity)}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _coerce(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in (types.UnionType, Union):
        candidates = [
            candidate for candidate in get_args(annotation) if candidate is not type(None)
        ]
        return _coerce(candidates[0], value) if candidates else value
    if annotation is datetime:
        return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if annotation is date:
        return value if isinstance(value, date) else date.fromisoformat(str(value))
    if annotation is bool:
        return bool(value)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    return value


def _entity_from_mapping[EntityT: CanonicalEntity](
    model: type[EntityT],
    values: Mapping[str, Any],
) -> EntityT:
    hints = get_type_hints(model)
    kwargs: dict[str, Any] = {}
    for item in fields(model):
        if item.name == "national_identifier":
            ciphertext = values.get("national_id_ciphertext")
            kwargs[item.name] = (
                EncryptedNationalIdentifier(
                    ciphertext=str(ciphertext),
                    last4=str(values["national_id_last4"]),
                    key_id=str(values["national_id_key_id"]),
                    algorithm=str(values["national_id_algorithm"]),
                )
                if ciphertext is not None
                else None
            )
        elif item.name == "metadata":
            raw_metadata = values.get("metadata_json", values.get("metadata", {}))
            kwargs[item.name] = (
                json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata
            )
        elif item.name in values:
            kwargs[item.name] = _coerce(hints[item.name], values[item.name])
    return model(**kwargs)


def _mapping(cursor: Any, row: Any) -> dict[str, Any]:
    names = [
        str(description.name if hasattr(description, "name") else description[0])
        for description in cursor.description
    ]
    return dict(zip(names, tuple(row), strict=True))


def _validate_as_of(as_of: datetime | None) -> None:
    if as_of is not None and as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")


class TemporalRepository[EntityT: CanonicalEntity]:
    """Secured-service persistence primitive with immutable version history."""

    def __init__(self, config: AdaConfig, model: type[EntityT]):
        if model not in ENTITY_MODELS:
            raise ValueError(f"Unsupported canonical model: {model!r}")
        self.config = config
        self.model = model
        self.columns = _columns(model)
        init_db(config)

    def create(
        self,
        entity: EntityT,
        *,
        changed_by: str | None = None,
        reason: str | None = None,
    ) -> EntityT:
        if entity.version != 1 or entity.deleted_at is not None:
            raise EntityValidationError("new entities must be active at version 1")
        self._validate(entity)
        actor = changed_by or entity.created_by
        values = _entity_values(entity)
        placeholders = ", ".join("?" for _ in self.columns)
        statement = (
            f"INSERT INTO {self.model.TABLE} ({', '.join(self.columns)}) "
            f"VALUES ({placeholders})"
        )
        connection = get_connection(self.config)
        try:
            execute(
                connection,
                self.config,
                statement,
                tuple(values[column] for column in self.columns),
            )
            self._insert_history(connection, entity, actor, reason)
            connection.commit()
            return entity
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(
        self,
        entity_id: str,
        *,
        as_of: datetime | None = None,
        include_deleted: bool = False,
    ) -> EntityT | None:
        _validate_as_of(as_of)
        connection = get_connection(self.config)
        try:
            if as_of is None:
                cursor = execute(
                    connection,
                    self.config,
                    f"SELECT {', '.join(self.columns)} FROM {self.model.TABLE} "
                    f"WHERE {self.model.ID_FIELD} = ?",
                    (entity_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                entity = _entity_from_mapping(self.model, _mapping(cursor, row))
            else:
                cursor = execute(
                    connection,
                    self.config,
                    """
                    SELECT payload_json, valid_from, valid_to, deleted_at
                    FROM canonical_entity_history
                    WHERE entity_type = ? AND entity_id = ?
                      AND valid_from <= ?
                      AND (valid_to IS NULL OR valid_to > ?)
                    ORDER BY version DESC
                    """,
                    (
                        self.model.ENTITY_TYPE,
                        entity_id,
                        as_of.isoformat(),
                        as_of.isoformat(),
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                entity = self._history_entity(_mapping(cursor, row))
            if entity.deleted_at is not None and not include_deleted:
                return None
            return entity
        finally:
            connection.close()

    def list(
        self,
        *,
        as_of: datetime | None = None,
        include_deleted: bool = False,
    ) -> list[EntityT]:
        _validate_as_of(as_of)
        connection = get_connection(self.config)
        try:
            if as_of is None:
                cursor = connection.execute(
                    f"SELECT {', '.join(self.columns)} FROM {self.model.TABLE} "
                    f"ORDER BY {self.model.ID_FIELD}"
                )
                entities = [
                    _entity_from_mapping(self.model, _mapping(cursor, row))
                    for row in cursor.fetchall()
                ]
            else:
                cursor = execute(
                    connection,
                    self.config,
                    """
                    SELECT payload_json, valid_from, valid_to, deleted_at
                    FROM canonical_entity_history
                    WHERE entity_type = ? AND valid_from <= ?
                      AND (valid_to IS NULL OR valid_to > ?)
                    ORDER BY entity_id
                    """,
                    (self.model.ENTITY_TYPE, as_of.isoformat(), as_of.isoformat()),
                )
                entities = [
                    self._history_entity(_mapping(cursor, row)) for row in cursor.fetchall()
                ]
            if include_deleted:
                return entities
            return [entity for entity in entities if entity.deleted_at is None]
        finally:
            connection.close()

    def update(
        self,
        entity: EntityT,
        *,
        expected_version: int,
        changed_by: str,
        reason: str | None = None,
        changed_at: datetime | None = None,
    ) -> EntityT:
        return self._mutate(
            entity,
            expected_version=expected_version,
            changed_by=changed_by,
            reason=reason,
            changed_at=changed_at,
            deleting=False,
        )

    def delete(
        self,
        entity_id: str,
        *,
        expected_version: int,
        changed_by: str,
        reason: str | None = None,
        changed_at: datetime | None = None,
    ) -> EntityT:
        current = self.get(entity_id, include_deleted=True)
        if current is None:
            raise EntityNotFoundError(f"{self.model.ENTITY_TYPE} {entity_id} was not found")
        return self._mutate(
            current,
            expected_version=expected_version,
            changed_by=changed_by,
            reason=reason,
            changed_at=changed_at,
            deleting=True,
        )

    def history(self, entity_id: str) -> builtins.list[EntityT]:
        connection = get_connection(self.config)
        try:
            cursor = execute(
                connection,
                self.config,
                """
                SELECT payload_json, valid_from, valid_to, deleted_at
                FROM canonical_entity_history
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY version
                """,
                (self.model.ENTITY_TYPE, entity_id),
            )
            return [self._history_entity(_mapping(cursor, row)) for row in cursor.fetchall()]
        finally:
            connection.close()

    def _mutate(
        self,
        candidate: EntityT,
        *,
        expected_version: int,
        changed_by: str,
        reason: str | None,
        changed_at: datetime | None,
        deleting: bool,
    ) -> EntityT:
        now = changed_at or datetime.now(UTC)
        if now.tzinfo is None:
            raise ValueError("changed_at must be timezone-aware")
        current = self.get(candidate.entity_id, include_deleted=True)
        if current is None:
            raise EntityNotFoundError(
                f"{self.model.ENTITY_TYPE} {candidate.entity_id} was not found"
            )
        if current.deleted_at is not None:
            raise DeletedEntityError(
                f"{self.model.ENTITY_TYPE} {candidate.entity_id} is deleted"
            )
        next_entity = cast(
            EntityT,
            replace(
                candidate,
                version=expected_version + 1,
                created_at=current.created_at,
                created_by=current.created_by,
                updated_at=now,
                updated_by=changed_by,
                valid_from=now,
                valid_to=None,
                deleted_at=now if deleting else None,
            ),
        )
        self._validate(next_entity)
        values = _entity_values(next_entity)
        update_columns = [column for column in self.columns if column != self.model.ID_FIELD]
        assignments = ", ".join(f"{column} = ?" for column in update_columns)
        parameters = tuple(values[column] for column in update_columns) + (
            candidate.entity_id,
            expected_version,
        )

        connection = get_connection(self.config)
        try:
            cursor = execute(
                connection,
                self.config,
                f"UPDATE {self.model.TABLE} SET {assignments} "
                f"WHERE {self.model.ID_FIELD} = ? AND version = ?",
                parameters,
            )
            if cursor.rowcount != 1:
                actual_row = execute(
                    connection,
                    self.config,
                    f"SELECT version FROM {self.model.TABLE} "
                    f"WHERE {self.model.ID_FIELD} = ?",
                    (candidate.entity_id,),
                ).fetchone()
                if actual_row is None:
                    raise EntityNotFoundError(
                        f"{self.model.ENTITY_TYPE} {candidate.entity_id} was not found"
                    )
                raise ConcurrencyConflictError(
                    self.model.ENTITY_TYPE,
                    candidate.entity_id,
                    expected_version,
                    int(actual_row[0]),
                )
            execute(
                connection,
                self.config,
                """
                UPDATE canonical_entity_history
                SET valid_to = ?
                WHERE entity_type = ? AND entity_id = ? AND version = ?
                  AND valid_to IS NULL
                """,
                (
                    now.isoformat(),
                    self.model.ENTITY_TYPE,
                    candidate.entity_id,
                    expected_version,
                ),
            )
            self._insert_history(connection, next_entity, changed_by, reason)
            connection.commit()
            return next_entity
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _insert_history(
        self,
        connection: Any,
        entity: EntityT,
        changed_by: str,
        reason: str | None,
    ) -> None:
        execute(
            connection,
            self.config,
            """
            INSERT INTO canonical_entity_history (
                entity_type, entity_id, version, payload_json, valid_from,
                valid_to, deleted_at, changed_by, change_reason, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.model.ENTITY_TYPE,
                entity.entity_id,
                entity.version,
                _history_payload(entity),
                entity.valid_from.isoformat(),
                entity.valid_to.isoformat() if entity.valid_to else None,
                entity.deleted_at.isoformat() if entity.deleted_at else None,
                changed_by,
                reason,
                datetime.now(UTC).isoformat(),
            ),
        )

    def _history_entity(self, row: Mapping[str, Any]) -> EntityT:
        payload = json.loads(str(row["payload_json"]))
        payload["valid_from"] = row["valid_from"]
        payload["valid_to"] = row["valid_to"]
        payload["deleted_at"] = row["deleted_at"]
        return _entity_from_mapping(self.model, payload)

    @staticmethod
    def _validate(entity: EntityT) -> None:
        errors = [
            issue
            for issue in validate_field_policy(entity)
            if issue.severity is ValidationSeverity.ERROR
        ]
        if errors:
            details = "; ".join(f"{issue.field}: {issue.message}" for issue in errors)
            raise EntityValidationError(details)


def repositories[EntityT: CanonicalEntity](
    config: AdaConfig,
    models: Iterable[type[EntityT]],
) -> dict[str, TemporalRepository[EntityT]]:
    """Construct repositories by stable entity type for service composition."""

    return {model.ENTITY_TYPE: TemporalRepository(config, model) for model in models}
