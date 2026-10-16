from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from ada.config import AdaConfig
from ada.domain import Organization, Personnel, deterministic_id
from ada.persistence import TemporalRepository
from ada.provenance import entity_provenance_refs
from ada.seed import DEFAULT_FIXTURE, seed_phase1
from ada.services import RollupService


def test_phase1_seed_is_deterministic_idempotent_and_normalized(
    phase0_config: AdaConfig,
) -> None:
    first = seed_phase1(phase0_config)
    second = seed_phase1(phase0_config)

    assert first.total_created == 30
    assert first.total_skipped == 0
    assert second.total_created == 0
    assert second.total_skipped == 30

    organizations = TemporalRepository(phase0_config, Organization).list()
    people = TemporalRepository(phase0_config, Personnel).list()
    assert len(organizations) == 4
    assert len(people) == 4
    assert people[0].personnel_id in {
        deterministic_id("personnel", "avery-morgan"),
        deterministic_id("personnel", "jordan-quinn"),
        deterministic_id("personnel", "riley-chen"),
        deterministic_id("personnel", "cameron-diaz"),
    }

    avery_id = deterministic_id("personnel", "avery-morgan")
    provenance = entity_provenance_refs(
        phase0_config,
        entity_type="personnel",
        entity_id=avery_id,
        entity_version=1,
    )
    assert provenance[0].method == "deterministic_fixture"
    assert provenance[0].confidence == 1.0

    repository = TemporalRepository(phase0_config, Personnel)
    avery = repository.get(avery_id)
    assert avery is not None
    repository.update(
        replace(avery, preferred_name="Ave"),
        expected_version=1,
        changed_by="editor@example.test",
    )
    seed_phase1(phase0_config)
    assert (
        entity_provenance_refs(
            phase0_config,
            entity_type="personnel",
            entity_id=avery_id,
            entity_version=2,
        )
        == ()
    )


def test_seed_hierarchy_rollup_and_fixture_safety(phase0_config: AdaConfig) -> None:
    seed_phase1(phase0_config)
    root_id = deterministic_id("organization", "ada-command")
    rollup = RollupService(phase0_config).personnel(root_id)
    assert rollup.total_personnel == 4

    fixture_text = DEFAULT_FIXTURE.read_text(encoding="utf-8")
    assert re.search(r"\b\d{3}-\d{2}-\d{4}\b", fixture_text) is None
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / "samples"
        / "phase1_seed"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["synthetic_only"] is True
    assert manifest["contains_plaintext_national_identifiers"] is False
