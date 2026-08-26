from __future__ import annotations

import os

import pytest

from ada.bedrock import AdaBedrockClient
from ada.config import AdaConfig


@pytest.mark.integration
def test_live_bedrock_healthcheck() -> None:
    if os.environ.get("ADA_RUN_BEDROCK_INTEGRATION") != "1":
        pytest.skip("Set ADA_RUN_BEDROCK_INTEGRATION=1 to allow a live model invocation")
    assert AdaBedrockClient(AdaConfig.from_env()).healthcheck(raise_on_error=True)
