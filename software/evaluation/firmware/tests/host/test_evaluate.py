"""Exercise the CLI and real C runner together, including filter independence."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools/evaluate.py"


def test_provenance_uses_actual_repository_from_another_cwd(tmp_path, monkeypatch):
    repository = Path(__file__).resolve().parents[5]
    spec = importlib.util.spec_from_file_location("evaluate_provenance", TOOL)
    evaluate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluate)
    assert evaluate.ROOT == repository
    expected_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    expected_dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repository
    ))
    check_output = subprocess.check_output
    calls = []

    def checked_output(argv, **kwargs):
        calls.append((argv, kwargs["cwd"]))
        return check_output(argv, **kwargs)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(evaluate.subprocess, "check_output", checked_output)
    result = evaluate.provenance()
    assert calls == [
        (["git", "rev-parse", "HEAD"], repository),
        (["git", "status", "--porcelain"], repository),
    ]
    assert result["git_commit"] == expected_commit
    assert result["working_tree_modified"] == expected_dirty
    assert result["dsp_sha256"] == hashlib.sha256(
        (TOOL.parent.parent / "src/stetho_dsp.c").read_bytes()
    ).hexdigest()


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
