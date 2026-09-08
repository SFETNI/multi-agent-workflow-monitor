from __future__ import annotations

import json
import zipfile
from pathlib import Path

from PIL import Image

from audit_public_candidate import audit, load_allowlist
from stage_release import stage
from make_release_archive import build

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_matches_explicit_allowlist(tmp_path):
    fresh = stage(ROOT, load_allowlist(ROOT / "release_allowlist.txt"), tmp_path / "candidate")
    result = audit(fresh, ROOT / "release_allowlist.txt")
    assert result["status"] == "PASS", result


def test_release_scanner_rejects_unallowlisted_file(tmp_path):
    candidate = tmp_path / "candidate"; candidate.mkdir()
    (candidate / "README.md").write_text("safe", encoding="utf-8")
    (candidate / "runtime.log").write_text("runtime", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"; allowlist.write_text("README.md\n", encoding="utf-8")
    result = audit(candidate, allowlist)
    assert result["status"] == "FAIL" and result["issue_count"] >= 2


def test_release_archive_members_and_hashes_match_manifest(tmp_path):
    output = tmp_path / "candidate.zip"; manifest_path = tmp_path / "manifest.json"
    result = build(ROOT, ROOT / "release_allowlist.txt", output, manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert names == [item["path"] for item in manifest["members"]]
        for item in manifest["members"]:
            import hashlib
            assert hashlib.sha256(archive.read(item["path"])).hexdigest() == item["sha256"]
    assert result == manifest


def test_release_archive_is_deterministic(tmp_path):
    first = tmp_path / "first.zip"; second = tmp_path / "second.zip"
    one = build(ROOT, ROOT / "release_allowlist.txt", first, tmp_path / "one.json")
    two = build(ROOT, ROOT / "release_allowlist.txt", second, tmp_path / "two.json")
    assert one["archive_sha256"] == two["archive_sha256"] and first.read_bytes() == second.read_bytes()


def test_media_dimensions_and_animation_receipt():
    media = ROOT / "demo" / "media"
    with Image.open(media / "public_monitor_1920x1080.png") as image:
        assert image.size == (1920, 1080)
    with Image.open(media / "public_monitor_1440x1000.png") as image:
        assert image.size == (1440, 1000)
    with Image.open(media / "public_monitor.gif") as image:
        assert image.size == (1600, 1239) and image.n_frames == 104 and image.info.get("loop") == 0


def test_four_skills_have_valid_frontmatter_and_resolved_links():
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert len(skills) == 4
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\nname: " + skill.parent.name + "\n")
        assert "\ndescription: " in text.split("---", 2)[1]
        for relative in __import__("re").findall(r"\]\(([^)]+)\)", text):
            assert (skill.parent / relative).is_file(), (skill, relative)
