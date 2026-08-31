# v0.4.0-pilot verification scope

## Buyout update (2026-08-31)

The licensing-only update replaces credit issuance/spending and the online client with a three-figure trial and CNY 39 signed unlimited `.svslicense` authorization. Historical ledger records are not deleted or silently converted. Drawing implementations and existing illustration files are unchanged.

Checks: 23 Python Skill tests (including 16 authorization tests) and 7 local owner-tool tests passed. Coverage includes trial reservations/cancellation, same-figure reuse, 100 consecutive post-buyout generations at zero cost, rejection of forged/altered files, revalidation of saved signatures, idempotent import, retirement of old credit issuance/activation and preservation of historical records. The 100-generation exercise is a test sample, not a product limit: the authorization has no balance, usage cap or expiry.

An isolated Windows PowerShell 5.1 smoke test generated a signed file using a temporary encrypted private key, imported it into a temporary client/ledger, and confirmed unlimited status. A legacy online config did not cause a network request. No production private key or customer license was used. Live Illustrator/PowerPoint rendering was not rerun for this licensing-only change.

## Original v0.3.0 drawing verification

The Illustrator integration and SVG contract checker were independently reimplemented for this revision. The previous geometry-cache and incremental replay modules are not included. Package dependencies and PowerPoint implementation remain unchanged.

Checks performed for this revision:

- Skill metadata validation and PowerShell syntax parsing.
- Seven Python unit tests for native/portable SVG validation, safe resources, source preservation, stable preparation and live text.
- Eight mocked document-bridge scenarios covering paint order, affine fit, review mode, failed transfer cleanup, locked layers and protected exports. These are not live Illustrator tests.
- The existing approved EGCG-SIS scene was preserved. Structural validation counted 877 SVG geometry elements and 46 text elements. The preparation change affects serialization/version/IDs, not scientific geometry.
- A separate Illustrator review import completed and a PNG preview was exported. The bridge reported 907 native paths and 46 text frames and rejected raster/placed reference objects. Its overall preview was visually checked against the approved version.

The SVG preparer now omits an optional XML declaration that caused an Illustrator 30.x import failure. Modal importer notices are suppressed only during import, with the previous setting restored afterward.

An additional exhaustive per-object comparison stalled and was stopped; it is not recorded as passed. Native append-mode rendering, all font substitutions, all gradient/clipping edge cases and every supported Office version are not certified by these checks. Keep reviewing each actual target app. An image preview is not a substitute for editable source vectors, and this report is not a claim of pixel-perfect identity or universal code originality.
