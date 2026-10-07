# Digital stethoscope — pre-implementation review draft

**Status: unapproved review draft, 2026-10-06.** This package translates the saved architecture
boards and derives a specification and detailed design for the thesis product. It does not
claim that the evaluation firmware already satisfies these requirements. Firmware is unchanged.

Review in this order:

1. [Product scope, sources and terminology](spec/product-scope.md)
2. [Use cases and workflows](requirements/use-cases.md)
3. [System requirements](requirements/system-requirements.md)
4. [Architecture diagrams, source fidelity and decisions](architecture/README.md)
5. [Per-component requirements](requirements/README.md)
6. [Interface contracts and detailed design](design/interfaces-and-behavior.md)
7. [Verification and traceability](testing/specification-verification.md)
8. [Review decisions and implementation readiness](planning/implementation-readiness.md)

Browse the [local diagram viewer](architecture/review.html). The checks performed on this draft
are recorded in [documentation validation](testing/evidence/2026-10-06-draft-validation.md); device tests remain planned.

Requirements follow the SW-Basis pattern: trigger/precondition → shall behavior → observable
outcome. Stable IDs connect use cases, system requirements, components and planned verification.
Source-backed behavior, derived contracts, proposed thresholds and unresolved choices are
distinguished. Numeric values inherited from bring-up are candidates unless the saved board
fixes them. No Zumo-specific lap, C/AVR or flash-percentage constraint is copied to this product.

**Review editing:** component Markdown files are the requirement text; `requirements/traceability.csv`
is their index. Update both when changing IDs or allocations. Diagrams are editable `.puml` files;
raw board snapshots are immutable provenance, not the place to edit the new design.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
