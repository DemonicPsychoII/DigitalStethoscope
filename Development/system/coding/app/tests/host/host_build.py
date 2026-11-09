"""Build every host test executable with one compiler configuration."""

from dataclasses import dataclass
import functools
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
APPLICATION = HERE.parents[1]
SUBSTITUTES = HERE / "include"
PORTAL_PAGE = APPLICATION / "L1_services/L1_PORTAL/portal.html"


@dataclass(frozen=True)
class HostExecutable:
    path: Path
    command: list
    compiler_version: str
    source_revision: str

    def record_identity(self, record_property):
        record_property("compiler_version", self.compiler_version)
        record_property("compiler_command", subprocess.list2cmdline(self.command))
        record_property("source_revision", self.source_revision)


def compiler():
    # shlex keeps compiler arguments (e.g. Zig's cc subcommand); quoted paths work.
    return shlex.split(os.environ.get("CC", "gcc"))


def run_compiler(arguments, input_text=None):
    command = compiler() + arguments
    try:
        return subprocess.run(
            command, input=input_text, capture_output=True, text=True, timeout=120
        )
    except OSError as error:
        pytest.fail(
            f"Host C compiler could not start ({command[0]}): {error}", pytrace=False
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"Host C compiler timed out: {error.cmd}", pytrace=False)


@functools.cache
def compiler_version():
    result = run_compiler(["--version"])
    if result.returncode:
        pytest.fail(f"Host compiler identity failed:\n{result.stderr}", pytrace=False)
    return result.stdout.splitlines()[0]


@functools.cache
def source_revision():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE, text=True, timeout=30
        ).strip()
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"Host source identity timed out: {error.cmd}", pytrace=False)
    except (OSError, subprocess.CalledProcessError) as error:
        pytest.fail(f"Git is required for host source identity: {error}", pytrace=False)


def build(directory, name, sources, include_directories=(), embed_portal_page=False):
    """Compile sources into directory/name with the substitute headers first on the path."""
    target = directory / (name + ".exe" if sys.platform == "win32" else name)
    includes = [SUBSTITUTES]
    if embed_portal_page:
        (directory / "portal.html.inc").write_text(
            ",".join(str(value) for value in PORTAL_PAGE.read_bytes()) + ",\n"
        )
        includes.append(directory)
    arguments = [
        "-std=c11",
        "-D_POSIX_C_SOURCE=200809L",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-g",
    ]
    if os.environ.get("STETHO_COVERAGE_DIRECTORY"):
        arguments += ["--coverage", "-O0"]
    if os.environ.get("STETHO_SANITIZERS", "").lower() == "true":
        arguments += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
    for include in (*includes, *include_directories):
        arguments += ["-I", str(include)]
    arguments += [str(source) for source in sources] + ["-o", str(target)]
    result = run_compiler(arguments)
    if result.returncode:
        pytest.fail(
            f"Host compile of {name} failed:\n{result.stdout}\n{result.stderr}",
            pytrace=False,
        )
    return HostExecutable(
        target, compiler() + arguments, compiler_version(), source_revision()
    )


@functools.cache
def error_numbers():
    result = run_compiler(
        ["-dM", "-E", "-I", str(SUBSTITUTES), "-x", "c", "-"], "#include <errno.h>\n"
    )
    if result.returncode:
        pytest.fail(f"Host errno.h could not be read:\n{result.stderr}", pytrace=False)
    definitions = dict(re.findall(r"^#define (E[A-Z0-9]+) (\w+)", result.stdout, re.M))
    numbers = {}
    for name, value in definitions.items():
        while value in definitions:
            value = definitions[value]
        if value.isdigit():
            numbers[name] = int(value)
    return numbers


def error_code(name):
    """Return the negative errno value that the host-compiled production code returns."""
    return -error_numbers()[name]
