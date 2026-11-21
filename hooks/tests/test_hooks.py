"""Each hook gets a fake event on stdin and must exit with the expected code.

Run: python -m pytest hooks/tests -q -p no:cacheprovider
Set CORTEX_HOOK_PYTHON to run the hooks under another interpreter, e.g.
CORTEX_HOOK_PYTHON=/usr/bin/python3 for the macOS system Python (3.9).
"""
import json
import os
import pathlib
import subprocess
import sys

import pytest

HOOKS = pathlib.Path(__file__).resolve().parents[1]
SESSION = "auto-session"
PY = os.environ.get("CORTEX_HOOK_PYTHON", sys.executable)


def run(script, event, env):
    result = subprocess.run([PY, str(HOOKS / script)], input=json.dumps(event),
                            capture_output=True, text=True, env=env)
    # /usr/bin/python3 is an xcrun shim; under a sandbox it warns about its own cache
    err = "".join(l for l in result.stderr.splitlines(True) if "xcrun_db" not in l)
    return result.returncode, err


@pytest.fixture
def env(tmp_path):
    e = dict(os.environ, CORTEX_AUTO_HOME=str(tmp_path / "auto"))
    e.pop("CORTEX_AUTO_THEME_CHECK", None)
    return e


def bash(command, session=SESSION, **extra):
    return {"hook_event_name": "PreToolUse", "session_id": session, "cwd": "/tmp",
            "tool_name": "Bash", "tool_input": {"command": command}, **extra}


def mark_auto(env, worktree=None):
    cmd = f'git -C /repo worktree add "{worktree}" -b auto/x' if worktree else \
        'python3 claim.py --vault "/v" --slot 1'
    assert run("guard_bash.py", bash(cmd), env)[0] == 0


# --- guard_bash -------------------------------------------------------------

DEPLOYS = [
    "git push origin auto/x",
    'git -C "/Users/b/.cortex-auto/worktrees/vcc/hero" push',
    "cd x && git push -u origin HEAD",
    "shopify theme push --store foo",
    "shopify theme publish -t 123",
    "rsync -av ./ host:/var/www",
    "scp a.php host:/tmp",
    "lftp -e 'mirror -R' host",
    "curl -T file.zip ftp://host/",
    "wp @staging plugin update --all",
    "wp db export --ssh=user@host",
    "bash -c 'git push'",
    "git --git-dir .git push",
    "git -c user.name='A B' push",
    "\\git push",
    "git subtree push --prefix dist origin gh-pages",
    "npx @shopify/cli theme push",
    "shopify theme share",
    "gh pr create --fill",
    "gh repo sync",
    "curl -F f=@x https://host/upload",
    "curl -d @file https://host/",
    "ssh host 'wp plugin update --all'",
    "g=git; $g push",
    "echo hi && $(git push)",
    "timeout 10 git push",
    "xargs git push",
    "find . -exec git push \\;",
    'git commit -m "$(git push)"',
    'git commit -m "`git push`"',
    '/bin/bash -lc "git push"',
    "git -c alias.p=push p",
    "git config alias.ship 'push origin HEAD'",
    "gh api repos/o/r/pulls -X POST",
    "gh api repos/o/r/issues -f title=x",
    "python3 -c \"import subprocess; subprocess.run(['git', 'push'])\"",
    "bash <<EOF\ngit push\nEOF",
    "sudo -u ben nice -n 5 git push",
    "if true; then git push; fi",
    "for i in 1; do git push; done",
    "until git push; do sleep 1; done",
    "{ git push; }",
    "! git push",
    "if test -d x; then shopify theme publish; fi",
    "env -S 'git push'",
    "git $(echo push)",
    "$(echo git) push",
    "gh pr merge 12",
    "gh release create v1",
    "gh workflow run deploy.yml",
    "git send-pack origin HEAD",
    "curl --json @f https://host/",
    "wget --post-file=a.zip https://host/",
    "rclone copy dist remote:site",
    "aws s3 sync dist s3://bucket",
    "watch git push",
    "watch -n 5 'git push'",
    "npx shopify theme push",
    "gh api graphql -f query='mutation { x }'",
    "gh gist create notes.md",
    "gh issue create --title x",
    "gh pr comment 3 --body hi",
    "shopify app deploy",
    "shopify theme delete -t 123",
    "git lfs push origin main",
    "vercel deploy --prod",
    "npx vercel",
    "cat <<EOF | bash\ngit push\nEOF",
    "f() { git push; }; f",
    "function ship { git push; }; ship",
    "\"x 'y\" ; git push",
]


@pytest.mark.parametrize("command", DEPLOYS)
def test_bash_normal_session_passes_deploys(env, command):
    assert run("guard_bash.py", bash(command, session="ben"), env)[0] == 0


@pytest.mark.parametrize("command", DEPLOYS)
def test_bash_auto_session_blocks_deploys(env, command):
    mark_auto(env)
    code, err = run("guard_bash.py", bash(command), env)
    assert code == 2 and "Blocked in an Auto run" in err


@pytest.mark.parametrize("command", [
    "git status", "git commit -m 'auto: hero 01 round 1'", "git log --oneline",
    "shopify theme check --path .", "shopify theme dev --port 9301", "wp plugin list",
    "python3 site_turn.py take --vault v --site s --brief b --step build",
    "rsync -a src/ dst/",
    "cat <<EOF > notes.md\ngit push\nEOF",
    "cat <<'EOF'\n$(git push)\nEOF",
    "echo 'git commit -m \"$(git push)\"'",
    "gh api repos/o/r/pulls",
    "timeout 60 shopify theme check --path .",
    "find . -name '*.liquid' -exec grep -l push {} +",
    "gh api graphql -f query='query { viewer { login } }'",
    "if git diff --quiet; then echo clean; fi",
    "aws s3 ls s3://bucket",
    "git -C $(pwd) status",
    "git -C $(git rev-parse --show-toplevel) log -1",
    'git commit -m "WIP; $(date)"',
    'git commit -m "things to do $(date +%F)"',
    'echo "step done | $(date)"',
    "echo 'a; $(b)'",
    "ls -la .git $(pwd)",
    "gh api -X GET search/issues -f q=repo:o/r",
    "\"/Apps/Bob's Tools/bin/tool\" --version",
    "cat vercel.json",
])
def test_bash_auto_session_allows_local_work(env, command):
    mark_auto(env)
    code, err = run("guard_bash.py", bash(command), env)
    assert code == 0 and err == ""


def test_bash_normal_session_odd_quoting_is_silent(env):
    code, err = run("guard_bash.py", bash("\"/Apps/Bob's Tools/bin/tool\" --version", session="ben"), env)
    assert code == 0 and err == ""


def test_guard_error_blocks_in_auto_run_and_passes_otherwise(env, tmp_path):
    # a hook given garbage tool_input crashes inside main(); guarded() decides the exit code
    mark_auto(env)
    bad = {"hook_event_name": "PreToolUse", "session_id": SESSION, "tool_name": "Bash",
           "tool_input": {"command": 12345}}
    code, err = run("guard_bash.py", bad, env)
    assert code == 2 and "guard error" in err
    bad["session_id"] = "ben"
    assert run("guard_bash.py", bad, env) == (0, "")


@pytest.mark.parametrize("command", [
    'grep -n "claim.py --slot" skills/auto/SKILL.md',
    "cat site_turn.py take",
    "echo python3 claim.py --slot 1",
])
def test_bash_mentioning_claim_does_not_mark_session(env, command):
    assert run("guard_bash.py", bash(command, session="ben"), env)[0] == 0
    assert run("guard_bash.py", bash("git push", session="ben"), env)[0] == 0


def test_bash_builder_agent_blocked_without_session_mark(env):
    event = bash("git push", session="other", agent_type="cortex-code:cortex-builder")
    assert run("guard_bash.py", event, env)[0] == 2


def test_bash_records_worktree(env, tmp_path):
    wt = tmp_path / "auto" / "worktrees" / "vcc" / "hero"
    mark_auto(env, worktree=wt)
    state = json.loads((tmp_path / "auto" / "sessions" / f"{SESSION}.json").read_text())
    assert state["worktree"] == str(wt)


# --- guard_write ------------------------------------------------------------

TICKET = """---
task: hero
ticket: 01
---

# Hero

## Acceptance criteria

- [ ] Hero fills the viewport at 390px

---

## Build round 1
"""


def edit(path, old, new, session=SESSION, **extra):
    return {"hook_event_name": "PreToolUse", "session_id": session, "tool_name": "Edit",
            "tool_input": {"file_path": str(path), "old_string": old, "new_string": new}, **extra}


@pytest.fixture
def ticket(tmp_path):
    path = tmp_path / "repo" / ".cortex" / "hero" / "ticket.md"
    path.parent.mkdir(parents=True)
    path.write_text(TICKET)
    return path


@pytest.mark.parametrize("session", ["ben", SESSION])
def test_ticket_tick_blocked_in_any_session(env, ticket, session):
    code, err = run("guard_write.py", edit(ticket, "- [ ] Hero", "- [x] Hero", session), env)
    assert code == 2 and "divider" in err


def test_ticket_overwrite_above_divider_blocked(env, ticket):
    event = {"hook_event_name": "PreToolUse", "session_id": "ben", "tool_name": "Write",
             "tool_input": {"file_path": str(ticket), "content": "# New\n\n---\n"}}
    assert run("guard_write.py", event, env)[0] == 2


def test_ticket_append_below_divider_allowed(env, ticket):
    event = edit(ticket, "## Build round 1\n", "## Build round 1\n\nCleared in 2 rounds.\n")
    assert run("guard_write.py", event, env)[0] == 0


def test_new_ticket_allowed(env, tmp_path):
    path = tmp_path / "repo" / ".cortex" / "new" / "02-footer.md"
    event = {"hook_event_name": "PreToolUse", "session_id": "ben", "tool_name": "Write",
             "tool_input": {"file_path": str(path), "content": TICKET}}
    assert run("guard_write.py", event, env)[0] == 0


def test_grill_file_not_a_ticket(env, tmp_path):
    path = tmp_path / "repo" / ".cortex" / "hero" / "grill-01.md"
    path.parent.mkdir(parents=True)
    path.write_text(TICKET)
    assert run("guard_write.py", edit(path, "- [ ] Hero", "- [x] Hero"), env)[0] == 0


def task_note(tmp_path, status):
    path = tmp_path / "vault" / "Tasks" / "Hero.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: freelance-task\ntask: hero\nstatus: {status}\nbilled: false\n---\n\n# Hero\n")
    return path


def test_auto_cannot_move_task_to_done(env, tmp_path):
    mark_auto(env)
    path = task_note(tmp_path, "review")
    code, err = run("guard_write.py", edit(path, "status: review", "status: done"), env)
    assert code == 2 and "review" in err


def test_auto_cannot_change_done_task_frontmatter(env, tmp_path):
    mark_auto(env)
    path = task_note(tmp_path, "done")
    assert run("guard_write.py", edit(path, "billed: false", "billed: true"), env)[0] == 2


def test_auto_can_move_task_to_review(env, tmp_path):
    mark_auto(env)
    path = task_note(tmp_path, "in-progress")
    assert run("guard_write.py", edit(path, "status: in-progress", "status: review"), env)[0] == 0


def test_normal_session_can_mark_done_task_billed(env, tmp_path):
    path = task_note(tmp_path, "done")
    assert run("guard_write.py", edit(path, "billed: false", "billed: true", "ben"), env)[0] == 0


# --- stop_gate --------------------------------------------------------------

def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


@pytest.fixture
def shopify_run(env, tmp_path):
    """A theme repo with a run worktree whose branch changed one section."""
    repo = tmp_path / "repo"
    (repo / "layout").mkdir(parents=True)
    (repo / "config").mkdir()
    (repo / "sections").mkdir()
    (repo / "layout" / "theme.liquid").write_text("x")
    (repo / "config" / "settings_schema.json").write_text("[]")
    (repo / "sections" / "old.liquid").write_text("old")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    wt = tmp_path / "auto" / "worktrees" / "vcc" / "hero"
    wt.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-q", str(wt), "-b", "auto/hero")
    (wt / "sections" / "hero.liquid").write_text("new")
    git(wt, "add", ".")
    git(wt, "commit", "-qm", "auto: hero 01 round 1")
    mark_auto(env, worktree=wt)
    return wt


def fake_theme_check(tmp_path, wt, error_in):
    report = [
        {"path": str(wt / "sections" / "old.liquid"),
         "offenses": [{"check": "UnknownFilter", "severity": "error", "start_row": 0, "message": "old"}]},
        {"path": str(wt / "sections" / "hero.liquid"),
         "offenses": [{"check": "LiquidHTMLSyntaxError", "severity": "error" if error_in else "warning",
                       "start_row": 4, "message": "bad tag"}]},
    ]
    out = tmp_path / "report.json"
    out.write_text(json.dumps(report))
    return f"cat {out}"


def stop_event(name, **extra):
    return {"hook_event_name": name, "session_id": SESSION, "stop_hook_active": False, **extra}


def test_builder_stop_blocked_on_theme_check_error(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    code, err = run("stop_gate.py", stop_event("SubagentStop", agent_type="cortex-code:cortex-builder"), env)
    assert code == 2 and "sections/hero.liquid:5" in err


def test_builder_stop_ignores_errors_from_before_the_run(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    code, _ = run("stop_gate.py", stop_event("SubagentStop", agent_type="cortex-code:cortex-builder"), env)
    assert code == 0


def test_other_subagent_stop_passes(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    assert run("stop_gate.py", stop_event("SubagentStop", agent_type="general-purpose"), env)[0] == 0


def evidence(tmp_path):
    return tmp_path / "auto" / "evidence" / "vcc" / "hero"


def closing(tmp_path, word):
    ev = evidence(tmp_path)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "closing").write_text(word + "\n")


def full_evidence(tmp_path):
    ev = evidence(tmp_path)
    (ev / "screenshots").mkdir(parents=True, exist_ok=True)
    (ev / "verdict-01-round-1.md").write_text("| item | pass |")
    (ev / "screenshots" / "01-390.png").write_bytes(b"png")


def marker(tmp_path):
    return tmp_path / "auto" / "sessions" / f"{SESSION}.json"


def test_mid_run_stop_passes_and_keeps_marker(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    for active in (False, True, True, True):
        assert run("stop_gate.py", stop_event("Stop", stop_hook_active=active), env)[0] == 0
    assert marker(tmp_path).exists()
    assert run("guard_bash.py", bash("git push origin auto/hero"), env)[0] == 2


def test_closing_review_needs_verdict_and_screenshot(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    closing(tmp_path, "review")
    code, err = run("stop_gate.py", stop_event("Stop"), env)
    assert code == 2 and "verdict" in err and "screenshot" in err
    assert marker(tmp_path).exists()


def test_closing_review_passes_with_evidence_and_clears(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    full_evidence(tmp_path)
    closing(tmp_path, "review")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert "0 error(s)" in (evidence(tmp_path) / "theme-check.txt").read_text()
    assert not marker(tmp_path).exists()


def test_closing_review_blocked_on_theme_check_even_with_evidence(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    full_evidence(tmp_path)
    closing(tmp_path, "review")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 2


def test_closing_review_blocked_after_builder_gave_up(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    full_evidence(tmp_path)
    (evidence(tmp_path) / "gate-gave-up.txt").write_text("SubagentStop: let through after 2 blocks.\n")
    closing(tmp_path, "review")
    code, err = run("stop_gate.py", stop_event("Stop"), env)
    assert code == 2 and "gate-gave-up" in err


def test_closing_blocked_clears_marker(env, tmp_path, shopify_run):
    closing(tmp_path, "blocked")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert not marker(tmp_path).exists()


def test_remark_keeps_worktree_and_base(env, tmp_path, shopify_run):
    before = json.loads(marker(tmp_path).read_text())
    cmd = "python3 site_turn.py take --vault v --site s --brief b --step build"
    assert run("guard_bash.py", bash(cmd), env)[0] == 0
    after = json.loads(marker(tmp_path).read_text())
    assert after["worktree"] == before["worktree"] == str(shopify_run)
    assert after.get("base") == before.get("base")


def test_normal_session_stop_passes(env):
    event = {"hook_event_name": "Stop", "session_id": "ben", "stop_hook_active": False}
    assert run("stop_gate.py", event, env)[0] == 0


def test_claimed_nothing_stop_passes_and_clears(env, tmp_path):
    mark_auto(env)  # claim.py ran, no worktree was ever made
    assert marker(tmp_path).exists()
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert not marker(tmp_path).exists()
    assert run("guard_bash.py", bash("git push"), env)[0] == 0  # Ben's later turns are normal


@pytest.mark.parametrize("content", ["", "   \n", "done"])
def test_unreadable_closing_blocks_with_a_clear_message(env, tmp_path, shopify_run, content):
    ev = evidence(tmp_path)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "closing").write_text(content)
    code, err = run("stop_gate.py", stop_event("Stop"), env)
    assert code == 2 and "couldn't be read" in err and "`review` or `blocked`" in err
    assert marker(tmp_path).exists()


def test_closing_first_word_is_used(env, tmp_path, shopify_run):
    closing(tmp_path, "blocked at build: bot protection")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert not marker(tmp_path).exists()


def test_marker_write_is_atomic(env, tmp_path, shopify_run):
    folder = tmp_path / "auto" / "sessions"
    assert [p.name for p in folder.iterdir()] == [f"{SESSION}.json"]  # no temp files left
    json.loads(marker(tmp_path).read_text())


def test_closing_word_is_case_insensitive(env, tmp_path, shopify_run):
    closing(tmp_path, "  Blocked ")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert not marker(tmp_path).exists()


def age(path, seconds=3600):
    t = path.stat().st_mtime - seconds
    os.utime(path, (t, t))


def test_new_run_sets_old_evidence_aside(env, tmp_path, shopify_run):
    ev = evidence(tmp_path)
    full_evidence(tmp_path)
    closing(tmp_path, "blocked")
    (ev / "gate-gave-up.txt").write_text("SubagentStop: old run\n")
    # the same brief runs again in a new session, on the same worktree path
    cmd = f'git -C /repo worktree add "{shopify_run}" -b auto/hero'
    assert run("guard_bash.py", bash(cmd, session="auto-2"), env)[0] == 0
    assert not ev.exists()
    assert len(list(ev.parent.glob("hero.before-*"))) == 1
    second = dict(stop_event("Stop"), session_id="auto-2")
    assert run("stop_gate.py", second, env)[0] == 0  # mid-run: nothing to close
    assert run("guard_bash.py", bash("git push", session="auto-2"), env)[0] == 2


def test_stale_evidence_files_are_ignored(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    ev = evidence(tmp_path)
    full_evidence(tmp_path)
    closing(tmp_path, "blocked")
    (ev / "gate-gave-up.txt").write_text("SubagentStop: old run\n")
    for p in [ev / "closing", ev / "gate-gave-up.txt", ev / "verdict-01-round-1.md",
              ev / "screenshots" / "01-390.png"]:
        age(p)
    # a stale `closing: blocked` doesn't end the run or clear the marker
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert marker(tmp_path).exists()
    assert run("guard_bash.py", bash("git push"), env)[0] == 2
    # at a real close, stale verdicts and screenshots don't count
    closing(tmp_path, "review")
    code, err = run("stop_gate.py", stop_event("Stop"), env)
    assert code == 2 and "verdict" in err and "screenshot" in err and "gate-gave-up" not in err
    # fresh evidence closes it, and the stale gave-up file doesn't force a block
    full_evidence(tmp_path)
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0
    assert not marker(tmp_path).exists()


def test_wordpress_php_lint(env, tmp_path):
    repo = tmp_path / "wp"
    repo.mkdir()
    (repo / "functions.php").write_text("<?php\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    wt = tmp_path / "auto" / "worktrees" / "jsc" / "footer"
    wt.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-q", str(wt), "-b", "auto/footer")
    (wt / "footer.php").write_text("<?php SYNTAX\n")
    mark_auto(env, worktree=wt)
    fake_php = tmp_path / "php"
    fake_php.write_text("#!/bin/sh\ngrep -q SYNTAX \"$2\" && { echo 'Parse error'; exit 255; }\nexit 0\n")
    fake_php.chmod(0o755)
    env["CORTEX_AUTO_PHP"] = str(fake_php)
    code, err = run("stop_gate.py", stop_event("SubagentStop", agent_type="cortex-code:cortex-builder"), env)
    assert code == 2 and "footer.php" in err
    (wt / "footer.php").write_text("<?php\n")
    assert run("stop_gate.py", stop_event("SubagentStop", agent_type="cortex-code:cortex-builder"), env)[0] == 0


# --- review round 1 ---------------------------------------------------------

def test_edit_that_cannot_be_verified_on_ticket_is_blocked(env, ticket):
    code, err = run("guard_write.py", edit(ticket, "text not in the file", "x", "ben"), env)
    assert code == 2 and "exact" in err


def test_edit_that_cannot_be_verified_elsewhere_passes(env, tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("hello\n")
    assert run("guard_write.py", edit(path, "not there", "x", "ben"), env)[0] == 0


BUILDER_STOP = dict(agent_type="cortex-code:cortex-builder")


def test_builder_gate_lets_go_after_two_blocks(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    assert run("stop_gate.py", stop_event("SubagentStop", **BUILDER_STOP), env)[0] == 2
    again = stop_event("SubagentStop", stop_hook_active=True, **BUILDER_STOP)
    assert run("stop_gate.py", again, env)[0] == 2
    assert run("stop_gate.py", again, env)[0] == 0
    assert "SubagentStop" in (evidence(tmp_path) / "gate-gave-up.txt").read_text()
    # a fresh stop (stop_hook_active false) starts counting again
    assert run("stop_gate.py", stop_event("SubagentStop", **BUILDER_STOP), env)[0] == 2


def test_closing_gate_gives_up_keeps_marker_then_releases(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=False)
    closing(tmp_path, "review")
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 2
    assert run("stop_gate.py", stop_event("Stop", stop_hook_active=True), env)[0] == 2
    assert run("stop_gate.py", stop_event("Stop", stop_hook_active=True), env)[0] == 0
    assert "Stop:" in (evidence(tmp_path) / "gate-gave-up.txt").read_text()
    assert marker(tmp_path).exists()
    assert run("guard_bash.py", bash("git push"), env)[0] == 2  # deploys stay blocked
    assert run("stop_gate.py", stop_event("Stop"), env)[0] == 0  # a resumed turn isn't held


def test_builder_allowed_when_cli_missing(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = "no-such-shopify-cli theme check --path {path}"
    assert run("stop_gate.py", stop_event("SubagentStop", **BUILDER_STOP), env)[0] == 0
    assert "did not run" in (evidence(tmp_path) / "theme-check.txt").read_text()


def test_check_cli_exit_codes(env, tmp_path, shopify_run):
    env["CORTEX_AUTO_THEME_CHECK"] = "no-such-shopify-cli"
    cli = [PY, str(HOOKS / "stop_gate.py"), "check", str(shopify_run)]
    assert subprocess.run(cli, env=env, capture_output=True).returncode == 3
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, shopify_run, error_in=True)
    assert subprocess.run(cli, env=env, capture_output=True).returncode == 1


@pytest.fixture
def orphan_run(env, tmp_path):
    """A worktree cut from a commit no local branch holds (like a remote-only ref)."""
    repo = tmp_path / "repo"
    for d in ("layout", "config", "sections"):
        (repo / d).mkdir(parents=True)
    (repo / "layout" / "theme.liquid").write_text("x")
    (repo / "config" / "settings_schema.json").write_text("[]")
    (repo / "sections" / "old.liquid").write_text("old")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    git(repo, "checkout", "-q", "--detach")
    git(repo, "branch", "-q", "-D", "main")
    wt = tmp_path / "auto" / "worktrees" / "vcc" / "hero"
    wt.parent.mkdir(parents=True)
    return repo, wt


def add_worktree_and_commit(repo, wt):
    git(repo, "worktree", "add", "-q", str(wt), "-b", "auto/hero")
    (wt / "sections" / "hero.liquid").write_text("new")
    git(wt, "add", ".")
    git(wt, "commit", "-qm", "auto: hero 01 round 1")


def test_recorded_base_limits_check_to_run_files(env, tmp_path, orphan_run):
    repo, wt = orphan_run
    cmd = f'git -C "{repo}" worktree add "{wt}" -b auto/hero'
    assert run("guard_bash.py", bash(cmd), env)[0] == 0  # records the base before the add runs
    add_worktree_and_commit(repo, wt)
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, wt, error_in=False)
    assert run("stop_gate.py", stop_event("SubagentStop", **BUILDER_STOP), env)[0] == 0
    report = (evidence(tmp_path) / "theme-check.txt").read_text()
    assert "in the 1 file(s) this run changed; 1 error(s) elsewhere" in report


def test_unknown_base_reports_without_blocking(env, tmp_path, orphan_run):
    repo, wt = orphan_run
    add_worktree_and_commit(repo, wt)
    mark_auto(env, worktree=wt)  # -C points nowhere, so no base is recorded
    env["CORTEX_AUTO_THEME_CHECK"] = fake_theme_check(tmp_path, wt, error_in=True)
    assert run("stop_gate.py", stop_event("SubagentStop", **BUILDER_STOP), env)[0] == 0
    assert "Couldn't tell which files" in (evidence(tmp_path) / "theme-check.txt").read_text()
