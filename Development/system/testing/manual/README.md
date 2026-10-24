# Executed manual test records

AI drafts procedures; Nico executes and signs the runs. Copy
[run-template.json](run-template.json) to `runs/<date>-<test-id>-<device>.json` after
execution. The template is deliberately incomplete and is not execution evidence.
No target run is implied by its presence or by an empty run directory.

Use the procedure at its full commit SHA. Copy every numbered step into the run,
including repeated matrix observations, with its action and observable expectation.
Record Pass, Fail, Blocked or Not run as `pass`, `fail`, `blocked` or `not-run`.
Every step needs observations, including the reason for blocked or unexecuted steps;
reference photos, logs and measurements where relevant. Never record credentials
or patient data. The device ID, firmware boot build ID, full firmware source SHA,
configuration and equipment identify the tested baseline.

After execution Nico supplies `sign_off` with `name: "Nico"`, an ISO 8601 `date`
including timezone, and `signature_reference` pointing to his signed record or
human-review acknowledgement. An agent must not fabricate a signature. An overall
pass requires every recorded step to pass; any failed step means fail, otherwise
an incomplete run is blocked. Sign-off records the observed outcome, including a
failed or blocked run; it does not claim independent review.

Run `python Development/system/testing/ci/manual_test_records.py`. CI checks each
JSON run under `manual/runs/` and rejects missing identities, observations, duplicate
step IDs, inconsistent outcomes or missing Nico sign-off. This checks record
completeness and consistency; it cannot authenticate a signature or prove physical
execution. Nico checks correspondence with all procedure steps during sign-off.

Created by GPT-6.1-Sol on behalf of Nico running in codex.
