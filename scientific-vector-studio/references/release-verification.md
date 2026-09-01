# v0.5.2-pilot verification scope

## Contact-data correction (2026-09-01)

The purchase prompt uses the immutable WeChat ID `XBBen01`. The same fixed prompt is used by the Python license manager, PowerShell gate, Skill instructions and licensing reference. The unit test verifies that the correct ID is present and no substituted initial appears in the runtime prompt.

## One-figure trial update (2026-09-01)

The free allowance is one unique completed figure. Technical failures, cancelled reservations, corrections using the same generation ID, and delivery of that same figure to Illustrator and PowerPoint do not consume another allowance. A second unique figure is blocked before app mutation unless a valid machine-bound buyout is active.

All 30 Skill tests passed after updating the allowance constant, purchase message and reservation tests. Tests cover the first free figure, rejection of a second unique figure, cancellation of a pending first figure, same-figure reuse and unlimited zero-cost use after buyout. Existing signed buyout files and historical usage records are preserved.

## Machine-bound authorization update (2026-08-31)

New signed payload version 3 binds one machine code to a non-expiring, unlimited buyout. Windows uses the system MachineGuid; only a product/platform-scoped SHA-256 code is displayed. No MAC address, raw identifier transmission, server call, device override or figure cap is added. Existing drawing code and assets are unchanged.

30 Skill tests and 8 owner-tool tests passed. Added checks cover same-machine activation, another-machine file rejection before ledger mutation, rejection after copying an activated ledger, signed-machine-code tampering, missing/invalid machine codes, stable hashed identifiers, and explicit reissuance for old unbound licenses. Windows PowerShell 5.1 smoke tests cover machine-code retrieval, owner file issuance, import and status with temporary keys/ledgers. No real customer file was issued. Mac/Linux identity branches are not live-device certified; public local code and cloned system IDs are not tamper-proof.

## Original v0.4 buyout verification (2026-08-31)

The licensing-only update replaces credit issuance/spending and the online client with a limited trial and CNY 39 signed unlimited `.svslicense` authorization. Historical ledger records are not deleted or silently converted. Drawing implementations and existing illustration files are unchanged.

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
