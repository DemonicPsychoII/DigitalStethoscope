"""VT-14: actual portal handlers, buffers and published page."""

import json
from pathlib import Path
from urllib.parse import parse_qs
import re
import subprocess

import pytest

PORTAL = "Development/system/design/PORTAL/interfaces-and-behavior.md#"
EXIT = PORTAL + "form-navigation-and-setup-exit"
REQUESTS = PORTAL + "requests-and-published-state"
CASES = []


def add(scenario, operation, argument, expected, basis, description):
    CASES.append(
        pytest.param(
            scenario, operation, argument, expected, basis, description, id=scenario
        )
    )


for name, body, expected in (
    ("protected", "network=selected-network&password=test-password", 202),
    ("plus-and-percent", "network=selected%2Dnetwork&password=test+password%21", 202),
    ("missing-name", "password=test-password", 400),
    ("missing-password", "network=selected-network", 400),
    ("empty-name", "network=&password=", 400),
    ("short-password", "network=selected-network&password=short", 400),
    ("open-password-on-protected", "network=selected-network&password=", 400),
    ("not-listed", "network=other&password=test-password", 400),
    ("bad-percent", "network=selected%GGnetwork&password=test-password", 400),
    ("trailing-percent", "network=selected-network&password=test-password%", 400),
    ("single-hex", "network=selected-network&password=test-password%2", 400),
    ("embedded-nul", "network=selected-network%00other&password=test-password", 400),
    ("ssid-overflow", "network=" + "n" * 33 + "&password=test-password", 400),
    ("password-overflow", "network=selected-network&password=" + "p" * 65, 400),
    ("nonhex-key", "network=selected-network&password=" + "g" * 64, 400),
    ("hex-key", "network=selected-network&password=" + "0123456789abcdef" * 4, 202),
    ("body-overflow", "network=selected-network&password=" + "p" * 321, 413),
):
    add(
        "portal-form-" + name,
        "form",
        body,
        expected,
        EXIT,
        "Decode a bounded listed network form; accept valid credentials with 202, reject malformed fields with 400 and oversized bodies with 413; erase form and consumed queue buffers.",
    )
for name, operation, body, expected in (
    ("open", "form-open", "network=open-network&password=", 202),
    (
        "open-with-password",
        "form-open",
        "network=open-network&password=test-password",
        400,
    ),
    (
        "maximum-name-passphrase",
        "form-maximum",
        "network=" + "N" * 32 + "&password=" + "p" * 63,
        202,
    ),
    (
        "maximum-encoded",
        "form-maximum",
        "network=" + "%4E" * 32 + "&password=" + "%61" * 64,
        202,
    ),
):
    add(
        "portal-form-" + name,
        operation,
        body,
        expected,
        EXIT,
        "Accept empty credentials only for an open SSID; accept 32-byte names, 63-byte passphrases and a fully encoded 64-hex-digit key within the form bound.",
    )
for status, name in (
    (0, "scanning"),
    (2, "connecting"),
    (4, "connected"),
    (5, "save-failed"),
    (6, "closing"),
):
    add(
        "portal-gate-" + name,
        "gate",
        str(status),
        None,
        EXIT,
        "Connect, Rescan, Cancel and Activity outside selection return 409 without queueing a request.",
    )
for scenario, operation, basis, description in (
    (
        "portal-routing-status-semantics",
        "routing",
        EXIT,
        "Registered paths and method masks drive a pinned-router substitute: unknown paths return 404 and unsupported methods return 405. Real socket routing remains a target check.",
    ),
    (
        "portal-fragmented-body-too-large",
        "fragment-overflow",
        EXIT,
        "An aggregate form body above the limit returns 413, queues nothing and erases its fragments.",
    ),
    (
        "portal-fragment-client-ownership",
        "fragment-owner",
        EXIT,
        "A second client receives 409 for a concurrent form; its poll and abort cannot steal or clear the first client's fragments. Production handler owns the form; HTTP scheduling is substituted.",
    ),
    (
        "portal-abort-wipes-form",
        "abort-wipes",
        EXIT,
        "Abort erases the form and releases ownership for another client.",
    ),
    (
        "portal-queue-four-full-503",
        "queue-full",
        EXIT,
        "Four queued requests fit; the fifth returns 503 without changing selection or the queue.",
    ),
    (
        "portal-post-failure-rescan-gate",
        "post-failure-rescan",
        EXIT,
        "Rescan after failed join is accepted with 202; Connect stays 409 throughout scanning until the completed list permits selection, then returns 202.",
    ),
    (
        "portal-stop-wipes-queue-and-form",
        "stop-wipes",
        REQUESTS,
        "Stop erases unread credentials and partial form storage and rejects further commands.",
    ),
    (
        "portal-restart-clears-state",
        "restart-clears",
        EXIT,
        "Restart clears credentials, address and error and selects the retained completed list.",
    ),
    (
        "portal-start-readiness-timeout",
        "start-timeout",
        "Development/system/design/WIFI/parameters.md",
        "No HTTP listener by one second fails startup and rejects commands; listener readiness is substituted.",
    ),
):
    add(scenario, operation, "", None, basis, description)
for delay, result in ((0, 0), (1000, 0), (2000, 1)):
    add(
        f"portal-stop-confirmation-{delay}",
        "stop-confirmation",
        str(delay),
        (result, min(delay, 1000)),
        REQUESTS,
        "A shutdown-in-progress -EALREADY needs listener completion evidence within one second; timeout prevents restart until confirmed stopped. Socket completion is substituted.",
    )
for name in ("stopped", "already-stopped"):
    add(
        "portal-no-listener-stop-" + name,
        "no-listener-stop",
        name,
        None,
        REQUESTS,
        "Startup without a listener fails; stopped or -EALREADY with a negative descriptor after the bounded wait confirms teardown and permits a later manual retry. HTTP readiness and stop results are substituted; HOTSPOT_START_FAILURE/manual hold is checked separately in L2.",
    )
for name, value in (
    ("html", "<img src=x onerror=alert(1)>"),
    ("quotes", "name\\\"'&<>"),
    ("controls", "network\n\t\x01"),
    ("maximum", '"' * 32),
):
    add(
        "portal-json-" + name,
        "status-json",
        value,
        None,
        EXIT,
        "All 16 SSIDs yield valid bounded JSON without raw control characters; polling queues no request.",
    )


@pytest.mark.parametrize(
    "scenario,operation,argument,expected,basis,description", CASES
)
def test_portal_service(
    scenario,
    operation,
    argument,
    expected,
    basis,
    description,
    service,
    record_property,
):
    for name, value in (
        ("scenario", scenario),
        ("vt_id", "VT-14"),
        ("basis", basis),
        ("expected", description),
    ):
        record_property(name, value)
    output = service("portal", operation, argument)
    if operation.startswith("form"):
        lines = output.splitlines()
        assert int(lines[0]) == expected
        if expected == 202:
            decoded = parse_qs(argument, keep_blank_values=True)
            assert lines[1] == decoded["network"][0]
            assert lines[2] == decoded["password"][0]
    elif operation == "stop-confirmation":
        assert tuple(map(int, output.split())) == expected
    elif operation == "status-json":
        status = json.loads(output)
        assert len(status["networks"]) == 16
        for index, network in enumerate(status["networks"]):
            assert network["name"] == re.sub(r"[\x00-\x1f]", "?", argument)
            assert network["password"] == (index % 2 != 0)


def test_page_html_and_p24(service, record_property, page_javascript_runtime):
    record_property("scenario", "portal-page-html-escaping-activity-and-poll")
    record_property("vt_id", "VT-14")
    record_property("basis", EXIT + "; Development/system/design/WIFI/parameters.md")
    record_property(
        "expected",
        "Render hostile SSIDs as text in list/form/result; Activity at most once per second; poll every second; open networks hide passwords. DOM and fetch are substitutes.",
    )
    page = service("portal", "page")
    script = page.split("<script>", 1)[1].split("</script>", 1)[0]
    record_property("javascript_runtime", str(page_javascript_runtime))
    harness = (
        r"""
const assert = require('node:assert/strict');
let timeMilliseconds = 10000;
let calls = [], timers = [];
let element = {innerHTML: ''};
global.document = {getElementById: () => element};
global.Date.now = () => timeMilliseconds;
global.fetch = (path, options) => {
  calls.push([path, options]);
  return Promise.resolve({json: () => Promise.resolve({status:'selecting',networks:[]}),ok:true});
};
global.setTimeout = (callback, delay) => timers.push(delay);
"""
        + script
        + r"""
const hostileName = `<img src=x onerror='attack()'>&"`;
networks = [{name:hostileName,password:false}];
list();
assert(!element.innerHTML.includes('<img'));
assert(element.innerHTML.includes('&#60;img'));
pick(0);
assert(!element.innerHTML.includes('<img'));
assert(!element.innerHTML.includes('password-input'));
for(let index=0; index<10; index++) activity();
timeMilliseconds += 999; activity();
assert.equal(calls.filter(call => call[0] === '/activity').length,1);
timeMilliseconds += 2; activity();
assert.equal(calls.filter(call => call[0] === '/activity').length,2);
networks[0].password=true; pick(0);
assert(element.innerHTML.includes('type="password"'));
show({status:'connected',address:hostileName,cause:hostileName,networks:[]});
assert(!element.innerHTML.includes('<img'));
setImmediate(() => { assert.deepEqual(timers,[1000]); });
"""
    )
    try:
        result = subprocess.run(
            [str(page_javascript_runtime), "-e", harness],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        pytest.fail(
            f"Portal JavaScript runtime could not execute ({page_javascript_runtime}): {error}",
            pytrace=False,
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_http_inactivity_configuration(record_property):
    record_property("scenario", "portal-http-inactivity-five-seconds")
    record_property("vt_id", "VT-14")
    record_property("basis", "Development/system/design/WIFI/parameters.md")
    record_property(
        "expected",
        "The application configures a five-second HTTP client inactivity timeout; actual socket expiry remains a target check.",
    )
    configuration = Path(__file__).resolve().parents[3] / "prj.conf"
    assert re.search(
        r"^CONFIG_HTTP_SERVER_CLIENT_INACTIVITY_TIMEOUT=5$",
        configuration.read_text(),
        re.MULTILINE,
    )
