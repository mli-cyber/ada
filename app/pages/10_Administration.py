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
from ada.platform.aws_auth import AwsSsoLoginError, stream_sso_login
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
platform_tab, aws_tab = st.tabs(["Platform & Security", "AWS Session (Local Only)"])

platform_tab.subheader("Resolved configuration (demo-safe)")
platform_tab.table(
    {"Setting": list(config.describe().keys()), "Value": list(config.describe().values())}
)

platform_tab.subheader("Current principal")
platform_tab.write(f"**User:** `{principal.user}`")
platform_tab.write(f"**Role:** `{principal.role.value}`")

platform_tab.subheader("Platform health")
db.init_db(config)
health = {
    "Relational DB": db.healthcheck(config),
    "Vector DB": vectors.healthcheck(config),
    "Object store": storage.healthcheck(config),
}
columns = platform_tab.columns(len(health))
for column, (name, healthy) in zip(columns, health.items(), strict=True):
    column.metric(name, "Healthy" if healthy else "Unavailable")

aws_tab.subheader("AWS SSO session")
aws_tab.warning(
    "Development-only surface. Remove it when production application-user OIDC is enabled."
)
aws_tab.caption(
    "Local-development helper. The short-lived device code is displayed only in this "
    "localhost session. Access keys, secret keys, session tokens, and cache contents are "
    "never shown."
)
aws_summary = config.describe_aws()
aws_tab.table({"Setting": list(aws_summary), "Value": list(aws_summary.values())})
if config.aws_profile:
    if aws_tab.button("Refresh AWS SSO login"):
        login_status = aws_tab.status("Starting AWS SSO device login...", expanded=True)
        try:
            for output_line in stream_sso_login(config):
                if output_line.startswith("https://"):
                    login_status.markdown(
                        f"[Open the AWS verification page]({output_line})"
                    )
                else:
                    login_status.code(output_line, language="text")
            login_status.update(label="AWS SSO login complete", state="complete")
            aws_tab.success("Credentials refreshed. You can run the Bedrock health check.")
        except AwsSsoLoginError as exc:
            login_status.update(label="AWS SSO login failed", state="error")
            aws_tab.error(str(exc))
else:
    aws_tab.warning("Set AWS_PROFILE in .env to enable the local SSO login button.")

if aws_tab.button(
    "Run live Bedrock health check",
    help="This invokes the active model and may cost tokens.",
):
    with aws_tab.spinner("Calling Bedrock..."):
        bedrock_healthy = AdaBedrockClient(config).healthcheck()
    if bedrock_healthy:
        aws_tab.success("Bedrock is reachable.")
    else:
        aws_tab.error("Bedrock health check failed. Refresh AWS SSO credentials and retry.")

platform_tab.subheader("Role × permission matrix")
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
platform_tab.dataframe(permission_rows, hide_index=True, use_container_width=True)

platform_tab.subheader("Seed-driven PII redaction")
seed_path = _ROOT / "samples" / "phase0_seed"
people = pd.read_csv(seed_path / "people_sample.csv")
field_tiers_raw = pd.read_json(seed_path / "field_tiers.json", typ="series").to_dict()
field_tiers = {name: PIITier(value) for name, value in field_tiers_raw.items()}
demo_role = Role(
    platform_tab.selectbox(
        "Preview as role",
        [role.value for role in Role],
        index=list(Role).index(principal.role),
    )
)
full_record = people.iloc[0].to_dict()
redacted_record = filter_record(full_record, demo_role, field_tiers)
left, right = platform_tab.columns(2)
left.caption("Full synthetic fixture")
left.json(full_record)
right.caption(f"View as {demo_role.value}")
right.json(redacted_record)

platform_tab.subheader("Model tier preview")
selected_tier = ModelTier(
    platform_tab.selectbox(
        "Budget tier",
        [tier.value for tier in ModelTier],
        index=list(ModelTier).index(ModelTier(config.active_tier)),
    )
)
tier_profile = ModelRegistry(config).profile(selected_tier)
platform_tab.json(
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
platform_tab.caption(
    "This previews a session choice. Set ADA__MODEL_TIER to persist the default."
)

platform_tab.subheader("Object-store round trip")
if platform_tab.button("Store and retrieve synthetic policy"):
    object_store = storage.get_object_store(config)
    content = (seed_path / "sample_policy.txt").read_bytes()
    key = "admin-demo/sample_policy.txt"
    location = object_store.put(key, content)
    if object_store.get(key) == content:
        platform_tab.success(f"Round trip succeeded: {location}")
    else:  # pragma: no cover - defensive UI path
        platform_tab.error("Round trip returned different content.")

platform_tab.divider()
platform_tab.subheader("Danger Zone")
platform_tab.warning(
    "Reset deletes the configured local SQLite, Chroma, and object-store data."
)
confirmation = platform_tab.text_input("Type RESET to enable local reset")
if platform_tab.button(
    "Reset local stores", type="primary", disabled=confirmation != "RESET"
):
    try:
        summary = reset_local(config, confirm=True, principal=principal)
        platform_tab.success("Local stores reset and reinitialized.")
        platform_tab.json(summary)
    except Exception as exc:
        platform_tab.error(f"Reset failed: {exc}")
