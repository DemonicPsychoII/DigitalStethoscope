#!/usr/bin/env python3
"""Fire research runs against the homelab pplx-agent proxy.

Usage: python run_research.py [id ...]     (no args = all runs in runs.json)
Results are written next to this script as <id>.json and <id>.md.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ENDPOINT = "http://192.168.2.98:8317/v1/chat/completions"
TOKEN = os.environ.get("CLIPROXY_API_KEY", "")
TIMEOUT = 1800
MAX_PARALLEL = 4


def call(run):
    model = "pplx-agent/preset-" + run["preset"]
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": run["prompt"]}],
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return run, None, "HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:500])
    except Exception as e:  # noqa: BLE001
        return run, None, "%s: %s" % (type(e).__name__, e)
    return run, data, None


def write_results(run, data):
    base = os.path.join(HERE, run["id"])
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump({"run": run, "response": data}, f, ensure_ascii=False, indent=1)

    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations") or []
    lines = [
        "# %s" % run["topic"],
        "",
        "- **Run-ID:** %s" % run["id"],
        "- **Preset:** %s" % run["preset"],
        "- **Modell:** %s" % data.get("model", "?"),
        "",
        "## Fragestellung",
        "",
        "```",
        run["prompt"],
        "```",
        "",
        "## Ergebnis",
        "",
        content,
        "",
    ]
    if citations:
        lines += ["## Quellen", ""]
        for i, c in enumerate(citations, 1):
            title = c.get("title") or c.get("url") or "?"
            lines.append("%d. [%s](%s)" % (i, title, c.get("url", "")))
        lines.append("")
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    if not TOKEN:
        print("ERROR: CLIPROXY_API_KEY not set")
        return 1
    with open(os.path.join(HERE, "runs.json"), encoding="utf-8") as f:
        runs = json.load(f)
    wanted = set(sys.argv[1:])
    if wanted:
        runs = [r for r in runs if r["id"] in wanted]

    print("Starting %d runs (max %d parallel)" % (len(runs), MAX_PARALLEL), flush=True)
    total_cost = 0.0
    failures = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        for run, data, err in pool.map(call, runs):
            if err:
                print("FAIL %-22s %s" % (run["id"], err), flush=True)
                failures.append(run["id"])
                continue
            write_results(run, data)
            usage = data.get("usage", {})
            cost = (usage.get("cost") or {}).get("total_cost", 0.0)
            total_cost += cost
            print("OK   %-22s preset=%-6s tokens=%-7s cost=$%.4f" % (
                run["id"], run["preset"], usage.get("total_tokens", "?"), cost), flush=True)

    print("---", flush=True)
    print("TOTAL COST $%.4f  |  failed: %s" % (total_cost, failures or "none"), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
