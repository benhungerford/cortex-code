# Cortex Code

A client build workflow that runs on two files: a **task** in an Obsidian vault, and a **ticket** in the repo.

Cortex owns the vault. Cortex Code owns the repo. The task is what you bill; the ticket is what you build from.

## What this is for

Shopify Liquid and WordPress PHP theme work, where there is no test runner and no type checker, so red-green is unavailable and the browser is the feedback loop.

## The two files

| | Task | Ticket |
|---|---|---|
| Lives in | vault `Tasks/`, or Monday | repo `.cortex/<task>/` |
| Is | the billing unit | one build session |
| Carries | hours, rate, billing state, a short client-readable summary | intent, decisions, criteria, and every QA and build round |
| Edited | by you, at sign-off | append-only after it is written |

One task has one or more tickets. Usually one. A homepage is one invoice and five sessions; an audit is one request and nine invoices. Tasks never nest — grouping is a `parent:` label in frontmatter that groups a view and nothing more.

## The moves

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

The order above is a default, not a gate. Tasks may exist before ideation runs, and often will — a client sends a list, and you ideate each item. Ideation may equally run first and produce the tasks. `/create-tickets` reads whatever exists and does not care which came first. Foundation and ideation are both skippable; a thirty-minute CSS fix goes straight to `/create-tickets`, and when it is unclear the move asks.

The task name is the only argument most moves take, and it is optional — with no argument each move lists what is ready and asks. Repo path, vault project, ticket folder, and stage are all derived.

Tasks are named for what they are — `Why Regenerative`, `Homepage` — not numbered. The kebab-case slug of that name is the key: it names the capture folder, it is what every grill, research, and ticket file carries to point back at the task, and it is written into the task's `cortex:` key once, at creation. Moves read the folder path out of that key rather than re-slugging the title, so a task can be retitled — or a Monday item's name can drift — without breaking anything underneath it.

A move boundary is a context boundary: every move starts cold with its file as the only input, which is what forces that file to be complete. A move may not print its handoff until every question asked and every finding surfaced is in the file, because after the clear there is no transcript to recover them from.

## The foundation

`/create-tickets` researches the repo on every task. Which snippet renders a button, what the class convention is, which app owns the price element — most of what it finds on task nine is the same as what it found on task one, and it is paid for nine times. `/foundation` pays for it once, scanning the repo and writing four files to `.cortex/foundation/`:

| File | Holds |
|---|---|
| `design-system.md` | Tokens with their definition sites, declared-but-dead among them, type scale, spacing, breakpoints, class convention and its counter-examples |
| `components.md` | Every reusable snippet and section: path, actual render signature, available variants |
| `platform.md` | Template and section architecture, custom-element conventions, and the events the theme emits |
| `concerns.md` | Third-party app surface, vendored CSS, do-not-touch areas, half-finished attempts |

Each file opens with a provenance header — generation date, commit SHA, the paths scanned — and every claim carries `file:line`. Anything inferred rather than observed is marked inferred, the same discipline that stops `qa` ticking what it did not see, applied to a document that later moves trust without re-checking.

### It is maintained, not regenerated

The obvious design is a SHA stamp diffed against `HEAD`, warning when stale. That fails in practice, because during an active build the repo moves underneath the foundation daily and the mover is you — the warning fires on nearly every ticket, and a warning that always fires is one you learn to click past.

So `/build` maintains it instead. When a build adds a reusable snippet, it appends that snippet's path and render signature to `components.md`; when it introduces a token or a new event, the corresponding file gets a line. This is a two-line edit at the moment the information is freshest, and it is exactly what those files exist to hold. The SHA check survives as a backstop: `/create-tickets` compares each file's stamp against `HEAD` and speaks up only when changed paths intersect what that file scanned.

## What is upstream

`grill-me`, `research`, and `prototype` began as adaptations of [`mattpocock-skills`](https://github.com/mattpocock/skills)' capture side trips, and are now carried here in full rather than depended on. Uninstall `mattpocock-skills` once these are installed — two skills named `research` and two named `prototype` in one session cannot be told apart at the point of invocation.

Upstream's `implement` is eight lines that delegate to `tdd`, typechecking, and a test suite. In a theme repo, none of those exist. Upstream's `qa` is deprecated, and was conversational bug intake rather than sign-off.

## Requirements

- The [`cortex-vault`](https://github.com/benhungerford/claude-cortex) MCP server, for resolving a repo to its vault project
- Each repo registered with Cortex, via `/cortex-register-repo`

Registering is the whole binding step. Cortex boot resolves the repo to its vault project and puts it in context before the first message, so the moves read what boot already resolved, fall back to `find_project_by_cwd` where boot could not run, and derive the rest by convention — tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`.

A hand-authored `docs/agents/issue-tracker.md` still works and is read last, but it is no longer required and nothing produces it. Where one exists and names a different project than Cortex resolved, the moves stop and say both rather than picking — a stale binding preferred silently is worse than one surfaced.

## The task is a billing record

Its frontmatter feeds an invoice roll-up. That drives the guardrails:

- Never delete a task or a ticket — cancelled work is closed in place with the reason recorded
- Never move a task to `done` — `review` is as far as an agent goes
- Never tick a criterion — an agent that ticks its own work ticks everything
- Never invent hours; propose them and invite correction
- Never rewrite Intent, Decisions, or Criteria on a ticket in flight — append instead

## Why the browser

On the first task run through this workflow, browser verification caught four bugs that read as correct code:

- An `IntersectionObserver` that never fires on a jump-scroll, because IO only fires on transitions
- A sticky bar showing $22.00 while the cart charged $18.70, because a subscription app renders its own price and never updates the theme's
- A one-shot price sync that raced the same app's asynchronous property write, failing intermittently
- A bar drawing on top of a cart drawer with a `z-index` eleven times higher, because it sat in a different stacking context

None of these break a test. All of them break a customer.

## Why an agent may not tick its own boxes

`build` owns the criteria completely. It loops — implement, verify in the browser, classify every criterion, fix the failures, go again — until every criterion passes or is blocked, or three rounds have run. `qa` walks none of them; its question is *was the ticket right?*, not *did the plan get followed?*

The pilot is why that split exists. On it, sign-off ticked all sixteen acceptance criteria in a single pass — including five that the same document, in the same edit, recorded as never exercised. It did not feel like lying. The work was finished, the criteria were the plan, the plan had been followed. The rule that fixes it — an item may only be ticked if it was *observed* to be true, in that session, in a browser — used to govern a criteria walk. It now governs what QA writes into a round: the test is whether you can say what you saw, and deductions still do not tick boxes.

`qa` collects — from Ben's edits, Pastel comments, client feedback, criteria `/build` reported as blocked, and what QA finds by looking at the screen — and appends each item to the ticket with an origin tag. It never moves a task to `done` without explicit acceptance. Acceptance is the empty case: when a round collects nothing, the only thing left to ask is whether to accept.

## Why QA writes into the ticket

Every item QA appends carries an origin — `found by QA`, `from Pastel`, `from Ben`, or `blocked in build` — and an optional `refines criterion N` when it sharpens something the ticket already asked for too loosely.

The tag is what a later audit measures ticket quality against. A ticket carrying a lot of `found by QA` was technically underspecified — the ticket didn't ask. One carrying a lot of `from Pastel` missed the client's expectations. One carrying a lot of `blocked in build` ran out of environment before it ran out of ticket. Three failures, three fixes, and only the tag tells them apart.

A second, optional axis rides after the origin tag: `refines criterion N`. It separates two ticket-creation failures the origin tag alone collapses into one — the ticket never mentioned this, versus the ticket asked for it but too loosely. The first means a question was never asked; the second means it was asked and answered imprecisely.

What QA learns at sign-off does not stay on the one ticket. Cross-project patterns — anything phraseable as a question `/create-tickets` should ask next time — land in `<vault>/Knowledge Base/ticket-gaps.md`. `/create-tickets` reads that file before the next ticket's criteria freeze, and a pattern that cost one project's QA round costs nothing on the next. That is the loop the origin tags were always pointing at and never closed.

## Status

`2.3.0` — the full chain, from a loose idea to a signed-off build. Nine moves: `foundation`, `ideation`, `grill-me`, `research`, `prototype`, `create-tasks`, `create-tickets`, `build`, `qa`, written against the task/ticket model in [`docs/design/2026-08-04-task-and-ticket-model.md`](docs/design/2026-08-04-task-and-ticket-model.md) and the expansion in [`docs/design/2026-08-05-workflow-expansion-design.md`](docs/design/2026-08-05-workflow-expansion-design.md).

`2.3.0` splits build from QA along a cleaner line, per [`docs/design/2026-08-09-build-loop-and-qa-intake.md`](docs/design/2026-08-09-build-loop-and-qa-intake.md). `/build` now owns its criteria completely and loops on them itself — implement, verify, classify, fix, go again — instead of handing a ticked checklist to sign-off. `/qa` becomes pure intake: it collects from five sources and appends, and it never re-walks a criterion. What QA learns at sign-off feeds a cross-project ledger, `<vault>/Knowledge Base/ticket-gaps.md`, that `/create-tickets` reads before the next ticket's criteria freeze.

`2.2.0` removed two identifiers. Tasks are named for what they are and keyed by the slug of that name, per [`docs/design/2026-08-07-semantic-task-names.md`](docs/design/2026-08-07-semantic-task-names.md). And the repo resolves to its vault project through Cortex boot rather than a hand-authored binding file, per [`docs/design/2026-08-07-vault-awareness-from-cortex-boot.md`](docs/design/2026-08-07-vault-awareness-from-cortex-boot.md).

**Tasks written under `2.1.0` need renaming.** A `task: TT-06` and its `cortex: .cortex/TT-06/` still resolve — nothing reads the ID as an ID — but they carry a name that tells a cold session nothing, which is the cost this version removed. Renaming one is a vault edit and a folder move, not something a move does for you.

**Tickets written under `2.2.0` carry `from criteria` tags.** They still read fine and nothing parses the tag mechanically, but they predate the split — a `from criteria` item was a criteria-walk finding, and `/qa` no longer produces criteria-walk findings. Leave them; rewriting a past round destroys the record it exists to be.

Measured always-on cost is **521 tokens** across the nine — 50 to 70 each, per `claude plugin details cortex-code`. Bodies cost 1.3k to 4.2k tokens each *on invocation only*, because every skill is `disable-model-invocation: true` and nothing fires them by accident.

Not yet written:

- `audit`, which reads the kept tickets after a project ends and reports where they came up short. Deliberately post-project work.
- Platform-skill references inside `/foundation` — it should reach for `shopify-horizon` and its WordPress equivalent rather than deriving conventions from the repo alone.

MIT.
