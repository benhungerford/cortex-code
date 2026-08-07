---
name: qa
description: Walk a ticket's criteria in a browser, tick only what you observe, append the round with origin tags, and take it to sign-off. Usage:/qa why-regenerative
disable-model-invocation: true
---

# qa

Walk the ticket's acceptance criteria, append what you found, and take the work to the human for sign-off.

This is the billing boundary. A task that reaches `done` is money owed, and the QA rounds on its ticket are the only durable record of what was actually checked. Everything here exists to keep that record true.

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

## 2. Collect the human's findings first

Before you start, ask whether there is anything from outside this session: a Pastel link, a comment from the client, something the human noticed themselves. Those are QA items like any other and they belong in this round with their own origin tag. Gathering them now means one round rather than two.

## 3. Rebuild the environment

Stand up whatever the ticket's "How this gets verified" section specifies. If you cannot — auth is broken, a service is down, bot protection is tripped — **stop and say so**. Do not review the diff instead and call it QA. A diff review is a different, weaker activity, and recording it as criteria-walking corrupts the record.

The browser rules from `build` apply unchanged: use a real rendering browser rather than an embedded pane, batch every assertion for a page state into one evaluation, capture the request rather than the appearance for anything transactional, and suspect anything a third-party app owns.

## 4. Walk the criteria

One at a time. For each, decide between three outcomes:

| Outcome | Meaning |
|---|---|
| **Ticked** | Observed true this session. Note what you saw. |
| **Unticked** | Not exercised, or exercised and inconclusive. Annotate *why*. |
| **Failed** | Exercised and false. Goes to step 7. |

Unticked is a normal, respectable outcome. A ticket that closes with nine unticked criteria and an honest note on each is worth more than one with sixteen ticks you cannot substantiate. The unticked ones are also the to-do list for whoever picks this up on a real device.

### Then ask the question the criteria do not

**Does the screen tell the truth?**

Criteria can all pass while the interface is wrong. On the pilot the cart was always correct — right variant, right selling plan, right price — and the bar displayed $22.00 while the shopper was about to pay $18.70. Every written criterion was satisfiable in that state.

So after the checklist, look at the thing:

- Read the rendered values against what the system will actually do.
- Open the drawers, modals, overlays, and banners the feature can collide with. Use `elementFromPoint` to find out what is genuinely on top; a `z-index` comparison means nothing across stacking contexts.
- Try it at more than one viewport width, and say which widths you actually used.
- Watch the flow end to end once, as a customer, rather than as a list.

Anything wrong here is a finding even though no criterion covers it. It goes in the round as `found by QA`, and it counts as a failure.

## 5. Append the QA round to the ticket

**Do not tick the Criteria section.** It is above the divider and it is frozen — it records what done was *meant* to be, and the audit needs it unmodified to compare against. Write a fresh checklist in your round instead.

```markdown
## QA — round 1 · 2026-08-06

Verified against `shopify theme dev` in Playwright at 320 / 390 / 430px.

- [x] Bar price matches cart on subscription select — *saw $18.70 in both the bar and the cart line* · from criteria
- [ ] Sold-out variant disables the button — *never exercised; no sold-out variant exists on the store* · from criteria
- [ ] **Fails.** Bar draws under the cart drawer at 390px — *`elementFromPoint` at the bar's centre returned the drawer overlay; separate stacking context, so the z-index is irrelevant* · found by QA
- [ ] **Fails.** Price should be hidden when no variant is chosen · from Pastel
- [ ] **Fails.** Spacing under the bar is 12px, should be 16 · from Ben
```

**Every item carries an origin.** One of four:

| Tag | Means |
|---|---|
| `from criteria` | The ticket predicted this check |
| `found by QA` | The ticket did not; you found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | The human raised it |

The tag is not bookkeeping. It is the entire signal the post-build audit runs on — a ticket whose items are all `from criteria` was a good ticket, one carrying a lot of `found by QA` was technically underspecified, and one carrying a lot of `from Pastel` missed the client's expectations. Those are different failures with different fixes, and only the tag tells them apart. **Never leave an item untagged**, and never tag something `from criteria` that no criterion actually predicted.

On a later round, re-check every unresolved item from the previous round and restate it with its original tag. An item that quietly stops appearing reads as resolved.

## 6. Reconcile the hours

Total the Work Log on the **vault task**. Check it against the task's frontmatter `hours`.

**Propose the number; never finalise it.** Elapsed session time is not billable time. Research done quickly, and dead ends the agent created for itself, are not the client's to pay for. On the pilot the agent logged 3 hours for work the human priced at 2.

State the total and the estimate range together, so an overrun is visible before it reaches an invoice rather than after.

## 7. When something fails

Do not fix it. QA that repairs its own findings has no independent record of what was wrong.

The round you appended is the record. Set the **task** to `status: in-progress` and hand back:

```
/clear
```
```
/build <task>
```

Failures found in QA stay in the ticket permanently, not just until they are fixed. They are the most useful part of it a year later, and deleting a resolved finding destroys the audit signal it carries.

## 8. Present for sign-off

Give the human, in this order:

1. **Ticked** — with the observation for each
2. **Unticked** — with the reason for each
3. **Anything the criteria missed** that you found by looking
4. **Hours** — proposed total against estimate
5. **The explicit ask:** accept, or send back

Do not bury the unticked list. It is the part the sign-off decision actually turns on.

## 9. On acceptance

Only when the human accepts, and only on the **task**:

- Write the summary — three or four sentences of what actually shipped, in terms a client would recognise. No criteria, no bug list; those live in the ticket, and duplicating them guarantees they drift.
- If tickets remain on this task, leave `status: in-progress` and print the handoff to `/build` for the next one.
- If that was the last ticket, `status: done`.
- Leave `billed: false` — invoicing is a separate act.
- Update the `Tasks/_MOC.md` row: status and hours.
- Log the closure.

If the human accepts while something is still open, say so plainly and let them decide again with that in hand.

## Guardrails

- **Never tick an item you did not observe.** This is the whole skill.
- **Never leave an item without an origin tag.**
- **Never edit above the ticket's divider.** If QA proves a decision wrong, that is an appended finding, not an edit.
- **Never move a task to `done` without explicit acceptance**, and never while a ticket on it is unfinished.
- **Never delete a task, a ticket, or a past finding.** Cancelled work closes in place with the reason recorded.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never fix what you find.** Hand it back to `build`.
- **Anything found after the human has reviewed is disclosed and re-offered**, never folded in silently. An approval covers the state the reviewer saw.
