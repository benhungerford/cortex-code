#!/usr/bin/env python3
"""Claim the next ready brief for an /auto pickup slot.

Several slots fire on a timer and may fire at once, so the claim is made
under a file lock: find the oldest `status: ready` brief, flip it to
`running`, and print what was claimed as JSON. Prints
`"claimed": null` with a reason when there is nothing to take.

The run itself validates the brief (intake). This only decides who goes
next and makes sure two slots never take the same brief. Briefs on one
site plan in parallel; the steps that drive the site take turns through
site_turn.py, not here. `--per-site` (0 = no limit) is kept for capping
whole runs per site if that is ever needed.
"""
import argparse
import datetime as dt
import fcntl
import json
import pathlib
import re
import sys

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
STALE_AFTER_HOURS = 8


def read_fields(text: str) -> dict:
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip('"')
    return fields


def set_fields(text: str, values: dict) -> str:
    match = FRONTMATTER.match(text)
    body = match.group(1)
    for key, value in values.items():
        line = f"{key}: {value}"
        if re.search(rf"^{key}:.*$", body, re.MULTILINE):
            body = re.sub(rf"^{key}:.*$", line, body, count=1, flags=re.MULTILINE)
        else:
            body += "\n" + line
    return text[: match.start(1)] + body + text[match.end(1):]


def load_briefs(briefs_dir: pathlib.Path) -> list[dict]:
    briefs = []
    for path in sorted(briefs_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        fields = read_fields(path.read_text(encoding="utf-8"))
        if fields.get("type") != "brief":
            continue
        briefs.append({"path": path, **fields})
    return briefs


def started_at(brief: dict):
    try:
        return dt.datetime.strptime(brief.get("run_started", ""), "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def claim(vault: pathlib.Path, slot: int, max_total: int, per_site: int, now: dt.datetime) -> dict:
    briefs = load_briefs(vault / "_Briefs")
    running = [b for b in briefs if b.get("status") == "running"]

    stale = [
        b["path"].name for b in running
        if (s := started_at(b)) and now - s > dt.timedelta(hours=STALE_AFTER_HOURS)
    ]
    result = {"claimed": None, "slot": slot, "running": len(running), "stale": stale}

    if len(running) >= max_total:
        result["reason"] = f"{len(running)} briefs already running (limit {max_total})"
        return result

    busy = {}
    for b in running:
        busy[b.get("project", "")] = busy.get(b.get("project", ""), 0) + 1

    ready = [b for b in briefs if b.get("status") == "ready"]
    ready.sort(key=lambda b: (b.get("created", ""), b["path"].stat().st_mtime))
    waiting = []
    for b in ready:
        if per_site and busy.get(b.get("project", ""), 0) >= per_site:
            waiting.append(b["path"].name)
            continue
        path = b["path"]
        stamp = now.strftime("%Y-%m-%dT%H:%M")
        text = set_fields(path.read_text(encoding="utf-8"), {
            "status": "running",
            "run_started": stamp,
            "run_slot": slot,
            "updated": now.strftime("%Y-%m-%d"),
        })
        path.write_text(text, encoding="utf-8")
        result.update(claimed=str(path), project=b.get("project", ""), run_started=stamp)
        if waiting:
            result["waiting"] = waiting
        return result

    if waiting:
        result["waiting"] = waiting
        result["reason"] = "every ready brief is on a site that already has a run"
    else:
        result["reason"] = "no ready briefs"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", required=True, type=pathlib.Path)
    parser.add_argument("--slot", required=True, type=int)
    parser.add_argument("--max-total", type=int, default=3)
    parser.add_argument("--per-site", type=int, default=0)
    args = parser.parse_args()

    lock_path = args.vault / ".claude" / "cortex-auto" / "claim.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = claim(args.vault, args.slot, args.max_total, args.per_site, dt.datetime.now())

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
