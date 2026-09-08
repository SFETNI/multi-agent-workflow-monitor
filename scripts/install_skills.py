#!/usr/bin/env python3
"""Install bundled Agent Skills into a target project's `.agents/skills` directory."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"


def available_skills() -> list[str]:
    names = []
    for item in sorted(SKILLS_ROOT.iterdir()):
        if item.is_dir():
            if (item / "SKILL.md").is_file():
                names.append(item.name)
    return names


def validate_skill_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "name:" not in text or "description:" not in text:
        raise RuntimeError(f"invalid skill manifest: {path}")


def validate_skill_name(name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,90}", name):
        raise RuntimeError(f"invalid skill name: {name!r}")


def plan_skill_paths(target: Path, skill_names: list[str]) -> tuple[dict[str, Path], list[tuple[str, Path, Path]]]:
    source_root = SKILLS_ROOT
    destination_root = target / ".agents" / "skills"
    sources = {}
    for name in skill_names:
        validate_skill_name(name)
        source = source_root / name
        if not source.is_dir():
            raise FileNotFoundError(f"missing skill: {name}")
        validate_skill_file(source / "SKILL.md")
        destination = destination_root / name
        sources[name] = source
        if destination.exists():
            raise FileExistsError(
                f"refusing to overwrite existing target skill: {destination}"
            )
    plan = [(name, sources[name], destination_root / name) for name in skill_names]
    return destination_root, plan


def copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, symlinks=False)


def run_list() -> int:
    names = available_skills()
    print("Available skills:")
    for name in names:
        print(f"  {name}")
    return 0


def run_install(target: Path, selected: list[str] | None, dry_run: bool) -> int:
    names = available_skills()
    if selected:
        missing = [name for name in selected if name not in names]
        if missing:
            raise FileNotFoundError(
                f"unknown skill(s): {', '.join(missing)}. Use --list to view available names."
            )
        names = selected
    destination_root, plan = plan_skill_paths(target.resolve(), names)
    print("Install plan:")
    print(f"  target: {target.resolve()}")
    print(f"  dry-run: {dry_run}")
    for name, source, destination in plan:
        print(f"  {name}: {source.relative_to(ROOT)} -> {destination}")

    if dry_run:
        print("DRY RUN: no files copied.")
        return 0

    destination_root.mkdir(parents=True, exist_ok=True)
    for _, source, destination in plan:
        copy_tree(source, destination)
    print("Install complete.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install bundled Agent Skills into a project's `.agents/skills` directory."
    )
    parser.add_argument("--list", action="store_true", help="list bundled skills and exit")
    parser.add_argument(
        "--target",
        type=Path,
        help="target project root (defaults to no action unless --list is used)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned copy operations without modifying files",
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=None,
        metavar="NAME",
        help="install only one named skill (repeatable)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        return run_list()
    if args.target is None:
        raise SystemExit("--target is required unless --list is set")
    target = args.target.expanduser().resolve()
    return run_install(target, args.skill, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
