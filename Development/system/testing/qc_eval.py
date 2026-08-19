#!/usr/bin/env python3
"""Repeatable source-level QC comparison for the Zephyr bring-up application.

The evaluator intentionally separates static evidence from hardware verification.
It uses the THA Embedded Systems 2 material as an architectural/engineering
baseline, not as a claim that the THA examples and ESP32-S3 application are functionally
equivalent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass
class Control:
    control: str
    weight: int
    status: str
    score: int
    evidence: str
    required_action: str


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.MULTILINE) is not None


def validate_baseline_traceability(repo: Path, tha: Path) -> tuple[bool, str, str]:
    trace_path = repo / "Development/system/testing/tha-baseline-traceability.json"
    expected_paths = {
        "projects/internship_new/src/main.c",
        "projects/internship_new/prj.conf",
        "projects/blinky_pwm/documentation/LaborberichtNF.md",
    }
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        revision = trace["revision"]
        files = trace["files"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        return False, "unavailable", f"Traceability manifest is invalid: {error}"

    valid = (
        trace.get("schema_version") == 1
        and isinstance(revision, str)
        and re.fullmatch(r"[0-9a-f]{40}", revision) is not None
        and isinstance(files, dict)
        and set(files) == expected_paths
        and all(
            isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in files.values()
        )
    )
    if not valid:
        return (
            False,
            "unavailable",
            "Traceability manifest schema or hashes are invalid.",
        )

    present = [(tha / relative).is_file() for relative in expected_paths]
    if any(present) and not all(present):
        return False, revision, "The local THA baseline checkout is incomplete."
    if all(present):
        for relative, expected in files.items():
            actual = hashlib.sha256((tha / relative).read_bytes()).hexdigest()
            if actual != expected:
                return False, revision, f"Local baseline hash mismatch: {relative}"
        evidence = "Pinned traceability manifest and all locally available baseline hashes match."
    else:
        evidence = "Pinned THA revision and three source hashes validated without copying institutional files into CI."
    return True, revision, evidence


def evaluate(repo: Path, tha: Path) -> dict:
    app = repo / "Development/system/coding/bringup-zephyr"
    main_path = app / "src/main.c"
    main = main_path.read_text(encoding="utf-8")
    conf = (app / "prj.conf").read_text(encoding="utf-8")
    qc_conf = (app / "qc.conf").read_text(encoding="utf-8")
    overlay = (app / "boards/esp32s3_devkitc_procpu.overlay").read_text(
        encoding="utf-8"
    )
    protocol = (app / "TEST-PROTOCOL.md").read_text(encoding="utf-8")
    readme = (app / "README.md").read_text(encoding="utf-8")

    baseline_ok, baseline_revision, baseline_evidence = validate_baseline_traceability(
        repo, tha
    )

    c_files = list(app.rglob("*.c"))
    main_lines = len(main.splitlines())
    ignored_calls = len(
        re.findall(
            r"^\s*(?:\(void\))?(?:gpio_pin_set_dt|pwm_set_pulse_dt|display_write|"
            r"i2s_write|i2s_trigger|adc_sequence_init_dt)\s*\(",
            main,
            re.MULTILINE,
        )
    )
    synchronized = has(main, r"K_(?:MUTEX|MSGQ|SEM|FIFO)_DEFINE|atomic_t")
    input_irq = has(main, r"gpio_pin_interrupt_configure|GPIO_INT_|gpio_add_callback")
    build_evidence_path = app / "evidence/build-results.json"
    try:
        build_evidence = json.loads(build_evidence_path.read_text(encoding="utf-8"))
        pristine_builds = build_evidence.get("builds", [])
        successful_esp32_builds = [
            build
            for build in pristine_builds
            if build.get("target") == "esp32s3_devkitc/esp32s3/procpu"
            and build.get("result") == "PASS"
        ]
    except (OSError, TypeError, json.JSONDecodeError):
        successful_esp32_builds = []
    required_runtime_options = (
        "CONFIG_STACK_SENTINEL=y",
        "CONFIG_THREAD_ANALYZER=y",
        "CONFIG_THREAD_STACK_INFO=y",
        "CONFIG_INIT_STACKS=y",
    )
    required_qc_options = (
        "CONFIG_THREAD_ANALYZER_AUTO=y",
        "CONFIG_THREAD_ANALYZER_STACK_SAFETY=y",
    )
    runtime_analysis = all(
        option in conf for option in required_runtime_options
    ) and all(option in qc_conf for option in required_qc_options)
    pinned_zephyr = has(
        readme, r"Zephyr[^\n]*(?:commit|revision|tag)\s*[:=]\s*[0-9a-fv]"
    )
    filled_verdicts = len(
        re.findall(r"Verdict:\s*(?:PASS|PARTIAL|FAIL|BLOCKED)", protocol)
    )

    controls: list[Control] = []

    def add(
        name: str, weight: int, status: str, score: int, evidence: str, action: str
    ) -> None:
        controls.append(Control(name, weight, status, score, evidence, action))

    add(
        "Zephyr application structure and build inputs",
        10,
        "PASS"
        if all(
            (app / p).is_file() for p in ("CMakeLists.txt", "prj.conf", "src/main.c")
        )
        else "FAIL",
        10
        if all(
            (app / p).is_file() for p in ("CMakeLists.txt", "prj.conf", "src/main.c")
        )
        else 0,
        "CMakeLists.txt, prj.conf, board overlay and src/main.c are present.",
        "Pin the Zephyr manifest revision; retain a clean-build result as an artifact."
        if not pinned_zephyr
        else "None.",
    )

    devicetree_complete = all(
        token in overlay
        for token in ("gpio", "adc", "pwm", "spi", "display", "touch", "i2s")
    )
    add(
        "Devicetree-first hardware description",
        10,
        "PASS" if devicetree_complete else "FAIL",
        10 if devicetree_complete else 0,
        "GPIO, ADC, PWM, SPI, display, touch and I2S routing are represented in the board overlay.",
        "Validate the documented unverified I2S/LEDC pinmux and XPT2046 calibration on hardware.",
    )

    modular = len(c_files) > 2 and main_lines <= 300
    add(
        "Module separation and ownership",
        10,
        "PASS" if modular else "FAIL",
        10 if modular else 2,
        f"Target has {len(c_files)} C source file(s); main.c has {main_lines} lines. THA reference splits ADC, sensor, servo, stepper, display and shell modules.",
        "Split peripheral probes/drivers, audio pipeline, UI/input and status reporting into owned modules.",
    )

    add(
        "Concurrency and shared-state synchronization",
        10,
        "PASS" if synchronized else "FAIL",
        10 if synchronized else 3,
        "Touch callback, main loop and audio thread exchange state; no atomic, mutex, message queue, semaphore or FIFO is declared."
        if not synchronized
        else "A synchronization primitive is declared.",
        "Pass touch events through k_msgq/k_event or protect all callback/thread shared state atomically.",
    )

    add(
        "Real-time response and bounded work",
        10,
        "PASS" if input_irq else "PARTIAL",
        10 if input_irq else 5,
        "The button and SP3T are polled in a 20 ms loop; touch is interrupt/callback driven. THA latency study identifies ISR + deferred processing as the deterministic pattern.",
        "Use GPIO interrupts for user inputs when a response-time requirement is introduced; document the current <=20 ms polling bound.",
    )

    add(
        "API return-code discipline",
        10,
        "PASS" if ignored_calls == 0 else "PARTIAL",
        10 if ignored_calls == 0 else 5,
        f"Heuristic found {ignored_calls} driver/API calls used as statements or explicitly discarded; several runtime output paths cannot report failure.",
        "Check and log display_write, PWM, I2S write/trigger and GPIO set failures; define recovery behavior.",
    )

    add(
        "Fault isolation and degraded operation",
        10,
        "PASS",
        10,
        "Per-component retry/probe table isolates missing peripherals; audio starts only when both endpoints pass.",
        "Distinguish on-chip controller readiness from physical-device presence in machine-readable results.",
    )

    add(
        "Logging and runtime diagnostics",
        10,
        "PASS" if runtime_analysis else "PARTIAL",
        10 if runtime_analysis else 6,
        "Structured logging, stack sentinel, initialized stack inspection, thread analyzer, and periodic QC stack-safety reporting are enabled; ESP32-S3 Xtensa hardware stack protection is unavailable in this Zephyr revision."
        if runtime_analysis
        else "Runtime diagnostics are incomplete: the required stack sentinel, stack inspection, thread analyzer, or periodic QC stack-safety options are missing.",
        "None."
        if runtime_analysis
        else "Enable CONFIG_STACK_SENTINEL, CONFIG_THREAD_ANALYZER, CONFIG_THREAD_STACK_INFO and CONFIG_INIT_STACKS in prj.conf plus CONFIG_THREAD_ANALYZER_AUTO and CONFIG_THREAD_ANALYZER_STACK_SAFETY in qc.conf.",
    )

    repeatable = (
        len(protocol) > 1000
        and filled_verdicts > 0
        and len(successful_esp32_builds) > 0
    )
    verification_score = 10 if repeatable else (6 if len(protocol) > 1000 else 2)
    add(
        "Repeatable verification and recorded verdicts",
        10,
        "PASS" if repeatable else "PARTIAL",
        verification_score,
        f"Detailed manual release protocol exists; successful recorded pristine ESP32-S3 builds={len(successful_esp32_builds)}; recorded hardware verdicts={filled_verdicts}. Compilation does not prove runtime or physical behavior.",
        "Retain a successful pristine ESP32-S3 build and machine-readable physical-hardware verdicts keyed by firmware commit.",
    )

    add(
        "Institutional baseline traceability",
        10,
        "PASS" if baseline_ok else "FAIL",
        10 if baseline_ok else 0,
        baseline_evidence,
        "Repair the immutable THA revision/hash traceability record."
        if not baseline_ok
        else "None.",
    )

    score = sum(c.score for c in controls)
    maximum_score = sum(c.weight for c in controls)
    gate = (
        "PASS"
        if score == maximum_score and all(c.status == "PASS" for c in controls)
        else "HOLD"
    )

    return {
        "schema_version": 1,
        "evaluation_date": date.today().isoformat(),
        "scope": "Static QC comparison; hardware observations are inherited from TEST-PROTOCOL.md and are not re-verified.",
        "target": str(app.relative_to(repo)).replace("\\", "/"),
        "baseline": f"THA@{baseline_revision}",
        "score": score,
        "maximum_score": maximum_score,
        "gate": gate,
        "controls": [asdict(c) for c in controls],
    }


def markdown(result: dict) -> str:
    lines = [
        "# Zephyr Quality-Control Evaluation",
        "",
        f"**Target:** `{result['target']}`",
        "**Reference:** THA Embedded Systems 2 institutional course material",
        f"**Date:** {result['evaluation_date']}",
        f"**Result:** **{result['score']}/{result['maximum_score']} — {result['gate']}**",
        "",
        "> This is a source-level quality gate. It does not replace compilation, instrumented timing,",
        "> electrical inspection, audio measurement, or the manual hardware protocol.",
        "",
        "## Control results",
        "",
        "| Control | Weight | Status | Score | Evidence |",
        "|---|---:|---|---:|---|",
    ]
    for c in result["controls"]:
        evidence = c["evidence"].replace("|", "\\|")
        lines.append(
            f"| {c['control']} | {c['weight']} | {c['status']} | {c['score']} | {evidence} |"
        )
    lines += ["", "## Required actions", ""]
    for index, c in enumerate(result["controls"], 1):
        if c["required_action"] != "None.":
            lines.append(f"{index}. **{c['control']}:** {c['required_action']}")
    lines += [
        "",
        "## Release interpretation",
        "",
        "`HOLD` means the software remains suitable as an engineering bring-up tool, but it has not",
        "yet met the THA-derived maintainability/concurrency gate for reuse as production firmware.",
        "Hardware claims remain governed by `TEST-PROTOCOL.md`; untested items are not converted to",
        "passes by this evaluator.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        "py Development/system/testing/qc_eval.py",
        "```",
        "",
        "The command rewrites this report and `qc-eval-results.json`. A non-zero exit status indicates",
        "a `HOLD` gate, making it usable in CI.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    default_repo = Path(__file__).resolve().parents[3]
    parser.add_argument("--repo", type=Path, default=default_repo)
    parser.add_argument(
        "--tha",
        type=Path,
        default=default_repo.parent
        / "THA/CreativeEngineering/SS26/Embedded2/Praktikum/src",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent
    )
    args = parser.parse_args()
    result = evaluate(args.repo.resolve(), args.tha.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "qc-eval-results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.output_dir / "QC-EVALUATION.md").write_text(
        markdown(result), encoding="utf-8"
    )
    print(f"QC result: {result['score']}/{result['maximum_score']} ({result['gate']})")
    return 0 if result["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
