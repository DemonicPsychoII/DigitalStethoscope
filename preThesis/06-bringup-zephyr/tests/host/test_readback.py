"""Exercise the actual readback tool against a local verified HTTPS endpoint."""

import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ssl
import subprocess
import threading
from types import SimpleNamespace
from urllib.error import URLError

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools/evaluate.py"
spec = importlib.util.spec_from_file_location("evaluate", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


@pytest.fixture
def server(tmp_path):
    key, cert = tmp_path / "key.pem", tmp_path / "ca.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ],
        check=True,
        capture_output=True,
    )
    resource = {
        "resourceType": "Observation",
        "id": "eval-1",
        "status": "final",
        "subject": {"reference": "Patient/test-patient"},
        "effectiveDateTime": "2026-09-16T12:00:00Z",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "valueQuantity": {
            "system": "http://unitsofmeasure.org",
            "code": "/min",
            "value": 72.5,
        },
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/redirect"):
                self.send_response(302)
                self.send_header("Location", "http://localhost/Observation/eval-1")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/fhir+json")
            self.end_headers()
            self.wfile.write(json.dumps(resource).encode())

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    args = SimpleNamespace(
        url=f"https://localhost:{httpd.server_port}/Observation/eval-1",
        ca=cert,
        patient="test-patient",
        bpm=72.5,
        timestamp="2026-09-16T12:00:00Z",
        output=tmp_path / "result.json",
    )
    yield args, resource
    httpd.shutdown()
    httpd.server_close()
    thread.join()


def test_valid_readback(server):
    args, _ = server
    tool.readback(args)
    assert json.loads(args.output.read_text())["verdict"] == "PASS"


@pytest.mark.parametrize("change", ["patient", "bpm", "timestamp", "id", "unit"])
def test_readback_rejects_mismatch(server, change):
    args, resource = server
    if change == "patient":
        args.patient = "wrong"
    elif change == "bpm":
        args.bpm = 80
    elif change == "timestamp":
        args.timestamp = "2026-09-16T12:00:01Z"
    elif change == "id":
        resource["id"] = "other"
    else:
        resource["valueQuantity"]["code"] = "Hz"
    with pytest.raises(ValueError):
        tool.readback(args)
    assert not args.output.exists()


def test_readback_rejects_wrong_hostname(server):
    args, _ = server
    args.url = args.url.replace("localhost", "127.0.0.1")
    with pytest.raises(URLError):
        tool.readback(args)


def test_readback_rejects_untrusted_ca(server, tmp_path):
    args, _ = server
    other = tmp_path / "other.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(tmp_path / "other.key"),
            "-out",
            str(other),
            "-days",
            "1",
            "-subj",
            "/CN=other",
        ],
        check=True,
        capture_output=True,
    )
    args.ca = other
    with pytest.raises(URLError):
        tool.readback(args)


def test_readback_refuses_plaintext_and_redirects(server):
    args, _ = server
    original = args.url
    args.url = original.replace("https:", "http:")
    with pytest.raises(ValueError):
        tool.readback(args)
    args.url = original.replace("/Observation/", "/redirect/Observation/")
    with pytest.raises(ValueError):
        tool.readback(args)
