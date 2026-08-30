# v0.3.0-pilot verification scope

The Illustrator integration and SVG contract checker were independently reimplemented for this revision. The previous geometry-cache and incremental replay modules are not included. Package dependencies and PowerPoint implementation remain unchanged.

Checks performed for this revision:

- Skill metadata validation and PowerShell syntax parsing.
- Seven Python unit tests for native/portable SVG validation, safe resources, source preservation, stable preparation and live text.
- Eight mocked document-bridge scenarios covering paint order, affine fit, review mode, failed transfer cleanup, locked layers and protected exports. These are not live Illustrator tests.
- The existing approved EGCG-SIS scene was preserved. Structural validation counted 877 SVG geometry elements and 46 text elements. The preparation change affects serialization/version/IDs, not scientific geometry.
- A separate Illustrator review import completed and a PNG preview was exported. The bridge reported 907 native paths and 46 text frames and rejected raster/placed reference objects. Its overall preview was visually checked against the approved version.

The SVG preparer now omits an optional XML declaration that caused an Illustrator 30.x import failure. Modal importer notices are suppressed only during import, with the previous setting restored afterward.

An additional exhaustive per-object comparison stalled and was stopped; it is not recorded as passed. Native append-mode rendering, all font substitutions, all gradient/clipping edge cases and every supported Office version are not certified by these checks. Keep reviewing each actual target app. An image preview is not a substitute for editable source vectors, and this report is not a claim of pixel-perfect identity or universal code originality.
