---
name: qa
description: Collect findings from every source, record the round with origin tags, then send back to build or take to sign-off. One task, or a CSV or doc of edits. Usage:/qa why-regenerative · /qa edits.csv
disable-model-invocation: true
---

# qa

Collect what the ticket missed, append it, and send the work back to `/build` or to Ben for sign-off.

`/build` already owns the criteria: it loops on them until they pass or are provably blocked. `/qa` asks a different question, *was the ticket right?*, and spends its budget on what ticket-creation missed. `/build` reads every unresolved item in the latest QA round as its work list on a return visit.

This is the billing boundary. A task at `done` is money owed, and the QA record (a round on the ticket, or a batch doc item attributed to it) is the only durable account of what the ticket failed to anticipate. Everything here exists to keep that record true.

## Two modes

| Form | Mode | Record lives in |
|---|---|---|
| `/qa <task>` | **Task mode**: one task, its tickets | a QA round appended to the ticket |
| `/qa <file or pasted list>` | **Batch mode**: a CSV, doc or list spanning many pages and tickets | one batch doc at `.cortex/qa/<batch-slug>.md` |

Batch mode exists because feedback doesn't arrive one ticket at a time: a client spreadsheet covering nine pages, forty lines from Ben's staging walk, a Pastel export. In batch mode the batch doc is the round's source of truth: the checklist you work off, the file `/build` reads, and the thing you tick. Tickets are referenced, not written to, until acceptance.

`/qa <task>`, e.g. `/qa why-regenerative`. With no argument, list tasks at `status: review` and ask. Match the argument against the slug in each task's `cortex:` key by prefix; when more than one matches, list them and ask.

`/qa <path>`, or `/qa` with content pasted after it, is batch mode (`.csv`, `.md`, `.txt`, a Pastel export, or pasted text). An existing path is batch mode; a task slug match is task mode. If it could be both, ask.

## The failure mode this skill is built against

An agent asked to sign off will tick everything. On the pilot, sign-off ticked all sixteen criteria in one pass, including five that the same document, in the same edit, described as never exercised. The work felt finished, so the boxes got ticked. That pressure is strongest exactly when the work feels done, on the criteria least interesting to check.

The rule: tick an item only if you observed it true, in this QA session, in a browser. Not because the code obviously does it, a shared form carries it, or it worked at build time. The test is whether you can say what you saw; see the Verdicts section of `../_shared/references/browser-verification.md` (relative to this skill's folder).

## 1. Read the ticket

In batch mode, do section 2 first, then read every ticket the attribution touched.

**Resolving the vault project.** Prefer what Cortex boot already resolved: the `<cortex-session>` block names the vault path and active project. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. Tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both. If nothing resolves, say the repo is not registered and point to `/cortex-register-repo`.

Read the capture folder at the path in the task's `cortex:` key; don't slug the title yourself. The ticket is `ticket.md`, or `NN-<slug>.md` where the task was split. `grill-*.md`, `research-*.md` and `prototype-*.md` are context only, and a grill's `## Still open` entry is a question the human declined to answer.

Read Intent, Decisions and Criteria above the divider, then every round below it. The latest Build round says what the builder claims and what they didn't check. Don't treat that list as authoritative either way: they may have missed something they thought they covered, or fixed something they forgot to mention.

## 2. Attribute the batch (batch mode only)

### Split it into items

One finding per row, bullet, comment or cell.

- Don't merge two complaints. "Spacing is off and the price is wrong" is two findings, possibly on two tickets. Merged, one gets fixed and the item gets ticked.
- Don't split one complaint into two half-findings that each look trivial and get deprioritized.

Keep the source's own wording. Paraphrasing a client's edit is how intent changes between the spreadsheet and the fix.

### Attribute each item to a ticket

Read every task folder and ticket in `.cortex/`, and match each finding on whatever the source gives: URL, page, section, component, or the files a ticket names.

| State | Means | What you do |
|---|---|---|
| **Attributed** | One ticket clearly covers it | Name the task slug and ticket file on the item |
| **Ambiguous** | Two or more tickets could own it | Write both, flag it, ask before working it |
| **Unattributed** | No ticket covers it | Its own section at the bottom of the doc |

The unattributed section is this move's most valuable output. Such an item is either work never ticketed or work never tasked. Say which and point to `/create-tickets` or `/create-tasks`. Don't attribute it to the nearest ticket to tidy the list; that is the record corruption origin tags exist to prevent.

### Write the batch doc

`.cortex/qa/<batch-slug>.md`, slugged from the source (`client-edits-aug`, `pastel-round-2`, `ben-walkthrough`), not a date alone.

```markdown
---
source: ~/Downloads/client-edits-2026-08-22.csv
opened: 2026-08-22
status: open
tasks: [why-regenerative, homepage]
---

# QA batch — client edits, August

Verified against `shopify theme dev` in Playwright at 390 / 768 / 1280px.
Checkout not examined — Shop Pay test session required device 2FA.

## Attributed

- [ ] **Fails.** Spacing under the bar is 12px, should be 16 · from Ben ·
      refines criterion 3 · `why-regenerative` / `02-sticky-bar.md`
- [ ] **Ambiguous.** Footer newsletter field has no error state · from Pastel ·
      could be `homepage` / `03-footer.md` or `newsletter` / `ticket.md`

## Unattributed

- [ ] Blog index has no pagination past page 3 · from Pastel — *no ticket
      covers the blog index; this is new work* → `/create-tasks`
```

Every item carries an origin tag (section 5) and an attribution. `refines criterion N` sits between them where it applies.

### Confirm before working it

Show Ben the doc's shape before verifying anything: item count, how many attributed, every ambiguous item, every unattributed one. Ambiguous items wait until resolved. Unattributed items are his decision (new ticket, new task, or out of scope).

## 3. Rebuild the environment

Stand up what the ticket's "How this gets verified" section specifies. In batch mode, stand up the union across every touched ticket once. Where two can't coexist, say so and work them in separate passes against the same doc.

If the environment won't stand up (broken auth, a service down, bot protection tripped), don't stop the round. Collect the four sources that need no browser, record that the screen was not examined and why, and still end at the ask in section 7. Never review the diff and record it as a look at the screen.

Where it does stand up, follow the browser reference, `../_shared/references/browser-verification.md` (relative to this skill's folder).

## 4. Collect

Gather from every source with an opinion:

- Edits Ben made or wants
- Pastel comments
- Client feedback
- Criteria `/build` reported as blocked, from the latest Build round
- What you find by looking at the screen

In batch mode the first three arrive pre-collected in the source doc. The blocked criteria (from every touched ticket's latest Build round) and the screen still need work. A batch with zero `found by QA` items means nobody looked.

Try any blocked criterion this session can reach: a different environment or a real device may get there. If you observe it true, tick it, keep its `blocked in build` origin, and note where you finally exercised it. If false, write it as `**Fails.**` with the same origin. If it still can't be exercised, carry it forward as its own item with its reason.

**Does the screen tell the truth?** Criteria can all pass while the interface is wrong; the browser reference has the pilot's $22.00 vs $18.70 cart. Follow its "Look at the page" section, try more than one viewport width and say which, and watch the flow end to end once as a customer. Anything wrong here is a `found by QA` finding and counts as a failure, even though no criterion covers it.

## 5. Record the round

In task mode, append a QA round to the ticket. In batch mode, tick and extend the batch doc and don't append rounds to tickets; duplicated items drift the moment one copy is fixed. Tickets get their pointer at acceptance (section 8). Everything else below applies to both modes.

Don't tick the Criteria section. It is frozen above the divider and records what done was meant to be; the audit compares against it. Write a fresh checklist in your round.

```markdown
## QA — round 1 · 2026-08-09

Verified against `shopify theme dev` in Playwright at 320 / 390 / 430px. Checkout
not examined — Shop Pay test session required device 2FA this pass.

- [ ] **Fails.** Bar draws under the cart drawer at 390px — *`elementFromPoint`
      at the bar's center returned the drawer overlay; separate stacking
      context* · found by QA
- [ ] **Fails.** Spacing under the bar is 12px, should be 16 · from Ben ·
      refines criterion 3
- [ ] Sold-out variant disables the button — *still no sold-out variant on the
      store; tried staging too* · blocked in build
- [x] Low-stock variant disables the button — *exercised on a real device;
      staging had a variant at qty 1* · blocked in build
```

Every item carries one origin:

| Tag | Means |
|---|---|
| `found by QA` | The ticket didn't predict it; you found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | Ben raised it |
| `blocked in build` | A criterion build couldn't exercise, carried forward |

The tag is the whole signal the post-build audit runs on. Lots of `found by QA` means the ticket was technically underspecified; lots of `from Pastel` means it missed the client's expectations; lots of `blocked in build` means it ran out of environment. Untagged items break that.

The optional `refines criterion N` marker separates "the ticket never mentioned this" (a question never asked) from "it got the behavior right but not the detail" (a question asked too loosely).

On a later task-mode round, re-check every unresolved item from the previous round and restate it with its original tag. An item that quietly disappears reads as resolved.

In batch mode, tick items in place and append a `## Round N` note: what was verified, at which widths, what couldn't be examined. New findings in a later round go into the doc, attributed the same way. Don't delete ticked items.

Edits that arrive mid-round, such as Ben sending more while the batch is open, go into the same batch doc rather than a new one: one doc per feedback source, not one per message.

## 6. Route what this round taught you

**Repo facts → `.cortex/foundation/concerns.md`, this round.** Test: would it still be true on this repo next month, on another ticket? For example, the subscription app rewrites the price node asynchronously after a variant change. `/build` needs it on the next pass. Skip if `.cortex/foundation/` is absent.

**Cross-project patterns → `<vault>/Knowledge Base/ticket-gaps.md`, at accept only.** The gate: can it be phrased as a question `/create-tickets` should ask? If not, it stays in the ticket. Group by topic, and give each entry the case that produced it:

```markdown
## Sticky / overlay elements

- **Ask:** what can sit on top of it — drawers, modals, banners?
  — *FKT bar drew under the cart drawer (why-regenerative, QA r1)*
```

The ledger waits for acceptance because it serves the next project, and a pattern written mid-project is written from half the picture.

## 7. Send back, or accept

Present, in order:

1. What was collected, with each origin
2. Anything still blocked, with why
3. The ask: send back to `/build`, or accept as it stands?

Acceptance is the empty case. A round carrying only an unreachable `blocked in build` item still collected something; present it and let Ben decide.

**Send-back, task mode:** set the task to `status: in-progress` and print:

```
/clear
```
```
/build <task>
```

**Send-back, batch mode:** set every task with an unticked attributed item to `in-progress`, and print one handoff per task with its open count:

```
why-regenerative — 4 open
```
```
/clear
```
```
/build why-regenerative all
```

Use `all` where the open items span more than one ticket on the task. Keep the batch doc at `status: open` with accurate attributions until every item is ticked, because `/build` reads its work list from it.

Findings stay in the ticket after they are fixed. They are the most useful part of it a year later.

## 8. On acceptance

In batch mode, acceptance is per task. Close the batch doc (`status: closed`) only when every item is ticked or explicitly accepted-with-open. At acceptance, append a pointer round to each ticket the batch touched:

```markdown
## QA — batch `client-edits-aug` · 2026-08-22

Reviewed in a batch covering why-regenerative and homepage. Findings are in
`.cortex/qa/client-edits-aug.md` — 2 items attributed to this ticket
(`found by QA` ×1, `from Ben` ×1, refines criterion 3), both resolved.

Accepted 2026-08-22.
```

Then, only when Ben accepts, on the task:

- Write the summary: three or four sentences of what shipped, in terms a client would recognize. No criteria or bug list; those live in the ticket.
- If tickets remain, leave `status: in-progress` and hand off to `/build` for the next one. If that was the last, `status: done`.
- Leave `billed: false`; invoicing is separate.
- Update the `Tasks/_MOC.md` row's status only. Hours and estimate columns are Ben's.
- Log the closure.
- Write the cross-project ledger entries from section 6.

If Ben accepts while something is still open, say so plainly and let him decide again with that in hand.

## Guardrails

- Tick only what you observed, and give every item an origin tag.
- Above the ticket's divider is frozen. A decision QA proves wrong becomes an appended finding.
- A task reaches `done` only on Ben's explicit acceptance, and not while a ticket on it is unfinished.
- Don't delete tasks, tickets or past findings. Cancelled work closes in place with the reason.
- `rate`, `billed`, `invoice`, `hours` and the estimate fields are Ben's. This move neither logs nor reconciles time.
- Unattributed is a real state. Don't attribute to the nearest ticket to tidy the list.
- During a batch round, the batch doc is the only copy of its items; tickets get the pointer at acceptance.
- A batch doc closes only when nothing in it is unticked and unexplained.
- Don't re-walk the criteria; `/build` owns them. Anything you find is a new item with its own origin.
- Anything found after Ben has reviewed is disclosed and re-offered, not folded in. An approval covers the state he saw.
