"""VT-07: Observation delivery under P13 in L2_COMMUNICATION, on the host simulation."""

from datetime import datetime, timedelta, timezone
import json

import pytest

from test_communication import create_simulation_runner, executable, plan

assert executable  # Session fixture shared with the VT-14 simulation.

DESIGN = "Development/system/design/system/"
P13 = DESIGN + "parameters.md (P13)"
DELIVERY = DESIGN + "interfaces-and-behavior.md (delivery decision and Sending)"
SUBMIT = 1_000
GLOBAL = 10_000
RESERVE = 1_000
GAP = 2_000
NONE, PENDING, DELIVERED, FAILED, NO_CLOCK = range(5)
ENOENT, ENODEV, EBUSY = -2, -19, -16
ENOTCONN, ECONNRESET = -107, -104
SIMULATED_UTC = datetime(2026, 11, 9, tzinfo=timezone.utc)


@pytest.fixture
def simulate(executable, record_property):
    run = create_simulation_runner(executable, record_property)

    def delivery(
        script="",
        until=SUBMIT + GLOBAL + 1_000,
        kind=0,
        server=True,
        stored=True,
        submit=SUBMIT,
    ):
        script = f"server {int(server)}\nregistration 1\n" + script
        script += f"event {submit} deliver {kind}\nevent {submit + GLOBAL} outcome 0\n"
        return run(script, until=until, stored=stored)

    return delivery


def evidence(record_property, scenario, basis, expected):
    record_property("scenario", "delivery-" + scenario)
    record_property("vt_id", "VT-07")
    record_property("basis", basis)
    record_property("expected", expected)


def logged(trace, prefix):
    for line in trace.production_log.splitlines():
        _, _, text = line.partition(" ")
        if text.startswith(prefix + " "):
            return text[len(prefix) + 1 :]
    raise AssertionError(f"{prefix} not logged:\n{trace.production_log}")


def expected_end(trace, submit=SUBMIT):
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
    assert f"Observation delivered: https://192.168.2.40:8443/fhir/Observation/8001/_history/1 (status {status})" in trace.production_log
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
        plan("tls", [0, -111, -111, -111, -111, 0]) + plan("exchange", [ENOTCONN])
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
        f"event {submit - 300} sntp_fail -110\n",
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
            {"script": "identity_error -5\n"}, ENODEV, id="no-device-registration"
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


def test_outcome_is_none_before_any_job(simulate, record_property):
    evidence(record_property, "no job", DELIVERY, "NONE before the first admission")
    trace = simulate("event 500 outcome 0\n" + plan("exchange", [201]))
    assert trace.values("delivery_outcome")[0] == NONE
