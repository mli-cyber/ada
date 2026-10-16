from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ada.config import AdaConfig
from ada.seed import seed_phase1


@pytest.fixture(autouse=True)
def local_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ADA__DATA_PATH", str(tmp_path / "data"))
    monkeypatch.setenv("ADA__DB_URL", f"sqlite:///{tmp_path / 'data' / 'ada.db'}")
    monkeypatch.setenv("ADA__CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("ADA__OBJECT_STORE_PATH", str(tmp_path / "objects"))


@pytest.mark.parametrize(
    "path",
    [
        "app/streamlit_app.py",
        "app/pages/3_Personnel.py",
        "app/pages/4_Organization.py",
        "app/pages/7_File_Import.py",
        "app/pages/10_Administration.py",
    ],
)
def test_phase0_streamlit_pages_render(path: str) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(repository_root / path).run(timeout=30)
    assert not app.exception


def test_administration_separates_local_aws_session() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(
        repository_root / "app/pages/10_Administration.py"
    ).run(timeout=30)
    assert [tab.label for tab in app.tabs] == [
        "Platform & Security",
        "AWS Session (Local Only)",
    ]


def test_phase1_read_only_demos_render_seeded_canonical_data() -> None:
    seed_phase1(AdaConfig.from_env())
    repository_root = Path(__file__).resolve().parents[1]

    personnel = AppTest.from_file(
        repository_root / "app/pages/3_Personnel.py"
    ).run(timeout=30)
    organization = AppTest.from_file(
        repository_root / "app/pages/4_Organization.py"
    ).run(timeout=30)

    assert not personnel.exception
    assert not organization.exception
    assert personnel.metric[0].label == "Canonical personnel"
    assert personnel.metric[0].value == "4"
    assert organization.metric[0].label == "Personnel in scope"
