"""Ada Phase 0 administration and boundary-health page."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ada.bedrock import AdaBedrockClient
from ada.config import AdaConfig
from ada.models.registry import ModelRegistry, ModelTier
from ada.platform import db, storage, vectors
from ada.platform.identity import (
    ROLE_PERMISSIONS,
    Permission,
    PIITier,
    Role,
    current_principal,
    filter_record,
)
from ada.platform.maintenance import reset_local

st.set_page_config(page_title="Ada - Administration", page_icon="A", layout="wide")
st.title("Administration")
st.caption("Phase 0 platform health, security boundaries, and local maintenance")

config = AdaConfig.from_env()
principal = current_principal(config)

st.subheader("Resolved configuration (non-secret)")
st.table({"Setting": list(config.describe().keys()), "Value": list(config.describe().values())})

st.subheader("Current principal")
st.write(f"**User:** `{principal.user}`")
st.write(f"**Role:** `{principal.role.value}`")

st.subheader("Platform health")
db.init_db(config)
health = {
    "Relational DB": db.healthcheck(config),
    "Vector DB": vectors.healthcheck(config),
    "Object store": storage.healthcheck(config),
}
columns = st.columns(len(health))
for column, (name, healthy) in zip(columns, health.items(), strict=True):
    column.metric(name, "Healthy" if healthy else "Unavailable")

if st.button(
    "Run live Bedrock health check",
    help="This invokes the active model and may cost tokens.",
):
    with st.spinner("Calling Bedrock..."):
        bedrock_healthy = AdaBedrockClient(config).healthcheck()
    if bedrock_healthy:
        st.success("Bedrock is reachable.")
    else:
        st.error("Bedrock health check failed. Refresh AWS SSO credentials and retry.")

st.subheader("Role × permission matrix")
permission_rows = []
for role in Role:
    permission_rows.append(
        {
            "role": role.value,
            **{
                permission.value: permission in ROLE_PERMISSIONS[role]
                for permission in Permission
            },
        }
    )
st.dataframe(permission_rows, hide_index=True, use_container_width=True)

st.subheader("Seed-driven PII redaction")
seed_path = _ROOT / "samples" / "phase0_seed"
people = pd.read_csv(seed_path / "people_sample.csv")
field_tiers_raw = pd.read_json(seed_path / "field_tiers.json", typ="series").to_dict()
field_tiers = {name: PIITier(value) for name, value in field_tiers_raw.items()}
demo_role = Role(
    st.selectbox(
        "Preview as role",
        [role.value for role in Role],
        index=list(Role).index(principal.role),
    )
)
full_record = people.iloc[0].to_dict()
redacted_record = filter_record(full_record, demo_role, field_tiers)
left, right = st.columns(2)
left.caption("Full synthetic fixture")
left.json(full_record)
right.caption(f"View as {demo_role.value}")
right.json(redacted_record)

st.subheader("Model tier preview")
selected_tier = ModelTier(
    st.selectbox(
        "Budget tier",
        [tier.value for tier in ModelTier],
        index=list(ModelTier).index(ModelTier(config.active_tier)),
    )
)
tier_profile = ModelRegistry(config).profile(selected_tier)
st.json(
    {
        "tier": tier_profile.tier.value,
        "primary": tier_profile.primary,
        "fallbacks": tier_profile.fallbacks,
        "max_tokens": tier_profile.max_tokens,
        "max_agent_loops": tier_profile.max_agent_loops,
        "allow_optional_passes": tier_profile.allow_optional_passes,
        "retrieval_top_k": tier_profile.retrieval_top_k,
    }
)
st.caption("This previews a session choice. Set ADA__MODEL_TIER to persist the default.")

st.subheader("Object-store round trip")
if st.button("Store and retrieve synthetic policy"):
    object_store = storage.get_object_store(config)
    content = (seed_path / "sample_policy.txt").read_bytes()
    key = "admin-demo/sample_policy.txt"
    location = object_store.put(key, content)
    if object_store.get(key) == content:
        st.success(f"Round trip succeeded: {location}")
    else:  # pragma: no cover - defensive UI path
        st.error("Round trip returned different content.")

st.divider()
st.subheader("Danger Zone")
st.warning("Reset deletes the configured local SQLite, Chroma, and object-store data.")
confirmation = st.text_input("Type RESET to enable local reset")
if st.button("Reset local stores", type="primary", disabled=confirmation != "RESET"):
    try:
        summary = reset_local(config, confirm=True, principal=principal)
        st.success("Local stores reset and reinitialized.")
        st.json(summary)
    except Exception as exc:
        st.error(f"Reset failed: {exc}")
