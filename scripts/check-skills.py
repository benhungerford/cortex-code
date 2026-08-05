#!/usr/bin/env python3
"""Structural gate for Cortex Code skills.

Checks every skills/*/SKILL.md for the frontmatter contract described in
docs/plans/2026-08-05-workflow-expansion.md. Exits 1 on any failure.
"""
import pathlib
import re
import sys

REQUIRED_ORDER = ["name", "description", "disable-model-invocation"]
MAX_DESCRIPTION = 200

def check(path: pathlib.Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return ["no YAML frontmatter delimited by --- at the top of the file"]

    body = match.group(1)
    problems = []
    keys = re.findall(r"^([A-Za-z0-9_-]+):", body, re.MULTILINE)

    if keys != REQUIRED_ORDER:
        problems.append(f"frontmatter keys are {keys}, expected {REQUIRED_ORDER}")

    name = re.search(r"^name:\s*(\S+)\s*$", body, re.MULTILINE)
    if not name:
        problems.append("no name")
    elif name.group(1) != path.parent.name:
        problems.append(f"name '{name.group(1)}' != directory '{path.parent.name}'")

    description = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
    if not description:
        problems.append("no description")
    else:
        value = description.group(1).strip()
        if len(value) > MAX_DESCRIPTION:
            problems.append(f"description is {len(value)} chars, max {MAX_DESCRIPTION}")
        if "Usage:/" not in value:
            problems.append("description has no 'Usage:/<move>' clause")

    if not re.search(r"^disable-model-invocation:\s*true\s*$", body, re.MULTILINE):
        problems.append("disable-model-invocation is not true")

    return problems

def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    skills = sorted(root.glob("skills/*/SKILL.md"))
    if not skills:
        print("FAIL: no skills found")
        return 1

    failed = False
    for path in skills:
        rel = path.relative_to(root)
        problems = check(path)
        if problems:
            failed = True
            for problem in problems:
                print(f"FAIL {rel}: {problem}")
        else:
            print(f"ok   {rel}")

    print("FAIL" if failed else f"PASS — {len(skills)} skills")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
