#!/usr/bin/env python3
"""List SVS scientific assets by id, name, alias, category or review state."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "scientific-library")
    parser.add_argument("--query", default="")
    parser.add_argument("--category")
    parser.add_argument("--status")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    data = json.loads((args.library / "manifest.json").read_text(encoding="utf-8"))
    needle = args.query.casefold().strip()
    rows = []
    for asset in data["assets"]:
        haystack = " ".join([asset["id"], asset["name_zh"], asset["name_en"], *asset["aliases"]]).casefold()
        if needle and needle not in haystack:
            continue
        if args.category and asset["category"] != args.category:
            continue
        if args.status and asset["review_status"] != args.status:
            continue
        rows.append(asset if args.all else {key: asset[key] for key in ("id", "name_zh", "name_en", "category", "review_status", "file")})
    print(json.dumps({"count": len(rows), "assets": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
