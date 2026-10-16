"""Read-only Phase 1 organization hierarchy and rollup demonstration."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ada.config import AdaConfig
from ada.domain import Organization
from ada.platform.identity import current_principal
from ada.services import (
    CanonicalService,
    OrganizationHierarchyService,
    OrganizationNode,
    RollupService,
)

st.set_page_config(page_title="Ada - Organization", page_icon="A", layout="wide")
st.title("Organization / Assignments")
st.caption("Phase 1 hierarchy, organization scope, and personnel rollups — read-only demo")

config = AdaConfig.from_env()
principal = current_principal(config)
records = CanonicalService(config, Organization, principal=principal).list()

if not records:
    st.info(
        "No canonical organizations are loaded. Run "
        "`uv run python scripts/seed_phase1.py` to load deterministic synthetic demo data."
    )
else:
    labels = {
        f"{record.get('code')} — {record.get('name')}": str(record["organization_id"])
        for record in records
    }
    selected_label = st.selectbox("Hierarchy root", labels)
    root_id = labels[selected_label]
    hierarchy = OrganizationHierarchyService(config, principal=principal)
    rollup = RollupService(config, principal=principal).personnel(root_id)
    tree = hierarchy.tree(root_id)

    total_column, organizations_column, date_column = st.columns(3)
    total_column.metric("Personnel in scope", rollup.total_personnel)
    organizations_column.metric("Organizations in scope", len(rollup.organization_ids))
    date_column.metric("As of", rollup.as_of.date().isoformat())

    def flatten(node: OrganizationNode, depth: int = 0) -> list[dict[str, object]]:
        row = {
            "Hierarchy": f"{'  ' * depth}{'↳ ' if depth else ''}{node.organization.name}",
            "Code": node.organization.code,
            "Type": node.organization.organization_type,
            "Status": node.organization.status.value,
            "Direct personnel": rollup.direct_counts.get(
                node.organization.organization_id,
                0,
            ),
            "Version": node.organization.version,
        }
        return [
            row,
            *[
                descendant
                for child in node.children
                for descendant in flatten(child, depth + 1)
            ],
        ]

    hierarchy_tab, directory_tab = st.tabs(["Hierarchy & rollup", "Organization directory"])
    hierarchy_tab.dataframe(flatten(tree), width="stretch", hide_index=True)
    hierarchy_tab.caption(
        "Personnel totals use active primary assignments and deduplicate canonical person IDs."
    )
    directory_tab.dataframe(
        [
            {
                "Code": record.get("code"),
                "Name": record.get("name"),
                "Short name": record.get("short_name"),
                "Type": record.get("organization_type"),
                "Status": record.get("status"),
                "Classification": record.get("classification"),
                "Version": record.get("version"),
            }
            for record in records
        ],
        width="stretch",
        hide_index=True,
    )
