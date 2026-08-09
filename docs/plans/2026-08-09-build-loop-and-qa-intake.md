# Build Loop and QA Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `/build` an internal verify-fix loop that owns the ticket's criteria outright, and reshape `/qa` from a criteria walk into a collection pass that appends new work to the ticket and hands it back.

**Architecture:** Every move is a single `skills/<name>/SKILL.md` file — prose an agent follows, with no runtime and no test suite. Correctness is enforced by `scripts/check-skills.py` (frontmatter only) plus a per-task read-through gate against [`docs/design/2026-08-09-build-loop-and-qa-intake.md`](../design/2026-08-09-build-loop-and-qa-intake.md). Three skills change and nothing new is created. The skills communicate only through file paths on disk, so the "Interfaces" block in each task is the authoritative contract.

**Tech Stack:** Markdown + YAML frontmatter, Python 3 (checker only), `git`.

## Global Constraints

- **No new skill.** Three files are modified. Sign-off stays inside `/qa` as its terminal state.
- **Frontmatter is untouched in all three files.** Keys stay exactly `name`, `description`, `disable-model-invocation: true`, in that order, and `description` stays under 200 characters with its `Usage:/` clause. If a description is reworded, re-check the length.
- **Voice matches the existing skills:** declarative, second person, no hedging, no emoji, no bullet padding. Claims are justified by what happened on the pilot where a pilot fact exists. Match the spelling of the file you are editing (`behaviour`, `summarising`) rather than normalising across files.
- **Never edit above a ticket's divider** remains a guardrail in both `/build` and `/qa`. Everything this plan adds appends.
- **Existing guardrails are preserved verbatim unless a task says otherwise:** never delete a task, ticket, or past finding; never move a task to `done` without explicit acceptance; never tick a criterion outside sign-off; never invent or adjust `rate`, `billed`, or `invoice`; propose hours and invite correction, never finalise them.
- **Path conventions, used verbatim:**
  - `.cortex/<task>/` — ticket and capture for a named task
  - `.cortex/foundation/concerns.md` — repo-scoped hazards
  - `<vault>/Knowledge Base/ticket-gaps.md` — the cross-project ledger
- **Dates in examples use `2026-08-09` or later.** Do not copy `2026-08-06` out of the existing examples as if it were today.
- **Origin tags are exactly four:** `found by QA`, `from Pastel`, `from Ben`, `blocked in build`. `from criteria` is retired and must not survive anywhere in `skills/`.

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `skills/build/SKILL.md` | Owns the criteria. Loops verify-fix until pass, blocked, or cap. | 1 |
| `skills/qa/SKILL.md` | Collection pass. Appends findings, routes learning, ends at send-back or accept. | 2 |
| `skills/create-tickets/SKILL.md` | Reads the gaps ledger before criteria freeze. | 3 |
| `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Roster prose and version. | 4 |

Tasks 1 and 2 are independent of each other in file terms but **must land in order** — task 2's `blocked in build` tag consumes a concept task 1 introduces, and a reviewer reading task 2 alone should be able to see where that tag comes from.

## Deviation from the spec, decided at planning time

The design document places the ledger read at `/create-tickets` **step 8**. Step 8 is the completeness gate, which runs *after* the criteria have been written — too late for a ledger question to change one.

Task 3 therefore puts the **read at step 4** ("Judge whether you have enough"), where gaps are already named and routed, and leaves a **one-line check at step 8** confirming each matching ledger question was answered or explicitly declared out of scope. This is the same mechanism the spec describes, hooked one step earlier so it can do its job.

---

### Task 1: The build loop

**Files:**
- Modify: `skills/build/SKILL.md` — rewrite `## 4. Verify in the browser`, amend `## 5. Append the Build round to the ticket`, amend `## 9. Hand off`

**Interfaces:**
- Consumes: the ticket's Acceptance criteria, above the divider, unchanged.
- Produces: one appended `## Build — round N · YYYY-MM-DD` section per session, carrying a **blocked list** and a **self-caught list**. Task 2's `blocked in build` origin tag reads the blocked list. The audit reads the self-caught list.
- Produces: a task at `status: review` on a clean-or-blocked exit, or held at `status: in-progress` on a cap exit with live failures.

- [ ] **Step 1: Read the file and the design first**

```bash
sed -n '65,125p' skills/build/SKILL.md
```

Read [`docs/design/2026-08-09-build-loop-and-qa-intake.md`](../design/2026-08-09-build-loop-and-qa-intake.md) sections "The build loop" and "The two questions" before editing. The browser discipline in the existing step 4 — real rendering browser, one page load then one batched `evaluate`, capture the request not the appearance, suspect third-party apps, look at the page — is **correct and stays**. Only the surrounding control flow changes.

- [ ] **Step 2: Rewrite the opening of `## 4. Verify in the browser`**

Replace the current two-line opening (from `This is the part that earns its keep.` through `plus every unresolved QA finding if this is a return round.`) with a loop statement. Keep every `###` subsection that follows it untouched and in place.

The new opening says, in the skill's voice:

Verification is a loop, not a pass. Each round: implement, verify in the browser, classify every criterion, fix the failures, go again.

Then the classification table:

```markdown
| | Means |
|---|---|
| **Pass** | Observed true this round. |
| **Fail** | Exercised and false. This is the round's work list. |
| **Blocked** | Could not be exercised, with the reason. |
```

Then the reasoning for blocked, which must carry the pilot fact: blocked is not failure and does not stall the loop — the pilot's *sold-out variant disables the button* had no sold-out variant on the store to test against, and no number of rounds produces one. Record why and move on.

On a return round from `/qa`, every unresolved item in the most recent QA round joins the criteria as loop input.

- [ ] **Step 3: Add the exits subsection**

Add a new `### Exit conditions` subsection at the **end** of section 4, after `### Record honestly`. Four exits:

- Every criterion passes or is blocked.
- Three rounds have run. Whatever is not green is reported as it stands.
- Bot protection trips, or the environment will not stand up. This defers to the existing rule in `### Treat the browser as expensive` — a tripped challenge ends verification for the session, and working around it is never an option. Do not restate the `429` / `cf-mitigated` detail here; cross-reference it.
- A fix would require changing something above the divider. That is a conversation, not a decision the loop gets to make.

Justify the cap in one line: a loop with no cap thrashes hardest on the bug it cannot solve, and every round costs a page load against a storefront that is already counting them.

- [ ] **Step 4: Amend `## 5. Append the Build round to the ticket`**

State plainly, before the existing example block: **one Build round is appended per session, not one per iteration.** Iterations are working state; the ticket is a record.

Then extend the example to show the new content. Replace the existing fenced example with:

````markdown
```markdown
## Build — round 1 · 2026-08-09

Three verify rounds. Moved the bar out of `main-product` into a root-level
render so it shares a stacking context with the drawer, then added the
no-variant price suppression after round 2 showed it flashing $0.00.

Caught by looking, not predicted by any criterion: the app's price node
rewrites asynchronously after a variant change, so the first recompute
raced it. Re-checks over a bounded window now.

Blocked: the sold-out criterion — no sold-out variant exists on the store
to test against.
```
````

Keep the existing paragraph about saying plainly what you did not address, and the existing paragraph about bugs no criterion predicted — but amend the second so it names the section: this is what the post-build audit reads to work out where the ticket came up short, and it is the **only** place that count survives now that the loop fixes its own findings.

- [ ] **Step 5: Amend `## 9. Hand off`**

Replace the current single-outcome hand-off with two outcomes.

Clean or blocked-only → task at `status: review`, print the existing handoff:

````markdown
```
/clear
```
```
/qa <task>
```
````

Cap hit with failures still standing → the task **stays at `status: in-progress`**. Say what is still failing and ask. State the reason in one line: that state is not ready for a human to sign anything off, and moving it to `review` would misrepresent it.

- [ ] **Step 6: Add the guardrail**

Append one line to `## Guardrails`:

**Never hand off at `review` with a criterion still failing.** Blocked is a handoff. Failing is not.

- [ ] **Step 7: Verify**

```bash
python3 scripts/check-skills.py && grep -n "Blocked\|Exit conditions\|round N\|per session" skills/build/SKILL.md
```

Expected: `PASS — 9 skills`, and the grep shows the classification table, the new `### Exit conditions` heading, and the one-round-per-session line.

- [ ] **Step 8: Read-through gate**

Read `skills/build/SKILL.md` end to end. Confirm: section numbering is still contiguous 1–9; the four `###` browser-discipline subsections survived unedited; `### Exit conditions` sits last inside section 4; the example date is `2026-08-09`; nothing above a ticket divider is described as editable.

- [ ] **Step 9: Commit**

```bash
git add skills/build/SKILL.md
git commit -m "Give build a verify-fix loop that owns the criteria to pass, blocked, or cap"
```

---

### Task 2: QA as a collection pass

**Files:**
- Modify: `skills/qa/SKILL.md` — replace `## 4. Walk the criteria` with a collection section, reorder sections 2–3, rewrite the tag table, add learning routing, rewrite the terminal step

**Interfaces:**
- Consumes: the most recent `## Build — round N` section from task 1, specifically its blocked list.
- Produces: one appended `## QA — round N · YYYY-MM-DD` section. Every item carries an origin tag from the four-tag set, optionally suffixed `· refines criterion N`. `/build` reads these as its return-visit work list — that contract already exists in `skills/build/SKILL.md` step 1 and does not change.
- Produces: lines appended to `.cortex/foundation/concerns.md` each round, and to `<vault>/Knowledge Base/ticket-gaps.md` at accept only.

- [ ] **Step 1: Read the file and the design first**

```bash
cat skills/qa/SKILL.md
```

Read [`docs/design/2026-08-09-build-loop-and-qa-intake.md`](../design/2026-08-09-build-loop-and-qa-intake.md) sections "QA is intake, not a gate", "Tagging gains a second axis", and "Where the learning lands".

The section `## The failure mode this skill is built against` — the sixteen-criteria ticking incident — **stays verbatim**. It is now about ticking at sign-off rather than ticking during a walk, but the pressure it describes is unchanged and the observation-versus-deduction test still governs every item written into a round.

- [ ] **Step 2: Rewrite the opening frame**

Amend the paragraph under `# qa` to state what the skill now is. It walks nothing. Its question is *was the ticket right?* — `/build` already owns *did we build what the ticket says?* and loops until it does.

Add, in the skill's voice: `/qa` is another way to add to the ticket; it happens to run after the build rather than before it. `/build` already reads it that way — its step 1 treats unresolved QA items as the work list for a return visit.

Keep the existing billing-boundary paragraph.

- [ ] **Step 3: Promote collection to the body of the skill**

Replace `## 2. Collect the human's findings first`, `## 3. Rebuild the environment`, and `## 4. Walk the criteria` with two sections.

**`## 2. Rebuild the environment`** — the existing content, unchanged. Stand up what "How this gets verified" specifies; if you cannot, stop and say so rather than reviewing the diff and calling it QA. The browser rules from `build` apply unchanged.

**`## 3. Collect`** — five sources, named as a list:

- Edits Ben made or wants
- Pastel comments
- Client feedback
- Criteria `/build` reported as blocked, from the most recent Build round
- What you find by looking at the screen

Then fold in the existing `### Then ask the question the criteria do not` content, promoted from a subsection to the heart of this one. It keeps its pilot fact: the cart was always correct — right variant, right selling plan, right price — and the bar displayed $22.00 while the shopper was about to pay $18.70. Every written criterion was satisfiable in that state.

Keep its four instructions: read rendered values against what the system will actually do; open the drawers, modals, overlays and banners the feature can collide with and use `elementFromPoint` rather than comparing `z-index` across stacking contexts; try more than one viewport width and say which; watch the flow end to end once as a customer.

Add one line about blocked criteria: try them if this session can — a different environment or a real device may exercise what the build session could not. If it still cannot, carry the item forward with its reason rather than dropping it.

- [ ] **Step 4: Rewrite the tag table and the example round**

In `## 4. Append the QA round to the ticket` (renumbered from 5), keep the instruction not to tick the frozen Criteria section. Replace the example with:

````markdown
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
```
````

Replace the four-row tag table with:

```markdown
| Tag | Means |
|---|---|
| `found by QA` | The ticket did not predict this; you found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | The human raised it |
| `blocked in build` | A criterion build could not exercise, carried forward |
```

`from criteria` is removed. Say why in one line: nothing in a QA round comes from criteria any more, because QA does not read them as a checklist.

Then add the second axis. `refines criterion N` is optional and sits after the origin tag. It separates two ticket-creation failures the origin tag alone collapses into one: *the ticket never mentioned this* and *the ticket got the behaviour right but not the detail*. The first means a question was never asked; the second means it was asked too loosely. Different fixes, and only the marker tells them apart.

Keep the existing paragraph on why the tag is the audit's entire signal, updating it to drop the `from criteria` case. Keep **never leave an item untagged**. Keep the rule that a later round restates every unresolved item with its original tag, because an item that quietly stops appearing reads as resolved.

- [ ] **Step 5: Add the learning-routing section**

Add a new `## 5. Route what this round taught you` before the hours section.

**Repo facts → `.cortex/foundation/concerns.md`, this round.** Test: *would this still be true on this repo next month, on a different ticket?* Example line: the subscription app rewrites the price node asynchronously after a variant change. Written now, because `/build` needs it on the very next pass — a hazard that lands after the work is finished has cost its full price and bought nothing.

Skip this entirely if `.cortex/foundation/` is absent; foundation is optional.

**Cross-project patterns → `<vault>/Knowledge Base/ticket-gaps.md`, at accept only.** State the test as the gate: **can it be phrased as a question `/create-tickets` should ask?** If it cannot, it is not a pattern and it stays in the ticket.

Show the format, grouped by topic:

````markdown
```markdown
## Sticky / overlay elements

- **Ask:** what is the spacing above and below, at each breakpoint?
  — *FKT bar shipped at 12px, client wanted 16 (why-regenerative, QA r1)*
- **Ask:** what can sit on top of it — drawers, modals, banners?
  — *FKT bar drew under the cart drawer (why-regenerative, QA r1)*
```
````

Each entry carries the case that produced it, because a question with no evidence behind it gets dropped the first time it feels tedious to ask.

Say why the timing differs: the ledger is about the next project, so nothing needs it sooner, and a pattern written mid-project is written from half the picture — round 2 routinely reframes what round 1 looked like.

- [ ] **Step 6: Replace section 7 with the terminal step**

`## 7. When something fails` and `## 8. Present for sign-off` collapse into one section, `## 7. Send back, or accept`.

Present in this order: what was collected, with the origin of each; anything still blocked, with why; hours proposed against estimate; then the explicit ask — **send back to `/build`, or accept as it stands?**

Acceptance is the empty case. When a round collects nothing, the only thing left to ask is whether to accept.

On send-back: set the **task** to `status: in-progress` and print the existing handoff:

````markdown
```
/clear
```
```
/build <task>
```
````

Keep the existing line that failures stay in the ticket permanently, not just until they are fixed — they are the most useful part of it a year later, and deleting a resolved finding destroys the audit signal it carries.

Keep `## 8. On acceptance` (renumbered) entirely as written, and add one line to it: write the cross-project ledger entries from section 5 now.

Keep `## 6. Reconcile the hours` as written.

- [ ] **Step 7: Update the guardrails**

Remove **Never fix what you find. Hand it back to `build`.** — it described the old boundary and now reads as forbidding the collection pass from noting what it noticed. Replace with:

**Never re-walk the criteria.** `/build` owns them. Anything you find is a new item with its own origin, not a re-test.

Keep every other guardrail. Amend **Never tick an item you did not observe** to say the rule now governs items written into a round rather than criteria being ticked.

- [ ] **Step 8: Verify**

```bash
python3 scripts/check-skills.py && grep -rn "from criteria" skills/ ; grep -n "refines criterion\|blocked in build\|ticket-gaps" skills/qa/SKILL.md
```

Expected: `PASS — 9 skills`; the `from criteria` grep returns **nothing**; the second grep shows the new tag, the ledger path, and the refines marker.

- [ ] **Step 9: Read-through gate**

Read `skills/qa/SKILL.md` end to end. Confirm: section numbering is contiguous; the sixteen-criteria failure-mode section survived verbatim; `## The failure mode this skill is built against` still governs what may be written into a round; the acceptance closure (summary, hours, `done`, MOC, `billed: false`) is unchanged; the example date is `2026-08-09`.

- [ ] **Step 10: Commit**

```bash
git add skills/qa/SKILL.md
git commit -m "Make QA a collection pass that appends to the ticket and ends at send-back or accept"
```

---

### Task 3: `/create-tickets` reads the gaps ledger

**Files:**
- Modify: `skills/create-tickets/SKILL.md` — amend `## 4. Judge whether you have enough`, add one line to `## 8. The completeness gate`

**Interfaces:**
- Consumes: `<vault>/Knowledge Base/ticket-gaps.md`, written by task 2's section 5. Absent on a first run — that is normal, not an error.
- Produces: criteria that answer the ledger's matching questions, or explicit out-of-scope lines where they do not apply.

- [ ] **Step 1: Read the file first**

```bash
sed -n '73,92p;163,185p' skills/create-tickets/SKILL.md
```

- [ ] **Step 2: Amend `## 4. Judge whether you have enough`**

Add a subsection, `### Ask what the last project taught you`, after the existing routing table and before the counter-pressure paragraph.

Read `<vault>/Knowledge Base/ticket-gaps.md`. It is a list of questions grouped by topic, each carrying the case that produced it, and it is written by `/qa` at sign-off out of what a finished ticket turned out not to have asked. Pull the sections whose topic matches what this ticket covers, and ask those questions before the criteria freeze.

Each one resolves to a criterion, a Decision, or an explicit out-of-scope line. **A ledger question left unanswered is the same gap the ledger exists to record**, which is how the same finding arrives twice.

If the file does not exist, skip this — the ledger accumulates, and an early project has nothing in it yet. Note that this is not a route-back: a ledger question is asked here and now, not deferred to `/grill-me`, unless the answer is genuinely one only the human can make.

- [ ] **Step 3: Add the completeness-gate line**

Add one bullet to the existing checklist in `## 8. The completeness gate`, after the hazard line:

- Every `ticket-gaps.md` question matching this ticket's topics is answered in Criteria or Decisions, or written down as out of scope.

- [ ] **Step 4: Verify**

```bash
python3 scripts/check-skills.py && grep -n "ticket-gaps" skills/create-tickets/SKILL.md
```

Expected: `PASS — 9 skills`, and two hits — one in section 4, one in section 8.

- [ ] **Step 5: Read-through gate**

Read sections 4 and 8 of `skills/create-tickets/SKILL.md`. Confirm the new subsection sits before the counter-pressure paragraph, does not read as another route-back, and says the file may be absent.

- [ ] **Step 6: Commit**

```bash
git add skills/create-tickets/SKILL.md
git commit -m "Have create-tickets ask what the last project's QA found missing"
```

---

### Task 4: Roster prose and version

**Files:**
- Modify: `README.md` — the `qa` section (around lines 101–111), the version section (around line 115)
- Modify: `.claude-plugin/plugin.json` — `version`
- Modify: `.claude-plugin/marketplace.json` — only if its plugin `description` still describes the old shape. It carries **no** `version` field; do not add one.

**Interfaces:**
- Consumes: the three skills as they stand after tasks 1–3.
- Produces: nothing another task reads. This is last for a reason — writing it before the skills settle guarantees it describes something that changed.

- [ ] **Step 1: Read what is there**

```bash
sed -n '95,125p' README.md && cat .claude-plugin/plugin.json && cat .claude-plugin/marketplace.json
```

- [ ] **Step 2: Rewrite the `qa` prose**

The current text says `qa` walks criteria, resists ticking pressure, never fixes what it finds, and that its origin tags let an audit measure ticket quality. Two of those are now wrong.

Rewrite to say: `/build` owns the criteria and loops until they pass, are blocked, or the cap is hit. `/qa` never walks them — it collects from five sources and appends, and acceptance is the empty case of that collection.

Keep the sixteen-criteria pilot fact. It is still the reason the observation-versus-deduction rule exists; it now governs what gets written into a round rather than what gets ticked during a walk.

Update the audit paragraph: `from criteria` is gone, so the measure is now `found by QA` (the ticket did not ask) against `refines criterion N` (it asked too loosely) against `from Pastel` (it missed the client's expectations). Three failures, three fixes.

Add two sentences on the ledger: what `/qa` learns at sign-off lands in `<vault>/Knowledge Base/ticket-gaps.md` as questions, and `/create-tickets` asks them on the next project. That is the loop the origin tags were always pointing at and never closed.

- [ ] **Step 3: Bump the version**

`2.2.0` → `2.3.0` in `.claude-plugin/plugin.json`. `marketplace.json` carries no version — leave it alone unless its plugin `description` still describes the old shape.

Rewrite the README version section for `2.3.0`. Still nine moves — name them unchanged — and say what this version is: `/build` owns its criteria and loops on them; `/qa` becomes intake; findings feed a cross-project ledger that `/create-tickets` reads. Link [`docs/design/2026-08-09-build-loop-and-qa-intake.md`](../design/2026-08-09-build-loop-and-qa-intake.md).

Add a migration note in the style of the existing `2.1.0` one: **tickets written under `2.2.0` carry `from criteria` tags.** They still read fine and nothing parses the tag mechanically, but they predate the split — a `from criteria` item was a criteria walk finding, which `/qa` no longer produces. Leave them; rewriting a past round destroys the record it exists to be.

- [ ] **Step 4: Verify**

```bash
python3 scripts/check-skills.py && grep -n "2.3.0" README.md .claude-plugin/*.json && grep -n "from criteria" README.md
```

Expected: `PASS — 9 skills`; `2.3.0` in all three files; the `from criteria` grep hits **only** the migration note.

- [ ] **Step 5: Read-through gate**

Read the README end to end against the three edited skills. Confirm no sentence still claims `qa` walks criteria or that `qa` never fixes what it finds, and that the moves list is still nine.

- [ ] **Step 6: Commit**

```bash
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Cortex Code 2.3.0 — build loops on its criteria, QA collects"
```

---

## Self-review notes

**Spec coverage.** Every design section maps to a task: the two questions and the build loop → task 1; QA as intake, the tagging axis, and both learning destinations → task 2; the ledger read → task 3. The design's "what changes, by file" list is fully covered, plus task 4 for roster prose the design did not mention.

**One accepted hole, restated from the spec.** Nothing independently re-verifies `/build`'s claim that the criteria pass. This is deliberate, argued in the design's closing section, and no task attempts to close it.

**Retired identifier.** `from criteria` is removed in task 2 and grepped for in tasks 2 and 4. It survives in exactly one place by design: the README migration note.
