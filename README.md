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
/ticket TT-06     research, then ask, then write the ticket
/clear
/build TT-06      implement, then prove it in a browser
/clear
/qa TT-06         walk the criteria, tick only what you saw
```

The task ID is the only argument, and it is optional — with no argument each move lists what is ready and asks. Repo path, vault project, ticket folder, and stage are all derived.

A move boundary is a context boundary: every move starts cold with its file as the only input, which is what forces that file to be complete. A move may not print its handoff until every question asked and every finding surfaced is in the file, because after the clear there is no transcript to recover them from.

## What is upstream

This plugin is deliberately small. [`mattpocock-skills`](https://github.com/mattpocock/skills) supplies per-repo setup and the capture side trips `/ticket` routes into — `grill-me`, `prototype`, `research`. It reads the vault unmodified via the **Other** issue-tracker option, which records the workflow as freeform prose in `docs/agents/issue-tracker.md`.

Upstream's `implement` is eight lines that delegate to `tdd`, typechecking, and a test suite. In a theme repo, none of those exist. Upstream's `qa` is deprecated, and was conversational bug intake rather than sign-off.

## Requirements

- [`mattpocock-skills`](https://github.com/mattpocock/skills) installed
- The [`cortex-vault`](https://github.com/benhungerford/claude-cortex) MCP server, for resolving a repo to its vault project
- A `docs/agents/issue-tracker.md` in each repo, naming that project's vault `Tasks/` folder and the repo's `.cortex/` ticket path

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

`qa` exists mostly to resist one pressure. On the pilot, sign-off ticked all sixteen acceptance criteria in a single pass — including five that the same document, in the same edit, recorded as never exercised. It did not feel like lying. The work was finished, the criteria were the plan, the plan had been followed.

So the rule is that a criterion may only be ticked if it was *observed* to be true, in that QA session, in a browser. The test is whether you can say what you saw. Deductions do not tick boxes, and unticked is a respectable outcome.

`qa` also never fixes what it finds — failures go back to `/build` — and never moves a task to `done` without explicit acceptance.

## Why QA writes into the ticket

QA is not limited to the criteria the ticket predicted. It appends its own findings, each tagged with where it came from — `from criteria`, `found by QA`, `from Pastel`, `from Ben`.

Two things fall out. A returning build session opens one file and sees the original intent alongside the specific thing that broke. And a later audit can measure ticket quality directly: a ticket whose QA items all trace back to criteria was a good ticket; one carrying a lot of `found by QA` was underspecified, and one carrying a lot of `from Pastel` missed the client's expectations. Different failures, different fixes.

## Status

`0.3.0` — `build` and `qa`, written against the task/ticket model in [`docs/design/2026-08-04-task-and-ticket-model.md`](docs/design/2026-08-04-task-and-ticket-model.md). Together they cost roughly 70 tokens resident — scaled from the 66 measured at `0.2.0`, whose descriptions were 15 characters shorter in total. The bodies are free until invoked. `ticket` is not written yet.

MIT.
