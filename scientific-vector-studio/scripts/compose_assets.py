#!/usr/bin/env python3
"""Compose SVS library assets into an editable portable SVG contact row or grid."""
import argparse
import copy
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)


def lname(tag):
    return tag.split("}")[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "scientific-library")
    parser.add_argument("--asset", action="append", required=True, help="Asset id; repeat for more objects")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--cell-width", type=float, default=280)
    parser.add_argument("--cell-height", type=float, default=230)
    parser.add_argument("--labels", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((args.library / "manifest.json").read_text(encoding="utf-8"))
    catalog = {item["id"]: item for item in manifest["assets"]}
    missing = [name for name in args.asset if name not in catalog]
    if missing:
        raise SystemExit("Unknown asset ids: " + ", ".join(missing))
    columns = max(1, args.columns)
    rows = math.ceil(len(args.asset) / columns)
    root = ET.Element(f"{{{NS}}}svg", {"version": "1.1", "viewBox": f"0 0 {columns * args.cell_width:g} {rows * args.cell_height:g}"})
    background = ET.SubElement(root, f"{{{NS}}}rect", {"id": "review-background", "x": "0", "y": "0", "width": f"{columns * args.cell_width:g}", "height": f"{rows * args.cell_height:g}", "fill": "#F7FAFB"})
    for index, asset_id in enumerate(args.asset):
        item = catalog[asset_id]
        source = ET.fromstring((args.library / item["file"]).read_bytes())
        col, row = index % columns, index // columns
        offset_x, offset_y = col * args.cell_width + 20, row * args.cell_height + 10
        group = ET.SubElement(root, f"{{{NS}}}g", {"id": f"instance-{index+1:02d}-{asset_id}", "transform": f"translate({offset_x:g} {offset_y:g})"})
        for node in list(source):
            cloned = copy.deepcopy(node)
            for desc in cloned.iter():
                if desc.get("id"):
                    desc.set("id", f"i{index+1:02d}-{desc.get('id')}")
            group.append(cloned)
        if args.labels:
            ET.SubElement(root, f"{{{NS}}}text", {"id": f"label-{index+1:02d}", "x": f"{offset_x + 120:g}", "y": f"{offset_y + 202:g}", "text-anchor": "middle", "font-family": "Arial, sans-serif", "font-size": "15", "font-weight": "700", "fill": "#24363D"}).text = f"{index+1:02d}  {item['name_zh']} / {item['name_en']}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit("Output exists; choose a new path")
    ET.ElementTree(root).write(args.output, encoding="utf-8", xml_declaration=False)
    print(json.dumps({"status": "PASS", "output": str(args.output.resolve()), "asset_count": len(args.asset)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
