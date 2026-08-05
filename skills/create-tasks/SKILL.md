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

## Propose first

Before anything is written, show the whole proposed set as one table:

| Title | Scope line | Proposed hours | `parent:` | Build order |
|---|---|---|---|---|

Show the whole set at once, not one row at a time. The shape of the split — how many tasks, what shares a `parent:`, what stands alone — is the thing being approved, and it can only be judged by seeing it whole. A table shown one row at a time hides exactly the decision that matters: whether this should have been three tasks instead of one, or one instead of three.

**Hours are proposed, not asserted, and correction is invited outright.** Say so when you show the table. Estimating badly here is a known failure mode already logged elsewhere in this plugin: on the pilot, the build move logged 3 hours for work the human had priced at 2. State what each estimate assumes — a comparable task, a rough sizing, whatever informed the number — and let the human place the real figure. An hours column with no stated assumption behind it is not a proposal, it's a guess wearing a proposal's clothes.

## Write only on approval

Nothing is written until the human approves the set as shown. If the human wants a change — split a row, fold two together, adjust an hour, rename a `parent:` — make the change in the table and show the table again. Do not write the tasks and then patch them to match what was actually asked for. The approval is of the table the human saw, and a table that changed after approval was never actually approved.

## The task file

Each approved row becomes one task file, with this frontmatter, verbatim — the task and ticket model's block minus `rate:` and plus `cortex:`, `rate` being the human's to set when they price the task:

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
billed: false
invoice: ""
cortex: .cortex/TT-06/
---
```

`billed` and `invoice` are written at their defaults because a new task is, by definition, unbilled. `rate` is deliberately absent — it's a real per-client number this move has no basis to know, and the human sets it.

`cortex:` is the pointer to the capture folder that `/create-tickets` will write into. Write it now, before that folder exists — the pointer is the contract, and the folder catches up to it.

The body carries the scope line, and a `## From the map` section listing the decisions that produced this task, each linking its closed question. That section is why `/create-tickets` inherits the reasoning behind the task instead of re-deriving it from scratch on a cold start.

## Where they are written

Wherever `docs/agents/issue-tracker.md` names. This keeps Obsidian and Monday a configuration difference, not a code path this move has to branch on.

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
- **Never nest tasks.** `parent:` is a grouping label, not a container — nothing resolves through it.
- **Never draw tasks from a map with open questions.** Name what's still open and stop.
- **Never write a task and then quietly adjust it.** A changed set is re-proposed, not patched in place.
