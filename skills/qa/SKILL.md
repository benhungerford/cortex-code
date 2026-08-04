---
name: qa
description: Walk a ticket's criteria in a browser, tick only what you observe, draft the Receipt, and take it to sign-off. Usage:/qa TT-06
disable-model-invocation: true
---

# qa

Walk the ticket's acceptance criteria, write the Receipt, and take the work to the human for sign-off.

This is the billing boundary. A ticket that reaches `done` is money owed, and its ticked criteria are the only durable record of what was actually checked. Everything here exists to keep that record true.

`/qa <ticket>` — e.g. `/qa TT-06`. The ticket ID is the only argument.

## The failure mode this skill is built against

An agent asked to sign off will tick everything.

On the pilot ticket, sign-off ticked all sixteen criteria in a single pass — including five that the same document, in the same edit, described as never exercised. Nothing about that felt like lying at the time. The work was finished, the criteria were the plan, the plan had been followed, so the boxes got ticked.

That is the pressure. It arrives exactly when the work feels done, and it is strongest on the criteria that are least interesting to check.

**The rule: a criterion may only be ticked if you observed it being true, in this QA session, in a browser.** Not because the code obviously does it. Not because a shared form carries it. Not because it worked when you built it.

The test: *can you say what you saw?* "The cart line came back with `selling_plan` set and a price of $18.70" is an observation. "The form carries the selling plan, so it must work" is a deduction. Deductions do not tick boxes.

## 1. Read the ticket

Find it via `docs/agents/issue-tracker.md`. Read Intent, Decisions, and the Receipt the build move left.

The Receipt tells you what the builder claims and what they say they did not check. **Do not treat their unchecked list as authoritative in either direction** — they may have missed something they thought they covered.

## 2. Rebuild the environment

Stand up whatever the ticket's "How this gets verified" section specifies. If you cannot — auth is broken, a service is down, bot protection is tripped — **stop and say so**. Do not review the diff instead and call it QA. A diff review is a different, weaker activity, and recording it as criteria-walking corrupts the record.

The browser rules from `build` apply unchanged: use a real rendering browser rather than an embedded pane, batch every assertion for a page state into one evaluation, capture the request rather than the appearance for anything transactional, and suspect anything a third-party app owns.

## 3. Walk the criteria

One at a time. For each, decide between three outcomes:

| Outcome | Meaning |
|---|---|
| **Ticked** | Observed true this session. Note what you saw. |
| **Unticked** | Not exercised, or exercised and inconclusive. Annotate *why*, inline. |
| **Failed** | Exercised and false. Goes to step 4. |

Unticked is a normal, respectable outcome. A ticket that ships with nine unticked criteria and an honest note on each is worth more than one with sixteen ticks you cannot substantiate. The unticked ones are also the to-do list for whoever picks this up on a real device.

Annotate inline, next to the box:

```markdown
- [ ] Sold-out variant disables the bar's button — *never exercised; no sold-out variant was tested*
```

### Then ask the question the criteria do not

**Does the screen tell the truth?**

Criteria can all pass while the interface is wrong. On the pilot the cart was always correct — right variant, right selling plan, right price — and the bar displayed $22.00 while the shopper was about to pay $18.70. Every written criterion was satisfiable in that state.

So after the checklist, look at the thing:

- Read the rendered values against what the system will actually do.
- Open the drawers, modals, overlays, and banners the feature can collide with. Use `elementFromPoint` to find out what is genuinely on top; a `z-index` comparison means nothing across stacking contexts.
- Try it at more than one viewport width, and say which widths you actually used.
- Watch the flow end to end once, as a customer, rather than as a list.

Anything wrong here is a finding even though no criterion covers it. Add it to the ticket as a new criterion, and treat it as a failure.

## 4. When something fails

Do not fix it. QA that repairs its own findings has no independent record of what was wrong.

Write the failure into the ticket — what you did, what you expected, what happened — set `status: in-progress`, and hand back:

```
/clear
```
```
/build <ticket>
```

Failures found in QA belong in the Receipt permanently, not just until they are fixed. They are the most useful part of it a year later.

## 5. Write the Receipt

The Receipt is what actually shipped, not what was planned. It is revised on every round, never rewritten:

- What was built — files, and the shape of the approach
- What was verified, and **how** — the observation, not the intention
- Every bug found and fixed, including during the build
- What was not checked, and why
- One dated section per revision round, with that round's hours

Write it so it answers "what did I pay for?" and "why does this file look like this?" without the conversation that produced it.

## 6. Reconcile the hours

Total the Work Log. Check it against the frontmatter `hours`.

**Propose the number; never finalise it.** Elapsed session time is not billable time. Research done quickly, and dead ends the agent created for itself, are not the client's to pay for. On the pilot the agent logged 3 hours for work the human priced at 2.

State the total and the estimate range together, so an overrun is visible before it reaches an invoice rather than after.

## 7. Present for sign-off

Give the human, in this order:

1. **Ticked** — with the observation for each
2. **Unticked** — with the reason for each
3. **Anything the criteria missed** that you found by looking
4. **Hours** — proposed total against estimate
5. **The explicit ask:** accept, or send back

Do not bury the unticked list. It is the part the sign-off decision actually turns on.

## 8. On acceptance

Only when the human accepts:

- `status: done`
- Leave `billed: false` — invoicing is a separate act
- Update the folder MOC: status and hours
- Log the closure

If the human accepts while something is still open, say so plainly and let them decide again with that in hand.

## Guardrails

- **Never tick a criterion you did not observe.** This is the whole skill.
- **Never move a ticket to `done` without explicit acceptance.**
- **Never delete a ticket.** Cancelled work closes in place, with the reason in the Receipt.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never rewrite Intent or Decisions.** If QA proves a decision wrong, that is a finding, not an edit.
- **Never fix what you find.** Hand it back to `build`.
- **Anything found after the human has reviewed is disclosed and re-offered**, never folded in silently. An approval covers the state the reviewer saw.
