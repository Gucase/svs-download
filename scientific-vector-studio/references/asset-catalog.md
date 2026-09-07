# Scientific asset catalog

The machine-readable catalog is `assets/scientific-library/manifest.json`. Asset SVGs use a `0 0 240 180` viewBox, stable semantic IDs and transparent backgrounds.

## Metadata contract

Each entry contains:

- `id`, `name_zh`, `name_en`, `aliases`, `category` and `file` for discovery;
- `views` for available orientation;
- `editable_parts` for semantic editing targets;
- `parameters` for safe customizations;
- `connection_anchors` as named coordinates in the asset viewBox;
- `illustrator_verified`, `powerpoint_verified` and `review_status` as truthful review evidence.

Allowed review states are `candidate`, `approved`, `needs_revision` and `deprecated`. Never infer app verification from schema validation or a PNG render.

## Library contents

- Connectors: straight, curved, bidirectional, inhibition, dashed and cyclic arrows.
- Labware: 20 common vessels, tubes, liquid-handling and culture items.
- Instruments: 15 common imaging, culture, sterilization, separation, electrophoresis, measurement and storage instruments.
- Biology: 11 reusable cell, organelle and molecular-structure assets.
- Medical: 8 generic anatomy and tissue-section assets.

The catalog contains 60 assets. Availability does not imply that every asset has passed Illustrator, PowerPoint or user review; inspect its metadata before use.

Use `python scripts/list_assets.py --all` to inspect availability. Use `python scripts/validate_asset.py --library assets/scientific-library` before distribution.

## Adding an asset

Create an original generic design from functional knowledge and geometric primitives. Do not trace a vendor image, BioRender asset, paper figure or user reference into the shared library. Add required semantic groups and anchors, validate, create a review render, inspect in both supported applications when claimed, and only then change `review_status` to `approved`.
