from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import yaml

from .models import PublicSnapshot, SchemaError, exact_keys, public_id, public_text

ROLE_ASSETS = Path(__file__).parent / "renderer" / "roles"


def role_svg(name: str) -> str:
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+\.svg", name):
        raise SchemaError("invalid role icon")
    path = ROLE_ASSETS / name
    if path.is_symlink() or not path.is_file():
        raise SchemaError("role icon must be an existing local approved SVG")
    try:
        text = path.read_text(encoding="utf-8")
        root = ElementTree.fromstring(text)
        if not root.tag.endswith("svg") or "<!" in text:
            raise ValueError()
        for node in root.iter():
            if node.tag.split("}")[-1] in {"script", "foreignObject", "image", "metadata"}:
                raise ValueError()
            for key, value in node.attrib.items():
                key = key.split("}")[-1].lower()
                if key.startswith("on") or key in {"href", "src"} or re.search(r"url\(\s*[^#]", value):
                    raise ValueError()
        return text
    except (OSError, ValueError, ElementTree.ParseError) as exc:
        raise SchemaError("invalid local role SVG") from exc


def parse_snapshot(raw: Any) -> PublicSnapshot:
    return PublicSnapshot.from_dict(raw)


def load_snapshot(path: str | Path) -> PublicSnapshot:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SchemaError("snapshot unavailable or malformed") from exc
    return parse_snapshot(raw)


def validate_config(raw: Any) -> dict[str, Any]:
    config = exact_keys(raw, {"schema_version", "application", "source", "freshness_seconds", "approved_metrics", "roles"}, "configuration")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise SchemaError("unsupported configuration version")
    app = exact_keys(config["application"], {"title", "subtitle", "bind_address", "path_display"}, "application configuration")
    if app["title"] != "Agent Workflow Monitor" or app["subtitle"] != "Read-only observability for multi-agent workstreams":
        raise SchemaError("invalid public product identity")
    if app["bind_address"] not in {"127.0.0.1", "localhost"}:
        raise SchemaError("application must bind to loopback")
    if app["path_display"] not in {"hidden", "basename", "configured-label"}:
        raise SchemaError("invalid path display mode")
    source = config["source"]
    if not isinstance(source, dict) or set(source) not in ({"adapter", "path"}, {"adapter", "path", "label"}):
        raise SchemaError("invalid source configuration")
    if source["adapter"] != "snapshot" or not isinstance(source["path"], str) or not source["path"]:
        raise SchemaError("v0.1 application requires a complete snapshot source")
    if "label" in source:
        public_text(source["label"], "source label", limit=80)
    freshness = exact_keys(config["freshness_seconds"], {"activity", "host"}, "freshness configuration")
    if any(type(value) is not int or value < 1 for value in freshness.values()):
        raise SchemaError("invalid freshness window")
    metrics = config["approved_metrics"]
    if not isinstance(metrics, list) or any(not isinstance(item, str) for item in metrics) or len(metrics) != len(set(metrics)) or not set(metrics) <= {"context_usage", "storage_usage", "host"}:
        raise SchemaError("invalid approved metrics")
    roles = config["roles"]
    if not isinstance(roles, dict) or not roles:
        raise SchemaError("role registry is empty")
    for key, value in roles.items():
        public_id(key, "role key")
        row = exact_keys(value, {"label", "icon"}, "role")
        public_text(row["label"], "role label", limit=80)
        role_svg(row["icon"])
    return config


def load_config(path: str | Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SchemaError("configuration unavailable or malformed") from exc
    return validate_config(raw)


def source_path(config: dict, config_path: Path) -> Path:
    """Resolve relative inputs beside the selected configuration, never CWD."""
    path = Path(config["source"]["path"])
    return path if path.is_absolute() else config_path.resolve().parent / path
