# Implementation and regression rules

SVS owns its drawing instructions, measured scene workflow, validation rules and application integration. Standard Python packages, SVG specifications and Adobe/Microsoft APIs are dependencies, not claims of SVS authorship. Supplied illustrations and network examples have their own provenance.

## Document-oriented Illustrator integration

The Windows entry point validates an authored SVG, attaches only to an already-running Illustrator, prepares a separate SVG 1.1 file, reserves the figure entitlement and invokes a small document bridge. Illustrator imports the vectors itself. The bridge either retains the native review document or copies its root objects as one editable group using a single artboard-coordinate transform. It does not parse geometry into a playback cache, incrementally replay points, or trace a reference bitmap.

The authored scene remains the source of truth. Preserve path commands, text, paint resources, clipping and paint order. Independent implementation is not synonymous with changing the approved appearance. SVG preparation may add IDs/version but must not alter scientific geometry.

## Safe changes

- Do not borrow another Skill's code and relabel it. Implement from the SVS requirements and public host APIs.
- Keep third-party package names and necessary notices intact; dependencies are allowed.
- Keep original references and approved vectors unchanged during a backend rewrite.
- Test validation, source preservation, document transfer order, rollback, optional exports and licensing reuse. Compare local renders of approved fixtures before and after preparation.
- Check native app objects and visual results separately; mocked tests do not certify Illustrator rendering or PowerPoint conversion.
- Preserve stable figure UsageIds. A backend regression check or another app rendition is not a new paid figure.
- History and earlier releases are not silently erased by replacing the current package. Provenance claims apply to the audited revision, not to all past artifacts.

This package does not certify that every short code fragment is globally unique, or that a supplied figure is original. It describes the implementation process and the evidence that can be checked.
