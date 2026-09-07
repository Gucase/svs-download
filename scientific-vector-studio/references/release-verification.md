# v0.6.0-pilot verification scope

## Two drawing modes and shared buyout (2026-09-07)

Reference Reconstruction and Scientific Asset Drawing use separate trial allowances. Reference Reconstruction permits one unique completed figure; Scientific Asset Drawing permits two unique completed canvases/briefs. Technical failures, cancelled reservations, corrections using the same stable UsageId, and delivery of the same work to Illustrator and PowerPoint do not consume another allowance. A UsageId cannot cross feature modes.

One valid machine-bound lifetime `.svslicense` authorization unlocks unlimited use of both modes. The verifier still validates the signed product, entitlement type and current machine before reserve, commit and status operations. Existing records without a feature mode are treated as Reference Reconstruction records so the previous one-figure allowance keeps its meaning.

All 39 Skill tests passed. Coverage includes independent one- and two-figure trial buckets, migration of unscoped trial records, pending reservations, cancellation and retry, cross-mode UsageId rejection, one-file unlock of both modes, 100 consecutive authorized generations, signature tampering, copied-file and copied-ledger rejection on another machine, stable hashed machine codes, SVG contracts and the 60-asset library.

The PowerShell wrappers expose `-FeatureMode reference_reconstruction` and `-FeatureMode scientific_asset_drawing`. Their defaults remain Reference Reconstruction for backward compatibility. Dry-run preparation does not modify entitlement state; real app delivery reserves before mutation, commits after success and cancels known failures.

## Drawing and application checks

Reference Reconstruction keeps the measured-source workflow: direct editable geometry, live text, local full-view and detail comparison, and separate inspection in Illustrator or PowerPoint. Scientific Asset Drawing uses independently authored generic assets or directly authored missing objects; realistic instrument work follows the dedicated construction and targeted-review standard.

The current Q-TOF and HPLC examples were created as grouped, editable PowerPoint shapes and visually reviewed in the open target application. Their GitHub images are PNG previews only; they demonstrate appearance, not the editability of the PNG files themselves. Continue to inspect each actual target document because fonts, gradients and conversions can vary by application version.
