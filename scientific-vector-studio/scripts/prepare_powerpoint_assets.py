#!/usr/bin/env python3
"""Split a Master SVG into text-free vector geometry and a live-text manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
STYLE_KEYS = {
    "fill", "font-family", "font-size", "font-weight", "font-style",
    "text-anchor", "opacity", "text-decoration",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def number(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    match = NUMBER_RE.search(value)
    return float(match.group(0)) if match else default


def style_map(value: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in (value or "").split(";"):
        if ":" in item:
            key, raw = item.split(":", 1)
            result[key.strip()] = raw.strip()
    return result


def presentation(node: ET.Element, inherited: dict[str, str]) -> dict[str, str]:
    current = dict(inherited)
    current.update({key: value for key, value in style_map(node.get("style")).items() if key in STYLE_KEYS})
    for key in STYLE_KEYS:
        if node.get(key) is not None:
            current[key] = str(node.get(key))
    return current


def rotation_of(node: ET.Element) -> float:
    transform = node.get("transform", "")
    match = re.search(r"rotate\(\s*([-+0-9.eE]+)", transform)
    return float(match.group(1)) if match else 0.0


def text_content(node: ET.Element) -> str:
    tspans = [child for child in list(node) if local_name(child.tag) == "tspan"]
    if not tspans:
        return "".join(node.itertext()).strip()
    lines = []
    if (node.text or "").strip():
        lines.append((node.text or "").strip())
    for child in tspans:
        value = "".join(child.itertext()).strip()
        if value:
            lines.append(value)
    return "\n".join(lines)


def collect_text(node: ET.Element, inherited: dict[str, str], output: list[dict]) -> None:
    current = presentation(node, inherited)
    if local_name(node.tag) == "text":
        content = text_content(node)
        if content:
            output.append({
                "id": node.get("id") or f"text-{len(output) + 1}",
                "content": content,
                "x": number(node.get("x")),
                "y": number(node.get("y")),
                "font_family": current.get("font-family", "Arial").strip("'\""),
                "font_size": number(current.get("font-size"), 12.0),
                "font_weight": current.get("font-weight", "normal"),
                "font_style": current.get("font-style", "normal"),
                "fill": current.get("fill", "#000000"),
                "text_anchor": current.get("text-anchor", "start"),
                "opacity": number(current.get("opacity"), 1.0),
                "rotation": rotation_of(node),
            })
        return
    for child in list(node):
        collect_text(child, current, output)


def remove_text(parent: ET.Element) -> None:
    for child in list(parent):
        if local_name(child.tag) == "text":
            parent.remove(child)
        else:
            remove_text(child)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare SVG geometry and live text for PowerPoint.")
    parser.add_argument("--input-svg", required=True, type=Path)
    parser.add_argument("--geometry-svg", required=True, type=Path)
    parser.add_argument("--text-json", required=True, type=Path)
    args = parser.parse_args()

    input_svg = args.input_svg.resolve()
    tree = ET.parse(input_svg)
    root = tree.getroot()
    view_box_values = [float(v) for v in re.split(r"[\s,]+", (root.get("viewBox") or "").strip()) if v]
    if len(view_box_values) != 4 or view_box_values[2] <= 0 or view_box_values[3] <= 0:
        raise ValueError("Master SVG requires a valid viewBox")

    texts: list[dict] = []
    collect_text(root, {}, texts)
    geometry_root = deepcopy(root)
    remove_text(geometry_root)
    geometry_root.set("data-scientific-vector-studio", "geometry-only")

    args.geometry_svg.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(geometry_root).write(args.geometry_svg, encoding="utf-8", xml_declaration=True)
    payload = {
        "schema_version": "1.0",
        "source_svg": str(input_svg),
        "view_box": view_box_values,
        "text_elements": texts,
    }
    args.text_json.parent.mkdir(parents=True, exist_ok=True)
    args.text_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "geometry_svg": str(args.geometry_svg.resolve()), "text_json": str(args.text_json.resolve()), "live_text_count": len(texts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"POWERPOINT_ASSET_ERROR|{exc}", file=sys.stderr)
        raise SystemExit(1)
