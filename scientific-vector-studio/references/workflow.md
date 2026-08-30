# Direct vector drawing workflow

## 1. Inspect and choose the format

Keep the source immutable and local. Make a lossless PNG working copy for TIFF inspection. Inspect actual geometry in supplied vector files; the extension alone proves nothing.

Record canvas dimensions, text/baselines, object bounds, contour landmarks, negative spaces, repeated-object counts, paint order and connector endpoints/directions. Use this measured scene across output variants.

Default to `illustrator-native` for Illustrator: paths, live text, native linear/radial gradients, opacity and vector clipping. The PowerPoint wrapper requires `portable`. For both apps derive outputs from the same scene, disclose material conversion differences and verify each.

Direct drawing is default. Do not substitute another automatic contour fitter for prohibited Image Trace. Explicit automatic-vectorization requests require agreement about the changed method.

## 2. Author semantic vectors

Build clean Bézier paths and shapes from measured landmarks, not pixel conversion. Preserve the source coordinate system and meaningful groups: subjects, chemical bonds, cells, arrows and labels. Assign stable IDs.

Draw layout/silhouettes, internal scientific linework, live text, then shading/details. Preserve irregular biological morphology and material cues. Do not regularize all cells or invent invisible features. Gradients represent soft tone, not missing fibres. Draw visible fine strokes separately.

Keep text live with explicit font, size, content and baseline. Use only local paint/clip resources. No raster payload, source bitmap, hidden reference, script or external asset may enter the output.

Native SVG declares version 1.1, not Tiny. `prepare_native_svg.py` adds IDs/version and audits; it does not add scientific geometry or automatically reproduce the image.

## 3. Compare and correct

Native preparation:

```powershell
python scripts/prepare_native_svg.py --input <authored.svg> --output <figure.illustrator.svg> --require-text
```

Portable validation:

```powershell
python scripts/validate_master_svg.py --svg <master.svg> --profile portable --require-text
```

Render locally with an available SVG renderer or target app. Compare source-sized renders:

```powershell
python scripts/compare_figure_renders.py --reference <reference.png> --candidate <candidate.png> --output-dir <comparison-dir>
```

Inspect whole layout plus detailed 100%/200% crops, especially labels, bonds, curves, arrowheads, thin fibres and shading. Use overlay/edge differences and alternating views for suspected shifts. Correct meaningful content/position errors and re-render after material changes.

Metrics and structural validation do not prove visual identity. Do not require zero pixel difference or claim an inspection that was not performed. Indeterminate texture cannot be recovered by increasing DPI.

## 4. Application review

Follow application-runtime.md. Show the authored vector working version in Illustrator without claiming final acceptance; the app need not remain empty pending every stylistic refinement. Preserve existing documents. Never use the reference or a QA PNG as delivered artwork.

Inspect native Text/Path/Gradient properties, clipping and absence of source raster objects with available tools. Preserve aspect ratio. Illustrator imports authored native vectors through the document bridge; review needs no save path. The PowerPoint wrapper keeps its save-path/licensing requirements.

## 5. Acceptance and saving

An explicit approval accepts that visual version. Record the approved version and stop unsolicited changes. Do not continue rejecting accepted texture differences because of an old exact-pixel rule. Approval does not establish unperformed technical tests, saved files or raster-to-vector conversion.

Open/unsaved is a valid review state. Save only on request or to an approved path, then verify the file. Report specific real blockers, not a routine failure footer. Use the Skill's signoff on accepted handoff.
