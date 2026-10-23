# Application development process

This describes how the digital stethoscope is developed: from requirements and design to implementation, tests and human review. The product includes its hardware and application software. The phone, server and external audio amplifier sit outside the system boundary.

The process is defined here. [Verification operations](../testing/ci/OPERATIONS.md) describes test execution and infrastructure. [Verification cases](../testing/specification-verification.md) contains the application-specific checks.

## The V-model

![Project V-model: design and implementation on the left, verification and acceptance on the right](v-model.svg)

On the way down, the developer agrees the requirements, architecture, detailed design and interfaces. Implementation follows that design: L2 (layer 2) application logic first, then L1 (layer 1) services and driver wrappers.

On the way up, AI (artificial intelligence) generates tests from those agreed documents. Automated tests check the implementation. The developer performs the manual device tests and signs off the recorded outcomes. Failures can send work back to any earlier step; changes to requirements, design or implementation are agreed by the developer.

## Current state and target

Architecture is organised into [system](../architecture/system/README.md), [WIFI](../architecture/WIFI/README.md) and [PORTAL](../architecture/PORTAL/README.md) pages with diagrams and editable-source links. Portal content is still mixed into the Wi-Fi views. Detailed design remains flat in `design/interfaces-and-behavior.md`, including dated decision sections. The matching system and component split under `design/` is stage 3 of the visibility trial and remains future work.

The application host batch will check communication logic with substitutes when its test PR is added. Component unit tests, real-service integration and device acceptance need further work. Medical-device compliance, software safety class and independent validation need a separate, sourced assessment.

## Documents and component PRs

Whole-system requirements stay together. The [architecture pages](../architecture/README.md) contain the relevant diagrams and links to their editable sources. [Detailed design](../design/interfaces-and-behavior.md) remains in its current flat layout until the stage 3 split.

Architecture defines components, responsibilities, boundaries and dependencies. Detailed design defines software flows, business logic, interface contracts, states, parameters and failure handling. Shared decisions belong at system level. PR (pull request) stage labels show progress. The [VT coverage check](../testing/ci/validate_docs.py) reports case references and explicit gaps. These records supply status without a page written by hand.

The whole-system baseline comes first. Each component then has separate PRs:

1. **Architecture:** components, responsibilities, boundaries and dependencies.
2. **Detailed design:** software flows, business logic, contracts and failure handling.
3. **Interfaces + L2:** agreed interfaces and application logic against substitute L1 services.
4. **L1 services:** service implementation and driver wrappers.
5. **Tests:** a generated component batch and a readable explanation of its coverage.

Design PRs are discussion material and linked context. Their review does not block implementation from starting. Each PR uses one stage label: `v:architecture`, `v:design`, `v:l2`, `v:l1` or `v:tests`. Its **Basis** section records the full design and requirements commit SHA (secure hash algorithm), the covered VT-xx and REQ-xx IDs (identifiers), and links to agreed decisions. For mixed work, use the main stage and list the other stages in the description. Infrastructure-only PRs explain why a stage or basis does not apply. The label and basis remain in the PR record after merge. Bring unresolved design choices back to discussion.

A necessary interface change gets its own interface-and-documentation PR. Dependent L1 implementation merges wait for that adjustment.

Implementation PRs may merge before the new test batch when existing required checks and reviews pass. Existing tests continue to run. The component's automated batch must pass before its implementation enters GitLab human review. Hardware cases still awaiting execution remain explicit.

Documents link requirements and design decisions to their implementation PRs and test evidence. Gaps are recorded in the affected document and addressed through the corresponding design, implementation or test PR.

## How tests are generated

The test basis is the requirements, architecture, detailed design and agreed interfaces. An AI session derives cases from identified revisions of these documents, with the implementation and existing harness available where needed.

```mermaid
flowchart LR
    Basis[Requirements and design] --> Cases[AI-generated cases]
    Cases --> Tests[Separate test PR]
    Tests --> Review[Checks and AI review]
    Review --> Human[Developer reviews case list]
    Human --> Evidence[Revision-specific results]
```

The generated batch covers normal operation, boundaries and specified failures, including timeouts and cancellation where relevant. It contains executable tests, test-only substitutes and manual procedures for cases that require the real device or human observation.

The test PR contains a case list: scenario, linked requirement or design basis, and expected result. The developer reviews this list and records agreement or findings in the PR before the test batch enters the GitLab baseline. AI reviews the executable test source. The description also explains how the cases run and what remains unverified. Results identify the tested source revision and distinguish real components from substitutes.

Claude and GPT models are used across authoring and independent review. CodeRabbit is the primary PR reviewer, with the existing repository fallback when unavailable. Separate sessions and models support the project's automated review.

Implementation follows the production design. Tests fit the agreed boundaries; they do not justify extra production hooks or abstractions just to make testing easier. Missing expected behavior returns to design discussion. A failed test is examined to locate the defect in the implementation, test, substitute or specification. An expectation is not changed merely to get a pass.

CI (continuous integration) executes committed tests. It does not regenerate them on each push. New cases and changes to existing expectations are explicit test-PR work.

## Deterministic simulation for L2 testing

The simulation runs production L2 logic on a host computer. Controlled substitutes provide the required L1 services and Zephyr kernel functions. This allows application behavior to be tested before the real services and drivers are ready.

```mermaid
flowchart LR
    Case[Scenario: state, inputs and event timing] --> L2[Production L2 logic]
    L2 <--> Services[Controlled L1 responses]
    Clock[Simulated clock and kernel functions] --> L2
    L2 --> Result[Observed calls, state and result]
    Result --> Check[Compare with the design expectation]
```

Each scenario starts with fresh state. Simulated time advances during waits, and events occur at selected times. The same executable and controlled scenario can therefore repeat a retry, timeout or cancellation without relying on radio behavior or real-time delays.

Thread and lock functions are controlled substitutes. These tests check application logic; real-service integration and device measurements check concurrent scheduling and physical timing.

## Manual component and final system tests

AI drafts manual procedures from the same test basis. The developer executes the steps, records observations and signs off the run. Reusable procedures belong under `testing/<COMPONENT>/` and `testing/system/`. Completed runs are records for a particular device and firmware build.

Each procedure is one short document:

| Section | Contents |
| --- | --- |
| Header | Test ID, title and linked requirement or design contract. |
| Device and software | One text field for device, firmware/build and setup identity. |
| Preconditions | A list of required starting conditions and equipment. |
| Execution | Numbered actions with an observable pass criterion in the action text. Each step has a Pass / Fail / Blocked / Not run selector and one note field. |
| Completion | Overall result and one sign-off field for name, date and signature reference. |

The GitLab review links the source procedure at its commit SHA. Notes contain observations, deviations and evidence references. Sign-off confirms the recorded execution and outcome. Independent review is recorded separately.

Component runs accompany their corresponding GitLab review. Final system acceptance is a separate record covering complete operator flows and system requirements, including failures. The procedure, firmware identity, evidence and dated sign-off remain together.

## GitHub development and GitLab human review

GitHub is the internal development source. GitLab provides the human-review layer. Architecture, design, interfaces/L2, L1 services and tests keep separate reviews on both platforms.

Transfer a component when its architecture, design, L2, L1 and test PR set is complete and its automated batch is green. Record any pending device cases and the developer's case-list review. Keep the separate stage reviews on GitLab.

For each baseline:

1. Create a Git tag at the exact source commit. Proposed name: `review/<component>/<YYYY-MM-DD>-<sequence>`, for example `review/wifi/2026-10-22-01`. A changed baseline gets a new tag.
2. Open the GitLab MR (merge request) with the tag, full source SHA and links to the component PR set and automated reviews.
3. Attach an evidence bundle to the MR before GitHub artifacts expire: 14 days for diagnostics and eight days for firmware. Include the case list with expected results, JUnit reports, logs, coverage gaps, toolchain/configuration identity, firmware manifest and checksums, and any completed manual records. Keep these files with the reviewed baseline.
4. Record human findings and the reviewed tag in the MR. Generated test source stays on GitHub initially, linked at the same SHA. Transfer it too if GitLab CI is introduced.

Internal development continues while human review is open. Transfer and feedback tracking are manual. GitLab findings return through GitHub PRs adapted to the newer implementation. Those changes pass the affected checks and return for human review. Approval stays attached to the revision actually reviewed.

The [verification operations](../testing/ci/OPERATIONS.md) document defines which suites run, where they run and what evidence they retain.
