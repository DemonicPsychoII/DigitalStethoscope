"""VT-07: Observation delivery under P13 in L2_COMMUNICATION, on the host simulation.

The transport cases at the end cover the SNTP and TLS preparation contracts (VT-08)
that delivery depends on.
"""

from datetime import datetime, timedelta, timezone
import json

import pytest

from host_build import error_code
from test_communication import create_simulation_runner, plan

DESIGN = "Development/system/design/system/"
P13 = DESIGN + "parameters.md (P13)"
DELIVERY = DESIGN + "interfaces-and-behavior.md (delivery decision and Sending)"
TRANSPORT = "Development/system/design/COMMUNICATION/secure-transport.md#"
TIME = "Development/system/design/COMMUNICATION/time-synchronization.md#"
SERVER = "Development/system/design/COMMUNICATION/server-communication.md#"
SUBMIT = 1_000
GLOBAL = 10_000
RESERVE = 1_000
BUDGET_END = SUBMIT + GLOBAL - RESERVE
GAP = 2_000
SETUP = 3_000
RECEIPT = 1_000
PREPARATION = 10_000
PREPARATION_RETRY = 60_000
KEEP_ALIVE_MARGIN = 5_000
MAPPING_LIMIT = 45_000_000
UNCERTAINTY_BUDGET = 100_000
# P23 event-check interval: the longest time a wait takes to notice Start or a deadline.
EVENT_CHECK = 200
# With the simulation's 100 ms join and TLS durations, boot applies its clock at 100 ms and verifies at 200 ms.
BOOT_ANCHOR = 100
BOOT_HANDSHAKE = 200
SIMULATED_UTC_SECONDS = 1_794_182_400
NONE, PENDING, DELIVERED, FAILED, NO_CLOCK = range(5)
ENOENT, ENODEV, EBUSY, EIO, EACCES = (
    error_code(name) for name in ("ENOENT", "ENODEV", "EBUSY", "EIO", "EACCES")
)
ENOTCONN, ECONNRESET, ECONNREFUSED, ETIMEDOUT = (
    error_code(name) for name in ("ENOTCONN", "ECONNRESET", "ECONNREFUSED", "ETIMEDOUT")
)
EBADMSG, EMSGSIZE = (error_code(name) for name in ("EBADMSG", "EMSGSIZE"))
SIMULATED_UTC = datetime(2026, 11, 9, tzinfo=timezone.utc)
SERVER_CONNECTION_FAILURE = "SERVER_CONNECTION_FAILURE"


def create_delivery_runner(executable, record_property):
    run = create_simulation_runner(executable, record_property)

    def delivery(
        script="",
        until=SUBMIT + GLOBAL + 1_000,
        kind=0,
        server=True,
        stored=True,
        submit=SUBMIT,
        after_submit="",
    ):
        script = f"server {int(server)}\nregistration 1\n" + script
        if submit is not None:
            # Same-time events arrive in script order, so after_submit follows the admission.
            script += f"event {submit} deliver {kind}\n" + after_submit
            script += f"event {submit + GLOBAL} outcome 0\n"
        return run(script, until=until, stored=stored)

    return delivery


@pytest.fixture
def simulate(simulation_executable, record_property):
    return create_delivery_runner(simulation_executable, record_property)


@pytest.fixture
def simulate_white_box(memory_executable, record_property):
    """Delivery runner whose white_box events change worker state that no public input reaches."""
    return create_delivery_runner(memory_executable, record_property)


def evidence(
    record_property, scenario, basis, expected, vt_id="VT-07", area="delivery"
):
    record_property("scenario", f"{area}-{scenario}")
    record_property("vt_id", vt_id)
    record_property("basis", basis)
    record_property("expected", expected)


def logged(trace, prefix):
    for line in trace.production_log.splitlines():
        _, _, text = line.partition(" ")
        if text.startswith(prefix + " "):
            return text[len(prefix) + 1 :]
    raise AssertionError(f"{prefix} not logged:\n{trace.production_log}")


def log_times(trace, text):
    return [
        int(line.partition(" ")[0])
        for line in trace.production_log.splitlines()
        if text in line
    ]


def between(trace, key, start, end):
    return [time for time in trace.times(key) if start <= time < end]


def expected_end(trace, submit=SUBMIT, anchor=None):
    if anchor is None:
        anchor = trace.times("sntp")[0]
    end = SIMULATED_UTC + timedelta(milliseconds=submit - anchor)
    return end.strftime("%Y-%m-%dT%H:%M:%S.") + f"{end.microsecond // 1000:03d}Z"


def assert_final(trace, outcome):
    assert trace.values("deliver_result") == [0]
    assert trace.last("delivery_outcome") == outcome
    requests = trace.times("exchange")
    assert all(SUBMIT <= time < SUBMIT + GLOBAL - RESERVE for time in requests)
    assert trace.values("exchange_same_observation") == [1] * len(requests)


@pytest.mark.parametrize("status", [201, 200])
def test_delivered_with_one_receipt(simulate, record_property, status):
    evidence(
        record_property,
        f"receipt {status}",
        P13,
        "one conditional POST /Observation, DELIVERED",
    )
    trace = simulate(plan("exchange", [status]))
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 1
    assert (
        f"Observation delivered: https://192.168.2.40:8443/fhir/Observation/8001/_history/1 (status {status})"
        in trace.production_log
    )
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["resourceType"] == "Observation"
    assert observation["device"] == {"reference": "Device/7400"}
    assert observation["effectiveDateTime"] == expected_end(trace)
    assert observation["valueQuantity"]["value"] == 72.3
    assert "subject" not in observation and "dataAbsentReason" not in observation
    end = expected_end(trace).replace(":", "%3A")
    assert logged(trace, "observation_condition") == (
        f"identifier=urn%3Astethoscope%3Ameasurement|7400%3A{end}"
    )


def test_poor_signal_sends_only_the_error_report(simulate, record_property):
    evidence(
        record_property, "poor signal", DELIVERY, "dataAbsentReason error, no value"
    )
    trace = simulate(plan("exchange", [201]), kind=1)
    assert_final(trace, DELIVERED)
    observation = json.loads(logged(trace, "observation_body"))
    assert "valueQuantity" not in observation
    assert observation["dataAbsentReason"]["coding"][0]["code"] == "error"


def test_server_error_is_retried_with_the_identical_request(simulate, record_property):
    evidence(
        record_property,
        "503 then 201",
        P13,
        "retry after the 2 s gap, same body and identity",
    )
    trace = simulate(plan("exchange", [503, 201]))
    assert_final(trace, DELIVERED)
    first_result, second_request = (
        trace.times("exchange_result")[0],
        trace.times("exchange")[1],
    )
    assert GAP <= second_request - first_result <= GAP + 300


@pytest.mark.parametrize("status", [412, 501, 400, 401, 404, 302])
def test_terminal_status_ends_after_one_request(simulate, record_property, status):
    evidence(record_property, f"terminal {status}", P13, "no retry, DELIVERY_FAILURE")
    trace = simulate(plan("exchange", [status, 201]))
    assert_final(trace, FAILED)
    assert trace.count("exchange") == 1
    assert "DELIVERY_FAILURE" in trace.production_log


def test_attempts_are_exhausted_after_four(simulate, record_property):
    evidence(
        record_property,
        "five 503 planned",
        P13,
        "exactly four requests, DELIVERY_FAILURE",
    )
    trace = simulate(plan("exchange", [503] * 5))
    assert_final(trace, FAILED)
    assert trace.count("exchange") == 4
    assert "DELIVERY_FAILURE" in trace.production_log


def test_lost_receipt_is_retried(simulate, record_property):
    evidence(
        record_property,
        "connection reset after the write",
        P13,
        "retry with the same conditional identity",
    )
    trace = simulate(plan("exchange", [ECONNRESET, 201]))
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 2


def test_receipt_timeout_is_cancelled_after_one_second(simulate, record_property):
    evidence(
        record_property,
        "no receipt",
        P13,
        "cancel at the 1 s write-and-receipt budget, reconnect, retry",
    )
    trace = simulate(plan("exchange", [201], delay=5_000) + plan("exchange", [201]))
    assert_final(trace, DELIVERED)
    first_request = trace.times("exchange")[0]
    cancel = trace.times("secure_cancel")[0]
    assert cancel - first_request <= 1_000 + 200
    assert trace.count("tls") == 2 and trace.count("exchange") == 2


def test_stale_connection_is_replaced_without_consuming_an_attempt(
    simulate, record_property
):
    evidence(
        record_property,
        "stale connection, then three 503",
        P13,
        "five requests, the fourth counted one delivers",
    )
    trace = simulate(plan("exchange", [ENOTCONN, 503, 503, 503, 201]))
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 5 and trace.count("tls") == 2


def test_failed_connection_setup_is_a_failed_attempt(simulate, record_property):
    evidence(
        record_property,
        "TLS fails after a stale connection",
        P13,
        "four failed setups, DELIVERY_FAILURE",
    )
    trace = simulate(
        plan("tls", [0] + [ECONNREFUSED] * 4 + [0]) + plan("exchange", [ENOTCONN])
    )
    assert_final(trace, FAILED)
    assert trace.count("tls") == 5 and trace.count("exchange") == 1
    assert "DELIVERY_FAILURE" in trace.production_log


def test_no_clock_anchor_reports_server_connection_failure(simulate, record_property):
    evidence(
        record_property,
        "anchor older than 12.5 h, SNTP fails",
        P13,
        "nothing sent, SERVER_CONNECTION_FAILURE instead of DELIVERY_FAILURE",
    )
    submit = 45_000_500
    trace = simulate(
        f"event {submit - 300} sntp_fail {ETIMEDOUT}\n",
        until=submit + GLOBAL + 1_000,
        submit=submit,
    )
    assert trace.last("delivery_outcome") == NO_CLOCK
    assert trace.values("exchange_observation") == []
    assert "no clock for the measurement end, result not sent" in trace.production_log
    assert "DELIVERY_FAILURE" not in trace.production_log


@pytest.mark.parametrize(
    "settings, result",
    [
        pytest.param({"stored": False}, ENOENT, id="wifi-not-configured"),
        pytest.param(
            {"script": f"identity_error {EIO}\n"}, ENODEV, id="no-device-registration"
        ),
        pytest.param({"server": False}, ENODEV, id="no-server-profile"),
    ],
)
def test_prerequisites_are_checked_once_without_waiting(
    simulate, record_property, settings, result
):
    evidence(
        record_property,
        f"prerequisite {result}",
        DELIVERY,
        "rejected at submission, nothing sent",
    )
    trace = simulate(**settings)
    assert trace.values("deliver_result") == [result]
    assert trace.values("exchange_observation") == []
    assert trace.last("delivery_outcome") == NONE


def test_second_submission_is_busy_while_a_job_runs(simulate, record_property):
    evidence(record_property, "second result", DELIVERY, "one job, no queue: Busy")
    script = plan("exchange", [503, 201]) + f"event {SUBMIT + 50} deliver 0\n"
    trace = simulate(script)
    assert trace.values("deliver_result") == [0, EBUSY]
    assert trace.last("delivery_outcome") == DELIVERED


def test_no_request_after_the_deadline(simulate, record_property):
    evidence(
        record_property,
        "job waits behind Wi-Fi setup",
        "Development/system/design/COMMUNICATION/secure-transport.md (no delayed send)",
        "the thread is busy until after the deadline: nothing is sent, DELIVERY_FAILURE",
    )
    script = plan("exchange", [201]) + "event 500 hold 0\nevent 15000 cancel 0\n"
    trace = simulate(script, until=25_000)
    assert trace.values("deliver_result") == [0]
    assert trace.values("exchange_observation") == []
    assert trace.last("delivery_outcome") in (PENDING, FAILED)
    assert "DELIVERY_FAILURE" in trace.production_log


def test_expired_retained_connection_is_not_reused_after_listening(
    simulate, record_property
):
    evidence(
        record_property,
        "Stop and submission after the keep-alive expired during listening",
        P13,
        "new setup with its own SNTP exchange before the request, DELIVERED",
    )
    submit = 600_000
    script = plan("exchange", [201]) + f"event 1000 start 0\nevent {submit} stop 0\n"
    trace = simulate(script, until=submit + GLOBAL + 1_000, submit=submit)
    assert trace.last("delivery_outcome") == DELIVERED
    request = trace.times("exchange")[-1]
    assert any(submit <= time < request for time in trace.times("tls"))
    assert any(submit <= time < request for time in trace.times("sntp"))


def test_cleanup_fault_still_ends_a_pending_job(simulate, record_property):
    evidence(
        record_property,
        "submission during setup, then a failed portal stop latches the cleanup fault",
        DELIVERY,
        "terminal outcome without another control event, nothing sent",
    )
    script = (
        "stop_failures 1\nevent 500 hold 0\nevent 2000 start 0\nevent 3000 stop 0\n"
    )
    trace = simulate(script, submit=1_500)
    assert trace.values("deliver_result") == [0]
    assert "WIFI_CLEANUP_FAILURE" in trace.production_log
    assert trace.values("exchange_observation") == []
    assert trace.last("delivery_outcome") in (FAILED, NO_CLOCK)


def test_outcome_is_none_before_any_job(simulate, record_property):
    evidence(record_property, "no job", DELIVERY, "NONE before the first admission")
    trace = simulate("event 500 outcome 0\n" + plan("exchange", [201]))
    assert trace.values("delivery_outcome")[0] == NONE


def test_fewer_attempts_when_the_gap_would_consume_the_remaining_budget(
    simulate, record_property
):
    evidence(
        record_property,
        "every receipt times out",
        P13,
        "each attempt cancelled at its 1 s receipt budget; an attempt follows a failure only "
        "when its 2 s gap ends before the deadline less the 1 s cleanup reserve: with 100 ms "
        "setups that admits three requests, then DELIVERY_FAILURE",
    )
    trace = simulate(plan("exchange", [201] * 5, delay=5_000))
    assert_final(trace, FAILED)
    requests = trace.times("exchange")
    failures = trace.times("secure_cancel_done")
    assert len(requests) == len(failures) == 3
    for request, failure in zip(requests, failures):
        assert RECEIPT <= failure - request <= RECEIPT + EVENT_CHECK
    setups = between(trace, "sntp_request", SUBMIT, BUDGET_END)
    for failure, setup in zip(failures, setups):
        assert failure + GAP < BUDGET_END and setup - failure >= GAP
    assert failures[-1] + GAP >= BUDGET_END
    for key in ("sntp_request", "tls", "exchange"):
        assert between(trace, key, failures[-1], SUBMIT + GLOBAL) == []
    assert "DELIVERY_FAILURE" in trace.production_log


def test_stalled_reconnect_is_cancelled_at_the_setup_budget(simulate, record_property):
    evidence(
        record_property,
        "lost receipt, then the TLS of the reconnect stalls",
        P13,
        "setup cancelled 3 s after it started (SNTP included); as a failed attempt it is "
        "followed by the 2 s gap, then a new setup delivers",
    )
    script = plan("tls", [0]) + plan("tls", [0], delay=10_000) + plan("tls", [0])
    trace = simulate(script + plan("exchange", [ECONNRESET, 201]))
    assert_final(trace, DELIVERED)
    _, stalled_setup, next_setup = trace.times("sntp_request")
    assert trace.values("secure_cancel") == [0]
    cancel = trace.times("secure_cancel")[0]
    released = trace.times("secure_cancel_done")[0]
    assert SETUP <= cancel - stalled_setup <= SETUP + EVENT_CHECK
    assert next_setup - released >= GAP
    assert trace.count("tls") == 3 and trace.count("exchange") == 2


@pytest.mark.parametrize(
    "script, requests",
    [
        pytest.param(
            plan("tls", [0, EACCES, 0]) + plan("exchange", [ECONNRESET, 201]),
            1,
            id="trust-rejected-in-handshake",
        ),
        pytest.param(
            f"certificate_valid_from {SIMULATED_UTC_SECONDS + 3_600}\n"
            + plan("exchange", [201]),
            0,
            id="certificate-not-yet-valid-at-the-setup-clock",
        ),
    ],
)
def test_certificate_failure_in_delivery_setup_is_terminal(
    simulate, record_property, script, requests
):
    evidence(
        record_property,
        "certificate failure during the delivery setup",
        TRANSPORT + "delivery-budget-boundary; " + P13,
        "one setup in the job, no retry, DELIVERY_FAILURE",
    )
    trace = simulate(script)
    assert_final(trace, FAILED)
    assert len(between(trace, "sntp_request", SUBMIT, SUBMIT + GLOBAL)) == 1
    assert trace.count("exchange") == requests
    assert "DELIVERY_FAILURE" in trace.production_log


@pytest.mark.xfail(
    strict=True,
    reason="Known defect #131: communication.c treats a setup that fails in DNS with "
    "-ENOENT (no IPv4 record, cause RESOLUTION) as terminal instead of a failed P13 attempt",
)
def test_failed_server_lookup_in_delivery_setup_is_retried(simulate, record_property):
    evidence(
        record_property,
        "reconnect fails in DNS without an IPv4 record",
        P13 + "; " + TIME + "flow-and-scheduling",
        "a failed lookup fails the setup, a failed attempt that P13 retries after the 2 s gap: DELIVERED",
    )
    script = plan("tls", [0, ENOENT, 0]) + plan("exchange", [ECONNRESET, 201])
    trace = simulate(script)
    assert_final(trace, DELIVERED)
    assert trace.count("tls") == 3 and trace.count("exchange") == 2


def test_retry_gap_starts_after_the_cancellation_released_the_attempt(
    simulate, record_property
):
    evidence(
        record_property,
        "receipt timeout whose cancellation takes 800 ms",
        P13,
        "the next attempt starts no earlier than 2 s after the release, not after the timeout",
    )
    script = "secure_cancel_delay 800\n" + plan("exchange", [201], delay=5_000)
    trace = simulate(script + plan("exchange", [201]))
    assert_final(trace, DELIVERED)
    released = trace.times("secure_cancel_done")[0]
    assert released - trace.times("secure_cancel")[0] == 800
    next_setup = between(trace, "sntp_request", SUBMIT, SUBMIT + GLOBAL)[0]
    assert next_setup - released >= GAP


def test_cancellation_and_release_finish_by_the_global_deadline(
    simulate, record_property
):
    evidence(
        record_property,
        "the last setup stalls into the end of the budget, cancellation takes 900 ms",
        P13,
        "setup capped by the remaining budget; release proven and the outcome latched by Stop + 10 s",
    )
    script = "secure_cancel_delay 900\n" + plan("tls", [0])
    script += plan("tls", [0, 0], delay=10_000) + plan("exchange", [ECONNRESET])
    trace = simulate(script)
    assert_final(trace, FAILED)
    deadline = SUBMIT + GLOBAL
    assert trace.times("sntp_request")[-1] + SETUP > BUDGET_END
    assert BUDGET_END <= trace.times("secure_cancel")[-1] <= BUDGET_END + EVENT_CHECK
    assert trace.count("secure_cancel") == trace.count("secure_cancel_done")
    assert all(time <= deadline for time in trace.times("secure_cancel_done"))
    assert all(time <= deadline for time in trace.times("tls_close"))


@pytest.mark.parametrize("result", [EBADMSG, EMSGSIZE], ids=["malformed", "oversized"])
def test_unusable_receipt_is_retried(simulate, record_property, result):
    evidence(
        record_property,
        f"exchange result {result}",
        SERVER + "observation-construction-and-delivery; " + P13,
        "an incomplete or malformed response is no receipt: retried after the 2 s gap with the same identity",
    )
    trace = simulate(plan("exchange", [result, 201]))
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 2
    failure = trace.times("exchange_result")[0]
    assert between(trace, "sntp_request", SUBMIT, SUBMIT + GLOBAL)[0] - failure >= GAP


def test_connection_past_keep_alive_is_replaced_without_consuming_an_attempt(
    simulate, record_property
):
    evidence(
        record_property,
        "keep-alive expired during listening, then three 503",
        P13 + "; " + TRANSPORT + "preparation-listening-and-recovery",
        "the over-age connection is closed and replaced inside attempt 1; all four attempts remain: DELIVERED",
    )
    submit = 600_000
    script = plan("exchange", [503, 503, 503, 201])
    script += f"event 1000 start 0\nevent {submit} stop 0\n"
    trace = simulate(script, until=submit + GLOBAL + 1_000, submit=submit)
    assert trace.last("delivery_outcome") == DELIVERED
    assert trace.count("exchange") == 4
    first_request = trace.times("exchange")[0]
    assert between(trace, "tls_close", submit, first_request)
    assert between(trace, "tls", submit, first_request)


def test_unproven_release_latches_cleanup_failure_instead_of_a_retry(
    simulate, record_property
):
    evidence(
        record_property,
        "receipt timeout, cancellation cannot prove release",
        P13,
        "WIFI_CLEANUP_FAILURE, no further setup or request, the job ends undelivered",
    )
    script = "secure_cancel_failures 1\n" + plan("exchange", [201], delay=5_000)
    trace = simulate(script + plan("exchange", [201]))
    assert trace.values("deliver_result") == [0]
    assert "WIFI_CLEANUP_FAILURE" in trace.production_log
    cancel = trace.times("secure_cancel")[0]
    assert trace.count("exchange") == 1
    for key in ("sntp_request", "tls", "exchange"):
        assert between(trace, key, cancel, SUBMIT + GLOBAL + 1_000) == []
    assert trace.last("delivery_outcome") == FAILED


def setup_order(trace):
    return [key for _, key, _ in trace.rows if key in ("sntp_request", "sntp", "tls")]


def test_every_connection_setup_starts_with_its_own_time_synchronization(
    simulate, record_property
):
    evidence(
        record_property,
        "reuse, then two reconnects",
        TIME + "parameters (P25-PLACEMENT)",
        "each setup applies a fresh SNTP clock before its handshake; the reused connection runs no SNTP",
    )
    trace = simulate(plan("exchange", [ECONNRESET, ECONNRESET, 201]))
    assert_final(trace, DELIVERED)
    assert trace.count("tls") == 3
    assert setup_order(trace) == ["sntp_request", "sntp", "tls"] * 3
    assert between(trace, "sntp_request", SUBMIT, trace.times("exchange")[0]) == []


def test_measurement_end_at_the_mapping_limit_is_frozen_from_the_anchor_at_stop(
    simulate, record_property
):
    evidence(
        record_property,
        "anchor exactly 12.5 h before the measurement end",
        TIME + "clock-mapping-and-native-behavior",
        "the anchor held at Stop qualifies and freezes the end; the new setup's clock does not change it",
    )
    submit = BOOT_ANCHOR + MAPPING_LIMIT
    trace = simulate(
        plan("exchange", [201]), until=submit + GLOBAL + 1_000, submit=submit
    )
    assert trace.times("sntp")[0] == BOOT_ANCHOR
    assert trace.last("delivery_outcome") == DELIVERED
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["effectiveDateTime"] == expected_end(trace, submit)
    assert observation["effectiveDateTime"] == "2026-11-09T12:30:00.000Z"


def test_stale_anchor_at_stop_is_replaced_by_the_delivery_setup_clock(
    simulate, record_property
):
    evidence(
        record_property,
        "anchor 1 ms beyond 12.5 h at Stop, delivery setup synchronizes",
        TIME + "clock-mapping-and-native-behavior",
        "the end is frozen from the anchor of the delivery setup, before the first request: DELIVERED",
    )
    submit = BOOT_ANCHOR + MAPPING_LIMIT + 1
    trace = simulate(
        plan("exchange", [201]), until=submit + GLOBAL + 1_000, submit=submit
    )
    assert trace.times("sntp")[0] == BOOT_ANCHOR
    assert trace.last("delivery_outcome") == DELIVERED
    delivery_anchor = between(trace, "sntp", submit, submit + GLOBAL)[0]
    assert delivery_anchor < trace.times("exchange")[0]
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["effectiveDateTime"] == expected_end(
        trace, submit, delivery_anchor
    )


WHITE_BOX_REGISTRATION_CHANGE = 1
WHITE_BOX_CLOCK_STEP = 2


def white_box(value, time=SUBMIT):
    return f"event {time} white_box {value}\n"


def test_device_id_is_frozen_at_admission(simulate_white_box, record_property):
    evidence(
        record_property,
        "registration publishes another Device id right after admission",
        DESIGN + "interfaces-and-behavior.md (NetworkJob)",
        "the Observation carries the Device id valid at admission, never the live one",
    )
    trace = simulate_white_box(
        plan("exchange", [503, 201]),
        after_submit=white_box(WHITE_BOX_REGISTRATION_CHANGE),
    )
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 2
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["device"] == {"reference": "Device/7400"}
    assert "|7400%3A" in logged(trace, "observation_condition")


def test_qualifying_anchor_at_admission_freezes_the_end_against_a_later_clock_step(
    simulate_white_box, record_property
):
    evidence(
        record_property,
        "qualifying anchor at admission, clock steps one hour before the first attempt",
        TIME + "clock-mapping-and-native-behavior",
        "the end mapped at admission is sent; the step and the retry's new setup clock do not change it",
    )
    trace = simulate_white_box(
        plan("exchange", [ECONNRESET, 201]),
        after_submit=white_box(WHITE_BOX_CLOCK_STEP),
    )
    assert_final(trace, DELIVERED)
    assert trace.count("exchange") == 2
    assert len(between(trace, "sntp", SUBMIT, SUBMIT + GLOBAL)) == 1
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["effectiveDateTime"] == expected_end(trace, anchor=BOOT_ANCHOR)


def test_end_without_an_anchor_at_admission_is_frozen_once_from_the_delivery_setup(
    simulate, record_property
):
    evidence(
        record_property,
        "no qualifying anchor at admission, two reconnects with their own clocks",
        TIME + "clock-mapping-and-native-behavior",
        "the first delivery setup's anchor freezes the end; retries resend identical bytes",
    )
    submit = BOOT_ANCHOR + MAPPING_LIMIT + 1
    trace = simulate(
        plan("exchange", [ECONNRESET, ECONNRESET, 201]),
        until=submit + GLOBAL + 1_000,
        submit=submit,
    )
    assert trace.last("delivery_outcome") == DELIVERED
    assert trace.values("exchange_same_observation") == [1, 1, 1]
    delivery_anchors = between(trace, "sntp", submit, submit + GLOBAL)
    assert len(delivery_anchors) == 3
    assert delivery_anchors[0] < trace.times("exchange")[0]
    observation = json.loads(logged(trace, "observation_body"))
    assert observation["effectiveDateTime"] == expected_end(
        trace, submit, delivery_anchors[0]
    )
    assert observation["effectiveDateTime"] != expected_end(
        trace, submit, delivery_anchors[-1]
    )


@pytest.mark.parametrize(
    "uncertainty, verified",
    [
        pytest.param(UNCERTAINTY_BUDGET, True, id="at-the-budget"),
        pytest.param(UNCERTAINTY_BUDGET + 1, False, id="above-the-budget"),
    ],
)
def test_reported_sntp_uncertainty_against_the_budget(
    simulate, record_property, uncertainty, verified
):
    evidence(
        record_property,
        f"Idle preparation, reported uncertainty {uncertainty} us",
        TIME + "parameters (P25-UNCERTAINTY-BUDGET)",
        "100 ms fits the budget and the setup verifies; more fails the exchange and the setup",
        vt_id="VT-08",
        area="transport",
    )
    trace = simulate(f"sntp_uncertainty {uncertainty}\n", until=5_000, submit=None)
    assert trace.count("sntp_request") >= 1
    if verified:
        assert trace.count("sntp") == 1 and trace.count("tls") == 1
        assert "Server connection verified" in trace.production_log
        assert SERVER_CONNECTION_FAILURE not in trace.production_log
    else:
        assert trace.count("sntp") == 0 and trace.count("tls") == 0
        assert SERVER_CONNECTION_FAILURE in trace.production_log


def test_no_time_or_transport_work_while_listening(simulate, record_property):
    evidence(
        record_property,
        "preparation retry falls due during a long listening session",
        TRANSPORT
        + "preparation-listening-and-recovery; "
        + TIME
        + "flow-and-scheduling",
        "no SNTP, TLS or HTTP between Start and Stop; preparation resumes after Stop",
        vt_id="VT-08",
        area="transport",
    )
    start, stop = 1_000, 200_000
    script = (
        plan("tls", [ECONNREFUSED, 0]) + f"event {start} start 0\nevent {stop} stop 0\n"
    )
    trace = simulate(script, until=stop + 10_000, submit=None)
    assert trace.times("tls_result")[0] + PREPARATION_RETRY < stop
    for key in ("sntp_request", "tls", "exchange"):
        assert between(trace, key, start, stop) == []
    assert between(trace, "sntp_request", stop, stop + 10_000)
    assert "Server connection verified" in trace.production_log


def test_stalled_idle_preparation_is_cancelled_at_its_deadline(
    simulate, record_property
):
    evidence(
        record_property,
        "TLS stalls in the Idle preparation",
        TRANSPORT + "parameters (P26-ATTEMPT, P26-RETRY)",
        "cancelled 10 s after the setup started with SNTP; SERVER_CONNECTION_FAILURE; "
        "next setup 60 s after the release",
        vt_id="VT-08",
        area="transport",
    )
    script = plan("tls", [0], delay=30_000) + plan("tls", [0])
    trace = simulate(script, until=80_000, submit=None)
    first_setup, next_setup = trace.times("sntp_request")
    cancel = trace.times("secure_cancel")[0]
    released = trace.times("secure_cancel_done")[0]
    assert trace.values("secure_cancel") == [0]
    assert PREPARATION <= cancel - first_setup <= PREPARATION + EVENT_CHECK
    assert trace.production_log.count(SERVER_CONNECTION_FAILURE) == 1
    assert next_setup - released >= PREPARATION_RETRY
    assert "Server connection verified" in trace.production_log


def test_start_interrupting_preparation_keeps_the_gap_without_an_error(
    simulate, record_property
):
    evidence(
        record_property,
        "Start during the handshake of the Idle preparation",
        TRANSPORT + "preparation-listening-and-recovery",
        "cancelled at Start without an error; the next setup waits 60 s after the release",
        vt_id="VT-08",
        area="transport",
    )
    start, stop = 1_000, 2_000
    script = plan("tls", [0], delay=5_000) + plan("tls", [0])
    script += f"event {start} start 0\nevent {stop} stop 0\n"
    trace = simulate(script, until=75_000, submit=None)
    cancel = trace.times("secure_cancel")[0]
    released = trace.times("secure_cancel_done")[0]
    assert start <= cancel <= start + EVENT_CHECK
    assert SERVER_CONNECTION_FAILURE not in trace.production_log
    assert trace.times("sntp_request")[1] - released >= PREPARATION_RETRY
    assert "Server connection verified" in trace.production_log


def test_server_connection_failure_latches_once_per_episode(simulate, record_property):
    evidence(
        record_property,
        "two failed preparations, success, failed delivery reconnects, failed preparations",
        TRANSPORT + "failure-indication",
        "one SERVER_CONNECTION_FAILURE per unavailable episode: none on later retries, "
        "a new one only after a success",
        vt_id="VT-08",
        area="transport",
    )
    script = plan("tls", [ECONNREFUSED, ECONNREFUSED, 0] + [ECONNREFUSED] * 10)
    script += plan("exchange", [ECONNRESET])
    trace = simulate(script, until=330_000, submit=130_000)
    verified = log_times(trace, "Server connection verified")
    latches = log_times(trace, SERVER_CONNECTION_FAILURE)
    failures = [
        time for time, key, value in trace.rows if key == "tls_result" and value < 0
    ]
    assert len(verified) == 1 and len(latches) == 2
    assert latches[0] < verified[0] < latches[1]
    assert len([time for time in failures if time < verified[0]]) == 2
    assert [time for time in failures if time > latches[1]]


@pytest.mark.parametrize(
    "setting",
    [
        pytest.param(
            f"certificate_valid_from {SIMULATED_UTC_SECONDS + 3_600}",
            id="not-yet-valid",
        ),
        pytest.param(
            f"certificate_valid_until {SIMULATED_UTC_SECONDS - 3_600}", id="expired"
        ),
    ],
)
def test_certificate_outside_its_validity_is_rejected_before_the_handshake(
    simulate, record_property, setting
):
    evidence(
        record_property,
        setting.replace("_", " "),
        TRANSPORT + "trust-and-server-profile-inputs",
        "validity checked against the fresh UTC clock of the setup: no handshake, SERVER_CONNECTION_FAILURE",
        vt_id="VT-08",
        area="transport",
    )
    trace = simulate(setting + "\n", until=5_000, submit=None)
    assert trace.count("sntp") == 1
    assert trace.count("tls") == 0
    assert f"{SERVER_CONNECTION_FAILURE} ({EACCES})" in trace.production_log


def test_idle_connection_closes_at_the_device_keep_alive(simulate, record_property):
    evidence(
        record_property,
        "server keep-alive 60 s, Idle without requests",
        TRANSPORT + "parameters (P26-KEEPALIVE)",
        "retained connection closed 55 s (server value less 5 s) after its handshake",
        vt_id="VT-08",
        area="transport",
    )
    trace = simulate("server_keep_alive 60\n", until=70_000, submit=None)
    device_keep_alive_end = trace.times("tls_result")[0] + 60_000 - KEEP_ALIVE_MARGIN
    assert trace.count("tls_close") == 1
    assert 0 <= trace.times("tls_close")[0] - device_keep_alive_end <= EVENT_CHECK


@pytest.mark.parametrize(
    "offset, reused",
    [
        pytest.param(-100, True, id="before-the-device-keep-alive"),
        pytest.param(0, False, id="at-the-device-keep-alive"),
    ],
)
def test_delivery_reuses_a_connection_only_below_the_device_keep_alive(
    simulate, record_property, offset, reused
):
    evidence(
        record_property,
        f"submission {offset} ms from the 55 s device keep-alive",
        TRANSPORT + "preparation-listening-and-recovery (step 6); P26-KEEPALIVE",
        "reused while idle for less than the device keep-alive, otherwise a new setup; DELIVERED",
    )
    submit = BOOT_HANDSHAKE + 60_000 - KEEP_ALIVE_MARGIN + offset
    trace = simulate(
        "server_keep_alive 60\n" + plan("exchange", [201]),
        until=submit + GLOBAL + 1_000,
        submit=submit,
    )
    assert trace.times("tls_result")[0] == BOOT_HANDSHAKE
    assert trace.last("delivery_outcome") == DELIVERED
    new_setups = between(trace, "tls", submit, trace.times("exchange")[0] + 1)
    assert (new_setups == []) == reused
