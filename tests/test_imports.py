"""Import smoke tests for the scaffold.

Ensures the package tree imports cleanly (no syntax errors in placeholders) and that the
Bedrock client can be constructed without AWS credentials (methods remain stubs).
"""

from __future__ import annotations

import importlib

import pytest

from ada.bedrock import AdaBedrockClient
from ada.config import AdaConfig

MODULES = [
    "ada",
    "ada.config",
    "ada.bedrock",
    "ada.platform.audit",
    "ada.domain.state",
    "ada.domain.dueouts",
    "ada.registry.registry",
    "ada.registry.profiles",
    "ada.agents.orchestrator",
    "ada.services.query_service",
    "ada.services.dueout_service",
    "ada.ingestion.structured",
    "ada.ingestion.unstructured",
    "ada.ingestion.dates",
    "ada.provenance.provenance",
    "ada.quality.data_quality",
    "ada.reports.exporters",
    "ada.workflows.engine",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)


def test_bedrock_client_constructs_without_aws() -> None:
    client = AdaBedrockClient(AdaConfig.from_env({}))
    # Product methods are scaffold stubs until later phases.
    with pytest.raises(NotImplementedError):
        client.chat([{"role": "user", "content": "hi"}])
    with pytest.raises(NotImplementedError):
        client.embed(["hello"])
