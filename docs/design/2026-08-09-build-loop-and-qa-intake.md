# The build loop and QA as intake

*2026-08-09 — design. Raised by Ben: QA is doing two jobs badly. Split the verification that belongs to building away from the intake that belongs to reviewing, and let `/build` run its own loop.*

## The problem

`/build` verifies once and hands off regardless of what it saw. Step 4 walks the criteria in a browser, step 5 records what passed and what did not, step 9 prints the handoff to `/qa`. A build that leaves three criteria failing exits exactly the same way as one that leaves none.

So `/qa` inherits work that was never review work. It re-walks the same criteria in the same browser against the same store, and the first thing it usually finds is a bug the builder could have caught in the same session it introduced. The round-trip through `/clear` and a cold `/qa` buys nothing except a fresh context window.

Meanwhile the job that *is* review work — finding what the ticket never asked about — is buried at step 4's tail, after the checklist, in a subsection. On the pilot that subsection is where the real finding came from: every criterion passed while the bar displayed $22.00 and the shopper was about to pay $18.70. The checklist could not have caught it, because the checklist was the thing that was wrong.

Both jobs are in one skill and the wrong one has top billing.

## The two questions

They separate cleanly once named:

| | Asks | Loops | Ends at |
|---|---|---|---|
| `/build` | Did we build what the ticket says? | Yes, internally | task `review` |
| `/qa` | Was the ticket right? | No | back to `/build`, or accept |

`/build` owns the criteria completely. It is the only move that walks them, and it does not stop walking them until they pass, are provably unexercisable, or it runs out of rope.

`/qa` never walks them. It takes build's pass claim and spends its whole budget on what ticket-creation missed.

## QA is intake, not a gate

The framing that follows from this: `/qa` is another way to add to the ticket. It happens to run after the build rather than before it.

`/build` already reads it that way. Step 1 says to read every unresolved item from the most recent QA round before touching anything, and calls that the actual work list for a return visit. The channel exists. What changes is what fills it — not the residue of a criteria walk, but a deliberate collection from every source that has an opinion:

- Edits Ben made or wants
- Pastel comments
- Client feedback
- Criteria `/build` reported as blocked
- What QA finds by looking at the screen

The cycle is therefore:

```
/create-tickets → /build → /qa → /build → /qa → … → accept
```

Acceptance is the empty case of intake. When a `/qa` round collects nothing, the only thing left to ask is whether to accept, so `/qa` asks it there rather than deferring to a separate move. A `/sign-off` skill would be a second name for the terminal state of this one.

## The build loop

Step 4 becomes iterative. Each round: implement, verify in the browser, classify every criterion, fix the failures, go again.

Three outcomes per criterion:

| | Means |
|---|---|
| **Pass** | Observed true this round. |
| **Fail** | Exercised and false. The loop's work list. |
| **Blocked** | Could not be exercised, with the reason. |

Blocked is not failure and does not stall the loop. The pilot's *sold-out variant disables the button* had no sold-out variant on the store to test against; no number of rounds produces one. The loop records why and moves on.

**Exit conditions:**

- Every criterion passes or is blocked.
- Three rounds have run. Whatever is not green is reported as it stands.
- Bot protection trips, or the environment will not stand up. The existing rule holds — a tripped challenge ends verification for the session, and working around it is never an option.
- A fix would require changing something above the divider. That is a conversation, not a decision the loop gets to make.

The cap exists because a loop with no cap thrashes hardest on the bug it cannot solve, and each round costs a page load against a live storefront that is already counting them.

**Status on exit.** `review` when everything passes or is blocked. When the cap is hit with real failures still standing, the task stays `in-progress` and the loop says so — that state is not ready for a human to sign anything off, and moving it to `review` would misrepresent it.

**Recording.** One Build round is appended per session, not one per iteration. Iterations are working state; the ticket is a record. The round states what shipped, how many rounds it took, what the loop caught that no criterion predicted, and every blocked criterion with its reason.

That third item matters more than it looks. It is the honest count of how much the ticket failed to anticipate, and it is the only place that count survives now that build fixes its own findings.

## Tagging gains a second axis

Origin stays required and unchanged:

| Tag | Means |
|---|---|
| `found by QA` | The ticket did not predict this; QA found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | The human raised it |
| `blocked in build` | A criterion build could not exercise, carried forward |

`from criteria` retires. Nothing in a QA round comes from criteria any more, because QA does not read them as a checklist.

What is new is an optional marker on top of the origin:

```markdown
- [ ] **Fails.** Bar draws under cart drawer at 390px · found by QA
- [ ] **Fails.** Spacing under bar is 12px, should be 16 · from Ben · refines criterion 3
- [ ] Sold-out disables button · blocked in build — no sold-out variant on store
```

`refines criterion N` separates two different ticket-creation failures that the origin tag alone collapses into one. *The ticket never mentioned this* and *the ticket got the behaviour right but not the detail* are both gaps, but the first means a question was never asked and the second means it was asked too loosely. They have different fixes, and only the marker tells them apart.

Ben's framing of this: a QA item may well touch something already checked. It is a change or an adjustment nobody considered, not a re-test.

## Where the learning lands

Every QA finding is by definition something ticket-creation missed. That makes the accumulated findings the most direct signal the plugin has about its own front end, and right now it evaporates into individual tickets nobody re-reads.

Two destinations, on two different clocks.

**Repo facts → `.cortex/foundation/concerns.md`, written immediately.**

Test: *would this still be true on this repo next month, on a different ticket?*

> The subscription app rewrites the price node asynchronously after a variant change.

Written the same round it is found, because `/build` needs it on the very next pass. A hazard that lands after the work is finished has cost its full price and bought nothing.

**Cross-project patterns → `<vault>/Knowledge Base/ticket-gaps.md`, written at accept.**

Test: **can it be phrased as a question `/create-tickets` should ask?** If it cannot, it is not a pattern and it stays in the ticket.

```markdown
## Sticky / overlay elements

- **Ask:** what is the spacing above and below, at each breakpoint?
  — *FKT bar shipped at 12px, client wanted 16 (why-regenerative, QA r1)*
- **Ask:** what can sit on top of it — drawers, modals, banners?
  — *FKT bar drew under the cart drawer (why-regenerative, QA r1)*
```

Grouped by topic so `/create-tickets` can pull the sections that apply. Each entry carries the case that produced it, because a question with no evidence behind it gets dropped the first time it feels tedious to ask.

Written at accept rather than per round, for two reasons. It is about the next project, so nothing needs it sooner. And a pattern written mid-project is written from half the picture — round 2 routinely reframes what round 1 looked like.

`/create-tickets` reads the ledger at its completeness gate, step 8, and asks the matching questions before the criteria freeze. The ledger is worth keeping only if the move that would have benefited from it actually reads it.

## What changes, by file

**`skills/build/SKILL.md`**
- Step 4 becomes a loop with pass/fail/blocked classification and the four exits
- Step 5 records one round per session, including self-caught findings and the blocked list
- Step 9 gains the cap-with-failures case, which holds at `in-progress`

**`skills/qa/SKILL.md`**
- Drops the criteria walk entirely
- Collection from all five sources becomes the body of the skill
- `from criteria` retires; `blocked in build` and `refines criterion N` are added
- Foundation routing runs each round; ledger routing runs at accept
- Ends with *send back, or accept* — acceptance keeps the existing closure

**`skills/create-tickets/SKILL.md`**
- Step 8 reads `ticket-gaps.md` and asks the matching questions before freezing criteria

## What this deliberately does not do

**No independent re-verification of the criteria.** Nothing checks build's claim that they pass. That is a real hole, and it is accepted: paying twice for the same six checks costs more than the failure mode it prevents, and the failure mode is visible anyway the moment a shipped feature does not work.

**No automatic promotion to the ledger.** A finding reaches `ticket-gaps.md` only when it can be stated as a question. Machinery that promoted everything would fill the ledger with one-offs and make `/create-tickets` slower for no return.

**No new skill.** Sign-off stays inside `/qa` as its terminal state.

**No change above the divider.** Intent, Decisions, and Criteria stay frozen in both moves. Everything here appends.
