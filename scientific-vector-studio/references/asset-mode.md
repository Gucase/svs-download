# Scientific Asset Drawing mode

Use this mode for a text brief requesting common biomedical, biological or laboratory objects. It is separate from Reference Reconstruction.

## Routing

- A supplied reference that must be matched uses Reference Reconstruction, even if some objects resemble library assets.
- A text request such as “画一个烧杯、离心机和三个离心管并用箭头连接” uses this mode.
- A redesign may combine both only when the user explicitly permits generic replacement. Preserve which elements came from the reference and which came from the library.

## Workflow

1. Parse the brief into objects, labels, relationships, requested app and scientific context.
2. Run `python scripts/list_assets.py --query <term>` or filter by category. Use aliases from the manifest rather than guessing filenames.
3. Inspect each candidate SVG and its metadata. Prefer `approved`; use `candidate` only for review and disclose that status.
4. Compose a coherent scene. Keep object scale, perspective, stroke weight, label hierarchy and connector endpoints consistent. An asset is a component, not a finished mechanism figure.
5. Validate the composition with `validate_master_svg.py` and each library entry with `validate_asset.py`. Render and inspect at normal size and 200%.
6. Open the authored vector in the already-open Illustrator or PowerPoint workflow described in `application-runtime.md`. Confirm object editability separately from appearance.
7. Ask the user to review scientific meaning and visual style. Do not add a newly drawn object to the maintained library until it has the review status required by `asset-catalog.md`.

For realistic laboratory equipment, follow `realistic-instrument-standards.md`. Prefer its single-pass construction route when the user asks for faster output.

## Composition and entitlement

The unit of work is the completed canvas/brief, not the number of assets. Reuse one stable UsageId for additions, rearrangements, corrections and Illustrator/PowerPoint renditions of the same canvas. A materially new brief or separate canvas is a new generation during the trial.

This mode includes two free unique canvases/briefs and uses the `scientific_asset_drawing` feature mode at reservation time. Reference Reconstruction has its own one-figure allowance. One valid machine-bound buyout authorization unlocks unlimited use of both modes.

## Parametric adaptation

Prefer changes that preserve the asset's identity: fill/stroke colors, liquid color, opacity, label, orientation, uniform scale and repeated count. Do not stretch instruments non-uniformly, remove defining components or recolor warning/status states in a way that changes meaning. For unsupported geometry changes, author a new candidate variant instead of distorting the approved master.
