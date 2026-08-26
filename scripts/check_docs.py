#!/usr/bin/env python3
"""Validate local Markdown links, anchors, and basic Mermaid structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = [ROOT / "README.md", *sorted((ROOT / "doc").rglob("*.md"))]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MERMAID = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value)
    return value.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    return {slug(match) for match in HEADING.findall(path.read_text(encoding="utf-8"))}


def check_links() -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}
    for source in MARKDOWN_FILES:
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            for raw_target in LINK.findall(line):
                if "://" in raw_target or raw_target.startswith(("mailto:", "#")):
                    if raw_target.startswith("#"):
                        target_path = source
                        fragment = raw_target[1:]
                    else:
                        continue
                else:
                    target, _, fragment = raw_target.partition("#")
                    target_path = (source.parent / target).resolve() if target else source
                    if not target_path.exists():
                        errors.append(
                            f"{source.relative_to(ROOT)}:{line_number}: missing {raw_target}"
                        )
                        continue
                if fragment and target_path.suffix == ".md":
                    known = anchor_cache.setdefault(target_path, anchors(target_path))
                    if fragment not in known:
                        errors.append(
                            f"{source.relative_to(ROOT)}:{line_number}: "
                            f"missing anchor #{fragment} in {target_path.relative_to(ROOT)}"
                        )
    return errors


def check_mermaid() -> list[str]:
    errors: list[str] = []
    pairs = {"]": "[", "}": "{", ")": "("}
    for source in MARKDOWN_FILES:
        for block_number, block in enumerate(MERMAID.findall(source.read_text()), 1):
            for line_number, line in enumerate(block.splitlines(), 1):
                stack: list[str] = []
                quoted = False
                for character in line:
                    if character == '"':
                        quoted = not quoted
                    elif not quoted and character in "[{(":
                        stack.append(character)
                    elif not quoted and character in "]})":
                        if not stack or stack.pop() != pairs[character]:
                            errors.append(
                                f"{source.relative_to(ROOT)} Mermaid {block_number}, "
                                f"line {line_number}: unbalanced delimiter"
                            )
                            break
                if quoted or stack:
                    errors.append(
                        f"{source.relative_to(ROOT)} Mermaid {block_number}, "
                        f"line {line_number}: unclosed quote/delimiter"
                    )
    return errors


def main() -> int:
    errors = [*check_links(), *check_mermaid()]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(MARKDOWN_FILES)} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
