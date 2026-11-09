"""VT-15: persistent Device registration in L2_COMMUNICATION, on the host simulation."""

import pytest

from test_communication import create_simulation_runner, executable, plan

assert executable  # Session fixture shared with the VT-14 simulation.

DESIGN = "Development/system/design/COMMUNICATION/server-communication.md#"
FLOW = DESIGN + "registration-flow-and-recovery"
RECORD = DESIGN + "registration-record"
IDENTITY = DESIGN + "physical-identity-and-server-binding"
RETRY = 60_000
ATTEMPT = 10_000
READY_STORED = "Device registration ready: Device/7400"
READY_NEW = "Device registration ready: Device/7501"
FAILURE = "DEVICE_REGISTRATION_FAILURE"
ENOTCONN = -107
ECONNREFUSED = -111
EIO = -5
UNAVAILABLE = "registration unavailable until restart"


@pytest.fixture
def simulate(executable, record_property):
    run = create_simulation_runner(executable, record_property)

    def registration(script="", until=5_000, server=True):
        return run(f"server {int(server)}\n" + script, until=until, stored=True)

    return registration


def evidence(record_property, scenario, basis, expected):
    record_property("scenario", "registration-" + scenario)
    record_property("vt_id", "VT-15")
    record_property("basis", basis)
    record_property("expected", expected)


def assert_registered_once(trace):
    assert trace.count("registration_read") == 1
    assert trace.values("exchange_device") == [1] * trace.count("exchange")
    assert trace.values("exchange_conditional") == [1] * trace.count("exchange")
    assert trace.values("exchange_body_identity") == [1] * trace.count("exchange")


def test_ready_from_stored_record(simulate, record_property):
    evidence(
        record_property, "stored", RECORD, "matching record: ready without a request"
    )
    trace = simulate("registration 1\n")
    assert trace.count("exchange") == 0 and trace.count("registration_write") == 0
    assert READY_STORED in trace.production_log
    assert FAILURE not in trace.production_log


@pytest.mark.parametrize(
    "record, status",
    [
        pytest.param(0, 201, id="no-record-created"),
        pytest.param(0, 200, id="no-record-existing-match"),
        pytest.param(2, 201, id="record-of-another-base-url"),
        pytest.param(3, 201, id="record-of-unsupported-version"),
        pytest.param(-22, 201, id="record-of-another-size"),
    ],
)
def test_conditional_registration(simulate, record_property, record, status):
    evidence(
        record_property,
        f"record {record}, status {status}",
        FLOW,
        "one conditional POST /Device, record saved, then ready",
    )
    setting = (
        f"registration_read_error {record}\n"
        if record < 0
        else f"registration {record}\n"
    )
    trace = simulate(setting + plan("exchange", [status]))
    assert_registered_once(trace)
    assert trace.count("exchange") == 1
    trace.before("tls_result", "exchange")
    assert trace.values("registration_saved") == [1]
    assert READY_NEW in trace.production_log
    assert FAILURE not in trace.production_log


@pytest.mark.parametrize(
    "first",
    [
        pytest.param(412, id="multiple-matches"),
        pytest.param(503, id="server-error"),
        pytest.param(501, id="unsupported"),
        pytest.param(401, id="rejected"),
        pytest.param(1, id="no-id-in-response"),
        pytest.param(2, id="representation-of-another-device"),
    ],
)
def test_failure_latches_and_retries_after_gap(simulate, record_property, first):
    evidence(
        record_property,
        f"first response {first}",
        FLOW,
        "DEVICE_REGISTRATION_FAILURE, no save, conditional retry 60 s later, then ready",
    )
    trace = simulate(plan("exchange", [first, 201]), until=75_000)
    assert_registered_once(trace)
    first_result, second_request = (
        trace.times("exchange_result")[0],
        trace.times("exchange")[1],
    )
    assert RETRY <= second_request - first_result <= RETRY + 1_000
    assert trace.count("exchange") == 2
    assert trace.values("registration_saved") == [1]
    assert trace.production_log.count(FAILURE) == 1
    assert READY_NEW in trace.production_log


def assert_retry_gaps(trace, gaps):
    requests = trace.times("exchange")
    results = trace.times("exchange_result")
    for result_time, next_request, gap in zip(results, requests[1:], gaps):
        assert gap <= next_request - result_time <= gap + 1_000


def test_failure_latches_once_per_episode(simulate, record_property):
    evidence(
        record_property,
        "two failures",
        FLOW,
        "one alert for the episode; the retry gap doubles from 60 s",
    )
    trace = simulate(plan("exchange", [503, 503, 201]), until=200_000)
    assert trace.count("exchange") == 3
    assert_retry_gaps(trace, [RETRY, 2 * RETRY])
    assert trace.production_log.count(FAILURE) == 1
    assert READY_NEW in trace.production_log


def test_fourth_failure_makes_registration_unavailable(simulate, record_property):
    evidence(
        record_property,
        "four failures",
        FLOW,
        "gaps 60 s, 120 s, 240 s; after the fourth failure no request until restart",
    )
    trace = simulate(plan("exchange", [503] * 5), until=1_000_000)
    assert trace.count("exchange") == 4
    assert_retry_gaps(trace, [RETRY, 2 * RETRY, 4 * RETRY])
    assert trace.production_log.count(FAILURE) == 1
    assert "registration unavailable until restart" in trace.production_log
    assert READY_NEW not in trace.production_log


def test_stale_retained_connection_is_replaced_within_the_attempt(
    simulate, record_property
):
    evidence(
        record_property,
        "stale connection",
        DESIGN + "observation-construction-and-delivery",
        "reconnect and send again inside the same attempt, without an alert",
    )
    trace = simulate(plan("tls", [0, 0]) + plan("exchange", [ENOTCONN, 201]))
    assert trace.count("tls") == 2 and trace.count("exchange") == 2
    first_request, second_request = trace.times("exchange")
    assert second_request - first_request < ATTEMPT
    assert trace.values("registration_saved") == [1]
    assert FAILURE not in trace.production_log
    assert READY_NEW in trace.production_log


def test_failed_reconnect_inside_the_attempt_waits_for_the_gap(
    simulate, record_property
):
    evidence(
        record_property,
        "stale connection, reconnect fails",
        FLOW,
        "no further issued preparation before 60 s after the failed attempt",
    )
    trace = simulate(
        plan("tls", [0, -111, 0]) + plan("exchange", [ENOTCONN, 201]), until=75_000
    )
    connects = trace.times("tls")
    failed_reconnect = trace.times("tls_result")[1]
    assert len(connects) == 3
    assert connects[2] - failed_reconnect >= RETRY
    assert trace.production_log.count(FAILURE) == 1
    assert READY_NEW in trace.production_log


def test_save_failure_keeps_the_id_and_saves_again_without_a_request(
    simulate, record_property
):
    evidence(
        record_property,
        "record save fails once",
        FLOW,
        "not ready until saved; the retry saves the kept id without a second POST",
    )
    trace = simulate(
        "registration_write_failures 1\n" + plan("exchange", [201]), until=75_000
    )
    assert trace.count("exchange") == 1
    first_write, second_write = trace.times("registration_write")
    assert RETRY <= second_write - first_write <= RETRY + 1_000
    assert trace.values("registration_saved") == [1]
    assert trace.production_log.count(FAILURE) == 1
    assert trace.production_log.index(READY_NEW) > trace.production_log.index(FAILURE)


def test_exchange_timeout_is_cancelled_at_the_attempt_deadline(
    simulate, record_property
):
    evidence(
        record_property, "no response", FLOW, "cancel at 10 s, alert, retry 60 s later"
    )
    trace = simulate(
        plan("exchange", [201], delay=30_000) + plan("exchange", [201]), until=80_000
    )
    first_request = trace.times("exchange")[0]
    cancel = trace.times("secure_cancel")[0]
    assert cancel - first_request <= ATTEMPT
    assert trace.values("secure_cancel")[0] == 1
    assert trace.count("exchange") == 2
    assert RETRY <= trace.times("exchange")[1] - cancel <= RETRY + 1_000
    assert trace.production_log.count(FAILURE) == 1
    assert READY_NEW in trace.production_log


def test_listening_interrupts_without_alert(simulate, record_property):
    evidence(
        record_property,
        "Start during the request",
        FLOW,
        "cancelled at once, no alert; the next attempt waits for the gap",
    )
    script = plan("exchange", [201], delay=5_000) + plan("exchange", [201])
    script += "event 1000 start 0\nevent 2000 stop 0\n"
    trace = simulate(script, until=70_000)
    cancel = trace.times("secure_cancel")[0]
    assert cancel <= 1_000 + 200
    assert FAILURE not in trace.production_log
    assert trace.count("exchange") == 2
    assert trace.times("exchange")[1] - cancel >= RETRY
    assert READY_NEW in trace.production_log


@pytest.mark.parametrize(
    "script",
    [
        pytest.param("identity_error -5\n", id="identity-read-failure"),
        pytest.param("registration_read_error -5\n", id="record-read-failure"),
    ],
)
def test_unavailable_registration_never_sends(simulate, record_property, script):
    evidence(
        record_property,
        script.split()[0],
        IDENTITY,
        "alert once, no request until restart",
    )
    trace = simulate(script, until=135_000)
    assert trace.count("exchange") == 0
    assert trace.production_log.count(FAILURE) == 1
    assert "registration unavailable until restart" in trace.production_log


def test_transport_failure_defers_registration(simulate, record_property):
    evidence(
        record_property,
        "TLS fails",
        FLOW,
        "registration needs verified transport: no request, no registration alert",
    )
    trace = simulate(plan("tls", [-111]), until=30_000)
    assert trace.count("exchange") == 0
    assert "SERVER_CONNECTION_FAILURE" in trace.production_log
    assert FAILURE not in trace.production_log


def log_times(trace, text):
    return [
        int(line.partition(" ")[0])
        for line in trace.production_log.splitlines()
        if text in line
    ]


def test_interrupted_attempt_does_not_count_toward_the_failure_limit(
    simulate, record_property
):
    evidence(
        record_property,
        "Start interrupts the first attempt, then only 503",
        FLOW,
        "interrupted attempt waits 60 s but is not counted: four failed attempts follow "
        "(gaps 60 s, 120 s, 240 s), then unavailable until restart",
    )
    script = plan("exchange", [201], delay=5_000) + plan("exchange", [503] * 5)
    script += "event 1000 start 0\nevent 2000 stop 0\n"
    trace = simulate(script, until=1_000_000)
    cancel = trace.times("secure_cancel")[0]
    assert cancel <= 1_000 + 200
    requests = trace.times("exchange")
    assert len(requests) == 5
    assert requests[1] - trace.times("secure_cancel_done")[0] >= RETRY
    failures = trace.times("exchange_result")
    assert len(failures) == 4
    for failure, next_request, gap in zip(
        failures, requests[2:], [RETRY, 2 * RETRY, 4 * RETRY]
    ):
        assert gap <= next_request - failure <= gap + 1_000
    alerts = log_times(trace, FAILURE)
    assert len(alerts) == 1
    assert alerts[0] >= failures[0]
    assert log_times(trace, UNAVAILABLE)[0] >= requests[-1]


def test_missing_prerequisites_consume_no_attempt(simulate, record_property):
    evidence(
        record_property,
        "transport unverified for 60 s, then only 503",
        FLOW,
        "no attempt while verified TLS is missing; afterwards all four failed attempts "
        "remain, then unavailable until restart",
    )
    script = plan("tls", [ECONNREFUSED, 0]) + plan("exchange", [503] * 5)
    trace = simulate(script, until=1_000_000)
    verified = log_times(trace, "Server connection verified")[0]
    assert trace.values("tls_result")[:2] == [ECONNREFUSED, 0]
    assert trace.times("tls")[1] - trace.times("tls_result")[0] >= RETRY
    requests = trace.times("exchange")
    assert len(requests) == 4
    assert requests[0] >= verified
    assert_retry_gaps(trace, [RETRY, 2 * RETRY, 4 * RETRY])
    assert log_times(trace, UNAVAILABLE)[0] >= requests[-1]


def test_without_server_profile_nothing_is_read_or_sent(simulate, record_property):
    evidence(record_property, "no server profile", FLOW, "registration not applicable")
    trace = simulate(until=30_000, server=False)
    assert trace.count("identity") == 0 and trace.count("registration_read") == 0
    assert trace.count("exchange") == 0 and trace.count("tls") == 0
    assert FAILURE not in trace.production_log
