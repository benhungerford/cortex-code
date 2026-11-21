#!/usr/bin/env python3
"""Stop / SubagentStop gate for Auto runs, and the run's code check.

SubagentStop (the cortex-builder agent): the builder can't return while
the code check finds errors in files the run changed.

Stop (the Auto coordinator): the main agent ends turns mid-run while it
waits on helpers, so Stop does nothing until close-out writes
`<evidence>/closing` (`review` or `blocked`). Then:
- `blocked`: the run has closed. The session's Auto marker is removed, so
  a session Ben resumes later is a normal one.
- `review`: the run can't close until the code check passes, the
  evidence folder holds a checker verdict (`verdict-*.md`) and a
  screenshot (`screenshots/*.png|jpg|jpeg`), and no gate has given up
  (`gate-gave-up.txt`). Once it all holds, the marker is removed.

Each gate blocks at most twice in a row (counted in the marker, reset
when `stop_hook_active` is false), then lets go and appends why to
`<evidence>/gate-gave-up.txt`. A Stop give-up keeps the marker, so
deploys stay blocked until the stale-marker prune, but later Stops in
that session pass. A check that can't run (no Shopify CLI, no php, no
way to tell which files the run changed) never blocks: its output says
so, and that output goes in the close-out report.

Sessions that are not Auto runs, or have no run worktree yet, pass.

The code check:
- Shopify theme: `shopify theme check -o json`, counting only errors in
  files this run changed. Client themes often carry errors from before
  the run, and those are not the builder's to fix.
- WordPress: `php -l` on every PHP file the run changed.
"Changed" is measured from the commit the worktree was cut from, which
the Bash guard records at `git worktree add`. The full output is saved
to `<evidence>/theme-check.txt`.

By hand, for the close-out report:
    python3 stop_gate.py check <worktree>
prints the check output and exits 0 on pass, 1 on fail, 3 when the check
could not run.

Tests swap the commands with CORTEX_AUTO_THEME_CHECK and CORTEX_AUTO_PHP.
"""
from __future__ import annotations

import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import auto_state  # noqa: E402

BUILDER = "cortex-code:cortex-builder"
MAX_BLOCKS = 2
PASS, FAIL, UNAVAILABLE = "pass", "fail", "unavailable"


def git(worktree: pathlib.Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def changed_files(worktree: pathlib.Path, base: str | None):
    """Files changed since the worktree was cut, or None when that can't be told."""
    if not (base and git(worktree, "rev-parse", "--verify", "--quiet", base + "^{commit}")):
        branch = git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
        own = git(worktree, "rev-list", "--reverse", "HEAD", "--not",
                  f"--exclude={branch}", "--branches").splitlines()
        if not own:
            base = "HEAD"
        else:
            base = git(worktree, "rev-parse", "--verify", "--quiet", f"{own[0]}^")
            if not base:
                return None  # cut from a ref no local branch holds: the whole history looks new
    names = set(git(worktree, "diff", "--name-only", base).splitlines())
    names |= set(git(worktree, "ls-files", "--others", "--exclude-standard").splitlines())
    return {n for n in names if n}


def kind(worktree: pathlib.Path) -> str:
    if (worktree / "layout" / "theme.liquid").exists() and (worktree / "config" / "settings_schema.json").exists():
        return "shopify"
    if (worktree / "wp-content").is_dir() or (worktree / "functions.php").exists() or any(worktree.glob("*.php")):
        return "wordpress"
    return "other"


def check_shopify(worktree: pathlib.Path, changed):
    template = os.environ.get("CORTEX_AUTO_THEME_CHECK",
                              "shopify theme check -o json --fail-level error --path {path}")
    cmd = shlex.split(template.replace("{path}", shlex.quote(str(worktree))))
    if not shutil.which(cmd[0]):
        return UNAVAILABLE, f"shopify theme check did not run: `{cmd[0]}` is not installed or not on PATH."
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return UNAVAILABLE, f"shopify theme check did not run: {exc}"
    raw = result.stdout
    try:
        report = json.loads(raw[raw.index("["):])
    except ValueError:
        return UNAVAILABLE, "shopify theme check gave no JSON report:\n" + (result.stderr or raw)[-2000:]

    lines, errors, elsewhere = [], 0, 0
    for entry in report:
        path = pathlib.Path(entry.get("path", ""))
        try:
            rel = str(path.resolve().relative_to(worktree.resolve())) if path.is_absolute() else str(path)
        except ValueError:
            rel = str(path)
        offenses = entry.get("offenses", [])
        if changed is not None and rel not in changed:
            elsewhere += sum(1 for o in offenses if o.get("severity") == "error")
            continue
        for o in offenses:
            if o.get("severity") == "error":
                errors += 1
            lines.append(f"{rel}:{o.get('start_row', 0) + 1}  {o.get('severity')}  "
                         f"{o.get('check')}  {o.get('message')}")
    if changed is None:
        lines.append(f"shopify theme check: {errors} error(s) in the whole theme. Couldn't tell which "
                     "files this run changed, so this is reported, not enforced.")
        return UNAVAILABLE, "\n".join(lines)
    lines.append(f"shopify theme check: {errors} error(s) in the {len(changed)} file(s) this run "
                 f"changed; {elsewhere} error(s) elsewhere in the theme, from before the run.")
    return (PASS if errors == 0 else FAIL), "\n".join(lines)


def check_wordpress(worktree: pathlib.Path, changed):
    php = os.environ.get("CORTEX_AUTO_PHP", "php")
    if not shutil.which(php):
        return UNAVAILABLE, f"php -l did not run: `{php}` is not installed or not on PATH."
    if changed is None:
        return UNAVAILABLE, "php -l did not run: couldn't tell which files this run changed."
    files = sorted(f for f in changed if f.endswith(".php") and (worktree / f).exists())
    lines, failed = [], 0
    for rel in files:
        result = subprocess.run([php, "-l", str(worktree / rel)], capture_output=True, text=True)
        if result.returncode != 0:
            failed += 1
            lines.append(f"{rel}: {(result.stdout + result.stderr).strip()}")
    lines.append(f"php -l: {failed} of {len(files)} changed PHP file(s) failed.")
    return (PASS if failed == 0 else FAIL), "\n".join(lines)


def run_check(worktree: pathlib.Path, base: str | None = None):
    changed = changed_files(worktree, base)
    site = kind(worktree)
    if site == "shopify":
        status, text = check_shopify(worktree, changed)
    elif site == "wordpress":
        status, text = check_wordpress(worktree, changed)
    else:
        status, text = PASS, "No code check for this repo: not a Shopify theme or a WordPress site."
    out = auto_state.evidence_dir(str(worktree))
    out.mkdir(parents=True, exist_ok=True)
    (out / "theme-check.txt").write_text(text + "\n", encoding="utf-8")
    return status, text


def gate(event: dict, state: dict, session: str, reason: str, evidence: pathlib.Path) -> int:
    """Block with `reason`, unless this gate has already blocked twice in a row."""
    name = event.get("hook_event_name", "")
    blocks = state.setdefault("blocks", {})
    if not event.get("stop_hook_active"):
        blocks[name] = 0
    if blocks.get(name, 0) >= MAX_BLOCKS:
        blocks[name] = 0
        if name == "Stop":
            state["stop_released"] = True
        auto_state.save(session, state)
        evidence.mkdir(parents=True, exist_ok=True)
        with open(evidence / "gate-gave-up.txt", "a", encoding="utf-8") as f:
            f.write(f"{name}: let through after {MAX_BLOCKS} blocks. Last reason:\n{reason}\n\n")
        return 0
    blocks[name] = blocks.get(name, 0) + 1
    auto_state.save(session, state)
    print(reason, file=sys.stderr)
    return 2


def hook() -> int:
    event = auto_state.read_event(sys.stdin)
    name = event.get("hook_event_name")
    session = event.get("session_id", "")
    state = auto_state.load(session)
    if not state:
        return 0
    worktree = pathlib.Path(state["worktree"]) if state.get("worktree") else None
    if not worktree or not worktree.is_dir():
        if name == "Stop" and not worktree:
            # claim.py found nothing, or intake blocked before the worktree:
            # there is no run to guard and no folder to write `closing` in.
            auto_state.clear(session)
        return 0
    evidence = auto_state.evidence_dir(str(worktree))

    def fresh(path: pathlib.Path) -> bool:
        return auto_state.fresh(path, state)

    if name == "SubagentStop":
        if event.get("agent_type") != BUILDER:
            return 0
        status, text = run_check(worktree, state.get("base"))
        if status != FAIL:
            return 0
        return gate(event, state, session, "The code check fails on files this run changed. "
                    "Fix these before returning, then commit:\n" + text, evidence)

    if name == "Stop":
        closing = evidence / "closing"
        if state.get("stop_released") or not fresh(closing):
            return 0  # mid-run turn end, or a close-out that already gave up
        words = closing.read_text(encoding="utf-8", errors="replace").split()
        word = words[0].lower() if words else ""
        if word == "blocked":
            auto_state.clear(session)
            return 0
        if word != "review":
            return gate(event, state, session, f"{closing} couldn't be read: it should hold one "
                        "word, `review` or `blocked`, matching the brief's status. Rewrite it.",
                        evidence)
        missing = []
        gave_up = evidence / "gate-gave-up.txt"
        if fresh(gave_up) and "SubagentStop:" in gave_up.read_text(encoding="utf-8"):
            missing.append(f"a builder returned with the code check still failing (see {gave_up})")
        if not [p for p in evidence.glob("verdict-*.md") if fresh(p)]:
            missing.append(f"no checker verdict in {evidence}/verdict-*.md")
        shots = [p for p in (evidence / "screenshots").glob("*")
                 if p.suffix.lower() in (".png", ".jpg", ".jpeg") and fresh(p)]
        if not shots:
            missing.append(f"no screenshot in {evidence}/screenshots/ (copy the checker's screenshots there)")
        status, text = run_check(worktree, state.get("base"))
        if status == FAIL:
            missing.append("the code check fails:\n" + text)
        if missing:
            return gate(event, state, session, "This Auto run can't close at review yet: "
                        + "; ".join(missing) + "\nIf the run can't produce these, close it as blocked: "
                        "set the brief to `status: blocked` and write `blocked` to " + str(closing) + ".",
                        evidence)
        auto_state.clear(session)
        return 0
    return 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "check":
        worktree = pathlib.Path(sys.argv[2]).expanduser()
        status, text = run_check(worktree, auto_state.base_for(str(worktree)))
        print(text)
        return {PASS: 0, FAIL: 1}.get(status, 3)
    return auto_state.guarded(hook)


if __name__ == "__main__":
    sys.exit(main())
