#!/usr/bin/env python3
"""Prepare authored vectors for Illustrator. Never traces, rasterizes or opens apps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from validate_master_svg import DRAWABLE, local_name, validate


def prepare(source: Path, output: Path, require_text: bool = False) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError("Use a separate output path; preserve the authored source.")
    if output.exists():
        raise ValueError("Output already exists; choose a new versioned output path.")
    source_bytes = source.read_bytes()
    if b'<!DOCTYPE' in source_bytes.upper() or b'<!ENTITY' in source_bytes.upper():
        raise ValueError('DTD/entity declarations are not accepted in authored SVG.')
    root = ET.fromstring(source_bytes)
    root.set("version", "1.1")
    root.attrib.pop("baseProfile", None)
    ids = {node.get("id") for node in root.iter() if node.get("id")}
    index = 1
    for node in root.iter():
        if local_name(node.tag) in DRAWABLE | {"text", "linearGradient", "radialGradient", "clipPath"} and not node.get("id"):
            while "svs-native-%04d" % index in ids:
                index += 1
            node.set("id", "svs-native-%04d" % index)
            ids.add(node.get("id"))
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create prevents accidental replacement of an existing approved version.
    with output.open("xb") as handle:
        # Illustrator 30.x rejects ElementTree's single-quoted XML declaration
        # on the regression fixture. SVG is UTF-8 without that optional header.
        ET.ElementTree(root).write(handle, encoding="utf-8", xml_declaration=False)
    report = validate(output, require_text, "illustrator-native")
    if report["status"] != "PASS":
        output.unlink()  # Only the new file created in this call is removed.
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--require-text", action="store_true")
    args = parser.parse_args()
    try:
        report = prepare(args.input, args.output, args.require_text)
    except (OSError, ValueError, ET.ParseError) as exc:
        report = {"status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
