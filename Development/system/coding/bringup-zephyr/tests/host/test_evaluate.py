"""Exercise the CLI and real C runner together, including filter independence."""

import json
from pathlib import Path
import subprocess
import sys

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools/evaluate.py"


@pytest.mark.parametrize("analysis", [None, "raw", "murmur", "matched"])
def test_evaluation_records_independent_filter_paths(tmp_path, analysis):
    wav = tmp_path / "heart.wav"
    subprocess.run([sys.executable, str(TOOL), "generate", str(wav)], check=True)
    output = tmp_path / "results"
    command = [
        sys.executable,
        str(TOOL),
        "evaluate",
        str(wav),
        "--reference-bpm",
        "72",
        "--reference",
        "synthetic fixture",
        "--output",
        str(output),
    ]
    if analysis:
        command += ["--analysis-filter", analysis]
    subprocess.run(command, check=True, capture_output=True, text=True)
    report = json.loads((output / "report.json").read_text())
    names = ["raw", "murmur", "bpm"]
    assert report["analysis_mode"] == (analysis or "bpm")
    assert [r["listening_filter"] for r in report["filters"]] == names
    expected = names if analysis == "matched" else [analysis or "bpm"] * 3
    assert [r["analysis_filter"] for r in report["filters"]] == expected
    estimates = [(output / f"{name}-estimates.csv").read_bytes() for name in names]
    if analysis != "matched":
        assert estimates[0] == estimates[1] == estimates[2]
    else:
        assert len(set(estimates)) > 1
    # Listening outputs must still change even with identical analysis estimates.
    assert len({(output / f"{name}.wav").read_bytes() for name in names}) == 3
