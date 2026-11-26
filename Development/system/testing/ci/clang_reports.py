#!/usr/bin/env python3
"""Report clang-tidy findings, cognitive complexity, MC/DC coverage and fuzzing runs.

The host scenarios are built once more with clang's MC/DC instrumentation; their compile
commands feed clang-tidy. Two libFuzzer targets then run for a fixed time each. Every result
is information only: no finding fails, and a missing clang toolchain is reported, not run.

Writes artifacts/ci/clang/report.md and clang.json, and appends the report to the GitHub
step summary.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APPLICATION = ROOT / "Development/system/coding/app"
HOST_TESTS = APPLICATION / "tests/host"
FUZZ_TARGETS = APPLICATION / "tests/fuzz"
VENDORED_PARSER = ROOT / "Development/system/coding/third_party/zephyr-http-parser"
TIDY_CONFIGURATION = Path(__file__).with_name("clang-tidy.yaml")
REPORT = ROOT / "artifacts/ci/clang"
WORK = ROOT / "build-clang-reports"
LLVM_VERSION = "18"
COMPLEXITY_LIMIT = 25
COMPLEXITY_SHOWN = 10
DEFAULT_FUZZ_SECONDS = 60
WARNING = re.compile(
    r"^(?P<path>[^\n]+?):(?P<line>\d+):(?P<column>\d+): warning: (?P<message>.*?) \[(?P<check>[\w.,-]+)\]$",
    re.MULTILINE,
)
COMPLEXITY = re.compile(r"function '(\w+)' has cognitive complexity of (\d+)")
FUZZ_BUILDS = {
    "fhir": {
        "source": "fhir_fuzz_target.c",
        "includes": [APPLICATION / "L1_services/L1_FHIR", APPLICATION / "common"],
        "extra_sources": [],
        "function": "fhir_parseDeviceRegistration, fhir_decodeRegistrationRecord",
    },
    "http_response": {
        "source": "http_response_fuzz_target.c",
        "includes": [APPLICATION / "L1_services/L1_WIFI", APPLICATION / "common"],
        "extra_sources": [
            VENDORED_PARSER / "http_parser.c",
            VENDORED_PARSER / "http_parser_url.c",
        ],
        "function": "wifi_readHttpResponse, wifi_finishHttpResponse",
    },
}


def llvm_tool(name: str) -> str | None:
    directory = Path(
        os.environ.get("STETHO_LLVM_DIRECTORY", f"/usr/lib/llvm-{LLVM_VERSION}/bin")
    )
    if (directory / name).is_file():
        return str(directory / name)
    return shutil.which(f"{name}-{LLVM_VERSION}")


def production_file(path: str | Path) -> str | None:
    """The application-relative path of a production source, or None for tests and vendor code."""
    try:
        relative = Path(path).resolve().relative_to(APPLICATION.resolve()).as_posix()
    except ValueError:
        return None
    return None if relative.startswith("tests/") else relative


def run(argv: list[str], **options) -> subprocess.CompletedProcess:
    print("+", subprocess.list2cmdline(argv), flush=True)
    return subprocess.run(
        argv, capture_output=True, text=True, errors="replace", **options
    )


# MC/DC coverage and the compile database


def instrumented_host_run(clang: str) -> dict:
    profiles = WORK / "profiles"
    records = WORK / "compile-commands.jsonl"
    profiles.mkdir(parents=True)
    environment = os.environ.copy()
    environment.pop("STETHO_COVERAGE_DIRECTORY", None)
    environment.update(
        {
            "CC": f"{clang} -fprofile-instr-generate -fcoverage-mapping -fcoverage-mcdc -O0",
            "LLVM_PROFILE_FILE": str(profiles / "%p-%m.profraw"),
            "STETHO_SANITIZERS": "false",
            "STETHO_COMPILE_COMMANDS": str(records),
        }
    )
    results = WORK / "host.xml"
    completed = run(
        [
            *(sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"),
            f"--basetemp={WORK / 'pytest'}",
            *("-o", "junit_family=xunit1", f"--junitxml={results}"),
            str(HOST_TESTS),
        ],
        env=environment,
        cwd=ROOT,
    )
    (WORK / "host.log").write_text(completed.stdout + completed.stderr, "utf-8")
    suite = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    if results.is_file():
        root = ElementTree.parse(results).getroot()
        element = root if root.tag == "testsuite" else root.find("testsuite")
        for key in suite:
            suite[key] = int(element.get(key, 0))
    entries = []
    if records.is_file():
        entries = [
            json.loads(line) for line in records.read_text("utf-8").splitlines() if line
        ]
    return {"suite": suite, "compile_commands": entries}


def mcdc_coverage(entries: list[dict]) -> dict:
    profiles = sorted((WORK / "profiles").glob("*.profraw"))
    objects = list(
        dict.fromkeys(
            entry["output"] for entry in entries if Path(entry["output"]).is_file()
        )
    )
    if not profiles or not objects:
        raise RuntimeError("the instrumented host run left no profiles or executables")
    listing = WORK / "profiles.txt"
    listing.write_text("\n".join(map(str, profiles)) + "\n", "utf-8")
    merged = WORK / "host.profdata"
    completed = run(
        [
            llvm_tool("llvm-profdata"),
            *("merge", "-sparse", "-f", str(listing), "-o", str(merged)),
        ]
    )
    if completed.returncode:
        raise RuntimeError(f"llvm-profdata failed: {completed.stderr.strip()[:500]}")
    arguments = [objects[0]] + [
        argument for path in objects[1:] for argument in ("-object", path)
    ]
    completed = run(
        [
            llvm_tool("llvm-cov"),
            *("export", "-summary-only", f"-instr-profile={merged}"),
            *arguments,
        ]
    )
    if completed.returncode:
        raise RuntimeError(f"llvm-cov failed: {completed.stderr.strip()[:500]}")
    files = {}
    for source in json.loads(completed.stdout)["data"][0]["files"]:
        relative = production_file(source["filename"])
        summary = source["summary"]
        if relative and summary["branches"]["count"]:
            files[relative] = {
                kind: {
                    "covered": summary[kind]["covered"],
                    "count": summary[kind]["count"],
                }
                for kind in ("branches", "mcdc")
                if kind in summary
            }
    return files


# clang-tidy


def compile_database(entries: list[dict]) -> list[dict]:
    """One entry per translation unit inside this repository, as clang-tidy expects."""
    database = {}
    for entry in entries:
        command = entry["arguments"]
        sources = [argument for argument in command if argument.endswith(".c")]
        output = command.index("-o")
        flags = [
            argument
            for index, argument in enumerate(command)
            if argument not in sources and index not in (output, output + 1)
        ]
        for source in sources:
            path = Path(source).resolve()
            inside = path.is_relative_to(ROOT.resolve())
            vendored = path.is_relative_to(VENDORED_PARSER.resolve())
            if inside and not vendored and str(path) not in database:
                database[str(path)] = {
                    "directory": entry["directory"],
                    "arguments": [*flags, "-c", str(path)],
                    "file": str(path),
                }
    return list(database.values())


def tidy(database: list[dict]) -> dict:
    directory = WORK / "tidy"
    directory.mkdir()
    (directory / "compile_commands.json").write_text(json.dumps(database), "utf-8")
    shutil.copy2(directory / "compile_commands.json", REPORT / "compile_commands.json")
    findings = {}
    complexity = {}
    failed = []
    for entry in database:
        completed = run(
            [
                llvm_tool("clang-tidy"),
                *("-p", str(directory), f"--config-file={TIDY_CONFIGURATION}"),
                "--quiet",
                entry["file"],
            ]
        )
        # clang-tidy exits non-zero for compiler errors only; warnings are its output.
        if completed.returncode and "error:" in completed.stdout + completed.stderr:
            failed.append(Path(entry["file"]).name)
        for match in WARNING.finditer(completed.stdout):
            relative = production_file(match["path"])
            if not relative:
                continue
            line = int(match["line"])
            if match["check"] == "readability-function-cognitive-complexity":
                found = COMPLEXITY.search(match["message"])
                if found:
                    complexity[f"{relative}:{found[1]}"] = {
                        "function": found[1],
                        "file": relative,
                        "line": line,
                        "score": int(found[2]),
                    }
                continue
            key = (relative, line, int(match["column"]), match["check"])
            findings[key] = match["message"]
    warnings = [
        {
            "file": file,
            "line": line,
            "column": column,
            "check": check,
            "message": message,
        }
        for (file, line, column, check), message in sorted(findings.items())
    ]
    ranked = sorted(
        complexity.values(),
        key=lambda entry: (-entry["score"], entry["file"], entry["line"]),
    )
    return {
        "translation_units": len(database),
        "failed_units": failed,
        "warnings": warnings,
        "complexity": ranked,
    }


# Fuzzing


def fuzz(clang: str, seconds: int) -> list[dict]:
    directory = WORK / "fuzz"
    headers = directory / "include/zephyr/net/http"
    headers.mkdir(parents=True)
    for header in VENDORED_PARSER.glob("*.h"):
        shutil.copy2(header, headers / header.name)
    results = []
    for name, build in FUZZ_BUILDS.items():
        result = {"target": name, "functions": build["function"], "seconds": seconds}
        results.append(result)
        executable = directory / name
        includes = [HOST_TESTS / "include", *build["includes"], directory / "include"]
        completed = run(
            [
                clang,
                *("-g", "-O1", "-std=c11", "-D_POSIX_C_SOURCE=200809L"),
                "-fsanitize=fuzzer,address,undefined",
                "-fno-sanitize-recover=undefined",
                *(argument for path in includes for argument in ("-I", str(path))),
                str(FUZZ_TARGETS / build["source"]),
                *map(str, build["extra_sources"]),
                *("-o", str(executable)),
            ]
        )
        if completed.returncode:
            result["outcome"] = "build failed"
            result["detail"] = completed.stderr.strip()[-800:]
            continue
        corpus = directory / f"{name}-corpus"
        shutil.copytree(FUZZ_TARGETS / "corpus" / name, corpus)
        crashes = REPORT / "fuzz"
        crashes.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        try:
            completed = run(
                [
                    str(executable),
                    f"-max_total_time={seconds}",
                    "-print_final_stats=1",
                    # The static CI guest has 1 GiB; libFuzzer's default limit is 2 GiB.
                    "-rss_limit_mb=512",
                    f"-artifact_prefix={crashes}/{name}-",
                    str(corpus),
                ],
                timeout=seconds + 300,
            )
        except subprocess.TimeoutExpired:
            result["elapsed"] = round(time.monotonic() - started)
            result["outcome"] = "timed out"
            continue
        log = completed.stdout + completed.stderr
        (REPORT / "fuzz" / f"{name}.log").write_text(log[-200_000:], "utf-8")
        result["elapsed"] = round(time.monotonic() - started)
        executed = re.search(r"stat::number_of_executed_units:\s*(\d+)", log)
        coverage = re.findall(r"\bcov: (\d+)", log)
        result["inputs"] = int(executed[1]) if executed else None
        result["coverage"] = int(coverage[-1]) if coverage else None
        result["corpus"] = sum(1 for path in corpus.iterdir() if path.is_file())
        if completed.returncode:
            summary = re.search(r"^SUMMARY: .*$", log, re.MULTILINE)
            reproducer = re.search(r"Test unit written to (\S+)", log)
            result["outcome"] = "crash"
            result["detail"] = summary[0] if summary else log.strip()[-800:]
            if reproducer:
                result["reproducer"] = Path(reproducer[1]).name
        else:
            result["outcome"] = "no crash"
    return results


# Report


def code(value: object, limit: int = 300) -> str:
    """Show text from the results only as a code span: no Markdown, HTML, links or mentions."""
    text = " ".join(str(value).split())[:limit]
    text = text.replace("`", "'").replace("|", "/")
    return f"`{text}`" if text else "–"


def number(value: object) -> str:
    return f"{value:,}" if isinstance(value, int) else "–"


def percent(covered: int, count: int) -> str:
    return f"{100 * covered / count:.1f}%" if count else "–"


def fraction(covered: object, count: object) -> str:
    covered, count = int(covered), int(count)
    return f"{covered}/{count} ({percent(covered, count)})"


def location(entry: dict) -> str:
    return code(f"{entry['file']}:{entry['line']}")


def complexity_table(entries: list[dict], start: int) -> str:
    rows = "".join(
        f"| {start + index} | {code(entry['function'])} | {location(entry)} | "
        f"{int(entry['score'])}{' ⚠' if int(entry['score']) > COMPLEXITY_LIMIT else ''} |\n"
        for index, entry in enumerate(entries)
    )
    return "| # | Function | Location | Score |\n| ---: | --- | --- | ---: |\n" + rows


def markdown(results: dict) -> str:
    """Render the results; every text taken from them appears only as a code span.

    The PR comment renders clang.json from a PR's evidence with this function from the
    default branch, so the results are untrusted input here.
    """
    text = [
        "### Clang reports (information only)\n",
        f"Toolchain: {code(results.get('toolchain', ''))}. No result here fails the check.\n",
    ]
    if results.get("not_run"):
        text.append(f"Not run: {code(results['not_run'])}\n")
        return "\n".join(text)
    suite = results.get("suite")
    if suite:
        broken = int(suite["failures"]) + int(suite["errors"])
        text.append(
            f"The MC/DC build ran {int(suite['tests'])} host tests"
            + (f"; {broken} failed or errored under clang." if broken else ".")
            + "\n"
        )
    errors = results.get("errors", {})
    for section in ("mcdc", "tidy", "fuzz"):
        if section in errors:
            text.append(f"**{section}** did not run: {code(errors[section])}\n")
    tidy_results = results.get("tidy")
    if tidy_results:
        warnings = tidy_results["warnings"]
        counts = {}
        for warning in warnings:
            counts[warning["check"]] = counts.get(warning["check"], 0) + 1
        failed = tidy_results["failed_units"]
        text.append("#### clang-tidy\n")
        text.append(
            f"{len(warnings)} warnings in production code, from "
            f"{int(tidy_results['translation_units'])} host translation units. Only files "
            "that the host tests compile are checked."
            + (
                f" Not analysed because of compile errors: {', '.join(map(code, failed))}."
                if failed
                else ""
            )
            + "\n"
        )
        if counts:
            text.append("| Check | Warnings |\n| --- | ---: |")
            text.extend(
                f"| {code(check)} | {count} |"
                for check, count in sorted(counts.items(), key=lambda item: -item[1])
            )
            details = "\n".join(
                f"- {location(warning)} {code(warning['message'])} ({code(warning['check'])})"
                for warning in warnings
            )
            text.append(
                f"\n<details><summary>All {len(warnings)} warnings</summary>\n\n{details}\n\n</details>\n"
            )
        ranked = tidy_results["complexity"]
        if ranked:
            over = sum(int(entry["score"]) > COMPLEXITY_LIMIT for entry in ranked)
            text.append("#### Cognitive complexity\n")
            text.append(
                f"{len(ranked)} functions score 1 or more; {over} are above {COMPLEXITY_LIMIT} (⚠). "
                "Zephyr macros are not counted.\n"
            )
            text.append(complexity_table(ranked[:COMPLEXITY_SHOWN], 1))
            if len(ranked) > COMPLEXITY_SHOWN:
                text.append(
                    f"<details><summary>The other {len(ranked) - COMPLEXITY_SHOWN} functions</summary>\n\n"
                    + complexity_table(ranked[COMPLEXITY_SHOWN:], COMPLEXITY_SHOWN + 1)
                    + "\n</details>\n"
                )
    coverage = results.get("mcdc")
    if coverage:
        text.append("#### MC/DC coverage\n")
        text.append(
            "MC/DC requires each condition of a decision to be shown to change the outcome on its own. "
            "Clang 18 measures decisions of up to six conditions.\n"
        )
        text.append("| Source | Branches | MC/DC conditions |\n| --- | ---: | ---: |")
        totals = {"branches": [0, 0], "mcdc": [0, 0]}
        for name, kinds in sorted(coverage.items()):
            cells = []
            for kind in totals:
                values = kinds.get(kind, {"covered": 0, "count": 0})
                totals[kind][0] += int(values["covered"])
                totals[kind][1] += int(values["count"])
                cells.append(fraction(values["covered"], values["count"]))
            text.append(f"| {code(name)} | {' | '.join(cells)} |")
        cells = [
            f"**{fraction(covered, count)}**" for covered, count in totals.values()
        ]
        text.append(f"| **Total** | {' | '.join(cells)} |\n")
    fuzzing = results.get("fuzz")
    if fuzzing:
        text.append("#### Fuzzing (libFuzzer with ASan and UBSan)\n")
        text.append(
            "| Target | Functions | Time | Inputs | Coverage | Result |\n"
            "| --- | --- | ---: | ---: | ---: | --- |"
        )
        for result in fuzzing:
            text.append(
                f"| {code(result['target'])} | {code(result['functions'])} | "
                f"{number(result.get('elapsed'))} s | {number(result.get('inputs'))} | "
                f"{number(result.get('coverage'))} | {code(result['outcome'])} |"
            )
        for result in fuzzing:
            if result.get("detail"):
                reproducer = (
                    f" Reproducer {code(result['reproducer'])} is in the static evidence under `clang/fuzz/`."
                    if result.get("reproducer")
                    else ""
                )
                text.append(
                    f"\n{code(result['target'])}: {code(result['detail'], 800)}{reproducer}"
                )
        text.append("")
    return "\n".join(text)


def collect(seconds: int) -> dict:
    tools = {
        name: llvm_tool(name)
        for name in ("clang", "clang-tidy", "llvm-profdata", "llvm-cov")
    }
    missing = [name for name, path in tools.items() if not path]
    if missing:
        return {
            "toolchain": f"Clang {LLVM_VERSION}",
            "not_run": f"no {', '.join(missing)} {LLVM_VERSION} on this machine "
            f"(Ubuntu packages clang-{LLVM_VERSION}, clang-tidy-{LLVM_VERSION}, "
            f"llvm-{LLVM_VERSION}, libclang-rt-{LLVM_VERSION}-dev)",
        }
    version = run([tools["clang"], "--version"]).stdout.splitlines()[0]
    results = {"toolchain": version, "errors": {}}
    host = instrumented_host_run(tools["clang"])
    results["suite"] = host["suite"]
    for section, action in (
        ("mcdc", lambda: mcdc_coverage(host["compile_commands"])),
        ("tidy", lambda: tidy(compile_database(host["compile_commands"]))),
        ("fuzz", lambda: fuzz(tools["clang"], seconds)),
    ):
        try:
            results[section] = action()
        except (
            OSError,
            subprocess.SubprocessError,
            RuntimeError,
            ValueError,
            KeyError,
        ) as error:
            results["errors"][section] = str(error) or type(error).__name__
    return results


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    seconds = int(os.environ.get("STETHO_FUZZ_SECONDS", DEFAULT_FUZZ_SECONDS))
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.rmtree(REPORT, ignore_errors=True)
    WORK.mkdir(parents=True)
    REPORT.mkdir(parents=True)
    results = collect(seconds)
    report = markdown(results)
    (REPORT / "clang.json").write_text(json.dumps(results, indent=2) + "\n", "utf-8")
    (REPORT / "report.md").write_text(report, "utf-8")
    print(report)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with Path(target).open("a", encoding="utf-8") as stream:
            stream.write(report + "\n")


if __name__ == "__main__":
    main()
