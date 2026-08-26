"""Local-development AWS SSO login helper."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Iterator

from ada.config import AdaConfig

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_SENSITIVE_VALUE = re.compile(
    r"(?i)\b(access.?token|refresh.?token|client.?secret|secret.?access.?key)"
    r"(\s*[:=]\s*)(\S+)"
)


class AwsSsoLoginError(RuntimeError):
    """Raised when the local AWS CLI cannot complete SSO login."""


def sso_login_command(config: AdaConfig) -> tuple[str, ...]:
    """Build the browser-independent AWS CLI device-login command."""

    if not config.aws_profile:
        raise AwsSsoLoginError("Set AWS_PROFILE before starting AWS SSO login")
    executable = shutil.which("aws")
    if executable is None:
        raise AwsSsoLoginError("AWS CLI v2 is not installed or is not on PATH")
    return (
        executable,
        "sso",
        "login",
        "--profile",
        config.aws_profile,
        "--use-device-code",
        "--no-browser",
    )


def _safe_output(line: str) -> str:
    cleaned = _ANSI_ESCAPE.sub("", line).rstrip()
    return _SENSITIVE_VALUE.sub(r"\1\2[REDACTED]", cleaned)


def stream_sso_login(config: AdaConfig) -> Iterator[str]:
    """Run local AWS device login and yield display-safe status lines."""

    command = sso_login_command(config)
    process = subprocess.Popen(  # noqa: S603 - fixed executable and arguments
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if process.stdout is None:  # pragma: no cover - subprocess invariant
        process.terminate()
        raise AwsSsoLoginError("Unable to read AWS CLI login output")

    try:
        for raw_line in process.stdout:
            line = _safe_output(raw_line)
            if line:
                yield line
    except GeneratorExit:
        if process.poll() is None:
            process.terminate()
        raise
    finally:
        process.stdout.close()

    return_code = process.wait()
    if return_code != 0:
        raise AwsSsoLoginError(f"AWS SSO login exited with status {return_code}")
