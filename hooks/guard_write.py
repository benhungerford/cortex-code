#!/usr/bin/env python3
"""PreToolUse guard for Write and Edit.

Always: a ticket's text above its `---` divider is frozen once written
(`.cortex/<task>/ticket.md` or `.cortex/<task>/NN-<slug>.md`). Writing a
new ticket is fine; changing that part of an existing one, ticking a
criterion included, is blocked.

In an Auto run only: a task note (`type: freelance-task`) can't be moved
to `status: done`, and a task that is already done can't have its
frontmatter changed. Normal sessions still need both, for acceptance and
for marking tasks billed.

An Edit whose old_string doesn't match a protected file exactly is
blocked, since the guard can't tell what it would change. Writes made
through Bash (sed -i, heredocs, scripts) don't pass through this hook.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import auto_state  # noqa: E402

TICKET = re.compile(r"/\.cortex/[^/]+/(?:ticket|\d{2}-[^/]+)\.md$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def proposed(tool: str, tool_input: dict, current: str):
    if tool == "Write":
        return tool_input.get("content", "")
    edits = tool_input.get("edits") or [tool_input]
    text = current
    for edit in edits:
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        if not old or old not in text:
            return None  # the edit will fail on its own
        text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def above_divider(text: str):
    """Everything up to and including the first `---` line after the frontmatter."""
    lines = text.replace("\r\n", "\n").split("\n")
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    for i in range(start, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[: i + 1])
    return None


def frontmatter(text: str):
    match = FRONTMATTER.match(text.replace("\r\n", "\n"))
    if not match:
        return None, {}
    fields = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip("\"'")
    return match.group(1), fields


def block(reason: str) -> int:
    print(reason, file=sys.stderr)
    return 2


def main() -> int:
    event = auto_state.read_event(sys.stdin)
    tool = event.get("tool_name")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    try:
        current = pathlib.Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0  # a new file
    new = proposed(tool, tool_input, current)
    is_ticket = TICKET.search(path.replace(os.sep, "/")) and above_divider(current) is not None
    is_task = frontmatter(current)[1].get("type") == "freelance-task" and auto_state.is_auto(event)
    if new is None:
        if is_ticket or is_task:
            return block(
                "This edit's old_string doesn't match the file exactly, so this guard can't "
                "tell what it would change in a protected file. Read the file again and use "
                "its exact text."
            )
        return 0

    if is_ticket:
        before = above_divider(current)
        if above_divider(new) != before:
            return block(
                "This ticket's Intent, Decisions and Criteria sit above the divider and "
                "are frozen once written; criteria are never ticked there either. "
                "Append below the divider instead, or, if the work has changed, write "
                "a new ticket on the same task."
            )

    if auto_state.is_auto(event):
        old_block, old_fields = frontmatter(current)
        new_block, new_fields = frontmatter(new)
        if old_fields.get("type") == "freelance-task":
            if old_fields.get("status") == "done" and new_block != old_block:
                return block(
                    "This task is done. Its frontmatter belongs to Ben now; an Auto "
                    "run leaves it alone."
                )
            if new_fields.get("status") == "done":
                return block(
                    "An Auto run goes as far as `status: review`. Only Ben moves a "
                    "task to done."
                )
    return 0


if __name__ == "__main__":
    sys.exit(auto_state.guarded(main))
