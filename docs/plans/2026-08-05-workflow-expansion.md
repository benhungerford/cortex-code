# Workflow Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow Cortex Code from three moves against an existing task to nine moves spanning a loose idea through a signed-off build, adding a durable map before the tasks and a durable foundation beneath them.

**Architecture:** Every move is a single `skills/<name>/SKILL.md` file with YAML frontmatter and a Markdown body. There is no runtime, no build step, and no test suite — the deliverable is prose that an agent follows. Correctness is enforced two ways: a structural checker (`scripts/check-skills.py`) that gates frontmatter, and a per-task read-through gate against the design document. Skills communicate only through file paths on disk, so the "Interfaces" block in each task below is the authoritative path contract.

**Tech Stack:** Markdown + YAML frontmatter, Python 3 (checker only), `git`, the `claude` CLI for token-cost verification.

## Global Constraints

- **Every skill is `skills/<name>/SKILL.md`.** One file per skill. No `references/` subdirectories — the existing three skills are single-file and 1,500–1,800 words, and the roster stays legible that way.
- **Frontmatter is exactly three keys, in this order:** `name`, `description`, `disable-model-invocation: true`. No other keys.
- **`name` must equal the containing directory name.** The checker enforces this.
- **`disable-model-invocation: true` on every skill, without exception.** Nothing in this plugin may fire by accident; every move is invoked deliberately.
- **`description` ends with a `Usage:` clause** in the existing style: `Usage:/build TT-06`. Descriptions are always-on token cost — keep each under 200 characters.
- **Voice matches the existing three skills:** declarative, second person, no hedging, no emoji, no bullet padding. Claims are justified by what happened on the pilot where a pilot fact exists. British-influenced spelling is used in places (`behaviour`, `summarising`) — match the file you are editing rather than normalising across files.
- **Path conventions, used verbatim everywhere:**
  - `.cortex/foundation/` — the four standing-fact files
  - `.cortex/ideation/<effort>/` — artifacts from a task-less ideation session
  - `.cortex/<task>/` — artifacts and tickets for a named task
  - `docs/agents/issue-tracker.md` — binds this repo to its vault project; every move that touches the vault reads it first and stops if it is absent
- **Standing guardrails that appear in every move that touches a task:** never delete a task or ticket; never move a task to `done`; never tick a criterion; never invent or adjust `rate`, `billed`, or `invoice`; propose hours and invite correction, never finalise them.
- **`/create-tasks` is the only move permitted to author a task, and only with human sign-off.** Every other move that finds a missing task stops and says so.
- **Dates in examples use `2026-08-05` or later.** Do not copy `2026-08-06` from the existing ticket skill's examples into new files as if it were today.

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `scripts/check-skills.py` | Structural gate: frontmatter shape, name/dir match, invocation flag | 1 |
| `skills/foundation/SKILL.md` | Scan the repo, write the four standing-fact files | 2 |
| `skills/grill-me/SKILL.md` | One-question-at-a-time interview; writes a transcript | 3 |
| `skills/research/SKILL.md` | Background agent against primary sources; writes cited findings | 4 |
| `skills/prototype/SKILL.md` | Throwaway UI variants or browser-run state harness | 5 |
| `skills/ideation/SKILL.md` | Chart and work a map of questions in the vault | 6 |
| `skills/create-tasks/SKILL.md` | Propose a task set, write only on approval | 7 |
| `skills/create-tickets/SKILL.md` | Assemble tickets from task + capture + foundation | 8 (replaces `skills/ticket/`) |
| `skills/build/SKILL.md` | Amended: maintains the foundation files | 9 |
| `skills/qa/SKILL.md` | Amended: names `/create-tickets` in its handoff | 9 |
| `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Roster, version, honest size claim | 10 |

Task order is a dependency order. Tasks 3–5 must land before task 6 (ideation names them), and tasks 2–5 before task 8 (create-tickets reads their outputs).

---

### Task 1: The skill checker

Every later task's verification step runs this. It exists first so that every subsequent task has a real red-green cycle rather than a read-through alone.

**Files:**
- Create: `scripts/check-skills.py`

**Interfaces:**
- Consumes: nothing
- Produces: `python3 scripts/check-skills.py` — exits `0` when every `skills/*/SKILL.md` is structurally valid, exits `1` and prints one `FAIL <path>: <reason>` line per problem otherwise. Every later task calls this exact command.

- [ ] **Step 1: Write the checker**

Create `scripts/check-skills.py`:

```python
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
    keys = re.findall(r"^([a-z-]+):", body, re.MULTILINE)

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
```

- [ ] **Step 2: Run it against the three existing skills — expect PASS**

```bash
python3 scripts/check-skills.py
```

Expected: three `ok` lines for `build`, `qa`, `ticket`, then `PASS — 3 skills`, exit `0`.

If `ticket` fails on the description length or the `Usage:` clause, do **not** loosen the checker — read `skills/ticket/SKILL.md` and report the discrepancy, because task 8 rewrites that file and needs to know.

- [ ] **Step 3: Prove the checker actually fails**

```bash
mkdir -p skills/__probe && printf -- '---\nname: wrong-name\ndescription: no usage clause here\n---\n\n# probe\n' > skills/__probe/SKILL.md
python3 scripts/check-skills.py; echo "exit=$?"
```

Expected: `FAIL skills/__probe/SKILL.md` lines naming the key order, the name/directory mismatch, the missing `Usage:/` clause, and the missing `disable-model-invocation`; then `FAIL` and `exit=1`.

- [ ] **Step 4: Remove the probe and confirm green again**

```bash
rm -rf skills/__probe && python3 scripts/check-skills.py; echo "exit=$?"
```

Expected: `PASS — 3 skills`, `exit=0`.

- [ ] **Step 5: Commit**

```bash
git add scripts/check-skills.py
git commit -m "Add a structural checker for skill frontmatter"
```

---

### Task 2: `/foundation`

**Files:**
- Create: `skills/foundation/SKILL.md`

**Interfaces:**
- Consumes: `docs/agents/issue-tracker.md` (to confirm the repo is bound); the repo itself
- Produces: `.cortex/foundation/design-system.md`, `.cortex/foundation/components.md`, `.cortex/foundation/platform.md`, `.cortex/foundation/concerns.md`. Tasks 8 and 9 read and write these exact four paths. Each file opens with the provenance frontmatter defined in Step 1 below.

- [ ] **Step 1: Write the skill**

Create `skills/foundation/SKILL.md` with this frontmatter verbatim:

```yaml
---
name: foundation
description: Scan the repo and write the four standing-fact files under .cortex/foundation/ that every ticket would otherwise re-derive. Usage:/foundation
disable-model-invocation: true
---
```

The body is yours to write in the house voice, and it must contain these sections carrying this content:

**`# foundation`** — an opening that states the problem it solves: `/create-tickets` researches the repo on every task, and most of what it finds is the same on task nine as on task one, paid for nine times.

**`## Inputs`** — `/foundation` takes no argument. It stops if `docs/agents/issue-tracker.md` is absent, in the same words `build` uses: this repo has not been bound to a vault project. It detects the platform from the repo (a `config/settings_schema.json` and `layout/theme.liquid` means Shopify; a `style.css` with a theme header or a `theme.json` means WordPress) and states which branch it took before scanning.

**`## Preconditions`** — foundation reads a repo that has something in it. On a new Horizon build there is nothing to scan on day one, so it runs after bootstrap, not before. If the repo is effectively empty, say so and stop rather than writing four near-empty files that later moves will trust.

**`## The four files`** — a table of the four paths and what each holds, taken from the design document:

| File | Holds |
|---|---|
| `design-system.md` | Tokens with their definition sites, declared-but-dead among them, type scale, spacing, breakpoints, class convention and its counter-examples |
| `components.md` | Every reusable snippet and section: path, actual render signature, available variants |
| `platform.md` | Template and section architecture, custom-element conventions, and the events the theme emits |
| `concerns.md` | Third-party app surface, vendored CSS, do-not-touch areas, half-finished attempts |

**`## Provenance`** — every file opens with this frontmatter, verbatim:

```yaml
---
generated: 2026-08-05
commit: a1b2c3d
platform: shopify
scanned:
  - assets/*.css
  - snippets/
  - sections/
---
```

`commit` is the short SHA of `HEAD` at generation. `scanned` is the glob list actually walked, not the list intended — task 9's staleness check intersects changed paths against it, and an aspirational entry makes the check lie.

**`## Evidence rules`** — every claim carries `file:line`. Anything inferred rather than observed is marked `(inferred)`. This is the same discipline that stops `qa` ticking what it did not see, applied to a document later moves trust without re-checking. A file that cannot cite a claim omits the claim.

**`## What each file must contain`** — one subsection per file, saying specifically what to look for. For `components.md`, require the *actual* render signature read out of the snippet's `{{ }}` and `{% liquid %}` usage — `{% render 'button', label: ..., url: ..., style: ... %}` — because the point of the file is that a build reaches for the existing snippet instead of hand-rolling an `<a class="btn">`. For `platform.md`, require the events the theme emits by name, because that is what a build listens to instead of polling. For `concerns.md`, require the third-party app surface — which app injects markup or styles and where — and justify it with the pilot fact: a subscription app rendered its `selling_plan` input inside the product form, and finding that changed the architecture before a line was written.

**`## Shopify` and `## WordPress`** — the platform branch. Name the concrete places each branch reads: for Shopify, `config/settings_schema.json`, `assets/*.css`, `snippets/`, `sections/`, `templates/*.json`, and the theme's JS entry; for WordPress, `theme.json`, `style.css`, `functions.php`, the block or pattern directory, and any enqueued stylesheet. Say plainly that the four files describe different objects on each platform and that a Shopify-shaped `components.md` in a WordPress repo is a wrong file, not a partial one.

**`## Guardrails`** — at minimum: never write a claim you cannot cite; never guess a render signature from a snippet's name; never overwrite a file with fewer facts than it had (a re-run that loses detail is a regression, so re-runs are additive unless the underlying file genuinely changed); never scan a repo that has not been bound to a vault project.

Do not write a handoff to another move. `/foundation` is not a chain step.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/foundation/SKILL.md` among the results, then `PASS — 4 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Read `skills/foundation/SKILL.md` start to finish against the "`/foundation`" section of `docs/design/2026-08-05-workflow-expansion-design.md`. Confirm all four file paths appear verbatim, the provenance block is present, the platform branch is present, and the "maintained, not regenerated" idea is stated — the SHA stamp exists so task 9's check can intersect it, not so `/foundation` re-runs weekly.

- [ ] **Step 4: Commit**

```bash
git add skills/foundation/SKILL.md
git commit -m "Add the foundation move: four standing-fact files per repo"
```

---

### Task 3: `/grill-me`

**Files:**
- Create: `skills/grill-me/SKILL.md`

**Interfaces:**
- Consumes: an optional task ID, or an ideation effort name
- Produces: `.cortex/<task>/grill-NN.md` when given a task; `.cortex/ideation/<effort>/grill-NN.md` when invoked from a map question. `NN` is zero-padded and increments from the highest existing file in that folder. Task 8 reads every `grill-*.md` in `.cortex/<task>/`.

- [ ] **Step 1: Write the skill**

Frontmatter verbatim:

```yaml
---
name: grill-me
description: A relentless one-question-at-a-time interview that settles what research cannot, written down as it goes. Usage:/grill-me TT-06
disable-model-invocation: true
---
```

Body sections and their content:

**`# grill-me`** — a relentless interview that reaches shared understanding on a plan, decision, or idea, and writes the result somewhere a cold session can read it.

**`## Inputs`** — `/grill-me <task>` writes to `.cortex/<task>/`. `/grill-me` with no argument, inside an ideation session, writes to `.cortex/ideation/<effort>/`. With neither, ask which before starting; do not guess a home, because a transcript written to the wrong folder is a transcript no later move will find.

**`## How to grill`** — carry over upstream's rules and state them as rules:
- Walk down each branch of the decision tree, resolving dependencies between decisions one at a time.
- For each question, give your recommended answer and the reason for it.
- **One question per message.** Asking several at once is bewildering and produces one answer to the easiest of them.
- If a *fact* can be found in the filesystem, the repo, or a tool, look it up rather than asking. The *decisions* are the human's — put each one to them and wait.
- Do not act on any of it until the human confirms shared understanding has been reached.

**`## Write as you go`** — append each answer to the transcript file as it is given, in the human's own terms rather than your summary of them. Not at the end, when you are summarising and will smooth what was said into something more agreeable. This mirrors the rule already in the ticket move, and it is the reason the transcript is worth reading cold.

**`## The transcript`** — the file shape, verbatim:

```markdown
---
task: TT-06
grilled: 2026-08-05
---

# Grill — TT-06

## Settled

- **<question>** — <the answer, in their words>

## Still open

- <question the human deferred, and what it blocks>
```

`Still open` is not a failure state. A question the human deliberately deferred is information task 8 needs; an empty `Still open` on a grill that ended early is a lie.

**`## Guardrails`** — never answer your own question and record it as settled (an agent that grills itself has broken the whole point of the move); never ask what the repo answers; never write a decision the human did not make; never finish while a question you asked is unanswered — either it is in `Settled`, or it is in `Still open`.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/grill-me/SKILL.md`, then `PASS — 5 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Confirm the file states the one-question-per-message rule, the look-up-facts rule, the write-as-you-go rule, and both write targets. Confirm it never tells the agent to answer on the human's behalf.

- [ ] **Step 4: Commit**

```bash
git add skills/grill-me/SKILL.md
git commit -m "Add the grill-me move"
```

---

### Task 4: `/research`

**Files:**
- Create: `skills/research/SKILL.md`

**Interfaces:**
- Consumes: a question, plus an optional task ID or ideation effort name
- Produces: `.cortex/<task>/research-NN-<slug>.md` or `.cortex/ideation/<effort>/research-NN-<slug>.md`. Task 8 reads every `research-*.md` in `.cortex/<task>/`.

- [ ] **Step 1: Write the skill**

Frontmatter verbatim:

```yaml
---
name: research
description: Investigate a question against primary sources in a background agent and capture the findings as a cited file. Usage:/research TT-06 <question>
disable-model-invocation: true
---
```

Body sections and their content:

**`# research`** — investigate a question whose answer lives outside the repo, and leave the answer somewhere a cold session can read it.

**`## Inputs`** — the question, plus the task or effort that names the write target. Same two-home rule as `grill-me`; ask rather than guess.

**`## Spin up a background agent`** — the reading is delegated so the calling session keeps working. Say this plainly.

**`## Primary sources only`** — official documentation, source code, specifications, and first-party APIs — never a secondary write-up of them. Follow every claim back to the source that owns it. Name the sources that exist for this workflow specifically: the Shopify dev MCP server for Shopify platform questions, the theme's own source, the app vendor's own documentation for third-party behaviour, and WordPress core or block-editor documentation for WordPress questions.

**`## Cite everything`** — one file, every claim carrying its source as a URL or a `file:line`. An uncited claim is a claim task 8 has to re-derive, which is the cost this move exists to remove.

**`## The findings file`** — the shape, verbatim:

```markdown
---
task: TT-06
question: Does the Loop widget expose a selling_plan change event?
researched: 2026-08-05
---

# Research — <question>

## Answer

<the short answer, first>

## Evidence

- <claim> — <https://source-that-owns-it>

## What this rules out

<the options this closes, and why>
```

`What this rules out` is the section that earns the file. An answer that does not change what gets built was not worth researching, and saying what it closes forces that check.

**`## Guardrails`** — never cite a blog post standing in for a specification; never report a fact you could not follow to its owning source; never answer from memory when a source exists; say plainly when the sources do not settle the question rather than producing a confident file.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/research/SKILL.md`, then `PASS — 6 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Confirm the file names the background agent, the primary-source rule, the citation rule, and both write targets.

- [ ] **Step 4: Commit**

```bash
git add skills/research/SKILL.md
git commit -m "Add the research move"
```

---

### Task 5: `/prototype`

**Files:**
- Create: `skills/prototype/SKILL.md`

**Interfaces:**
- Consumes: a question, plus an optional task ID or ideation effort name
- Produces: `.cortex/<task>/prototype-NN-<slug>.md` or `.cortex/ideation/<effort>/prototype-NN-<slug>.md` — a pointer file recording the question, the verdict, and the branch the throwaway code lives on. The code itself lives on a throwaway git branch, never on the default branch.

- [ ] **Step 1: Write the skill**

Frontmatter verbatim:

```yaml
---
name: prototype
description: Build throwaway code that answers a design or behaviour question — UI variants on one route, or real theme state driven in a browser. Usage:/prototype TT-06
disable-model-invocation: true
---
```

Body sections and their content:

**`# prototype`** — throwaway code that answers a question. The question decides the shape.

**`## Pick a branch`** — two, and getting it wrong wastes the whole prototype:
- *What should this look like?* → the **UI** branch.
- *Does this behave right?* → the **behaviour** branch.

If the question is genuinely ambiguous and the human is not reachable, pick from the surrounding code — a template or section means UI, a script or state interaction means behaviour — and state the assumption at the top of the prototype.

**`## UI branch`** — several radically different takes on one throwaway template, switchable by a query parameter, with a floating switcher so the human can flip between them without editing a URL by hand. Follow whatever routing or template convention the theme already uses; do not invent a new top-level structure. Radically different is the requirement — three variations on one idea answer nothing.

**`## Behaviour branch`** — a throwaway route that exercises the real theme JS in a real browser: cart drawer, variant selection, price sync, whatever the question is about. Render the full relevant state on screen after every action so the human can see what changed.

State why this departs from the usual approach: the conventional logic prototype is an interactive terminal application driving a state machine, and there is no runtime for that in a theme repo. More importantly, the browser is this workflow's entire feedback loop. On the pilot, four bugs that read as correct code were caught only in a browser — an `IntersectionObserver` that never fires on a jump-scroll, a sticky bar showing a price the cart did not charge, a one-shot sync racing an app's asynchronous property write, and a stacking-context collision that a `z-index` comparison could not see. A logic prototype that does not run in a browser cannot answer the questions that actually bite here.

**`## Rules for both branches`** — carry these over and keep them as numbered rules:
1. Throwaway from day one and clearly marked as such. Locate it next to what it prototypes so the context is obvious, and name it so a casual reader can see it is not production.
2. One command to run it. The human must be able to start it without thinking.
3. No persistence. State lives in memory.
4. No polish. No tests, no error handling beyond what makes it runnable, no abstractions.
5. Surface the state. Print or render everything relevant after every action or variant switch.
6. Capture it when done. Fold the validated decision into the real work, commit the prototype to a throwaway branch off the default branch, and leave the pointer file.

**`## The pointer file`** — the shape, verbatim:

```markdown
---
task: TT-06
prototyped: 2026-08-05
branch: prototype/sticky-bar-variants
---

# Prototype — <question>

## Verdict

<what was decided, and what the human said when they saw it>

## What it ruled out

<the options this closed>
```

**`## Guardrails`** — never leave prototype code on the default branch; never let a prototype grow error handling or tests; never record a verdict the human did not give (the UI and behaviour branches both exist to be reacted to, and a prototype nobody looked at has no verdict); never keep a prototype alive as production code because it worked.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/prototype/SKILL.md`, then `PASS — 7 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Confirm both branches are present, the behaviour branch is browser-based rather than terminal-based, all six shared rules are present, and the pointer-file shape matches.

- [ ] **Step 4: Commit**

```bash
git add skills/prototype/SKILL.md
git commit -m "Add the prototype move, with its logic branch retargeted at the browser"
```

---

### Task 6: `/ideation`

**Files:**
- Create: `skills/ideation/SKILL.md`

**Interfaces:**
- Consumes: a loose idea (charting mode), or a map (working mode); `docs/agents/issue-tracker.md` to resolve the vault project; the three capture moves from tasks 3–5
- Produces: a map note in the vault project, with question notes as children; artifacts in `.cortex/ideation/<effort>/`. Task 7 reads the map's `## Decisions so far` section.

- [ ] **Step 1: Write the skill**

Frontmatter verbatim:

```yaml
---
name: ideation
description: Chart a foggy effort as a map of questions in the vault, then resolve them one per session until the way to the destination is clear. Usage:/ideation
disable-model-invocation: true
---
```

Body sections and their content:

**`# ideation`** — a loose idea has arrived, too big for one session and wrapped in fog: the way to the destination is not visible yet. Ideation charts that way as a map, then works its questions one at a time until nothing is left to decide. It is about finding the way, not charging at the destination.

**`## Vocabulary`** — state the collision explicitly, because a reader arriving from wayfinding will expect the other word. These are **questions**, not tickets. A question resolves into a decision and then closes. A ticket in this plugin is a build session: append-only, and it does not close until the work ships.

**`## Plan, don't do`** — ideation produces decisions, not deliverables. Each question resolves a decision, and the map is done when nothing is left to decide before someone goes and builds. The pull to just do the work is the signal you have reached the edge of the map, and the response is `/create-tasks`, not building.

**`## The map`** — a note in the active vault project, resolved through `docs/agents/issue-tracker.md`. It is an index, not a store: a decision lives in exactly one place, its question, and the map gists and links rather than restating. The body, verbatim:

```markdown
## Destination

<what reaching the end of this map looks like — the spec, decision, or change
this effort is finding its way to. One or two lines; every session orients to
it before choosing a question.>

## Notes

<domain; skills every session should consult; standing preferences>

## Decisions so far

- [[<closed question>]] — <one-line gist of the answer>

## Not yet specified

<in-scope fog that cannot be phrased sharply yet; graduates as the frontier advances>

## Out of scope

<work ruled beyond the destination; closed, never graduates>
```

**`## Questions`** — child notes of the map. Each carries a type — `research`, `prototype`, `grilling`, or `task` — and a `blocked_by:` frontmatter list, since Obsidian has no native dependency edge. The frontmatter, verbatim:

```yaml
---
type: question
map: "<map note name>"
question_type: grilling
blocked_by: []
status: open
---
```

The **frontier** is the open questions with no unclosed blocker. There is no claim or assignee mechanic: upstream assigns a question before work starts so concurrent sessions skip it, and that solves a problem this workflow does not have — one person, one session at a time. An open unblocked question is takeable, and that is the whole rule.

**`## Question types`** — four, each saying which move resolves it:
- **research** — a fact a decision waits on, resolved by `/research` as a background agent. The only type that may run in parallel.
- **prototype** — resolved by `/prototype`, when "how should it look" or "how should it behave" is the question.
- **grilling** — resolved by `/grill-me`. The default case.
- **task** — manual work that must happen before a decision can be made: signing up for a service so its API can be judged, provisioning access, getting the client to send the assets. Nothing to decide, but the discussion is blocked until it is done. It is the one type that *does* rather than decides, and it earns its place by unblocking a decision. Resolved when the work is done; the answer records what was done and any facts later questions depend on.

**`## Fog of war`** — the map is deliberately incomplete. Beyond the live questions is the fog: decisions you can tell are coming but cannot yet pin down. Resolving a question clears the fog ahead of it. The test for fog-or-question is whether you can *state* the question precisely now, not whether you can answer it: sharp enough to phrase means a question, even if blocked; not sharp enough means `Not yet specified`. Do not pre-slice fog into question-sized pieces.

**`## Out of scope`** — fog gathers only toward the destination, so work beyond it is out of scope, not fog. When a question turns out to sit past the destination, close it and leave one line in `Out of scope` with the gist and the reason. It stays out of `Decisions so far`, which records the route actually walked.

**`## Where artifacts live`** — `.cortex/ideation/<effort>/`. Ideation frequently runs the week a project is won, before a repo exists; in that case the map holds those artifacts inline and they move to `.cortex/ideation/<effort>/` once there is a repo. Say plainly that this is a normal case, not an edge one, and that blocking on a missing repo would push the work back into a chat window.

**`## Charting a map`** — numbered:
1. Name the destination. Grill to pin down what this map is finding its way to. The destination fixes the scope, so it is settled first.
2. Map the frontier — grill again, breadth-first, fanning out across the space rather than deep on one thread. If this surfaces no fog, the way is already clear and the effort fits one session: say so and stop, because it does not need a map.
3. Create the map with Destination and Notes filled in, `Decisions so far` empty, and the fog sketched into `Not yet specified`.
4. Create the questions you can specify now, then wire `blocked_by` in a second pass.
5. Fire the research questions as background agents in parallel.
6. Stop. Charting is one session's work and resolves nothing by hand.

**`## Working a map`** — numbered:
1. Load the map, not every question body.
2. Choose a question: the one named, or the first on the frontier.
3. Resolve it with the move its type names, zooming into related or closed questions on demand.
4. Record the resolution on the question, close it, and append the one-line gist to `Decisions so far`.
5. Add newly surfaced questions and graduate any fog the answer made specifiable, clearing each graduated patch from `Not yet specified` so it lives only as its new question. If the answer reveals a question sits beyond the destination, rule it out of scope rather than resolving it.

**One question per session, research excepted.**

**`## Handoff`** — when the map has no open questions, print:

```
/clear
```
```
/create-tasks
```

**`## Guardrails`** — never resolve more than one question per session (research excepted); never answer a grilling or prototype question on the human's behalf; never restate a decision on the map that its question already holds; never write a task — that is `/create-tasks`, and only with sign-off; never let fog past the destination become `Not yet specified`.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/ideation/SKILL.md`, then `PASS — 8 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Confirm: the word "ticket" never refers to a map child anywhere in the file; the claim mechanic is absent and its absence is justified; all four question types are present; both charting and working modes are numbered; the no-repo-yet case is covered; the handoff names `/create-tasks`.

```bash
grep -n "ticket" skills/ideation/SKILL.md
```

Expected: hits only where the file is *distinguishing* a question from a ticket, in the Vocabulary section. Any other hit is the collision leaking back in — fix it.

- [ ] **Step 4: Commit**

```bash
git add skills/ideation/SKILL.md
git commit -m "Add the ideation move: a map of questions in the vault"
```

---

### Task 7: `/create-tasks`

**Files:**
- Create: `skills/create-tasks/SKILL.md`

**Interfaces:**
- Consumes: a closed map's `## Decisions so far` (task 6), or a brief handed in directly; `docs/agents/issue-tracker.md` to resolve where tasks are written
- Produces: task notes in the vault `Tasks/` folder or Monday items, each carrying a pointer to `.cortex/<task>/` and the map decisions that produced it. Task 8 reads these.

- [ ] **Step 1: Write the skill**

Frontmatter verbatim:

```yaml
---
name: create-tasks
description: Propose a set of billable tasks from a closed map or a brief, then write them only once the human has approved the set. Usage:/create-tasks
disable-model-invocation: true
---
```

Body sections and their content:

**`# create-tasks`** — the move that turns a cleared map into billable work. State immediately that this is the one move permitted to author a task, that it inverts a standing rule, and that it is only allowed to because it never writes without sign-off.

**`## Inputs`** — a map whose questions are all closed, or a brief handed in directly. With neither, ask. If a map has open questions, say which and stop: tasks drawn from an unfinished map carry decisions that have not been made.

**`## What a task is`** — the billing unit. It lives in the vault, or arrives from Monday and is mirrored there. It carries hours, rate, billing state, and a short client-readable summary of what shipped. Tasks never nest — `parent:` is a grouping label and nothing more. Reference the two shapes from the model: a site audit is nine tasks sharing a `parent:`; a homepage rebuild is one task and five tickets.

**`## Propose first`** — the table shown before anything is written, with these columns: title, scope line, proposed hours, `parent:`, build order. Show the whole set at once, because the shape of the split is the thing being approved and it cannot be judged one row at a time.

**Hours are proposed and explicitly invited to be corrected.** Use the pilot fact already in the build move: the agent logged 3 hours for work the human priced at 2. State the estimate, say what it assumes, and let the human place it.

**`## Write only on approval`** — nothing is written until the human approves the set. Changes to the table are made in the table and re-shown, not written and then amended.

**`## The task file`** — the frontmatter, verbatim, matching the model:

```yaml
---
type: freelance-task
task: TT-06
client: Acme Coffee
project: Shopify Website Build
parent: "Q3 audit"
status: todo
estimate_low: 1
estimate_high: 2
hours: 0
cortex: .cortex/TT-06/
---
```

`cortex:` is the pointer to the capture folder. `/create-tickets` follows it, so it is written even before the folder exists.

The body carries the scope line, and a `## From the map` section listing the decisions that produced this task, each linking its closed question. That section is why `/create-tickets` inherits the reasoning instead of re-deriving it.

**`## Where they are written`** — wherever `docs/agents/issue-tracker.md` names, so Obsidian and Monday stay a configuration difference rather than a code path.

**`## Handoff`** — print:

```
/clear
```
```
/create-tickets <task>
```

**`## Guardrails`** — never write a task without explicit approval of the set; never invent hours (propose them); never invent or adjust `rate`, `billed`, or `invoice`; never nest tasks; never draw tasks from a map with open questions; never write a task and then quietly adjust it — a changed set is re-proposed.

- [ ] **Step 2: Run the checker**

```bash
python3 scripts/check-skills.py
```

Expected: `ok   skills/create-tasks/SKILL.md`, then `PASS — 9 skills`, exit `0`.

- [ ] **Step 3: Read-through gate**

Confirm the propose-then-approve gate is unmissable, the hours guardrail is present, the `cortex:` frontmatter key is present, and the task frontmatter matches the model document's shape.

- [ ] **Step 4: Commit**

```bash
git add skills/create-tasks/SKILL.md
git commit -m "Add the create-tasks move: propose a task set, write only on approval"
```

---

### Task 8: `/create-tickets`

Replaces `skills/ticket/`. The move loses its inline side trips and gains an assembly step that routes back instead of filling gaps itself.

**Files:**
- Rename: `skills/ticket/SKILL.md` → `skills/create-tickets/SKILL.md` (via `git mv`, so history follows)
- Modify: the renamed file throughout

**Interfaces:**
- Consumes: the task (task 7); every `grill-*.md`, `research-*.md`, `prototype-*.md` in `.cortex/<task>/` (tasks 3–5); all four `.cortex/foundation/*.md` (task 2)
- Produces: `.cortex/<task>/ticket.md`, or `.cortex/<task>/01-<slug>.md`, `02-<slug>.md` … when split. `build` and `qa` read these; both already do, and their reading is unchanged.

- [ ] **Step 1: Rename the directory, preserving history**

```bash
git mv skills/ticket skills/create-tickets
python3 scripts/check-skills.py; echo "exit=$?"
```

Expected: `FAIL skills/create-tickets/SKILL.md: name 'ticket' != directory 'create-tickets'`, then `FAIL`, `exit=1`. This is the failing check for this task.

- [ ] **Step 2: Update the frontmatter**

Replace the frontmatter block in `skills/create-tickets/SKILL.md` with this verbatim:

```yaml
---
name: create-tickets
description: Assemble one or more build tickets from the task, its capture folder, and the foundation files — routing back when something is missing. Usage:/create-tickets TT-06
disable-model-invocation: true
---
```

- [ ] **Step 3: Run the checker to confirm the rename is clean**

```bash
python3 scripts/check-skills.py; echo "exit=$?"
```

Expected: `ok   skills/create-tickets/SKILL.md`, `PASS — 9 skills`, `exit=0`.

- [ ] **Step 4: Commit the rename before rewriting the body**

Two commits, so the rename is reviewable separately from the content change.

```bash
git add -A skills/
git commit -m "Rename the ticket move to create-tickets"
```

- [ ] **Step 5: Rewrite the body**

Keep intact, editing only the move name where it appears: `## 4. Decide whether it is one sitting`, `## 5. Write the ticket` including the ticket template and the whole `### Writing criteria` subsection, `## 6. Record the scoping time`, and `## 7. The completeness gate`. These carry the plugin's hardest-won content and none of it changes.

Replace `## 1. Route on what you were handed` through `## 3. Then ask` with this structure:

**`## 1. Read everything that already exists`** — in this order, and say the order matters:
1. The task, followed from wherever `docs/agents/issue-tracker.md` names. Read its `## From the map` section — those decisions are already made and are not to be relitigated.
2. Every file in `.cortex/<task>/` — `grill-*.md`, `research-*.md`, `prototype-*.md`. State that a `Still open` entry in a grill transcript and a `What this rules out` section in a research file are the two highest-value things in that folder.
3. All four `.cortex/foundation/*.md`.

**`## 2. Check the foundation is current`** — compare each foundation file's `commit:` stamp against `HEAD`. Speak up **only when changed paths intersect that file's `scanned:` list**. When it fires, offer a targeted re-run of the affected file, not a full regeneration. State why the check is deliberately quiet: `/build` maintains these files as it goes, so a check that fires weekly is a check the human learns to click past.

```bash
git diff --name-only <stamped-commit>..HEAD
```

**`## 3. Research the repo`** — keep the existing section's substance, which is the strongest content in the current file: which files actually render the thing, what the platform already gives you, what third-party apps are in the path, whether the thing is uniform, what is already there. Keep the Loop Subscriptions pilot story and the 38-of-38 verification story verbatim. Add one line: what the foundation files already establish is not re-derived here — this pass covers what is specific to *this* task.

**`## 4. Judge whether you have enough`** — the new heart of the move. Ask whether a cold `/build` session could work from what you have. If not, **name the specific hole, say which move fills it, and stop.** Do not fill gaps inline.

Give the routing table verbatim:

| What is missing | Where it goes |
|---|---|
| A decision only the human can make | `/grill-me <task>` |
| A fact that lives outside the repo | `/research <task> <question>` |
| An answer that has to be seen rather than described | `/prototype <task>` |
| The destination itself is unclear — what to build, not how | `/ideation` |

State the reason for stopping rather than continuing: each route-back is a fresh cold session with a single job, rather than a grill buried three thousand words into a research pass. This is what removing the side trips buys.

Then state the counter-pressure, so the move does not become a machine for deferring: research and the capture folder settle most things. Route back for what genuinely blocks a ticket, not for every question you could imagine asking.

Renumber the retained sections to follow (`## 5. Decide whether it is one sitting`, and so on).

In `## 5`, keep the split rule and strengthen the plural: the move may write one ticket or several, each researched on its own terms, and where the split is not obvious it is proposed with a one-line description per ticket and confirmed before writing. Keep the existing signs-it-needs-splitting list.

Update `## Inputs`: with no argument, list every task at `todo` that has no ticket in `.cortex/` yet and ask which. Keep the never-invent-a-task rule and narrow it in one clause: only `/create-tasks` authors a task, and only with sign-off.

Update the handoff to print `/build <task>` — unchanged from today.

In `## Guardrails`, keep every existing line, and add: **never fill a gap inline that a capture move exists to fill.**

- [ ] **Step 6: Run the checker and confirm the old name is gone**

```bash
python3 scripts/check-skills.py
grep -rn "/ticket\b" skills/ README.md
```

Expected: `PASS — 9 skills`; the `grep` returns nothing, or only hits where the word `ticket` is the noun rather than the move name. `build` and `qa` refer to the ticket *file* throughout and those hits are correct — check each one rather than replacing blindly.

- [ ] **Step 7: Commit**

```bash
git add skills/create-tickets/SKILL.md
git commit -m "Rewrite create-tickets as an assembler that routes back on gaps"
```

---

### Task 9: Foundation maintenance in `/build`, and the `/qa` handoff

**Files:**
- Modify: `skills/build/SKILL.md` — add a maintenance section, update the handoff reference
- Modify: `skills/qa/SKILL.md` — update any reference to the old move name

**Interfaces:**
- Consumes: `.cortex/foundation/*.md` (task 2)
- Produces: those same files, kept current. Task 8's staleness check depends on this maintenance happening — without it, the check fires constantly and gets ignored.

- [ ] **Step 1: Read both files first**

```bash
grep -n "ticket\|/qa\|/build" skills/qa/SKILL.md | head -40
```

Note every place `qa` names another move, so step 3 changes only the ones that are move names.

- [ ] **Step 2: Add foundation maintenance to `/build`**

Insert a new section into `skills/build/SKILL.md` between `## 5. Append the Build round to the ticket` and `## 6. Record the work on the task`, renumbering the sections that follow. Its content:

**`## 6. Keep the foundation current`** — if `.cortex/foundation/` exists, update it as part of this build, not as a separate chore:

- A new reusable snippet or section → append its path and its actual render signature to `components.md`.
- A new token, or a token that changed meaning → the corresponding line in `design-system.md`.
- A new event the theme emits, or a new custom element convention → `platform.md`.
- A third-party app hazard you hit → `concerns.md`.

Bump the `commit:` stamp and extend `scanned:` if you touched a path it did not cover.

Justify it in one line: these files exist so `/create-tickets` does not re-derive standing facts on every task, and they are only worth trusting if the move that changes the repo is also the move that records the change. Skip the section entirely if `.cortex/foundation/` is absent — foundation is optional.

- [ ] **Step 3: Update move-name references in both files**

In `skills/build/SKILL.md` and `skills/qa/SKILL.md`, change any reference to the `/ticket` **move** to `/create-tickets`. Leave every reference to the ticket **file** alone — `build` reads "the ticket", `qa` walks "the ticket's criteria", and those are correct nouns.

Add one line to `skills/build/SKILL.md`'s Guardrails: **never let the foundation files drift from what you just built.**

- [ ] **Step 4: Verify**

```bash
python3 scripts/check-skills.py
grep -n "foundation" skills/build/SKILL.md
grep -rn "ticket move\|/ticket " skills/build/SKILL.md skills/qa/SKILL.md
```

Expected: `PASS — 9 skills`; the `foundation` grep shows the new section and the guardrail line; the last grep returns nothing.

- [ ] **Step 5: Read-through gate**

Read `skills/build/SKILL.md` end to end. Confirm the section numbering is contiguous after the insert, the handoff still prints `/qa <task>`, and the new section says foundation is optional.

- [ ] **Step 6: Commit**

```bash
git add skills/build/SKILL.md skills/qa/SKILL.md
git commit -m "Have build maintain the foundation files, and point both moves at create-tickets"
```

---

### Task 10: Roster, version, and the honest size claim

**Files:**
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the nine skills from tasks 2–9
- Produces: the published description of the plugin, and a verified token cost

- [ ] **Step 1: Bump the version and update the plugin description**

In `.claude-plugin/plugin.json`, set `"version": "2.0.0"` — the move rename is a breaking change for anyone who typed `/ticket`. Replace `description` with one that covers the whole span rather than the three original moves:

```json
"description": "A client build workflow from a loose idea to a signed-off build. Charts a map of open questions, proposes the billable tasks, assembles the build tickets, implements against their criteria, and verifies in a real browser — for themes and sites where a test runner does not exist."
```

Add `"wayfinding"` and `"design-system"` to `keywords`.

- [ ] **Step 2: Update the marketplace entry**

In `.claude-plugin/marketplace.json`, replace the `cortex-code` entry's `description` — it currently says "vault-backed tickets", which predates the task/ticket split:

```json
"description": "From a loose idea to a signed-off build: map the open questions, propose the tasks, assemble the tickets, build against their criteria, and verify in a real browser."
```

- [ ] **Step 3: Rewrite the README's moves section**

Replace the current three-command block under `## The moves` with the full chain, and state plainly that the order is a default rather than a gate:

````markdown
```
/foundation                once per repo, then maintained by /build
/ideation                  chart the fog; resolve one question per session
  ├ /grill-me
  ├ /research
  └ /prototype
/create-tasks              proposed task set → you approve → written
/create-tickets            task + capture + foundation → one or more tickets
/build
/qa
```
````

Tasks may exist before ideation runs, and often will — a client sends a list and you ideate each item. Ideation may equally run first and produce the tasks. `/create-tickets` reads whatever exists and does not care which came first. Foundation and ideation are both skippable; a thirty-minute CSS fix goes straight to `/create-tickets`, and when it is unclear the move asks.

- [ ] **Step 4: Add a README section on the foundation**

The four files, what each holds, and the reason they are maintained by `/build` rather than regenerated: during an active build the repo moves underneath the foundation daily and the mover is you, so a staleness warning that fires weekly is one you learn to click past.

- [ ] **Step 5: Correct the "deliberately small" claim and the upstream section**

The README currently says the plugin is deliberately small and depends on `mattpocock-skills`. Both are now wrong. Replace the `## What is upstream` section with a short note that `grill-me`, `research`, and `prototype` began as adaptations of that plugin's skills and are now carried here, so `mattpocock-skills` should be uninstalled — two skills named `research` and two named `prototype` in one session cannot be told apart at the point of invocation.

Remove `mattpocock-skills` from `## Requirements`.

- [ ] **Step 6: Verify the plugin loads and measure the real cost**

Push, then refresh the installed copy — the marketplace entry points at the GitHub remote, not this working directory, so local commits are not visible to the CLI until they are pushed.

```bash
git push origin main
```

```bash
claude plugin marketplace update benhungerford-cortex-code && claude plugin details cortex-code
```

Expected: `Skills (9)` listing `build`, `create-tasks`, `create-tickets`, `foundation`, `grill-me`, `ideation`, `prototype`, `qa`, `research`. Note the reported always-on figure.

- [ ] **Step 7: Write the measured cost into the README**

Update `## Status` with the real number from step 6 — do not write the ~540 estimate from the design document. The 1.0.0 entry reported 179 tokens measured, and the same honesty applies here. Set the version to `2.0.0` and list what is still not written: `audit`, and platform-skill references inside `/foundation`.

- [ ] **Step 8: Final check and commit**

```bash
python3 scripts/check-skills.py
```

Expected: `PASS — 9 skills`, exit `0`.

```bash
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Cortex Code 2.0.0 — the full chain from idea to sign-off"
git push origin main
```

---

## Self-Review

**Spec coverage.** Every section of the design document maps to a task: `/foundation` → 2 and 9 (maintenance); `/ideation` → 6; the three capture moves → 3, 4, 5; `/create-tasks` → 7; `/create-tickets` → 8; `/build` and `/qa` → 9; the cost and README honesty note → 10. The "not in this version" items — `audit` and platform-skill references — are recorded in task 10 step 7 rather than implemented, matching the spec.

**Path consistency.** `.cortex/foundation/{design-system,components,platform,concerns}.md` is used identically in tasks 2, 8, and 9. `.cortex/<task>/` artifact names — `grill-NN.md`, `research-NN-<slug>.md`, `prototype-NN-<slug>.md` — are defined in tasks 3–5 and read back in task 8 step 5. The `cortex:` task frontmatter key is defined in task 7 and followed in task 8.

**Known gap, accepted.** The skill bodies are written by the implementer from the section-by-section content specified in each task, rather than reproduced verbatim in this plan. Six skills at 1,500–1,800 words each would make the plan longer than the thing it describes. What *is* verbatim is everything with a contract attached: all frontmatter, every file template, every path, and every guardrail list. The prose between them is the deliverable, not a placeholder.
