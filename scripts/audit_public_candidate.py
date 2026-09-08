#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path, PurePosixPath

TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".jsonl", ".md", ".py", ".toml", ".yaml", ".yml", ".txt", ".svg"}
MEDIA_SUFFIXES = {".png", ".gif"}
RUNTIME_NAMES = {".env", "secrets.toml", ".pytest_cache", "__pycache__", "runtime", "state", ".local"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z"}
HTTP_PREFIX = "http" + "://"
ALLOWED_URLS = {HTTP_PREFIX + "127.0.0.1:8765/", HTTP_PREFIX + "www.w3.org/2000/svg"}


def allowed_url(value: str) -> bool:
    trimmed = value.rstrip("/\"")
    if trimmed in {item.rstrip("/\"") for item in ALLOWED_URLS}:
        return True
    return re.fullmatch(HTTP_PREFIX + r"127\.0\.0\.1(?::\d{1,5})?(?:/.*)?", value) is not None


def load_allowlist(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if lines != sorted(set(lines)):
        raise ValueError("allowlist must be unique and sorted")
    for line in lines:
        item = PurePosixPath(line)
        if item.is_absolute() or ".." in item.parts or line.endswith("/"):
            raise ValueError("allowlist contains an unsafe member")
    return lines


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text_issues(relative: str, text: str, external_terms: tuple[str, ...]) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    slash = "/"
    unix_pattern = re.compile(slash + r"(?:home|Users|mnt|private|var/tmp)/[^\s<>'\"`]+", re.I)
    windows_pattern = re.compile(r"\b[A-Za-z]:\\[^\s<>'\"`]+")
    uuid_pattern = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    credential_pattern = re.compile(r"(?:api[_-]?key|secret|bearer|password|access[_-]?token)\s*[:=]\s*[^\s,}\]]+", re.I)
    url_pattern = re.compile(r"https?://[^\s<>'\"`)]+", re.I)
    patterns = (
        ("absolute_unix_path", unix_pattern), ("absolute_windows_path", windows_pattern),
        ("uuid", uuid_pattern), ("credential_assignment", credential_pattern),
    )
    for category, pattern in patterns:
        if pattern.search(text):
            issues.append((category, relative))
    for match in ip_pattern.finditer(text):
        if match.group(0) != "127.0.0.1":
            issues.append(("network_address", relative))
            break
    for match in url_pattern.finditer(text):
        if not allowed_url(match.group(0)):
            issues.append(("remote_url", relative))
            break
    source_map_marker = "source" + "MappingURL"
    if source_map_marker in text or relative.endswith(".map"):
        issues.append(("source_map", relative))
    parent_posix = "." + "./"
    parent_windows = "." + "." + chr(92)
    if parent_posix in text or parent_windows in text:
        issues.append(("parent_traversal", relative))
    lowered = text.casefold()
    for term in external_terms:
        if term.casefold() in lowered:
            issues.append(("external_denylist", relative))
            break
    return issues


def _media_issues(path: Path, relative: str) -> list[tuple[str, str]]:
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.format not in {"PNG", "GIF"}:
                return [("unsupported_media", relative)]
            allowed_info = {"background", "duration", "extension", "loop", "transparency", "version"}
            extra = set(image.info) - allowed_info
            if extra:
                return [("media_metadata", relative)]
            if "extension" in image.info and image.info["extension"][0] != b"NETSCAPE2.0":
                return [("media_metadata", relative)]
            if image.width < 1 or image.height < 1:
                return [("invalid_media", relative)]
    except Exception:
        return [("invalid_media", relative)]
    return []


def audit(root: Path, allowlist_path: Path, *, denylist_path: Path | None = None) -> dict:
    root = root.resolve()
    allowlist = load_allowlist(allowlist_path)
    external_terms: tuple[str, ...] = ()
    if denylist_path is not None:
        external_terms = tuple(line.strip() for line in denylist_path.read_text(encoding="utf-8").splitlines() if line.strip())
    issues: list[tuple[str, str]] = []
    actual = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(("symlink", relative))
            continue
        if not path.is_file():
            if path.name in RUNTIME_NAMES:
                issues.append(("runtime_artifact", relative))
            continue
        actual.append(relative)
        if path.name in RUNTIME_NAMES or path.suffix.lower() in {".log", ".pid", ".pyc"}:
            issues.append(("runtime_artifact", relative))
        if path.suffix.lower() in ARCHIVE_SUFFIXES:
            issues.append(("embedded_archive", relative))
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore", ".gitattributes", "LICENSE"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                issues.append(("invalid_text", relative))
            else:
                issues.extend(_text_issues(relative, text, external_terms))
        elif path.suffix.lower() in MEDIA_SUFFIXES:
            issues.extend(_media_issues(path, relative))
        else:
            issues.append(("unsupported_binary", relative))
    missing = sorted(set(allowlist) - set(actual))
    extra = sorted(set(actual) - set(allowlist))
    issues.extend(("missing_allowlisted_file", item) for item in missing)
    issues.extend(("file_not_allowlisted", item) for item in extra)
    unique = sorted(set(issues))
    categories: dict[str, int] = {}
    for category, _relative in unique:
        categories[category] = categories.get(category, 0) + 1
    return {
        "status": "PASS" if not unique else "FAIL",
        "files_checked": len(actual),
        "allowlisted_files": len(allowlist),
        "issue_count": len(unique),
        "categories": categories,
        "issues": [{"category": category, "path": relative} for category, relative in unique],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an exact public candidate without reproducing matching values.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--denylist", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--staged", action="store_true", help="audit a fresh allowlisted copy of a development tree")
    args = parser.parse_args()
    if args.staged:
        from stage_release import stage
        with tempfile.TemporaryDirectory(prefix="awm-audit-") as temporary:
            root = stage(args.root, load_allowlist(args.allowlist), Path(temporary) / "candidate")
            result = audit(root, args.allowlist, denylist_path=args.denylist)
    else:
        result = audit(args.root, args.allowlist, denylist_path=args.denylist)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['status']} files={result['files_checked']} issues={result['issue_count']}")
        for category, count in sorted(result["categories"].items()):
            print(f"{category}: {count}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
