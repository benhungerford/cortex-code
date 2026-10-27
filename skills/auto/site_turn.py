#!/usr/bin/env python3
"""Take or give back a site's turn for the steps that use the live site.

Briefs on the same site plan in parallel, but only one at a time may run
the steps that drive the site in a browser (prototype, build, QA). Those
steps take the site's turn first. Waiting runs queue in the order they
asked, and a turn held by a brief that is no longer `running` (its run
died, ended, or blocked without giving it back) is freed automatically.

    site_turn.py take --vault V --site S --brief B --step build [--wait 540]
    site_turn.py give --vault V --site S --brief B

Prints JSON. `take` exits 0 when granted, 3 when still waiting.
"""
import argparse
import datetime as dt
import fcntl
import json
import pathlib
import re
import sys
import time

POLL_SECONDS = 30


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M")


def is_running(vault: pathlib.Path, brief: str) -> bool:
    path = vault / brief
    if not path.exists():
        return False
    match = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return bool(match) and match.group(1) == "running"


class Turns:
    """The turns file, read and written under an exclusive lock."""

    def __init__(self, vault: pathlib.Path):
        folder = vault / ".claude" / "cortex-auto"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "site-turns.json"
        self.lock_path = folder / "site-turns.lock"

    def __enter__(self):
        self.lock = open(self.lock_path, "w")
        fcntl.flock(self.lock, fcntl.LOCK_EX)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}
        return self.data

    def __exit__(self, *exc):
        if exc[0] is None:
            self.path.write_text(json.dumps(self.data, indent=2) + "\n")
        self.lock.close()


def try_take(vault: pathlib.Path, site: str, brief: str, step: str) -> dict:
    with Turns(vault) as data:
        turn = data.setdefault(site, {"holder": None, "queue": []})

        # Drop anyone whose run is no longer going.
        freed = None
        if turn["holder"] and not is_running(vault, turn["holder"]["brief"]):
            freed = turn["holder"]["brief"]
            turn["holder"] = None
        turn["queue"] = [w for w in turn["queue"] if is_running(vault, w["brief"])]

        if turn["holder"] and turn["holder"]["brief"] == brief:
            turn["holder"]["step"] = step
            return {"granted": True, "site": site, "step": step, "already_held": True}

        if not any(w["brief"] == brief for w in turn["queue"]):
            turn["queue"].append({"brief": brief, "step": step, "since": now_stamp()})

        first = turn["queue"][0]["brief"]
        if turn["holder"] is None and first == brief:
            waited_since = turn["queue"].pop(0)["since"]
            turn["holder"] = {"brief": brief, "step": step, "since": now_stamp()}
            result = {"granted": True, "site": site, "step": step, "queued_since": waited_since}
        else:
            position = next(i for i, w in enumerate(turn["queue"]) if w["brief"] == brief) + 1
            result = {
                "granted": False,
                "site": site,
                "held_by": turn["holder"],
                "position": position,
            }
        if freed:
            result["freed_stale"] = freed
        return result


def give(vault: pathlib.Path, site: str, brief: str) -> dict:
    with Turns(vault) as data:
        turn = data.get(site, {"holder": None, "queue": []})
        held = bool(turn["holder"]) and turn["holder"]["brief"] == brief
        if held:
            turn["holder"] = None
        turn["queue"] = [w for w in turn["queue"] if w["brief"] != brief]
        data[site] = turn
        return {"released": held, "site": site}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["take", "give"])
    parser.add_argument("--vault", required=True, type=pathlib.Path)
    parser.add_argument("--site", required=True, help="the brief's project: vault path")
    parser.add_argument("--brief", required=True, help="the brief's path from the vault root")
    parser.add_argument("--step", default="build")
    parser.add_argument("--wait", type=int, default=0, help="seconds to keep trying before giving up")
    args = parser.parse_args()

    if args.action == "give":
        print(json.dumps(give(args.vault, args.site, args.brief), indent=2))
        return 0

    deadline = time.monotonic() + args.wait
    while True:
        result = try_take(args.vault, args.site, args.brief, args.step)
        if result["granted"] or time.monotonic() >= deadline:
            break
        time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))
    print(json.dumps(result, indent=2))
    return 0 if result["granted"] else 3


if __name__ == "__main__":
    sys.exit(main())
