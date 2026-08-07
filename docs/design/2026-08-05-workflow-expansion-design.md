# The workflow expansion

*2026-08-05 — design agreed, not yet implemented. Extends the task and ticket model of [2026-08-04](2026-08-04-task-and-ticket-model.md); nothing in that document is superseded.*

## What changed

`1.0.0` ships three moves and starts at a task that already exists. That was deliberate — the plugin reads tasks, it does not invent them — and it left two things outside the plugin entirely.

**The work before the task.** A client hands over a loose idea, not a task list. Getting from "rebuild the site" to nine tasks with hours on them is real work, it happens before anything billable is named, and today it happens in a chat window that dies with the session.

**The facts every ticket re-derives.** `/ticket` researches the repo on every task. Which snippet renders a button, what the class convention is, which app owns the price element — most of that is the same on task nine as it was on task one, and it is paid for nine times.

So the roster grows from three moves to nine, and the plugin gains a durable artifact at each end: a **map** before the tasks, and a **foundation** beneath them.

## The moves

```
/foundation                once per repo, then maintained by /build
/ideation                  chart the fog; resolve one question per session
  ├ /grill-me
  ├ /research
  └ /prototype
/create-tasks              proposed task set → you approve → written
/create-tickets            task + ideation → one or more tickets
/build
/qa
```

The order is a default, not a gate. Tasks may exist before ideation runs, and often will — a client sends a list, you ideate each item. Ideation may equally run first and produce the tasks. `/create-tickets` reads whatever exists and does not care which came first.

Foundation and ideation are both skippable. A thirty-minute CSS fix goes straight to `/create-tickets`. When it is unclear, the move asks rather than assuming.

## `/foundation`

Reads the repo and writes four files to `.cortex/foundation/`. These are the standing facts `/create-tickets` would otherwise re-derive per task.

| File | Holds |
|---|---|
| `design-system.md` | Tokens with their definition sites, declared-but-dead among them, type scale, spacing, breakpoints, class convention and its counter-examples |
| `components.md` | Every reusable snippet and section: path, actual render signature, available variants |
| `platform.md` | Template and section architecture, custom-element conventions, and the events the theme emits |
| `concerns.md` | Third-party app surface, vendored CSS, do-not-touch areas, half-finished attempts |

Each file opens with a provenance header: generation date, commit SHA, and the paths scanned. Every claim carries `file:line`. Anything inferred rather than observed is marked inferred — the same discipline that stops `qa` ticking what it did not see, applied to a document that later moves will trust without re-checking.

### It is maintained, not regenerated

The obvious design — stamp a SHA, diff it against `HEAD`, warn when stale — fails in practice, because during an active build the repo moves underneath the foundation daily and the mover is you. The warning fires on nearly every ticket, and a warning that always fires is one you learn to click past.

So `/build` maintains it. When a build adds a reusable snippet, it appends that snippet's path and render signature to `components.md`; when it introduces a token or a new event, the corresponding file gets a line. This is a two-line edit at the moment the information is freshest, and it is exactly what those files exist to hold.

The SHA check survives as a backstop rather than a routine: `/create-tickets` compares each file's stamp against `HEAD`, and speaks up only when *changed paths intersect what that file scanned*. Correctly maintained, it stays quiet for weeks. When it does fire, it offers a targeted re-run of the affected file, not a full regeneration.

### Preconditions

Foundation reads a repo that has something in it. On a new Horizon build there is nothing to scan on day one, so it runs after bootstrap, not before. On WordPress the four files describe genuinely different objects — no `settings_schema.json`, no sections, but a `theme.json` and a block library — so the move branches on platform.

Future work: foundation should be able to reference the skills that know a platform's conventions, `shopify-horizon` first among them, rather than deriving those conventions from the repo alone. Not in this version.

## `/ideation`

Wayfinding, under the name this plugin uses for it. A loose idea has arrived, too big for one session and wrapped in fog: the way to the destination is not visible yet. Ideation charts that way as a **map**, then works its **questions** one at a time until nothing is left to decide.

The vocabulary is deliberate. Upstream calls these ticket; this plugin's ticket is a build session and cannot mean two things. Here they are **questions** — each resolves into a decision, and then closes. A ticket, by contrast, is append-only and never closes until the work ships.

### The map

A note in the active vault project. It is an index, not a store: a decision lives in exactly one place — its question — and the map gists and links rather than restating.

```markdown
## Destination
<what reaching the end of this map looks like. One or two lines.>

## Notes
<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far
- [<closed question>](link) — <one-line gist of the answer>

## Not yet specified
<in-scope fog that cannot be phrased sharply yet; graduates as the frontier advances>

## Out of scope
<work ruled beyond the destination; closed, never graduates>
```

Questions are child notes. Each carries a type — `research`, `prototype`, `grilling`, or `task` — and a `blocked_by:` frontmatter list, since Obsidian has no native dependency edge. The **frontier** is the open questions with no unclosed blocker.

**No claim mechanic.** Upstream assigns a question to a developer before work starts so concurrent sessions skip it. That solves a problem this workflow does not have — one person, one session at a time. An open unblocked question is takeable, and that is the whole rule.

One question per session, research excepted. Research questions resolve as background agents and may run in parallel.

### Where ideation's artifacts live

The map is a vault note. The documents its questions produce — grill transcripts, research findings, prototype pointers — go to `.cortex/ideation/<effort>/`.

Ideation frequently runs the week a project is won, before a repo exists. In that case the map holds those artifacts inline, and they move to `.cortex/ideation/<effort>/` once there is a repo to move them into. This is a real case, not an edge one, and blocking on a missing repo would push the work back into a chat window.

## `/grill-me`, `/research`, `/prototype`

Three capture moves, invoked from ideation or directly against a task. Their write target is determined by whether a task is named:

- Named a task → `.cortex/<task>/`
- Invoked from a map question → `.cortex/ideation/<effort>/`

Most invocations will be the first. The moves are the same either way.

**`/grill-me`** — a relentless interview that maps the work as a design tree and works it in rounds, asking the whole frontier at once, each question numbered and carrying a recommended answer. Facts in the repo or reachable by tool are found by a dispatched sub-agent rather than asked for; anything needing a primary source routes to `/research` instead, so it lands cited. Decisions are always put to the human and waited on, and it does not act until shared understanding is confirmed.

**`/research`** — a background agent investigating against primary sources: Shopify dev docs, theme source, first-party app documentation. Never a secondary write-up. Findings land as one cited Markdown file per question.

**`/prototype`** — throwaway code that answers a question, in one of two shapes:

- *What should this look like?* Several radically different takes on one throwaway template, switchable by query param.
- *Does this behave right?* A throwaway route that exercises real theme JS state in a real browser — cart drawer, variant selection, price sync — rendering the full relevant state after every action.

The second branch is a departure from upstream, which builds an interactive terminal application to drive a state machine. There is no runtime for that in a theme repo, and more importantly the browser is this workflow's entire feedback loop. A logic prototype that does not run in a browser cannot answer the questions that actually bite here.

### These skills are copied, not depended on

`mattpocock-skills` is removed as a dependency once these land. Keeping it installed would put two skills named `research` and two named `prototype` in the same session with different behavior, and no reliable way to tell which one an invocation reached.

## `/create-tasks`

Fires when a map has no open questions, or when tasks are being drawn up from a brief directly.

It reads Decisions-so-far and proposes the task set as a table — title, scope line, proposed hours, `parent:` grouping label, build order — and **writes nothing until approved**. Hours are proposed and explicitly invited to be corrected.

This is the one move that authors billing records, and it inverts a standing rule. `/create-tickets` inherits the rule in narrowed form: *only `/create-tasks` may author a task, and only with sign-off.* A ticket move that finds no task still stops.

Tasks are written wherever `docs/agents/issue-tracker.md` names, so Obsidian and Monday remain a configuration difference rather than a code path.

Each task it writes carries a pointer to its `.cortex/<task>/` folder and the map decisions that produced it, so `/create-tickets` inherits the reasoning instead of re-deriving it.

## `/create-tickets`

The move formerly called `/ticket`, with its side trips removed and an assembly step in their place.

It reads, in order: the task; everything in `.cortex/<task>/`; the foundation files; then the repo. Then it judges whether it has enough to write a ticket a cold `/build` can work from.

**If it does not, it names the specific hole, says which move fills it, and stops.** It does not fill gaps inline. This is what the removal of the side trips buys: each route-back is a fresh cold session with a single job, rather than a grill buried three thousand words into a research pass.

**It may write one ticket or several.** The task and ticket model already provides for this — a homepage is one task and five tickets, numbered under `.cortex/homepage/`. Where it writes several, each is still researched on its own terms; if the split it proposes is not obvious, it says so and confirms before writing. A ticket is expensive on purpose, and writing five cheaply would reintroduce exactly the failure the move exists to prevent.

The append-only rule, the frozen-above-the-divider rule, and the never-author-a-task rule all carry over unchanged.

## `/build` and `/qa`

Unchanged, with one addition: `/build` maintains the foundation files as described above.

`/qa` is where every round of feedback lands, internal and client alike. Findings continue to be tagged by origin — `from criteria`, `found by QA`, `from Pastel`, `from Ben` — and continue to accumulate in the ticket rather than anywhere else. Multiple QA rounds against one ticket is the normal case, not the exception, and the value is that a returning build session opens one file and sees the original intent alongside every round of what broke.

Whether a revision round is separately billable is a question about the task, and the human answers it. No move decides that.

## Cost

Nine moves, all `disable-model-invocation: true`, at roughly 60 tokens of always-on description each — about 540 tokens, up from 179. Bodies load on invocation only.

The README's claim to be deliberately small needs rewriting rather than repeating. The plugin is no longer three moves against an existing task; it is a workflow from a loose idea to a signed-off build. That is a larger claim and it should be made honestly.

## Not in this version

- **Platform skill references in `/foundation`.** It should reach for `shopify-horizon` and its WordPress equivalent rather than deriving conventions from the repo alone.
- **`audit`.** Still deliberately post-project: reads the kept tickets after a project ends and reports where they came up short.
