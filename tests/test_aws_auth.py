from __future__ import annotations

from typing import Any

import pytest

from ada.config import AdaConfig
from ada.platform import aws_auth
from ada.platform.aws_auth import AwsSsoLoginError, sso_login_command, stream_sso_login


class _FakeStdout(list[str]):
    def close(self) -> None:
        pass


class _FakeProcess:
    def __init__(self, lines: list[str], return_code: int = 0) -> None:
        self.stdout = _FakeStdout(lines)
        self.return_code = return_code
        self.terminated = False

    def wait(self) -> int:
        return self.return_code

    def poll(self) -> int | None:
        return self.return_code

    def terminate(self) -> None:
        self.terminated = True


def test_sso_login_requires_profile() -> None:
    with pytest.raises(AwsSsoLoginError, match="AWS_PROFILE"):
        sso_login_command(AdaConfig.from_env({}))


def test_stream_sso_login_uses_device_flow_and_redacts_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    process = _FakeProcess(
        [
            "Open this page:\n",
            "https://device.sso.example.test/\n",
            "access_token=must-not-display\n",
        ]
    )
    monkeypatch.setattr(aws_auth.shutil, "which", lambda name: "/usr/local/bin/aws")

    def fake_popen(command: tuple[str, ...], **kwargs: Any) -> _FakeProcess:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return process

    monkeypatch.setattr(aws_auth.subprocess, "Popen", fake_popen)
    config = AdaConfig.from_env({"AWS_PROFILE": "ada-dev"})
    output = list(stream_sso_login(config))

    assert captured["command"] == (
        "/usr/local/bin/aws",
        "sso",
        "login",
        "--profile",
        "ada-dev",
        "--use-device-code",
        "--no-browser",
    )
    assert output[-1] == "access_token=[REDACTED]"


def test_stream_sso_login_reports_cli_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aws_auth.shutil, "which", lambda name: "/usr/local/bin/aws")
    monkeypatch.setattr(
        aws_auth.subprocess,
        "Popen",
        lambda *args, **kwargs: _FakeProcess(["login failed\n"], return_code=2),
    )
    with pytest.raises(AwsSsoLoginError, match="status 2"):
        list(stream_sso_login(AdaConfig.from_env({"AWS_PROFILE": "ada-dev"})))
