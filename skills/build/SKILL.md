---
name: build
description: Build a repo ticket, then loop a fresh checker agent that verifies it in a real browser until every criterion passes. One ticket, a whole task, or parallel worktrees. Usage:/build why-regenerative
disable-model-invocation: true
---

# build

Implement the work a ticket describes, then prove it works by looking at it.

Shopify Liquid and WordPress PHP have no test runner or type checker, so red-green is unavailable and the browser is the feedback loop. The rules for that loop are in `skills/_shared/references/browser-verification.md` (from this skill's folder, `../_shared/references/browser-verification.md`). Read it before the first check round.

## Two files

| | Task | Ticket |
|---|---|---|
| Where | vault `Tasks/` | this repo, `.cortex/<task>/` |
| Is | the billing record | your brief |
| You write | `status`, and nothing else | one appended Build round |

You build from the ticket and bill against the task. Don't re-derive scope from the task; it deliberately carries no criteria.

## Inputs

`/build <task>`, e.g. `/build why-regenerative`. Optional.

**Resolving the vault project.** Prefer what Cortex boot already resolved: the `<cortex-session>` block names the vault path and active project. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. Tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both; quietly preferring either makes a stale binding worse. If nothing resolves, say the repo is not registered and point to `/cortex-register-repo`.

**No argument:** list every task at `todo` or `in-progress` with its status, and ask which.

**A task with one unaccepted ticket:** take it, say which, and start.

**A task with several unaccepted tickets:** list them and ask which mode. Defaulting to the lowest ticket turns a five-ticket task into five commands nobody asked for, and defaulting to parallel trips bot protection.

| Choice | Runs |
|---|---|
| One at a time | The lowest-numbered unaccepted ticket, then hand off |
| All, sequentially | Every unaccepted ticket, in order, without pausing |
| All, in parallel | Every unaccepted ticket at once, one worktree each |

Recommend sequential unless the tickets are provably disjoint and Ben has accepted the browser cost.

Explicit forms skip the ask: `/build <task> 02` (that ticket), `/build <task> one`, `/build <task> all` (sequential), `/build <task> all --parallel`.

Sections 1–8 are one ticket's pass. The mode decides how many run and in what order.

## Run modes

### Sequential: `/build <task> all`

List every `NN-<slug>.md` in `.cortex/<task>/` that is not yet accepted, say the list, then run sections 1–8 on each in number order without asking. Between tickets, print one line: the ticket, how many check rounds it took, and anything blocked.

The task stays `in-progress` for the whole run and moves to `review` only after the last ticket clears.

The whole run halts on any of the three stop conditions in **Exit conditions**:

- **A stall.** Say which ticket stalled and on what. Don't skip ahead; a stalled ticket usually means the ticket is wrong, and building more on top of it compounds that.
- **Bot protection, or the environment won't stand up.** This is session-wide: no later ticket can be verified either. Say which ticket it tripped on and name every ticket never started.
- **A fix that needs something above a divider.** That is a conversation.

Completed tickets keep their Build rounds and commits. Report what shipped, what held, and what was never reached, in that order.

### Parallel: `/build <task> all --parallel`

One `Agent` per ticket with `isolation: "worktree"`, all spawned in one message. Not the default, and not free.

First run the overlap check: read the files each ticket names. If two tickets name the same file, say which and offer sequential for the whole set. Don't fan out a partial set; a half-parallel run makes the merge order ambiguous.

Then say the browser cost and get a yes. Every agent runs its own checker loop against the same live storefront, and four at once is the most reliable way to trip bot protection, which ends the whole run. If the tickets can only be verified against one shared live environment, recommend sequential instead of asking.

Each agent gets the repo path, its ticket path, sections 1–8 of this file, and the browser reference. It appends its own Build round and commits in its own worktree. Its prompt also says:

- Don't write `.cortex/foundation/`. Parallel appends to `concerns.md` conflict silently on merge. Return foundation findings instead.
- Don't stamp `commit:`. The SHA that matters is the one after the merge.

Afterwards the orchestrator merges each branch in ticket order, writes the collected foundation updates as one edit, commits, stamps `commit:` on every foundation file touched, and reports per ticket. A stalled or blocked agent holds the task at `in-progress`, same as sequential.

## 1. Read the ticket. It is the contract.

Tasks are named, not numbered. Match the argument against the slug in each task's `cortex:` key by prefix (`why-reg` finds `why-regenerative`). When more than one matches, list them and ask; names share prefixes often.

Read the capture folder at the path in `cortex:`. Don't slug the title yourself; the title is display and may have been reworded.

The ticket is `ticket.md`, or `NN-<slug>.md` where the task was split. `grill-*.md`, `research-*.md` and `prototype-*.md` are context only. A grill's `## Still open` entry is a question the human declined to answer, not part of the brief.

A `---` divider splits the ticket.

**Above it, Intent, Decisions and Criteria are settled.** They came out of a `/create-tickets` session that researched the repo and asked the human. Don't relitigate them, improve them, or build something adjacent. If the work can't be done as described, stop and say why.

**Criteria are the definition of done.** Read them before writing anything; they usually encode a hazard. On the pilot, three criteria existed only because research found a subscription app inside the product form.

**Below it are the rounds.** On a return visit, every unresolved item in the most recent QA round is the work list. Read them all before touching anything.

**Then check `.cortex/qa/` for an open batch doc.** `/qa` run against a CSV, doc or pasted list writes findings there, each attributed to a ticket. Any unticked item attributed to this ticket is part of your work list on the same terms as a QA round item. Pass those items to the checker verbatim with the criteria.

Set the task to `status: in-progress` if it isn't already.

## 2. Orient before editing

Read the files the ticket names and confirm they still say what the ticket claims; the repo may have moved since. Branch first if you're on the default branch.

## 3. Implement

Follow the ticket's approach. Prefer the platform's own data and events: listen to events the theme already emits, read structured data the platform publishes, and drive existing elements rather than duplicating them. Duplicating a form is how you silently lose a hidden input some app owns.

## 4. Check with a fresh agent, fix, repeat

A goal loop, not a fixed number of passes. Each round: you implement; a fresh checker subagent verifies the work in a real browser against the criteria and returns pass / fail / blocked; you fix every failure; a new checker runs from scratch.

The loop ends only when a checker returns a round with no failures. You don't grade your own build, and the checker's browser session is the round's whole browser budget, so don't verify alongside it.

### Spawning the checker

One synchronous `Agent` call per round, with `subagent_type: cortex-code:cortex-checker`. If that agent is unavailable or has no browser tools (Playwright not installed), fall back to `general-purpose` and say in the prompt that it must not edit any file.

The checker starts with no memory of your reasoning, which is the point. Give it:

- The repo path, ticket path, and URL(s).
- Every criterion, verbatim.
- Every unresolved item from the latest QA round, verbatim.
- Every unticked item attributed to this ticket in an open `.cortex/qa/` batch doc, verbatim.
- What changed this round: files touched, one line each. What, not why it should work.
- The browser reference (`../_shared/references/browser-verification.md`), verbatim.

Don't tell it what you expect to pass or send your own verification notes; a primed checker confirms your conclusion. Require, per item, the item verbatim, a verdict, and the observation behind it. A verdict with no observation means re-run the round.

Blocked doesn't stall the loop. The pilot's "sold-out variant disables the button" had no sold-out variant on the store to test against. Record why and move on.

On a return round, unresolved QA items are gated exactly like criteria. Ben's `from Ben · refines criterion 3` item clears by being observed true or provably blocked, not by being mentioned.

### Exit conditions

The loop passes when a checker round returns every criterion and every unresolved QA item as pass or blocked. That is the only clean exit.

There is no round cap. A loop that quits at three on a bug it was one round from solving is worse than one that keeps going.

It stops without passing only for:

- **No progress.** Two consecutive rounds where the same item fails with an unchanged observation. Stop and say so. Items that improve each round keep going.
- **Bot protection trips, or the environment won't stand up.** See the browser reference. Ends verification for the session.
- **A fix would change something above the divider.** That is a conversation.

In all three, report whatever isn't green exactly as it stands.

## 5. Append the Build round to the ticket

One Build round per session, not per check round. Append it at the end of the ticket; don't edit above the divider.

```markdown
## Build — round 1 · 2026-08-09

Five check rounds, cleared on the fifth. Moved the bar out of `main-product` into a
root-level render so it shares a stacking context with the drawer, then added the
no-variant price suppression after round 2 showed it flashing $0.00.

Caught by looking, not predicted by any criterion: the app's price node rewrites
asynchronously after a variant change, so the first recompute raced it.

Blocked: the sold-out criterion — no sold-out variant exists on the store.
```

Say what you changed and why, and what you didn't address and why. On a return round, resolve the previous QA round item by item: pass, blocked with a reason, or still failing. An item you discuss but don't fix or block is still failing.

Call out any bug you found that no criterion predicted. The post-build audit reads those lines to see where the ticket fell short, and this is the only place that count survives.

## 6. Keep the foundation current

If `.cortex/foundation/` exists, update it as part of the build:

- New reusable snippet or section → its path and actual render signature in `components.md`.
- New token, or one that changed meaning → `design-system.md`.
- New theme event or custom element convention → `platform.md`.
- A third-party app hazard you hit → `concerns.md`.

Extend `scanned:` if you touched a path it didn't cover. Skip this if `.cortex/foundation/` is absent.

## 7. Commit, then stamp the foundation

Commit the build, then set `commit:` on each foundation file you touched to the short SHA of the new `HEAD`. Stamping before the commit names the pre-build state, so `/create-tickets` would see the build's own edits against `scanned:` and flag every ticket stale. Skip if there is no foundation.

## 8. Leave the task's record alone

`status` is the only task field this move touches.

Don't log or estimate time. Session time isn't billable time: quick research and self-made dead ends aren't the client's to pay for, and an agent can't tell them apart from the inside. On the pilot the agent logged 3 hours for work Ben priced at 2. `hours` and the estimate fields are Ben's, set in Obsidian. Don't write a summary on the task either; that's written once at sign-off.

## 9. Hand off

On an `all` run, sections 1–8 repeat per ticket and this runs once at the end.

**Clean or blocked-only:** set the task to `status: review` and print:

```
/clear
```
```
/qa <task>
```

**Stopped without passing** (stalled, bot-blocked, or held on an above-the-divider question): the task stays `in-progress`. Say what's still failing, quote the checker's last observation, and ask. The next move is another `/build`, since a fresh session gets a fresh environment and a checker with no memory of the stall:

```
/clear
```
```
/build <task>
```

## Guardrails

The task is a billing record; the ticket is the evidence behind it.

- Don't delete a task or ticket. Cancelled work is closed in place with the reason.
- `review` is as far as this skill moves a task. Only Ben moves it to `done`.
- Above the divider is frozen. Append below it.
- Criteria checkboxes stay unticked forever. What passed is recorded in the Build round.
- `rate`, `billed`, `invoice`, `hours` and the estimate fields are Ben's.
- Anything found after Ben has reviewed is disclosed and re-offered, not folded in. An approval covers the state he saw.
- A task goes to `review` only when nothing is failing. Blocked is a handoff; failing, or answered but not fixed, is not.
- On a multi-ticket task, ask for the run mode unless the command named one.
- A stalled ticket halts a whole-task run; don't skip it.
- No parallel fan-out across tickets that share a file, and none without stating the bot-protection cost first.
- In parallel runs only the orchestrator writes `.cortex/foundation/` and stamps `commit:`.
- If you changed any code after the last clean round, even a comment, run another round.
