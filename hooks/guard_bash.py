#!/usr/bin/env python3
"""PreToolUse guard for Bash.

Marks the session as an Auto run when it runs claim.py --slot or
site_turn.py take with Python, or adds a worktree under
~/.cortex-auto/worktrees/ (recording the commit it was cut from). In an
Auto run it blocks anything that sends work off the machine: git push
(also git subtree push and a git alias set to push), Shopify CLI theme
push/publish/share (also through npx @shopify/cli), gh pr create, gh repo
sync and gh api writes, rsync/scp to a remote host, sftp/lftp/ftp/ssh,
curl uploads (-T, -F, -d @file), and remote WP-CLI.

How it reads a command: it splits on shell operators and reads each part
word by word, after dropping wrappers (sudo, env, timeout, xargs, nice,
nohup, find -exec and the like). It also reads `bash -c` / `-lc` strings,
`eval`, `$(...)` and backticks (also inside double quotes), and the body
of a heredoc fed to a shell. Other heredoc bodies are data and ignored.

Shell keywords (if/then/do/while/until/!/{ and the like) are skipped
before the command word is read.

It fails closed in a marked session where it can't read the command: a
command word or git subcommand built by command substitution
(`$(echo git) push`, `git $(echo push)`) is blocked, and so is a variable
command word (`$g push`) that names a push, publish or upload. For
`python -c`, `node -e` and the like it looks for a literal push or
publish in the code string, so a harmless string such as
`s='git push'` is blocked too. That trade is deliberate in an
unattended run.

What it can't see: npm or make scripts, shell functions and aliases,
scripts on disk, and code an interpreter builds at run time.

hooks.json runs this with `python3` from PATH. If python3 is missing the
hook fails to start, which Claude Code treats as a non-blocking error,
so the guards are off on that machine. `onFailure: "block"` would close
that gap but would also block every Bash call in normal sessions there,
so it isn't set.

Normal sessions pass straight through to the permission rules, where
these commands ask instead.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import auto_state  # noqa: E402

# wrapper -> options that take a value
WRAPPERS = {
    "sudo": {"-u", "-g", "-h", "-p", "-C"}, "env": {"-u", "-C", "-S"}, "command": set(),
    "builtin": set(), "exec": {"-a"}, "nohup": set(), "time": set(), "nice": {"-n"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"}, "stdbuf": {"-i", "-o", "-e"},
    "xargs": {"-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a"}, "caffeinate": {"-t", "-w"},
    "watch": {"-n", "-d", "-g"}, "coproc": set(),
}
RESERVED = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "!", "{", "}",
            "case", "esac", "select", "function"}
TAKES_ONE_ARG = {"timeout"}  # the duration
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
GIT_REMOTE_WRITES = {"push", "send-pack"}
ALWAYS_REMOTE = {"sftp", "lftp", "ftp", "ssh", "rclone"}
GH_WRITES = {("pr", "create"), ("pr", "merge"), ("pr", "comment"), ("repo", "sync"),
             ("release", "create"), ("release", "upload"), ("workflow", "run"),
             ("gist", "create"), ("issue", "create")}
SUBST = "__CMDSUBST__"  # stands in for a $(...) or `...` once its body is read
SHELLS = {"bash", "sh", "zsh", "dash"}
INTERPRETERS = re.compile(r"^(python[\d.]*|node|ruby|perl|php|osascript)$")
PYTHON = re.compile(r"^python(\d+(\.\d+)?)?$")
REMOTE_PATH = re.compile(r"^([\w.-]+@)?[\w.-]+:|://")
LITERAL_DEPLOY = re.compile(r"\bgit\b[^\n]*\bpush\b|\btheme\s+(push|publish|share)\b|\bgh\s+pr\s+create\b")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def substitutions(command: str) -> tuple[str, list[str]]:
    """Split out $(...) and `...` that the shell would run.

    Returns the command with each one replaced by SUBST, and their bodies.
    Single-quoted text is left alone; double-quoted text is scanned.
    """
    out, bodies, i, n, dq = [], [], 0, len(command), False
    while i < n:
        c = command[i]
        if c == "'" and not dq:
            end = command.find("'", i + 1)
            end = n - 1 if end == -1 else end
            out.append(command[i:end + 1])
            i = end + 1
            continue
        if c == '"':
            dq = not dq
        if c == "\\":
            out.append(command[i:i + 2])
            i += 2
            continue
        if command.startswith("$(", i):
            depth, j = 1, i + 2
            while j < n and depth:
                depth += {"(": 1, ")": -1}.get(command[j], 0)
                j += 1
            bodies.append(command[i + 2:j - 1])
            out.append(SUBST)
            i = j
            continue
        if c == "`":
            end = command.find("`", i + 1)
            end = n if end == -1 else end
            bodies.append(command[i + 1:end])
            out.append(SUBST)
            i = end + 1
            continue
        out.append(c)
        i += 1
    return "".join(out), bodies


def split_heredocs(command: str) -> tuple[str, list[tuple[str, str, bool]]]:
    """The command without heredoc bodies, and (line, body, quoted) for each heredoc.

    A quoted delimiter (<<'EOF') means the body is not expanded.
    """
    lines = command.split("\n")
    kept, docs, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        kept.append(line)
        i += 1
        for match in HEREDOC.finditer(line):
            body = []
            while i < len(lines) and lines[i].strip() != match.group(2):
                body.append(lines[i])
                i += 1
            i += 1  # the terminator
            docs.append((line, "\n".join(body), bool(match.group(1))))
    return "\n".join(kept), docs


def segments(command: str) -> list[list[str]]:
    """Split a command line into simple commands, each a list of words."""
    text = re.sub(r"<<-?\s*(['\"]?)[A-Za-z_][A-Za-z0-9_]*\1", " ", command)
    text = text.replace("`", " ; ").replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    try:
        words = list(lexer)
    except ValueError:
        words = text.split()
    out, current = [], []
    for word in words:
        if word and set(word) <= set(";&|()<>"):
            if current:
                out.append(current)
            current = []
        else:
            current.append(word)
    if current:
        out.append(current)
    return out


def argv(words: list[str]) -> list[str]:
    """Drop leading keywords, assignments, wrappers and their options, and backslash escapes."""
    words = [w[1:] if w.startswith("\\") else w for w in words]
    changed = True
    while words and changed:
        changed = False
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] == "$"
                         or words[0] in RESERVED):
            if words[0] == "function" and len(words) > 1:
                words = words[1:]  # `function name {` drops the name too
            words, changed = words[1:], True
        if words and os.path.basename(words[0]) in WRAPPERS:
            prog = os.path.basename(words[0])
            valued = WRAPPERS[prog]
            words, changed = words[1:], True
            while words and words[0].startswith("-") and words[0] != "-":
                if prog == "env" and words[0] in ("-S", "--split-string") and len(words) > 1:
                    words = split_words(words[1]) + words[2:]  # env -S 'git push'
                    break
                if prog == "env" and words[0].startswith("--split-string="):
                    words = split_words(words[0].split("=", 1)[1]) + words[1:]
                    break
                words = words[2:] if words[0] in valued else words[1:]
            if prog in TAKES_ONE_ARG and words and not words[0].startswith("-"):
                words = words[1:]
    if words and " " in words[0]:  # watch "git push", xargs sh -c style strings
        try:
            split = shlex.split(words[0])
        except ValueError:
            return words  # a path with a stray quote, say; read it as it is
        if split and split[0] != words[0]:
            return argv(split + words[1:])
    return words


def split_words(text: str) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def git_subcommand(args: list[str]):
    i = 1
    while i < len(args):
        a = args[i]
        if a in GIT_OPTS_WITH_VALUE:
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            return i
    return None


def git_reason(args: list[str]):
    i = git_subcommand(args)
    if i is None:
        return None
    sub, rest = args[i], args[i + 1:]
    configs = [args[k + 1] for k in range(1, i) if args[k] == "-c" and k + 1 < i]
    aliases = {c.split("=", 1)[0][len("alias."):]: c.split("=", 1)[1]
               for c in configs if c.startswith("alias.") and "=" in c}
    if sub in GIT_REMOTE_WRITES or (sub in ("subtree", "lfs") and "push" in rest):
        return f"git {sub}"
    if sub.startswith(("$", SUBST)):
        return "a git subcommand that can't be read"
    if sub in aliases and re.search(r"\bpush\b", aliases[sub]):
        return "git push through an alias"
    if sub == "config" and any(a.startswith("alias.") for a in rest) and any("push" in a for a in rest):
        return "a git alias for push"
    return None


def reason_for(args: list[str], depth: int):
    prog = os.path.basename(args[0])
    rest = args[1:]

    if prog in SHELLS:
        for j, w in enumerate(rest):
            if w.startswith("-") and not w.startswith("--") and "c" in w[1:] and j + 1 < len(rest):
                return deploy_reason(rest[j + 1], depth + 1)
        return None
    if prog == "eval":
        return deploy_reason(" ".join(rest), depth + 1)
    if prog == "find":
        for flag in ("-exec", "-execdir", "-ok", "-okdir"):
            if flag in rest:
                inner = rest[rest.index(flag) + 1:]
                inner = inner[: inner.index(";")] if ";" in inner else inner
                inner = [w for w in inner if w not in ("+", "{}")]
                return reason_for(argv(inner), depth + 1) if argv(inner) else None
        return None
    if INTERPRETERS.match(prog):
        for j, w in enumerate(rest):
            if w in ("-c", "-e", "-r") and j + 1 < len(rest) and LITERAL_DEPLOY.search(rest[j + 1]):
                return "a push or publish run from an interpreter"
        return None

    if args[0].startswith(SUBST):
        return "a command word built by command substitution"
    if prog == "git":
        return git_reason(args)
    if args[0].startswith("$") and any(w in ("push", "publish", "upload") for w in rest):
        return "a push through a variable command"

    shopify = any(os.path.basename(w) == "shopify" or w.startswith("@shopify/cli") for w in args)
    for area, actions in (("theme", ("push", "publish", "share", "delete")), ("app", ("deploy", "release"))):
        if shopify and area in args:
            after = args[args.index(area) + 1:]
            if after and after[0] in actions:
                return f"shopify {area} {after[0]}"

    runners = ("npx", "pnpm", "bunx", "yarn", "dlx", "exec")
    vercel = [j for j, w in enumerate(args) if os.path.basename(w) == "vercel"
              and (j == 0 or os.path.basename(args[j - 1]) in runners)]
    if vercel:
        after = [w for w in args[vercel[0] + 1:] if not w.startswith("-")]
        if not after or after[0] in ("deploy", "redeploy", "promote", "alias") or "--prod" in args:
            return "vercel deploy"

    if prog == "gh" and len(rest) >= 2:
        if (rest[0], rest[1]) in GH_WRITES:
            return f"gh {rest[0]} {rest[1]}"
        if rest[0] == "api" and rest[1] == "graphql":
            if "--input" in rest or any("mutation" in w.lower() for w in rest):
                return "gh api graphql mutation"
        elif rest[0] == "api":
            method = None
            for j, w in enumerate(rest):
                if w in ("-X", "--method") and j + 1 < len(rest):
                    method = rest[j + 1].upper()
                elif w.startswith("--method="):
                    method = w.split("=", 1)[1].upper()
                elif w.startswith("-X") and len(w) > 2:
                    method = w[2:].upper()
            fields = any(w in ("-f", "-F", "--field", "--raw-field", "--input") or
                         w.startswith(("--field=", "--raw-field=", "--input=")) for w in rest)
            if method in WRITE_METHODS or (method is None and fields):
                return f"gh api {method or 'POST'}"
    if prog in ALWAYS_REMOTE:
        return f"{prog} to another host"
    if prog in ("rsync", "scp"):
        if any(REMOTE_PATH.search(w) for w in rest if not w.startswith("-")):
            return f"{prog} to another host"
    if prog == "curl":
        for j, w in enumerate(rest):
            nxt = rest[j + 1] if j + 1 < len(rest) else ""
            if w in ("-T", "--upload-file", "-F", "--form", "--form-string") or \
                    (w.startswith(("-F", "-T")) and len(w) > 2):
                return "curl upload"
            if w in ("-d", "--data", "--data-binary", "--data-urlencode") and nxt.startswith("@"):
                return "curl upload"
            if re.match(r"^(-d|--data(-binary|-urlencode)?=)@", w):
                return "curl upload"
            if w == "--json" or w.startswith("--json="):
                return "curl --json post"
    if prog == "wget" and any(w.split("=", 1)[0] in ("--post-file", "--post-data", "--body-file",
                                                      "--body-data", "--method") for w in rest):
        return "wget upload"
    if prog == "aws" and len(rest) >= 2 and (
            (rest[0] == "s3" and rest[1] in ("cp", "sync", "mv")) or
            (rest[0] == "s3api" and rest[1].startswith(("put-", "upload-", "copy-")))):
        return f"aws {rest[0]} {rest[1]}"
    if prog == "wp" and rest and (rest[0].startswith("@") or
                                  any(w.startswith(("--ssh=", "--http=")) for w in rest)):
        return "remote WP-CLI"
    return None


def deploy_reason(command: str, depth: int = 0):
    if depth > 4:
        return None
    text, docs = split_heredocs(command)
    text, bodies = substitutions(text)
    for _, body, quoted in docs:
        if not quoted:
            bodies += substitutions(body)[1]
    for inner in bodies:
        reason = deploy_reason(inner, depth + 1)
        if reason:
            return reason
    for line, body, _ in docs:
        # a heredoc fed to a shell, directly or through a pipe, is run
        runs = [argv(s) for s in segments(substitutions(line)[0])]
        if any(a and os.path.basename(a[0]) in SHELLS for a in runs):
            reason = deploy_reason(body, depth + 1)
            if reason:
                return reason
    for seg in segments(text):
        args = argv(seg)
        if args:
            reason = reason_for(args, depth)
            if reason:
                return reason
    return None


def starts_run(command: str) -> bool:
    """A real Python run of claim.py --slot or site_turn.py take."""
    for seg in segments(command):
        args = argv(seg)
        if args and PYTHON.match(os.path.basename(args[0])):
            args = [a for a in args[1:] if not a.startswith("-") or a == "--slot"]
        if not args:
            continue
        script = os.path.basename(args[0])
        if script == "claim.py" and "--slot" in args:
            return True
        if script == "site_turn.py" and len(args) > 1 and args[1] == "take":
            return True
    return False


def worktree_add(command: str):
    """(path, base commit) of a `git worktree add`, if the command has one."""
    for seg in segments(command):
        args = argv(seg)
        if not args or os.path.basename(args[0]) != "git":
            continue
        i = git_subcommand(args)
        if i is None or args[i:i + 2] != ["worktree", "add"]:
            continue
        repo = args[args.index("-C") + 1] if "-C" in args[:i] else "."
        rest, j, positional = args[i + 2:], 0, []
        while j < len(rest):
            tok = rest[j]
            if tok in ("-b", "-B", "--reason"):
                j += 2
            elif tok.startswith("-"):
                j += 1
            else:
                positional.append(tok)
                j += 1
        if not positional:
            continue
        path = os.path.expandvars(os.path.expanduser(positional[0]))
        start = positional[1] if len(positional) > 1 else "HEAD"
        base = subprocess.run(["git", "-C", os.path.expanduser(repo), "rev-parse", "--verify",
                               "--quiet", start + "^{commit}"], capture_output=True, text=True).stdout.strip()
        return path, base or None
    return None


def main() -> int:
    event = auto_state.read_event(sys.stdin)
    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    session = event.get("session_id", "")

    added = worktree_add(command)
    if added and auto_state.under_worktrees(added[0]):
        auto_state.mark(session, worktree=os.path.abspath(added[0]), base=added[1])
    elif starts_run(command):
        auto_state.mark(session)

    if not auto_state.is_auto(event):
        return 0
    reason = deploy_reason(command)
    if reason:
        print(
            f"Blocked in an Auto run: {reason}. An unattended run ends with a "
            "committed local branch and nothing leaves the machine. Leave this "
            "step for Ben and note it in the run log.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(auto_state.guarded(main))
