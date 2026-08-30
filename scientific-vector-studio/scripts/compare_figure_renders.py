#!/usr/bin/env python3
"""Create alignment QA artifacts from reference and rendered figure images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps


def ink_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    ink = np.any(rgb < 245, axis=2)
    ys, xs = np.nonzero(ink)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def normalized_bbox(bbox: tuple[int, int, int, int] | None, width: int, height: int):
    if bbox is None:
        return None
    x0, y0, x1, y1 = bbox
    return [round(x0 / width, 5), round(y0 / height, 5), round(x1 / width, 5), round(y1 / height, 5)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a rendered vector figure with its raster reference")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    reference_path = Path(args.reference).resolve()
    candidate_path = Path(args.candidate).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    reference = Image.open(reference_path).convert("RGB")
    candidate_original = Image.open(candidate_path).convert("RGB")
    candidate = ImageOps.pad(candidate_original, reference.size, method=Image.Resampling.LANCZOS, color="white")
    candidate.save(output_dir / "candidate-normalized.png")

    overlay = Image.blend(reference, candidate, 0.5)
    overlay.save(output_dir / "overlay-50.png")
    ImageChops.difference(reference, candidate).save(output_dir / "absolute-difference.png")

    reference_edges = reference.filter(ImageFilter.FIND_EDGES).convert("L")
    candidate_edges = candidate.filter(ImageFilter.FIND_EDGES).convert("L")
    ImageChops.difference(reference_edges, candidate_edges).save(output_dir / "edge-difference.png")

    gap = 20
    side_by_side = Image.new("RGB", (reference.width * 2 + gap, reference.height), "white")
    side_by_side.paste(reference, (0, 0))
    side_by_side.paste(candidate, (reference.width + gap, 0))
    side_by_side.save(output_dir / "side-by-side.png")

    ref_array = np.asarray(reference, dtype=np.int16)
    cand_array = np.asarray(candidate, dtype=np.int16)
    mae = float(np.abs(ref_array - cand_array).mean() / 255.0)
    ref_bbox = normalized_bbox(ink_bbox(reference), reference.width, reference.height)
    cand_bbox = normalized_bbox(ink_bbox(candidate), reference.width, reference.height)
    bbox_delta = None
    if ref_bbox and cand_bbox:
        bbox_delta = [round(cand_bbox[i] - ref_bbox[i], 5) for i in range(4)]

    report = {
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "reference_size": list(reference.size),
        "candidate_original_size": list(candidate_original.size),
        "reference_ink_bbox_normalized": ref_bbox,
        "candidate_ink_bbox_normalized": cand_bbox,
        "candidate_minus_reference_bbox_delta": bbox_delta,
        "normalized_mean_absolute_pixel_difference": round(mae, 6),
        "review_required": True,
        "review_note": "Pixel difference is diagnostic only. Approve layout by anchors, baselines, arrow endpoints, panel bounds, and scientific fidelity.",
    }
    (output_dir / "comparison-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, **report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
