---
name: qa
description: Collect findings from every source that has an opinion, append the round with origin tags, and send back to build or take it to sign-off. Usage:/qa why-regenerative
disable-model-invocation: true
---

# qa

Collect what the ticket missed, append what you found, and send it back to `/build` or take it to the human for sign-off.

`/qa` walks nothing. `/build` already owns the criteria completely — it loops on them until they pass, are provably unexercisable, or it runs out of rope. `/qa`'s question is different: *was the ticket right?* It spends its whole budget on what ticket-creation missed, not on re-confirming what `/build` already claims.

`/qa` is another way to add to the ticket. It happens to run after the build rather than before it. `/build` already reads it that way — its step 1 treats every unresolved item from the most recent QA round as the actual work list for a return visit.

This is the billing boundary. A task that reaches `done` is money owed, and the QA rounds on its ticket are the only durable record of what the ticket failed to anticipate — what Ben and the client asked for that nobody wrote down before the work started. Everything here exists to keep that record true.

`/qa <task>` — e.g. `/qa why-regenerative`. Optional; with no argument, list the tasks at `status: review` and ask which. Tasks are named, not numbered — match the argument against the slug in each task's `cortex:` key by prefix, and when more than one matches, list the matches and ask rather than taking the first.

## The failure mode this skill is built against

An agent asked to sign off will tick everything.

On the pilot, sign-off ticked all sixteen criteria in a single pass — including five that the same document, in the same edit, described as never exercised. Nothing about that felt like lying at the time. The work was finished, the criteria were the plan, the plan had been followed, so the boxes got ticked.

That is the pressure. It arrives exactly when the work feels done, and it is strongest on the criteria that are least interesting to check.

**The rule: an item may only be ticked if you observed it being true, in this QA session, in a browser.** Not because the code obviously does it. Not because a shared form carries it. Not because it worked when it was built.

The test: *can you say what you saw?* "The cart line came back with `selling_plan` set and a price of $18.70" is an observation. "The form carries the selling plan, so it must work" is a deduction. Deductions do not tick boxes.

## 1. Read the ticket

**Resolving the vault project.** Prefer what Cortex boot already resolved — the `<cortex-session>` block in context names the vault path and the active project, and at L3 it is fully resolved before the first message. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. From a resolved project both paths follow by convention: tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both — silently preferring either is how a stale binding gets worse instead of better. If nothing resolves, stop and say this repo has not been registered with Cortex; `/cortex-register-repo` is the move that binds it.

Then read the capture folder at the path the task's `cortex:` key names — read it out of that key rather than slugging the task's title yourself. The ticket is `ticket.md`, or `NN-<slug>.md` where the task was split. Everything else in that folder — `grill-*.md`, `research-*.md`, `prototype-*.md` — is capture, read for context only, and a grill's `## Still open` entry is a question the human declined to answer rather than part of the brief.

Read Intent, Decisions, and Criteria above the divider, then every round below it. The most recent Build round tells you what the builder claims and what they say they did not check. **Do not treat their unchecked list as authoritative in either direction** — they may have missed something they thought they covered, and they may have fixed something they forgot to mention.

## 2. Rebuild the environment

Stand up whatever the ticket's "How this gets verified" section specifies — this feeds the fifth collection source only, what you find by looking at the screen. If you cannot — auth is broken, a service is down, bot protection is tripped — do not stop the round. Collect the four sources that need no browser (Ben's edits, Pastel comments, client feedback, criteria `/build` reported as blocked) as normal, record in the round that the screen was not examined and why, and still end at the explicit ask in section 7. What you must never do is review the diff instead and call it a look at the screen — a diff review is a different, weaker activity, and recording it as screen-truth corrupts the record.

Where the environment does stand up, the browser rules from `build` apply unchanged: use a real rendering browser rather than an embedded pane, batch every assertion for a page state into one evaluation, capture the request rather than the appearance for anything transactional, and suspect anything a third-party app owns.

## 3. Collect

Gather from every source that has an opinion:

- Edits Ben made or wants
- Pastel comments
- Client feedback
- Criteria `/build` reported as blocked, from the most recent Build round
- What you find by looking at the screen

Try any blocked criterion this session can exercise — a different environment or a real device may reach what the build session could not. If it still cannot be exercised, carry the item forward with its reason rather than dropping it. Each blocked criterion carried forward becomes its own item in the round, one line each with its own reason.

If you do exercise a `blocked in build` item and observe it true, tick it. It keeps its `blocked in build` origin — that is where it came from — and the line notes where you finally exercised it: the device, environment, or condition that reached it. It does not get re-tagged `found by QA`; you did not find it, you cleared it. If you exercise it and observe it false, write it as a `**Fails.**` item, still with `blocked in build` origin, same as any other fail.

**Does the screen tell the truth?**

Criteria can all pass while the interface is wrong. On the pilot the cart was always correct — right variant, right selling plan, right price — and the bar displayed $22.00 while the shopper was about to pay $18.70. Every written criterion was satisfiable in that state.

So look at the thing:

- Read the rendered values against what the system will actually do.
- Open the drawers, modals, overlays, and banners the feature can collide with. Use `elementFromPoint` to find out what is genuinely on top; a `z-index` comparison means nothing across stacking contexts.
- Try it at more than one viewport width, and say which widths you actually used.
- Watch the flow end to end once, as a customer, rather than as a list.

Anything wrong here is a finding even though no criterion covers it. It goes in the round as `found by QA`, and it counts as a failure.

## 4. Append the QA round to the ticket

**Do not tick the Criteria section.** It is above the divider and it is frozen — it records what done was *meant* to be, and the audit needs it unmodified to compare against. Write a fresh checklist in your round instead.

```markdown
## QA — round 1 · 2026-08-09

Verified against `shopify theme dev` in Playwright at 320 / 390 / 430px.

- [ ] **Fails.** Bar draws under the cart drawer at 390px — *`elementFromPoint`
      at the bar's centre returned the drawer overlay; separate stacking
      context, so the z-index is irrelevant* · found by QA
- [ ] **Fails.** Spacing under the bar is 12px, should be 16 · from Ben ·
      refines criterion 3
- [ ] **Fails.** Price should be hidden when no variant is chosen · from Pastel
- [ ] Sold-out variant disables the button — *still no sold-out variant on the
      store; tried on staging too* · blocked in build
- [x] Low-stock variant disables the button — *exercised on a real device this
      round; staging had a variant at qty 1* · blocked in build
```

**Every item carries an origin.** One of four:

| Tag | Means |
|---|---|
| `found by QA` | The ticket did not predict this; you found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | The human raised it |
| `blocked in build` | A criterion build could not exercise, carried forward |

The old tag that credited an item to the criteria is retired. Nothing in a QA round is credited that way any more, because QA does not read the criteria as a checklist.

The tag is not bookkeeping. It is the entire signal the post-build audit runs on — a ticket carrying a lot of `found by QA` was technically underspecified, one carrying a lot of `from Pastel` missed the client's expectations, and one carrying a lot of `blocked in build` ran out of environment before it ran out of ticket. Those are different failures with different fixes, and only the tag tells them apart. **Never leave an item untagged.**

An optional second axis sits after the origin tag: `refines criterion N`. It separates two ticket-creation failures the origin tag alone collapses into one — *the ticket never mentioned this* and *the ticket got the behaviour right but not the detail*. The first means a question was never asked; the second means it was asked too loosely. Different fixes, and only the marker tells them apart.

On a later round, re-check every unresolved item from the previous round and restate it with its original tag. An item that quietly stops appearing reads as resolved.

## 5. Route what this round taught you

**Repo facts → `.cortex/foundation/concerns.md`, this round.** Test: *would this still be true on this repo next month, on a different ticket?* Example line: the subscription app rewrites the price node asynchronously after a variant change. Write it now — `/build` needs it on the very next pass, and a hazard that lands after the work is finished has cost its full price and bought nothing.

Skip this entirely if `.cortex/foundation/` is absent; foundation is optional.

**Cross-project patterns → `<vault>/Knowledge Base/ticket-gaps.md`, at accept only.** The test is the gate: **can it be phrased as a question `/create-tickets` should ask?** If it cannot, it is not a pattern and it stays in the ticket.

Group by topic:

```markdown
## Sticky / overlay elements

- **Ask:** what is the spacing above and below, at each breakpoint?
  — *FKT bar shipped at 12px, client wanted 16 (why-regenerative, QA r1)*
- **Ask:** what can sit on top of it — drawers, modals, banners?
  — *FKT bar drew under the cart drawer (why-regenerative, QA r1)*
```

Each entry carries the case that produced it, because a question with no evidence behind it gets dropped the first time it feels tedious to ask.

The timing differs because the two ledgers answer to different clocks. The foundation file is about the very next pass on this repo, so it cannot wait. The ledger is about the next project, so nothing needs it sooner — and a pattern written mid-project is written from half the picture; round 2 routinely reframes what round 1 looked like.

## 6. Reconcile the hours

Total the Work Log on the **vault task**. Check it against the task's frontmatter `hours`.

**Propose the number; never finalise it.** Elapsed session time is not billable time. Research done quickly, and dead ends the agent created for itself, are not the client's to pay for. On the pilot the agent logged 3 hours for work the human priced at 2.

State the total and the estimate range together, so an overrun is visible before it reaches an invoice rather than after.

## 7. Send back, or accept

Present, in this order:

1. **What was collected**, with the origin of each
2. **Anything still blocked**, with why
3. **Hours** — proposed total against estimate
4. **The explicit ask:** send back to `/build`, or accept as it stands?

Acceptance is the empty case. When a round collects nothing, the only thing left to ask is whether to accept. A round carrying only a `blocked in build` item that no environment can reach is not the empty case — it collected something, it just cannot resolve it. Present it as it stands and let the human decide whether to accept with it open or send back anyway.

**On send-back:** set the **task** to `status: in-progress` and print the existing handoff:

```
/clear
```
```
/build <task>
```

Failures found in QA stay in the ticket permanently, not just until they are fixed. They are the most useful part of it a year later, and deleting a resolved finding destroys the audit signal it carries.

## 8. On acceptance

Only when the human accepts, and only on the **task**:

- Write the summary — three or four sentences of what actually shipped, in terms a client would recognise. No criteria, no bug list; those live in the ticket, and duplicating them guarantees they drift.
- If tickets remain on this task, leave `status: in-progress` and print the handoff to `/build` for the next one.
- If that was the last ticket, `status: done`.
- Leave `billed: false` — invoicing is a separate act.
- Update the `Tasks/_MOC.md` row: status and hours.
- Log the closure.
- Write the cross-project ledger entries from section 5 now.

If the human accepts while something is still open, say so plainly and let them decide again with that in hand.

## Guardrails

- **Never tick an item you did not observe.** This rule now governs items written into a round rather than criteria being ticked.
- **Never leave an item without an origin tag.**
- **Never edit above the ticket's divider.** If QA proves a decision wrong, that is an appended finding, not an edit.
- **Never move a task to `done` without explicit acceptance**, and never while a ticket on it is unfinished.
- **Never delete a task, a ticket, or a past finding.** Cancelled work closes in place with the reason recorded.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never re-walk the criteria.** `/build` owns them. Anything you find is a new item with its own origin, not a re-test.
- **Anything found after the human has reviewed is disclosed and re-offered**, never folded in silently. An approval covers the state the reviewer saw.
