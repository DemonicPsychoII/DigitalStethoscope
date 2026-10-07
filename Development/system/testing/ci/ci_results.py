"""Required accounting rejects failure, cancellation and missing selector output."""

import argparse
import os


def problems(
    plan: str,
    static: str,
    heavy: str,
    firmware: str,
    native: str,
    publish: str,
    daily: str,
    reuse: str = "",
) -> list[str]:
    if plan != "success":
        return [f"check selection did not succeed: {plan}"]
    if daily not in {"true", "false"}:
        return ["daily decision is missing or invalid"]
    if any(value not in {"true", "false"} for value in (firmware, native, publish)):
        return ["suite selection is missing or invalid"]
    if daily == "false":
        return (
            []
            if static == heavy == "skipped"
            else ["unchanged daily run executed unexpected jobs"]
        )
    errors = []
    if static != "success":
        errors.append(f"static verification did not succeed: {static}")
    required = (
        firmware == "true" or native == "true" or (publish == "true" and not reuse)
    )
    if heavy != ("success" if required else "skipped"):
        errors.append(
            f"selected heavy work did not produce its expected result: {heavy}"
        )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--static", required=True)
    parser.add_argument("--heavy", required=True)
    args = parser.parse_args()
    errors = problems(
        args.plan,
        args.static,
        args.heavy,
        os.environ.get("FIRMWARE", ""),
        os.environ.get("NATIVE", ""),
        os.environ.get("PUBLISH", ""),
        os.environ.get("DAILY", ""),
        os.environ.get("REUSE", ""),
    )
    if errors:
        raise SystemExit("; ".join(errors))
    print(
        "All selected verification passed; unselected work is explicitly accounted for."
    )


if __name__ == "__main__":
    main()
