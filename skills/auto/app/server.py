#!/usr/bin/env python3
"""The brief app: a local page for writing briefs and watching their runs.

The files in the vault's _Briefs/ are the record; this is a view over
them. It writes only what Ben would write by hand (a new brief, the
sections of a draft or ready brief, and draft <-> ready) and leaves
everything the run sets alone.

    python3 server.py [--vault PATH] [--port 8765] [--no-open]

Binds to 127.0.0.1 only. Stops when the terminal closes or on Ctrl-C.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_VAULT = pathlib.Path.home() / "Documents" / "The Vault"

SECTIONS = [
    ("What", "One to three sentences. What should exist when this is done?", True),
    ("Designs", "- Figma links, screenshots, Pastel links", True),
    ("Where", "- Staging or unlaunched site URL (the repo comes from the project)", False),
    ("Done looks like", "- What you'd check first at review", False),
    ("Already decided", "- Anything you've settled, so it doesn't guess. Site facts go here too (which form plugin, video embeds, etc.)", False),
    ("Don't touch", "- Modules, apps or files to leave alone", False),
    ("Ask me before", "- Anything you don't want guessed. It will still keep going, but these go to the top of the review list.", False),
]
PLACEHOLDERS = {name: hint for name, hint, _ in SECTIONS}
EDITABLE = {"draft", "ready"}
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
LOG_LINE = re.compile(r"^- (\d{2}:\d{2}) → (\d{2}:\d{2}) · \*\*(.+?)\*\*")


class Vault:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.briefs = root / "_Briefs"

    # ---- reading -------------------------------------------------------

    def brief_path(self, name: str) -> pathlib.Path:
        """A brief's path from its file name. Refuses anything outside _Briefs/."""
        name = pathlib.PurePath(name).name
        if not name.endswith(".md") or name.startswith("_"):
            raise ValueError("not a brief")
        return self.briefs / name

    def projects(self) -> list[dict]:
        registry = json.loads((self.root / ".claude/cortex/registry.json").read_text())
        found = []
        for p in registry["projects"]:
            if not p["vault_path"].startswith("Work/TBL/") or not p.get("repo_paths"):
                continue
            repo = p["repo_paths"][0]
            is_git = subprocess.run(
                ["git", "-C", repo, "rev-parse", "--git-dir"], capture_output=True
            ).returncode == 0
            found.append({
                "path": p["vault_path"],
                "label": p["vault_path"].removeprefix("Work/TBL/").replace("/", " — ", 1),
                "git": is_git,
            })
        return sorted(found, key=lambda p: p["label"])

    def read(self, path: pathlib.Path) -> dict:
        text = path.read_text(encoding="utf-8")
        fields = parse_fields(text)
        title = re.search(r"^# (.+)$", text, re.MULTILINE)
        sections = parse_sections(text)
        brief = {
            "file": path.name,
            "title": title.group(1).strip() if title else path.stem,
            "status": fields.get("status", "draft"),
            "project": fields.get("project", ""),
            "created": fields.get("created", ""),
            "fields": fields,
            "sections": {name: sections.get(name, "") for name, _, _ in SECTIONS},
            "run_log": sections.get("Run log", ""),
        }
        brief.update(timing(fields, brief["run_log"]))
        brief["review_note"] = review_note(brief["run_log"])
        return brief

    def list(self) -> list[dict]:
        turns = {}
        turns_file = self.root / ".claude/cortex-auto/site-turns.json"
        if turns_file.exists():
            turns = json.loads(turns_file.read_text())
        out = []
        for folder, done in ((self.briefs, False), (self.briefs / "_Done", True)):
            if not folder.exists():
                continue
            for path in folder.glob("*.md"):
                if path.name.startswith("_"):
                    continue
                if parse_fields(path.read_text(encoding="utf-8")).get("type") != "brief":
                    continue
                brief = self.read(path)
                brief.pop("sections")
                brief["done"] = done
                brief["phase"] = phase(brief, turns)
                out.append(brief)
        return sorted(out, key=lambda b: (b["created"], b["file"]), reverse=True)

    # ---- writing -------------------------------------------------------

    def create(self, title: str, project: str, sections: dict) -> dict:
        title = clean_title(title)
        path = self.brief_path(title + ".md")
        if path.exists():
            raise ValueError(f"A brief called “{title}” already exists.")
        if project not in {p["path"] for p in self.projects()}:
            raise ValueError("Pick a project from the list.")
        today = dt.date.today().isoformat()
        body = "\n\n".join(section_block(n, sections.get(n, ""), req) for n, _, req in SECTIONS)
        text = (
            f"---\ntype: brief\nstatus: draft\nproject: \"{project}\"\nrun_started:\nrun_ended:\n"
            f"blocked_minutes:\ntags:\n  - \"#type/brief\"\ncreated: {today}\nupdated: {today}\n---\n\n"
            f"# {title}\n\n> Set `status: ready` when this is filled in. Only **What** and **Designs** are required.\n\n"
            f"{body}\n\n## Run log\n\n_Filled in by the run. Don't edit._\n\n"
            f"---\n*Related:* [[{project}/_MOC|Project]] · [[_Briefs/_MOC|Briefs]]\n"
        )
        path.write_text(text, encoding="utf-8")
        self.log("CREATED", path.name, "_Briefs/", f"Brief created in the brief app ({project})")
        self.add_to_moc(title)
        return self.read(path)

    def update(self, name: str, sections: dict, status: str | None) -> dict:
        path = self.brief_path(name)
        text = path.read_text(encoding="utf-8")
        current = parse_fields(text).get("status", "draft")
        if current not in EDITABLE:
            raise ValueError(f"This brief is {current}. Only draft and ready briefs can be edited.")
        for name_, _, _ in SECTIONS:
            if name_ in sections:
                text = replace_section(text, name_, sections[name_])
        new_status = status or current
        if new_status not in EDITABLE:
            raise ValueError("The app only moves a brief between draft and ready.")
        if new_status == "ready":
            problems = self.ready_problems(text)
            if problems:
                raise ValueError(" ".join(problems))
        text = set_field(text, "status", new_status)
        text = set_field(text, "updated", dt.date.today().isoformat())
        path.write_text(text, encoding="utf-8")
        note = "Sections edited in the brief app"
        if new_status != current:
            note += f"; status {current} → {new_status}"
        self.log("UPDATED", path.name, "_Briefs/", note)
        return self.read(path)

    def ready_problems(self, text: str) -> list[str]:
        """The intake checks the app can make without touching the site."""
        problems = []
        sections = parse_sections(text)
        for name, _, required in SECTIONS:
            if required and is_blank(name, sections.get(name, "")):
                problems.append(f"Fill in {name}.")
        project = parse_fields(text).get("project", "")
        match = next((p for p in self.projects() if p["path"] == project), None)
        if not match:
            problems.append("The project has no registered repo.")
        elif not match["git"]:
            problems.append("This site isn't a git repo yet, so a run would stop at intake.")
        return problems

    def add_to_moc(self, title: str):
        moc = self.briefs / "_MOC.md"
        text = moc.read_text(encoding="utf-8")
        line = f"- [[{title}]]"
        if line in text:
            return
        if "## All briefs" not in text:
            text = text.replace("\n---\n*Related:*", "\n## All briefs\n\n---\n*Related:*", 1)
        head, tail = text.split("## All briefs\n", 1)
        end = re.search(r"^(---|## )", tail, re.MULTILINE).start()
        items = [l for l in tail[:end].splitlines() if l.strip()] + [line]
        text = head + "## All briefs\n\n" + "\n".join(items) + "\n\n" + tail[end:]
        text = set_field(text, "updated", dt.date.today().isoformat())
        moc.write_text(text, encoding="utf-8")
        self.log("MOC_UPDATED", "_MOC.md", "_Briefs/_MOC.md", f"Added {title}")

    def log(self, action: str, file: str, dest: str, note: str):
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.root / "_changelog.txt", "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {action} | FILE: {file} | DEST: {dest} | NOTE: {note}\n")

    def totals(self) -> list[dict]:
        sites = {}
        for b in self.list():
            if not b.get("run_minutes"):
                continue
            s = sites.setdefault(b["project"], {
                "project": b["project"], "runs": 0, "run_minutes": 0,
                "build_minutes": 0, "blocked_minutes": 0, "queued_minutes": 0,
            })
            s["runs"] += 1
            for key in ("run_minutes", "build_minutes", "blocked_minutes", "queued_minutes"):
                s[key] += b.get(key) or 0
        return sorted(sites.values(), key=lambda s: s["project"])


# ---- parsing helpers -------------------------------------------------------

def parse_fields(text: str) -> dict:
    match = FRONTMATTER.match(text)
    fields = {}
    if match:
        for line in match.group(1).splitlines():
            m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", line)
            if m:
                fields[m.group(1)] = m.group(2).strip('"')
    return fields


def set_field(text: str, key: str, value) -> str:
    match = FRONTMATTER.match(text)
    body = match.group(1)
    if re.search(rf"^{key}:.*$", body, re.MULTILINE):
        body = re.sub(rf"^{key}:.*$", f"{key}: {value}", body, count=1, flags=re.MULTILINE)
    else:
        body += f"\n{key}: {value}"
    return text[: match.start(1)] + body + text[match.end(1):]


def parse_sections(text: str) -> dict:
    sections = {}
    parts = re.split(r"^## (.+?)\s*$", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        name = re.sub(r"\s*\(required\)$", "", parts[i]).strip()
        body = re.split(r"^---\s*$", parts[i + 1], maxsplit=1, flags=re.MULTILINE)[0]
        sections[name] = body.strip()
    return sections


def section_block(name: str, content: str, required: bool) -> str:
    heading = f"## {name} (required)" if required else f"## {name}"
    return f"{heading}\n\n{content.strip() or PLACEHOLDERS[name]}"


def replace_section(text: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf"(^## {re.escape(name)}(?: \(required\))?[ \t]*\n)(.*?)(?=^## |^---\s*$)",
        re.MULTILINE | re.DOTALL,
    )
    body = (content.strip() or PLACEHOLDERS[name]) + "\n\n"
    if not pattern.search(text):
        raise ValueError(f"Couldn't find the {name} section in this brief.")
    return pattern.sub(lambda m: m.group(1) + "\n" + body, text, count=1)


def is_blank(name: str, content: str) -> bool:
    return not content.strip() or content.strip() == PLACEHOLDERS[name]


def clean_title(title: str) -> str:
    title = re.sub(r"[\\/:*?\"<>|#^\[\]]", "", title).strip()
    if not title:
        raise ValueError("Give the brief a name.")
    return title


def minutes(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def timing(fields: dict, run_log: str) -> dict:
    fmt = "%Y-%m-%dT%H:%M"
    try:
        start = dt.datetime.strptime(fields.get("run_started", ""), fmt)
    except ValueError:
        return {"run_minutes": None, "steps": []}
    try:
        end = dt.datetime.strptime(fields.get("run_ended", ""), fmt)
    except ValueError:
        end = dt.datetime.now() if fields.get("status") == "running" else None
    run = int((end - start).total_seconds() // 60) if end else None
    blocked = minutes(fields.get("blocked_minutes"))
    queued = minutes(fields.get("queued_minutes"))
    steps = []
    for line in run_log.splitlines():
        m = LOG_LINE.match(line.strip())
        if not m:
            continue
        a, b = (dt.datetime.strptime(t, "%H:%M") for t in m.group(1, 2))
        span = int((b - a).total_seconds() // 60) % (24 * 60)
        steps.append({"step": m.group(3), "start": m.group(1), "minutes": span})
    return {
        "run_minutes": run,
        "blocked_minutes": blocked,
        "queued_minutes": queued,
        "build_minutes": max(0, run - blocked - queued) if run is not None else None,
        "steps": steps,
    }


def review_note(run_log: str):
    match = re.search(r"\[\[([^\]|]*Auto Review[^\]|]*)", run_log)
    return match.group(1) if match else None


def phase(brief: dict, turns: dict) -> str:
    """What a running brief is doing right now, in a word or two."""
    if brief["status"] != "running":
        return brief["status"]
    turn = turns.get(brief["project"], {})
    me = f"_Briefs/{brief['file']}"
    if (turn.get("holder") or {}).get("brief") == me:
        return "building"
    if any(w.get("brief") == me for w in turn.get("queue", [])):
        return "waiting for site"
    return "planning"


# ---- HTTP ------------------------------------------------------------------

def make_handler(vault: Vault):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status: int, payload, content_type="application/json"):
            body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")

        def guard(self, action):
            try:
                self.send(200, action())
            except (ValueError, FileNotFoundError) as e:
                self.send(400, {"error": str(e)})

        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(url.query)
            if url.path == "/":
                self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/briefs":
                self.guard(lambda: {"briefs": vault.list(), "totals": vault.totals(),
                                    "vault": vault.root.name})
            elif url.path == "/api/brief":
                self.guard(lambda: vault.read(vault.brief_path(query.get("file", [""])[0])))
            elif url.path == "/api/projects":
                self.guard(lambda: {"projects": vault.projects()})
            else:
                self.send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/brief":
                return self.send(404, {"error": "not found"})
            data = self.body()
            self.guard(lambda: vault.create(data.get("title", ""), data.get("project", ""),
                                            data.get("sections", {})))

        def do_PUT(self):
            if self.path != "/api/brief":
                return self.send(404, {"error": "not found"})
            data = self.body()
            self.guard(lambda: vault.update(data.get("file", ""), data.get("sections", {}),
                                            data.get("status")))

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", type=pathlib.Path, default=DEFAULT_VAULT)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    vault = Vault(args.vault.expanduser().resolve())
    if not vault.briefs.is_dir():
        print(f"No _Briefs/ folder in {vault.root}", file=sys.stderr)
        return 1

    for port in range(args.port, args.port + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(vault))
            break
        except OSError:
            continue
    else:
        print("No free port near", args.port, file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{port}/"
    print(f"Briefs: {url}  (Ctrl-C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
