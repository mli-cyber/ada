"""Read-only Phase 1 canonical personnel demonstration."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ada.config import AdaConfig
from ada.domain import Personnel
from ada.platform.identity import current_principal
from ada.services import CanonicalService

st.set_page_config(page_title="Ada - Personnel", page_icon="A", layout="wide")
st.title("Personnel")
st.caption("Phase 1 canonical records — read-only demo; conversational CRUD arrives in Phase 3")

config = AdaConfig.from_env()
principal = current_principal(config)
records = CanonicalService(config, Personnel, principal=principal).list()

st.write(f"Viewing as **{principal.role.value}** (`{principal.user}`)")
st.caption("Fields outside this role's PII access are redacted by the service layer.")

if not records:
    st.info(
        "No canonical personnel records are loaded. Run "
        "`uv run python scripts/seed_phase1.py` to load deterministic synthetic demo data."
    )
else:
    query = st.text_input(
        "Search personnel",
        placeholder="Name, employee number, position, or grade",
    ).strip().lower()

    def searchable(record: dict[str, object]) -> bool:
        values = (
            record.get("first_name"),
            record.get("last_name"),
            record.get("preferred_name"),
            record.get("employee_number"),
            record.get("position_title"),
            record.get("rank_grade"),
        )
        return not query or any(query in str(value).lower() for value in values if value)

    filtered = [record for record in records if searchable(record)]
    st.metric("Canonical personnel", len(filtered))
    st.dataframe(
        [
            {
                "Name": " ".join(
                    part
                    for part in (
                        str(record.get("first_name", "")),
                        str(record.get("last_name", "")),
                    )
                    if part
                ),
                "Employee #": record.get("employee_number"),
                "Status": record.get("status"),
                "Position": record.get("position_title"),
                "Grade": record.get("rank_grade"),
                "Version": record.get("version"),
            }
            for record in filtered
        ],
        width="stretch",
        hide_index=True,
    )

    if filtered:
        options = {
            f"{record.get('last_name')}, {record.get('first_name')} "
            f"({str(record['personnel_id'])[:8]})": record
            for record in filtered
        }
        selection = st.selectbox("Personnel detail", options)
        selected = options[selection]
        left, right = st.columns(2)
        left.json(
            {
                "identity": {
                    "personnel_id": selected.get("personnel_id"),
                    "employee_number": selected.get("employee_number"),
                    "first_name": selected.get("first_name"),
                    "middle_name": selected.get("middle_name"),
                    "last_name": selected.get("last_name"),
                    "preferred_name": selected.get("preferred_name"),
                    "status": selected.get("status"),
                }
            }
        )
        right.json(
            {
                "assignment_profile": {
                    "position_title": selected.get("position_title"),
                    "rank_grade": selected.get("rank_grade"),
                    "primary_email": selected.get("primary_email"),
                    "phone": selected.get("phone"),
                },
                "governance": {
                    "classification": selected.get("classification"),
                    "version": selected.get("version"),
                    "valid_from": selected.get("valid_from"),
                    "updated_by": selected.get("updated_by"),
                },
            }
        )
