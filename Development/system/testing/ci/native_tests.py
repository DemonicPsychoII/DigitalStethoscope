"""Run instrumented ztest logic and retain logs plus a JUnit execution record."""

import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from build_support import APP, ROOT, build_env, west_command


def report(output: str, returncode: int, target: Path) -> None:
    names = re.findall(r"\bPASS - (test_\w+)", output)
    passed = (
        returncode == 0 and "PROJECT EXECUTION SUCCESSFUL" in output and bool(names)
    )
    suite = ET.Element(
        "testsuite",
        name="bringup.logic",
        tests=str(len(names) if passed else 1),
        failures="0" if passed else "1",
    )
    if passed:
        for name in names:
            ET.SubElement(suite, "testcase", name=name, classname="app_logic")
    else:
        case = ET.SubElement(suite, "testcase", name="native_execution")
        ET.SubElement(
            case, "failure", message="native tests did not complete successfully"
        ).text = output
    ET.ElementTree(suite).write(target, encoding="utf-8", xml_declaration=True)
    if not passed:
        raise RuntimeError("native tests failed or reported no executed test cases")


def main() -> None:
    target = ROOT / "artifacts/native"
    target.mkdir(parents=True, exist_ok=True)
    workspace = ROOT / ".ci-workspace"
    env = build_env(workspace)
    env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    build = ROOT / "build-logic"
    command = [
        *west_command(workspace),
        "build",
        "--pristine=always",
        "-b",
        "native_sim/native/64",
        str(APP / "tests/logic"),
        "-d",
        str(build),
        "--",
        "-DCONFIG_ASAN=y",
        "-DCONFIG_UBSAN=y",
    ]
    with (target / "build.log").open("w") as stream:
        result = subprocess.run(
            command, env=env, stdout=stream, stderr=subprocess.STDOUT
        )
    print((target / "build.log").read_text())
    if result.returncode:
        raise SystemExit(result.returncode)
    result = subprocess.run(
        [str(build / "zephyr/zephyr.exe")],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    print(result.stdout)
    (target / "execution.log").write_text(result.stdout)
    report(result.stdout, result.returncode, target / "junit.xml")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
            stream.write(
                "### Native logic: PASS (ASan + UBSan; simulated, not target evidence)\n"
            )


if __name__ == "__main__":
    main()
