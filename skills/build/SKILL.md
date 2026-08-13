---
name: build
description: Implement a repo ticket, then loop against a fresh checker agent that verifies it in a real browser until every criterion passes. For theme work with no test runner. Usage:/build why-regenerative
disable-model-invocation: true
---

# build

Implement the work described by a ticket, then prove it works by looking at it.

This exists because the usual build loop assumes a test runner and a type checker. Shopify Liquid and WordPress PHP have neither, so red-green is unavailable and the browser is the feedback loop instead. That is not a downgrade — on the pilot the browser caught four real bugs, none of which a test suite would plausibly have caught, and in every case the code read correctly.

## Two files

| | Task | Ticket |
|---|---|---|
| Where | vault `Tasks/` | this repo, `.cortex/<task>/` |
| Is | the billing record | your brief |
| You write | `status`, and nothing else | one appended Build round |

You build from the ticket. You bill against the task. Never re-derive scope from the task — it deliberately does not carry criteria.

## Inputs

`/build <task>` — e.g. `/build why-regenerative`. Optional.

**Resolving the vault project.** Prefer what Cortex boot already resolved — the `<cortex-session>` block in context names the vault path and the active project, and at L3 it is fully resolved before the first message. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. From a resolved project both paths follow by convention: tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both — silently preferring either is how a stale binding gets worse instead of better. If nothing resolves, stop and say this repo has not been registered with Cortex; `/cortex-register-repo` is the move that binds it.

**With no argument:** read the resolved `Tasks/` folder, list every task at `todo` or `in-progress` with its status, and ask which. Do not pick one silently.

**With a task that has several tickets:** take the lowest-numbered `NN-<slug>.md` ticket that is not yet accepted, and say which one you took before doing anything else. `/build homepage 02` overrides.

## 1. Read the ticket. It is the contract.

Tasks are named, not numbered. Match the argument against the slug in each task's `cortex:` key by prefix — `why-reg` finds `why-regenerative` — and **when more than one task matches, list the matches and ask.** Names share prefixes far more often than sequential IDs did, so taking the first match is how you build the wrong thing.

Then read the capture folder at the path `cortex:` names. Read it out of that key rather than slugging the task's title yourself: the title is display and may have been reworded, and re-deriving the folder from it is what would make a rename break the link.

The ticket is `ticket.md`, or `NN-<slug>.md` where the task was split. Everything else in that folder — `grill-*.md`, `research-*.md`, `prototype-*.md` — is capture, read for context only, and a grill's `## Still open` entry is a question the human declined to answer rather than part of the brief.

The ticket has a frozen half and an appended half, split by a `---` divider.

**Above the divider — Intent, Decisions, Criteria — is settled.** It came out of a `/create-tickets` session that researched the repo and asked the human about what research could not settle. Do not relitigate it, do not improve it, and do not quietly build something adjacent. If the work genuinely cannot be done as described, stop and say why — that is a conversation, not a decision you get to make.

**Criteria are the definition of done.** Read them before writing anything, because they usually encode a hazard the ticket found. On the pilot, three criteria existed only because research discovered a subscription app inside the product form.

**Below the divider are the rounds.** If QA has run, its findings are there with an origin tag on each. This is the actual work list for a return visit — the specific thing that broke, not the whole ticket again. Read every unresolved item from the most recent QA round before you touch anything.

Set the **task** to `status: in-progress` if it is not already.

## 2. Orient before editing

Read the files the ticket names. Confirm they still say what the ticket claims — a ticket written a week ago describes a repo that may have moved.

Branch before touching anything if you are on the default branch.

## 3. Implement

Follow the ticket's stated approach. Prefer the platform's own data and events over anything you invent:

- If the theme already emits an event for a state change, listen to it rather than polling or re-deriving.
- If the platform publishes structured data on the page, read it rather than scraping rendered markup.
- If an element already exists that does the thing, drive that element rather than duplicating its behaviour. Duplicating a form is how you silently lose a hidden input that some app owns.

## 4. Check with a fresh agent, fix, repeat

This is a goal loop, not a fixed number of passes. It runs until the ticket passes.

Each round:

1. You implement.
2. You spawn a **checker subagent** that verifies the work in a real browser against the ticket's criteria and returns a pass / fail / blocked list.
3. You fix every item it returned failing.
4. Go again — a new checker, from scratch.

The loop ends when a checker returns a round with no failures. Not when you believe the work is done. **You do not grade your own build.** The checker's verdict is the only thing that closes the loop, and its browser session is the round's entire browser budget — you do not verify in parallel with it.

### Spawning the checker

One `Agent` call per round, synchronous (`run_in_background: false`) — you have nothing to do until the verdict lands. Use `subagent_type: Explore`: it cannot write files, which is exactly the guarantee you want from a checker. Fall back to `general-purpose` only if `Explore` is unavailable, and then state in the prompt that it must not edit any file.

The checker starts with no memory of your reasoning, and that is the point. Give it:

- The repo path, the ticket path, and the URL(s) to verify against.
- Every criterion, **verbatim** from above the divider.
- Every unresolved item from the most recent QA round, verbatim.
- What changed this round — files touched, one line each. What you changed, not why it should work.
- The browser rules below. They bind the checker as much as they bind you.

Do not tell it what you expect to pass, and do not send it your own verification notes. A checker primed with your conclusion confirms your conclusion.

Require it to return, per item: the criterion verbatim, a verdict, and **the observation behind the verdict**. A verdict with no observation is not a check — re-run the round. A `fail` says what it saw on the page, never what it inferred from reading the code.

| | Means |
|---|---|
| **Pass** | The checker observed it true in the browser this round. |
| **Fail** | The checker exercised it and it was false. This is your work list. |
| **Blocked** | The checker could not exercise it, with the reason. |

Blocked is not failure and does not stall the loop. The pilot's *sold-out variant disables the button* had no sold-out variant on the store to test against, and no number of rounds produces one. Record why and move on.

On a return round from `/qa`, every unresolved item in the most recent QA round joins the criteria as checker input, and it is gated on exactly the same terms as a criterion: passing means the checker observed it fixed, blocked means it says why it could not be exercised, and neither is the same as deciding not to fix it. Ben's `from Ben · refines criterion 3` item does not clear itself by being mentioned in the round — it clears by being observed true or provably blocked, same as a criterion that started the round failing.

### Browser rules — yours and the checker's

#### Use a real rendering browser

Use Playwright. Do **not** verify scroll, observer, or animation behaviour in an embedded preview pane — panes commonly stop producing frames when nothing is capturing them, and `IntersectionObserver` delivery is tied to frame production. A pane that has stopped painting reports a freshly-constructed observer as never firing. Nothing errors. The results simply lie, and they lie in both directions: on the pilot the same code got a false pass and then a false fail.

Embedded panes also clamp the viewport. If you ask for 320px and get 362px, you have not tested 320px.

#### Treat the browser as expensive

Automated request volume against a live storefront trips bot protection, not merely rate limiting. On the pilot this returned `429` with `cf-mitigated: challenge` and did not clear across four minutes of polling. **Working around bot protection is never an option**, so a tripped challenge ends verification for the session.

Therefore:

- One page load, then **one** `evaluate` that runs every assertion for that page state and returns them together.
- Never poll in a loop to wait for a service. Wait once, generously.
- Never re-load a page to check one more thing you could have checked in the same pass.

#### Capture the request, not the appearance

For anything transactional — a cart add, a form post, a checkout step — wrap `XMLHttpRequest.prototype.send` and `window.fetch` and record the payload, then let it through. This proves what the server actually received rather than what the page appeared to do, and it costs one page load instead of a dozen clicks.

Then read the resulting state once, from the platform's own JSON endpoint, and compare against what the UI claimed.

#### Suspect anything a third-party app owns

Third-party widgets are the most common source of bugs that survive review:

- **They write properties, not attributes.** `MutationObserver` does not report a property write, and a `div` styled as a control emits no `change` event. If a widget can change state, assume you will not be told.
- **Their updates are asynchronous.** A single recompute after an interaction races them and fails intermittently. Re-check over a bounded window instead of guessing one delay. Intermittent display bugs on a price reach production.
- **They render their own values.** Mirroring the theme's element can be faithful and still wrong, because the app never updated it.

#### Look at the page, not just the assertions

Criteria can pass while the screen is wrong. On the pilot the cart was always correct and the bar still displayed a price the shopper was not about to pay. Take a screenshot at a real viewport width and read it. Open the drawers, modals, and overlays the feature might collide with, and use `elementFromPoint` to find out what is actually on top — a `z-index` comparison is meaningless across stacking contexts, and raising the number looks like a fix while changing nothing.

### Exit conditions

**The loop passes** when a checker round returns every criterion and every unresolved QA item as pass or blocked. That is the only clean exit, and it is the one you are aiming for.

**There is no round cap.** Run as many rounds as the work takes. A loop that quits at three on a bug it was one round from solving is worse than one that keeps going, and a fresh checker each round is a real signal to run against rather than your own conviction.

The loop stops without passing only for:

- **No progress.** Two consecutive rounds where the same item fails and the checker's observation of it is unchanged. Your fix moved nothing. Stop and say so — repeating a fix that already failed is thrash, not a round. This is a stall condition, not a round budget: items that improve each round keep going, however many rounds that takes.
- **Bot protection trips, or the environment will not stand up.** See `#### Treat the browser as expensive` above. Ends verification for the session.
- **A fix would require changing something above the divider.** That is a conversation, not a decision the loop gets to make.

In all three, whatever is not green is reported exactly as it stands.

## 5. Append the Build round to the ticket

One Build round is appended per session, not one per check round. Check rounds are working state; the ticket is a record. Say how many ran and how the last one landed.

Add a section at the end of the ticket. Never edit above the divider.

```markdown
## Build — round 1 · 2026-08-09

Five check rounds, cleared on the fifth. Moved the bar out of `main-product` into a root-level
render so it shares a stacking context with the drawer, then added the
no-variant price suppression after round 2 showed it flashing $0.00.

Caught by looking, not predicted by any criterion: the app's price node
rewrites asynchronously after a variant change, so the first recompute
raced it. Re-checks over a bounded window now.

Blocked: the sold-out criterion — no sold-out variant exists on the store
to test against.
```

Say what you changed and why, and say plainly what you did not address and why. On a return round, resolve the previous QA round item by item — each one passes, is blocked with a reason, or is still failing and holds the handoff, on the same terms as a criterion. Answering an item is not resolving it; one you discuss but do not fix or block is still failing.

If you found and fixed a bug that no criterion predicted, say so here. Those are the most useful lines in the file a year later, and this is what the post-build audit reads to work out where the ticket came up short, and it is the **only** place that count survives now that the loop fixes its own findings.

## 6. Keep the foundation current

If `.cortex/foundation/` exists, update it as part of this build, not as a separate chore:

- A new reusable snippet or section → append its path and its actual render signature to `components.md`.
- A new token, or a token that changed meaning → the corresponding line in `design-system.md`.
- A new event the theme emits, or a new custom element convention → `platform.md`.
- A third-party app hazard you hit → `concerns.md`.

Extend `scanned:` if you touched a path it did not cover.

These files exist so `/create-tickets` does not re-derive standing facts on every task, and they are only worth trusting if the move that changes the repo is also the move that records the change.

Skip this section entirely if `.cortex/foundation/` is absent — foundation is optional.

## 7. Commit, then stamp the foundation

Commit this build's work, then set the `commit:` stamp on each foundation file you touched to the short SHA of the resulting `HEAD`. The order matters: a stamp taken before the commit names the state this build changed, so `/create-tickets` intersects the build's own edits against `scanned:` and fires the staleness check on every ticket.

Skip the stamp if `.cortex/foundation/` is absent.

## 8. Leave the task's record alone

`status` is the only field on the **vault task** this move touches. The record of what happened this session is the Build round on the ticket, and that is where it stays.

**Do not log time, and do not estimate it.** Elapsed session time is not billable time — research you did quickly and dead ends you created for yourself are not the client's to pay for, and an agent has no way to tell those apart from the inside. On the pilot the agent logged 3 hours for work the human priced at 2. `hours` and the estimate fields are the human's, filled in Obsidian.

Do not write a summary onto the task either. That is written once, at sign-off, from the whole ticket.

## 9. Hand off

Clean or blocked-only — a checker round returned every criterion and every unresolved QA item as pass or blocked — stop with the task at `status: review`. The verdict that closes this out is the checker's, not yours. Print the handoff:

```
/clear
```
```
/qa <task>
```

Loop stopped without passing — stalled, bot-blocked, or held on an above-the-divider question — the task **stays at `status: in-progress`**. Say what is still failing, quote the checker's last observation of it, and ask. That state is not ready for a human to sign anything off, and moving it to `review` would misrepresent it.

The next move on a held ticket is another `/build` session, not `/qa` — nothing here is ready for review. A fresh session gets a fresh environment and a checker with no memory of the stall, which is often enough to break it. Print the handoff:

```
/clear
```
```
/build <task>
```

## Guardrails

The task is a billing record. The ticket is the evidence behind it.

- **Never delete a task or a ticket.** Cancelled work is closed in place with the reason recorded.
- **Never move a task to `done`.** `review` is as far as this skill goes. Only the human accepts.
- **Never edit above the ticket's divider.** Intent, Decisions, and Criteria are frozen. Append.
- **Never tick a criterion.** No move ticks the frozen Criteria section — its checkboxes stay unticked by design, above the divider, forever. The record of what passed lives in the Build round below the divider, not in ticked boxes above it.
- **Never invent or adjust `rate`, `billed`, `invoice`, `hours`, or either estimate field.** Those are the human's, set in Obsidian.
- **Anything found after the human has reviewed** is disclosed and re-offered, never folded in silently. An approval covers the state the reviewer saw.
- **Never let the foundation files drift from what you just built.**
- **Never hand off at `review` with a criterion or an unresolved QA item still failing.** Blocked is a handoff. Failing is not — and an item merely answered without being fixed or blocked is still failing.
- **Never close the loop on your own verdict.** Every exit to `review` is a checker round that came back clean. If you changed code after the last clean round — even a one-liner, even a comment — run another round.
