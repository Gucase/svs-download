#!/usr/bin/env python3
"""Validate the SVS scientific asset manifest and portable SVG structure."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from validate_master_svg import local_name, validate

REQUIRED = {"id", "name_zh", "name_en", "aliases", "category", "file", "views", "editable_parts", "parameters", "connection_anchors", "illustrator_verified", "powerpoint_verified", "review_status"}
STATUSES = {"candidate", "approved", "needs_revision", "deprecated"}
FORBIDDEN = {"image", "filter", "mask", "script", "foreignObject", "use"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "scientific-library")
    args = parser.parse_args()
    manifest_path = args.library / "manifest.json"
    errors, reports, seen = [], [], set()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    for item in manifest.get("assets", []):
        missing = sorted(REQUIRED - set(item))
        if missing:
            errors.append(f"{item.get('id', '?')}: missing metadata {missing}")
            continue
        if item["id"] in seen:
            errors.append(f"duplicate asset id: {item['id']}")
        seen.add(item["id"])
        if item["review_status"] not in STATUSES:
            errors.append(f"{item['id']}: invalid review_status")
        svg_path = args.library / item["file"]
        report = validate(svg_path, False, "portable")
        reports.append({"id": item["id"], "status": report["status"], "geometry_count": report["geometry_count"]})
        if report["status"] != "PASS":
            errors.extend(f"{item['id']}: {message}" for message in report["errors"])
            continue
        root = ET.fromstring(svg_path.read_bytes())
        element_ids = {node.get("id") for node in root.iter() if node.get("id")}
        node_types = {local_name(node.tag) for node in root.iter()}
        bad = sorted(node_types & FORBIDDEN)
        if bad:
            errors.append(f"{item['id']}: forbidden nodes {bad}")
        for part in item["editable_parts"]:
            if part not in element_ids:
                errors.append(f"{item['id']}: editable part id not found: {part}")
        for name, point in item["connection_anchors"].items():
            if not isinstance(point, list) or len(point) != 2 or not all(isinstance(value, (int, float)) for value in point):
                errors.append(f"{item['id']}: invalid anchor {name}")
    expected = manifest.get("asset_count")
    if expected != len(manifest.get("assets", [])):
        errors.append("asset_count does not match manifest assets")
    print(json.dumps({"status": "FAIL" if errors else "PASS", "asset_count": len(seen), "errors": errors, "reports": reports}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
