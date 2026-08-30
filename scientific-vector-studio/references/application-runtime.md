# Application workflow

The user opens the application and document. Do not launch/restart it, force focus or alter unrelated artwork. A new vector review tab is permitted. The bridge may close only the temporary SVG document it created for a transfer, never a pre-existing user document. If using Computer Use, follow that skill instead of mixing direct UI automation in the same turn.

## Illustrator

Windows Illustrator 2026 / 30.x is the tested host. The bridge requires Windows PowerShell 5.1 (`powershell.exe`), Python and an already-running Illustrator document. It does not install Adobe products or implement macOS live control.

1. Directly author and locally compare the scientific scene. Use SVG 1.1 with native paths, live text, optional gradients/opacity and vector-only clipping. No raster or automatic tracing.
2. Validate/prepare with `prepare_native_svg.py --input <authored.svg> --output <new.svg>`. Add `--require-text` when the reference contains labels. Preserve the authored source.
3. Run `place_svg_in_illustrator.ps1 -InputSvg <new.svg> -Mode review -UsageId <stable-figure-id>` for a separate native vector tab. Use `-Mode append` for the current canvas, with Placement and MaxWidthFraction/MaxHeightFraction controlling the uniform artboard fit. Existing content remains untouched; rerunning append adds a new version group, so inspect before retrying an ambiguous interruption.
4. The wrapper reserves/commits entitlement itself. Reuse the same UsageId across revisions and apps. `-DryRun` validates without app access, charging or creating output. Per-object delayed playback is not supported.
5. Inspect actual native paths/text, shading, clipping, strokes and layout. The bridge temporarily disables modal import notices to avoid COM waits, then immediately restores the interaction setting. This is not permission to ignore conversion defects: check fonts, clipping and shading in the actual output. The bridge rejects imported raster/linked items and lost text; successful import is not a visual acceptance certificate. A CMYK target may change RGB colors; retain the target profile and disclose meaningful differences.
6. OutputAi and OutputPng are optional, explicit, non-existing destinations with existing parent folders. With append these exports cover the target document/artboard, including existing artwork. Omit them when saving was not requested. An export failure is reported separately from successful editable output, which remains available.
7. User review accepts appearance. Report actual save status without a routine rejection/unsaved footer.

Alternatively, use supported native app controls to open the prepared SVG. Reserve/commit/cancel with `native_usage.ps1` only for this manual route. Do not call both entitlement routes for the same operation. Opening authored SVG is vector import, not Image Trace.

## PowerPoint

The existing `place_svg_in_powerpoint.ps1` / `prepare_powerpoint_assets.py` workflow separates portable geometry from text and recreates native text boxes in an open presentation. Use RequireEditableGeometry when individual native shapes are mandatory; Office conversion varies by version.

Use the same measured scene, not a raster screenshot or an independently redesigned figure. Gradients/clipping require supported native Office reconstruction and actual inspection; the portable wrapper does not automatically certify them. Obtain agreement for material conversion differences. Preserve previously approved PowerPoint artwork during unrelated Illustrator backend changes.

## Verification and errors

Compare source and result at full view and in detailed crops. Test object editability independently of image similarity. On failure remove only the current operation's newly created objects; never close or delete a user document. If COM disconnects after submission, inspect the app before retrying because completion may be uncertain.
