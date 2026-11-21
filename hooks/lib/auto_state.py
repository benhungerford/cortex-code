"""Shared state for the Cortex Code Auto guard hooks.

A session counts as an Auto run once it runs `claim.py --slot` or
`site_turn.py take` with Python, or creates a worktree under
~/.cortex-auto/worktrees/, or when the hook fires inside one of the
plugin's builder or checker agents.
The Bash guard records that in one small JSON file per session, and the
other hooks read it. Normal sessions never get a file, so every guard
that keys off it leaves them alone.

claim.py's own `claim.lock` can't be the signal: it is a flock target
that stays on disk after every claim, and it is shared by every session.

The marker stays for the whole run, including turns the main agent ends
while it waits on helpers. The stop gate removes it only once the run
has closed; anything left behind is pruned after STALE_DAYS.

Paths can be moved for tests with CORTEX_AUTO_HOME.
"""
from __future__ import annotations

import io
import json
import os
import pathlib
import re
import sys
import time

STALE_DAYS = 3


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CORTEX_AUTO_HOME", "~/.cortex-auto")).expanduser()


def worktrees_root() -> pathlib.Path:
    return home() / "worktrees"


def _state_path(session_id: str) -> pathlib.Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "none")
    return home() / "sessions" / f"{safe}.json"


def load(session_id: str):
    try:
        return json.loads(_state_path(session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save(session_id: str, state: dict) -> None:
    """Write the marker atomically, so a hook reading it never sees half a file."""
    path = _state_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    os.replace(tmp, path)


def guarded(main) -> int:
    """Run a hook's main(). An unexpected error blocks in an Auto run, passes otherwise."""
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError:
        event = {}
    sys.stdin = io.StringIO(raw)
    try:
        return main()
    except Exception as exc:  # noqa: BLE001 - a guard must not fail open in a run
        try:
            auto = is_auto(event)
        except Exception:  # noqa: BLE001
            auto = False
        if auto:
            print(f"Cortex Code guard error ({type(exc).__name__}: {exc}). Blocked to be "
                  "safe in an Auto run; note it in the run log.", file=sys.stderr)
            return 2
        return 0


def mark(session_id: str, worktree: str | None = None, base: str | None = None) -> dict:
    state = load(session_id) or {"started": time.strftime("%Y-%m-%dT%H:%M")}
    if worktree:
        state["worktree"] = worktree
        state["base"] = base
        state["run_epoch"] = time.time()
        set_aside_evidence(worktree)
    save(session_id, state)
    _prune(_state_path(session_id).parent)
    return state


def set_aside_evidence(worktree: str) -> None:
    """A new run on the same brief starts with an empty evidence folder.

    An earlier run's folder is renamed with a timestamp, never deleted.
    """
    folder = evidence_dir(worktree)
    if folder.exists():
        try:
            folder.rename(folder.with_name(f"{folder.name}.before-{time.strftime('%Y%m%d-%H%M%S')}"))
        except OSError:
            pass


def fresh(path: pathlib.Path, state: dict) -> bool:
    """True when an evidence file was written during this run."""
    try:
        return path.stat().st_mtime >= state.get("run_epoch", 0) - 1
    except OSError:
        return False


def base_for(worktree: str):
    """The recorded base commit of a run worktree, from any session marker."""
    target = os.path.realpath(os.path.expanduser(worktree))
    for path in (home() / "sessions").glob("*.json"):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if state.get("worktree") and os.path.realpath(state["worktree"]) == target:
            return state.get("base")
    return None


def clear(session_id: str) -> None:
    """The run has closed: the session is a normal one from here on."""
    try:
        _state_path(session_id).unlink()
    except OSError:
        pass


def _prune(folder: pathlib.Path) -> None:
    cutoff = time.time() - STALE_DAYS * 86400
    for old in folder.glob("*.json"):
        try:
            if old.stat().st_mtime < cutoff:
                old.unlink()
        except OSError:
            pass


def under_worktrees(path: str) -> bool:
    if not path:
        return False
    root = str(worktrees_root().resolve())
    try:
        resolved = str(pathlib.Path(path).expanduser().resolve())
    except OSError:
        return False
    return resolved == root or resolved.startswith(root + os.sep)


AUTO_AGENTS = ("cortex-code:cortex-builder", "cortex-code:cortex-checker")


def is_auto(event: dict) -> bool:
    """True inside an Auto run: a marked session, or one of the run's own agents.

    A session opened by hand inside a run's worktree is not an Auto run, so
    Ben can still push a branch he has reviewed (the permission rules ask).
    """
    if event.get("agent_type") in AUTO_AGENTS:
        return True
    return load(event.get("session_id", "")) is not None


def evidence_dir(worktree: str) -> pathlib.Path:
    """~/.cortex-auto/worktrees/<id>/<slug> -> ~/.cortex-auto/evidence/<id>/<slug>.

    Kept outside the worktree so verdicts and screenshots never end up
    committed on the run branch.
    """
    wt = pathlib.Path(worktree).expanduser().resolve()
    try:
        rel = wt.relative_to(worktrees_root().resolve())
    except ValueError:
        rel = pathlib.Path(wt.name)
    return home() / "evidence" / rel


def read_event(stream) -> dict:
    try:
        return json.load(stream)
    except ValueError:
        return {}
