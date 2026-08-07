---
name: create-tasks
description: Propose a set of billable tasks from a closed map or a brief, then write them only once the human has approved the set. Usage:/create-tasks
disable-model-invocation: true
---

# create-tasks

The move that turns a cleared map into billable work.

Every other move in this plugin is forbidden from authoring a task. `create-tickets`' guardrails say it plainly: never invent a task, because a task is a billing record and the plugin reads them rather than creating them. `create-tasks` is the one exception to that rule, and it is only allowed to be the exception because it never writes without explicit human approval of the whole proposed set. If you finish reading this file still able to imagine it writing a task unattended, read it again — that reading is wrong.

## Inputs

`/create-tasks <map>` — the name of a map whose questions are all closed. A brief handed in directly works too. With neither, ask what to draw the tasks from.

If a map has open questions, do not propose tasks against it. Say which questions are still open and stop. A task drawn from an unfinished map carries decisions that have not been made yet, and the billing record ends up resting on a guess rather than a resolution.

The same applies to `Not yet specified`. A map is only finished when that section is empty too — anything left in it is an in-scope decision still coming. Name what you found there and stop.

## What a task is

Not a ticket, and not a substitute for one. A task is the billing unit — it names the client and the price and it stops there. A ticket is a build session's brief, written later by `/create-tickets`, and it carries the intent, the decisions, and the criteria a cold `/build` needs. This move produces the first; it never touches the second, and a proposed task table with build steps or acceptance criteria in it has drifted into writing tickets by another name.

It lives in the vault, or arrives from Monday and is mirrored there. It carries hours, rate, billing state, and a short client-readable summary of what shipped — what you would show the client, not what you'd hand a build session. Tasks never nest. `parent:` is a grouping label and nothing more; it groups a view, and no move ever resolves anything through it.

The task and ticket model covers this with two shapes, and a proposed set should recognize which one it's drawing. A site audit is nine independent tasks that share `parent: "Q3 audit"`, each with its own hours and its own ticket. A homepage rebuild is the opposite: one task, because the client is billed for one deliverable, with five tickets underneath it doing the five sections of work. Getting this wrong in either direction either fragments one deliverable into a client-facing invoice with nine line items, or buries nine independent pieces of work inside one task nobody can bill piecemeal.

## Name the task for what it is

A task is titled semantically — `Why Regenerative`, `Homepage`, `Currency selector flag bloat`. Not an ID. `TT-06` tells a cold session nothing about what it is holding, and every move in this plugin starts cold, so an identifier that has to be looked up is a cost paid on every read. Tasks pulled from a Monday board arrive named already; minting a number to sit in front of the name invents a second identity for something that had one.

The title is display. Alongside it sits a **slug** — the kebab-case form of the title, `Why Regenerative` → `why-regenerative` — and the slug is the key. It names the capture folder, it is what `task:` carries in every grill, research, prototype, and ticket file underneath, and it is written into `cortex:` once, here, at creation.

**Derive the slug once and never again.** Every downstream move reads it out of `cortex:`, and no move re-slugs a title at read time. That is the whole reason a task can be renamed later without breaking anything: retitle it in Obsidian, let a Monday item's name drift, and the folder and its join keys stay pointed at each other. A move that re-derives the slug from the current title has quietly made the title load-bearing again.

Keep the slug short. Slug the title, not the scope line — three or four words. Where a title is long enough that its full slug would make an unusable path, cut it at the first phrase that still identifies the work, and show the cut in the table so the human sees what the folder will be called.

**Check for a collision before writing.** Look for an existing `.cortex/<slug>/` and an existing task carrying that slug. If either exists, say so and ask for a distinguishing name. Do not append a suffix — a `homepage-2` is the meaningless identifier this naming exists to remove, reintroduced at the one moment a human was standing right there able to say `Homepage refresh` instead. A `Homepage` in Q1 and a `Homepage` in Q3 is the normal way this happens, and the proposal table is where it should surface.

## Propose first

Before anything is written, show the whole proposed set as one table:

| Title | Slug | Scope line | Proposed hours | `parent:` | Build order |
|---|---|---|---|---|---|

Show the whole set at once, not one row at a time. The shape of the split — how many tasks, what shares a `parent:`, what stands alone — is the thing being approved, and it can only be judged by seeing it whole. A table shown one row at a time hides exactly the decision that matters: whether this should have been three tasks instead of one, or one instead of three.

**Hours are proposed, not asserted, and correction is invited outright.** Say so when you show the table. Estimating badly here is a known failure mode already logged elsewhere in this plugin: on the pilot, the build move logged 3 hours for work the human had priced at 2. State what each estimate assumes — a comparable task, a rough sizing, whatever informed the number — and let the human place the real figure. An hours column with no stated assumption behind it is not a proposal, it's a guess wearing a proposal's clothes.

## Write only on approval

Nothing is written until the human approves the set as shown. If the human wants a change — split a row, fold two together, adjust an hour, rename a `parent:` — make the change in the table and show the table again. Do not write the tasks and then patch them to match what was actually asked for. The approval is of the table the human saw, and a table that changed after approval was never actually approved.

## The task file

Each approved row becomes one task file, with this frontmatter, verbatim — the task and ticket model's block minus `rate:` and plus `cortex:`, `rate` being the human's to set when they price the task:

```yaml
---
type: freelance-task
task: why-regenerative
client: Acme Coffee
project: Shopify Website Build
parent: "Q3 audit"
status: todo
estimate_low: 1
estimate_high: 2
hours: 0
billed: false
invoice: ""
cortex: .cortex/why-regenerative/
---
```

The note's filename carries the title — `Why Regenerative.md`. `task:` carries the slug, because it is a join key rather than a label, and every capture file underneath this task repeats it to point back here.

`billed` and `invoice` are written at their defaults because a new task is, by definition, unbilled. `rate` is deliberately absent — it's a real per-client number this move has no basis to know, and the human sets it.

`cortex:` is the pointer to the capture folder that `/create-tickets` will write into. Write it now, before that folder exists — the pointer is the contract, and the folder catches up to it. It is also the only place the slug is authoritative: downstream moves read this key rather than recomputing it, which is what keeps a retitled task from losing its capture folder.

The body carries the scope line, and a `## From the map` section listing the decisions that produced this task, each linking its closed question. That section is why `/create-tickets` inherits the reasoning behind the task instead of re-deriving it from scratch on a cold start.

## Where they are written

**Resolving the vault project.** Prefer what Cortex boot already resolved — the `<cortex-session>` block in context names the vault path and the active project, and at L3 it is fully resolved before the first message. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. From a resolved project both paths follow by convention: tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both — silently preferring either is how a stale binding gets worse instead of better. If nothing resolves, stop and say this repo has not been registered with Cortex; `/cortex-register-repo` is the move that binds it.

This keeps Obsidian and Monday a configuration difference, not a code path this move has to branch on.

## Handoff

```
/clear
```
```
/create-tickets <task>
```

## Guardrails

- **Never write a task without explicit approval of the set.** Approval of one row is not approval of the table.
- **Never invent hours.** Propose them, state the assumption behind each one, and invite correction.
- **Never invent a `rate`.** Set `billed` and `invoice` to nothing but their defaults — `false` and `""`. Those belong to billing, not to this move.
- **Never number a task.** It is named for what it is, and the slug of that name is the key.
- **Never write a task whose slug collides with an existing one.** Say so and ask for a distinguishing name; never append a suffix yourself.
- **Never nest tasks.** `parent:` is a grouping label, not a container — nothing resolves through it.
- **Never draw tasks from a map with open questions.** Name what's still open and stop.
- **Never write a task and then quietly adjust it.** A changed set is re-proposed, not patched in place.
