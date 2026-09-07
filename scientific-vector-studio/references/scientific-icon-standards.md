# Scientific icon standards

## Scientific recognizability

An icon should remain identifiable without its label. Include the minimum defining components and arrange them plausibly: a centrifuge needs a lid/rotor and controls; a thermocycler needs a heated lid and sample block; a micropipette needs plunger, volume body, shaft and disposable tip. Do not add decorative parts that imply nonexistent function.

Use generic equipment architecture. Never add manufacturer silhouettes, logos, model numbers, protected UI layouts or false certification marks. Exact experimental setup, scale and safety details remain the user's responsibility.

## Drawing system

- Base viewBox: `0 0 240 180`; transparent canvas.
- Use clean closed paths, rounded joins/caps and stable IDs. Prefer 2.5–3 px outlines at master scale.
- Use restrained two- or three-tone shading to describe form. Solid-fill portable masters are preferred; native gradients may be added in a figure when the target workflow supports and needs them.
- Keep functional parts in semantic groups and repeated parts as separate objects. Text is optional and must remain live when present.
- Do not use raster nodes, filters, masks, scripts, event handlers, external resources or font outlines presented as live text.

## Review gates

1. **Structure:** schema, viewBox, IDs, forbidden nodes, semantic parts and anchors pass automated checks.
2. **Visual:** normal-size and 200% renders have no broken paths, accidental overlaps, clipping or inconsistent strokes.
3. **Scientific:** a reviewer can identify the object and its defining parts; orientation and relationships are plausible.
4. **Application:** actual Illustrator and PowerPoint imports remain editable before either verification field becomes true.
5. **User:** visual acceptance is recorded before promotion from `candidate` to `approved`.

Automated validation does not certify scientific accuracy or originality by itself.

For a photo-like instrument illustration, the restrained icon rules above are insufficient by themselves. Read `realistic-instrument-standards.md` and use layered vector materials, physical depth and a credible exterior silhouette while retaining semantic editability.
