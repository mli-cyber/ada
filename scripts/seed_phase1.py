#!/usr/bin/env python3
"""Load deterministic Phase 1 demo data into the configured database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ada.config import AdaConfig
from ada.seed import seed_phase1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, help="Override the normalized seed JSON")
    arguments = parser.parse_args()
    result = seed_phase1(
        AdaConfig.from_env(),
        fixture_path=arguments.fixture,
    )
    print(
        json.dumps(
            {
                "created": result.created,
                "skipped": result.skipped,
                "total_created": result.total_created,
                "total_skipped": result.total_skipped,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
