---
name: create-tickets
description: Assemble one or more build tickets from the task, its capture folder, and the foundation files — routing back when something is missing. Usage:/create-tickets why-regenerative
disable-model-invocation: true
---

# create-tickets

Write the file a cold build session will work from.

Everything downstream is only as good as this. `/build` reads the ticket and loops on the criteria until they pass or are blocked; `/qa` never re-walks them, so a criterion this move fails to write is a criterion nothing downstream checks. A vague ticket does not produce a vague build — it produces a confident build of the wrong thing, and the cost surfaces two rounds later as findings tagged `found by QA`.

So this move is allowed to be expensive. It is the one place in the workflow where thoroughness is cheaper than speed.

This move assembles. The capture moves — `/grill-me`, `/research`, `/prototype` — did the asking, the reading, and the building-to-see, and left their output on disk. This move reads all of it, researches what is specific to this task, and judges whether that is enough. When it is not, it names the hole and routes back rather than filling it here.

## Inputs

`/create-tickets <task>` — e.g. `/create-tickets why-regenerative`. Optional, and it is normal to hand it more than the name.

Tasks are named, not numbered, and the argument is matched against the slug in a task's `cortex:` key by prefix — `why-reg` finds `why-regenerative`. Names share prefixes far more often than sequential IDs did, so **when more than one task matches, list the matches and ask.** Never take the first.

**Resolving the vault project.** Prefer what Cortex boot already resolved — the `<cortex-session>` block in context names the vault path and the active project, and at L3 it is fully resolved before the first message. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. From a resolved project both paths follow by convention: tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both — silently preferring either is how a stale binding gets worse instead of better. If nothing resolves, stop and say this repo has not been registered with Cortex; `/cortex-register-repo` is the move that binds it.

**With no argument:** read the resolved `Tasks/` folder, list every task at `todo` that has no ticket in `.cortex/` yet, and ask which. Do not pick one silently.

**If the named task does not exist in the vault:** stop. The plugin reads tasks; it does not invent them — a task is a billing record, and only `/create-tasks` authors one, only with sign-off. Say what is missing and what its frontmatter needs. Never create a task as a side effect of being asked for a ticket.

**If a ticket already exists for this task:** stop and say so. Above the divider is frozen once written. If the work has genuinely changed, that is a new ticket on the same task, numbered after the existing one.

## 1. Read everything that already exists

Whatever came with the command — a paragraph of detail, a live URL, a Figma link, a screenshot, a Pastel link — is intent, not evidence. Confirm every factual claim in it against the code before it reaches a criterion; people misremember their own repos. Reproduce a described bug before describing it. The rest feeds the section 3 repo pass, and what that pass cannot settle goes through the section 4 table.

Read in this order. The order matters — each layer narrows what the next one has to establish, and reading the repo before reading the capture folder means re-deriving facts somebody already wrote down.

1. **The task**, in the resolved `Tasks/` folder. Its frontmatter carries `cortex:`, the pointer to the capture folder — read the folder path out of that key rather than slugging the task's title yourself. The title is display and may have been reworded since; `cortex:` is the contract and has not. Read its `## From the map` section: those decisions are already made, and they are not to be relitigated here. A ticket that reopens a settled map decision spends the human's attention on a question they already answered.

2. **Every file in `.cortex/<task>/`** — `grill-*.md`, `research-*.md`, `prototype-*.md`. Read all of them, including the ones that look tangential. Two things in that folder are worth more than the rest: a `Still open` entry in a grill transcript, because it is a question the human deliberately declined to answer and it may be exactly what blocks this ticket; and a `What this rules out` section in a research file, because it closes options you would otherwise spend the ticket weighing.

3. **The ideation artifacts behind this task.** Follow the task's `## From the map` links to their questions, and read whatever those questions produced in `.cortex/ideation/<effort>/`. The map carries the decision; it does not carry the research that settled it or the prototype branch that proved it, and both are written into that folder by moves that ran before the task existed. Nothing else in the workflow opens it.

4. **All four `.cortex/foundation/*.md`** — `design-system.md`, `components.md`, `platform.md`, `concerns.md`. These are the standing facts about this repo. `concerns.md` in particular names the third-party app surface, and that is the most common source of a hazard a ticket has to encode. If these files do not exist, say so and offer `/foundation`. Do not treat their absence as a blocker — a small fix does not need them.

## 2. Check the foundation is current

Skip this check entirely when the foundation files are absent. Otherwise, compare each foundation file's `commit:` stamp against `HEAD`.

```bash
git diff --name-only <stamped-commit>..HEAD
```

Speak up **only when the changed paths intersect that file's `scanned:` list**. When it fires, offer a targeted re-run of the affected file, not a full regeneration of all four.

This check is deliberately quiet. `/build` maintains the foundation files as it goes, so correctly maintained they stay accurate for weeks at a time. A check that fires every week is a check the human learns to click past, and then it is worth nothing on the week it was right.

## 3. Research the repo

What the foundation files already establish is not re-derived here. This pass covers what is specific to *this* task — the files this work actually touches, and the hazards that only show up once you know what is being built.

On the pilot this is what earned the whole move. Research found that `{% form 'product' %}` wrapped every block on the product page and that the Loop Subscriptions widget rendered its `selling_plan` input inside that same form. That one fact changed the architecture before a line was written — a sticky bar with its own form would have silently converted subscribers into one-time buyers, looked completely correct, and shipped. Three of the ticket's criteria existed only because of it.

What to establish, every time:

- **Which files actually render the thing.** Not which files sound like they do.
- **What the platform already gives you.** Events the theme emits, JSON it publishes, elements that already do the job. Building a second one of something is how you lose a hidden input some app owns.
- **What third-party apps are in the path.** These are the most common source of bugs that survive review. If an app can change state, assume you will not be told about it.
- **Whether the thing is uniform.** On the pilot, 38 of 38 live products rendered the same section, which is why one implementation covered every case. That was verified, not assumed — six alternate templates existed and none were assigned.
- **What is already there.** Half-finished attempts, dead gates, and settings that look relevant and are not.

Say what you checked and what you found, with file and line references. A claim in a ticket that cannot be traced to a file is a claim `/build` will have to re-derive.

## 4. Judge whether you have enough

Ask the question plainly: could a cold `/build` session, opening only the ticket you are about to write, do this work correctly?

If it could, write it. If it could not, **name the specific hole, say which move fills it, and stop.** Do not fill the gap inline.

| What is missing | Where it goes |
|---|---|
| A decision only the human can make | `/grill-me <task>` |
| A fact that lives outside the repo | `/research <task> <question>` |
| An answer that has to be seen rather than described | `/prototype <task> <question>` |
| The destination itself is unclear — what to build, not how | `/ideation` |

Stopping is cheaper than continuing because each route-back is a fresh cold session with a single job, rather than a grill buried three thousand words into a research pass. A question asked in its own session gets the whole session's attention and lands in a file. A question asked mid-assembly gets whatever attention is left, and lands in a transcript that is about to be cleared. That is what removing the side trips buys.

A task that arrived with no ideation behind it and an empty capture folder is the normal small-task path, not a gap. Repo research alone is often enough for it.

### Ask what the last project taught you

Read `<vault>/Knowledge Base/ticket-gaps.md`. This file may not exist — the ledger accumulates, and an early project has nothing in it yet. If it exists, pull the sections whose topic matches what this ticket covers. Each one is a question the last project's QA asked too late, and it resolves to a criterion, a Decision, or an explicit out-of-scope line in this ticket.

A ledger question left unanswered is the same gap the ledger exists to record — that is how the same finding arrives twice. This is not a route-back: ask these questions here and now, in this session, unless the answer is genuinely one only the human can make. If it is, say so explicitly. Deferred questions route to `/grill-me`, but not as a side effect of reading the ledger.

The counter-pressure matters just as much, or this becomes a machine for deferring. Research and the capture folder settle most things. Route back for what genuinely blocks a ticket — a decision the ticket cannot be written without, a fact a criterion depends on — not for every question you could imagine asking. A move that routes back on the third read of a well-captured folder has stopped assembling and started stalling.

## 5. Decide whether it is one sitting

If what you have described is more than one build session's worth of work, say so and propose a split. This is part of the job, not something to wait to be asked for.

This move may write one ticket or several. A homepage with five sections is one task and five tickets. Each ticket is independently buildable and independently verifiable, and each is researched on its own terms — five tickets written cheaply from one pass of research is the failure this move exists to prevent. The hours still land on the one task.

Where the split is not obvious, propose it with a one-line description of each ticket and the order, and confirm before writing anything. The human approves it. Then write them as `01-<slug>.md`, `02-<slug>.md`, and so on in `.cortex/<task>/`.

Signs it needs splitting: more than roughly a dozen criteria, more than one page or template, or a build step that has to finish before the next one can even be described.

## 6. Write the ticket

`.cortex/<task>/ticket.md`, or the numbered files if you split. Everything you write now sits above the divider and is frozen the moment you hand off.

```markdown
---
task: sticky-add-to-cart
ticket: 01
created: 2026-08-06
---

# Sticky add-to-cart on mobile PDP

## Intent

What the work is and why it exists. The problem in the shopper's terms, then
the fix in the developer's. Include how to reproduce it.

### What the repo says

Findings with file and line references. The hazards you found, and what each
one rules out.

## Decisions taken at ticket

- Bar proxies to the real submit button rather than posting its own request.
- Mobile only. Desktop is unchanged.

## Acceptance criteria

- [ ] ...

## How this gets verified

The environment, and the fallback if it is unavailable.

---
```

The `---` at the end is the divider. Everything below it belongs to `/build` and `/qa`.

### Writing criteria

Criteria are the definition of done, and they are also what the audit measures this ticket against later. Write each one so that a person in a browser can say *what they saw*.

- **Observable, not architectural.** "The cart line comes back with `selling_plan` set and a price of $18.70" can be ticked. "The bar uses the existing form" cannot — it is a decision, and it belongs in Decisions.
- **One thing each.** A criterion joined by "and" produces a half-tick nobody can record.
- **Name the conditions.** Which viewport width, which variant, which state. A criterion that does not say where to stand cannot be failed honestly.
- **Encode the hazards you found.** If research turned up a third-party app, a stacking context, or an async write, there is a criterion for it. These are the ones that pay for the research.
- **Include the states nobody demonstrates.** Sold out, no variant selected, empty cart, one item, the longest product title on the store.

Then read them back and ask: *if every one of these were ticked, could the screen still be wrong?* On the pilot the answer was yes — every criterion was satisfiable in a state where the bar showed $22.00 and the cart charged $18.70. If the answer is yes, there is a criterion missing.

## 7. Record the scoping time

Add a Work Log row to the **vault task** for this session, marked as scoping.

Whether scoping is billable to the client or overhead is unsettled — flag the row rather than deciding it. State the time, say it is scoping, and let the human place it.

**Propose the number; never finalise it.** Research you did quickly is not the client's to pay for.

## 8. The completeness gate

**Do not print the handoff until every question you asked and every finding you surfaced is in the ticket.**

After the `/clear` there is no transcript. Anything that exists only in this conversation is gone, and the build session will rediscover it the expensive way or not at all.

Before handing off, check:

- Every answer the human gave is written down, in their terms rather than your summary of them.
- Every repo finding is in "What the repo says", with its file reference.
- Every hazard has either a criterion or an explicit out-of-scope line.
- Every `ticket-gaps.md` question matching this ticket's topics is answered in Criteria or Decisions, or written down as out of scope.
- Every decision made in conversation is in Decisions.
- "How this gets verified" names a real environment, and says what to do when it is unavailable.

Then set the task to `status: todo` and print:

```
/clear
```
```
/build <task>
```

## Guardrails

- **Never write a ticket without researching the repo first**, however clear the request seems. The clear ones are where the unexamined assumption hides.
- **Never ask what the repo can answer.**
- **Never fill a gap inline that a capture move exists to fill.** Name the hole, name the move, and stop.
- **Never invent a task.** Only `/create-tasks` authors one, and only with sign-off.
- **Never overwrite an existing ticket.** Above the divider is written once. Changed work is a new ticket.
- **Never write a criterion you could not observe in a browser.** If it cannot be observed, it is a decision, and it goes in Decisions where nobody will be tempted to tick it.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never hand off with an unanswered question still in the conversation.** Either it is in the ticket or it is not settled.
