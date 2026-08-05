---
name: build
description: Implement a repo ticket against its criteria and verify it in a real browser. For theme work with no test runner. Usage:/build TT-06
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
| You write | one Work Log row, proposed hours, `status` | one appended Build round |

You build from the ticket. You bill against the task. Never re-derive scope from the task — it deliberately does not carry criteria.

## Inputs

`/build <task>` — e.g. `/build TT-06`. Optional.

**With no argument:** read the vault `Tasks/` folder named by `docs/agents/issue-tracker.md`, list every task at `todo` or `in-progress` with its status and estimate, and ask which. Do not pick one silently.

**With a task that has several tickets:** take the lowest-numbered ticket that is not yet accepted, and say which one you took before doing anything else. `/build homepage 02` overrides.

If `docs/agents/issue-tracker.md` does not exist, stop and say so — this repo has not been bound to a vault project.

## 1. Read the ticket. It is the contract.

Resolve the task ID by prefix match, then read `.cortex/<task>/`.

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

## 4. Verify in the browser

This is the part that earns its keep. Work through the Criteria one at a time, plus every unresolved QA finding if this is a return round.

### Use a real rendering browser

Use Playwright. Do **not** verify scroll, observer, or animation behaviour in an embedded preview pane — panes commonly stop producing frames when nothing is capturing them, and `IntersectionObserver` delivery is tied to frame production. A pane that has stopped painting reports a freshly-constructed observer as never firing. Nothing errors. The results simply lie, and they lie in both directions: on the pilot the same code got a false pass and then a false fail.

Embedded panes also clamp the viewport. If you ask for 320px and get 362px, you have not tested 320px.

### Treat the browser as expensive

Automated request volume against a live storefront trips bot protection, not merely rate limiting. On the pilot this returned `429` with `cf-mitigated: challenge` and did not clear across four minutes of polling. **Working around bot protection is never an option**, so a tripped challenge ends verification for the session.

Therefore:

- One page load, then **one** `evaluate` that runs every assertion for that page state and returns them together.
- Never poll in a loop to wait for a service. Wait once, generously.
- Never re-load a page to check one more thing you could have checked in the same pass.

### Capture the request, not the appearance

For anything transactional — a cart add, a form post, a checkout step — wrap `XMLHttpRequest.prototype.send` and `window.fetch` and record the payload, then let it through. This proves what the server actually received rather than what the page appeared to do, and it costs one page load instead of a dozen clicks.

Then read the resulting state once, from the platform's own JSON endpoint, and compare against what the UI claimed.

### Suspect anything a third-party app owns

Third-party widgets are the most common source of bugs that survive review:

- **They write properties, not attributes.** `MutationObserver` does not report a property write, and a `div` styled as a control emits no `change` event. If a widget can change state, assume you will not be told.
- **Their updates are asynchronous.** A single recompute after an interaction races them and fails intermittently. Re-check over a bounded window instead of guessing one delay. Intermittent display bugs on a price reach production.
- **They render their own values.** Mirroring the theme's element can be faithful and still wrong, because the app never updated it.

### Look at the page, not just the assertions

Criteria can pass while the screen is wrong. On the pilot the cart was always correct and the bar still displayed a price the shopper was not about to pay. Take a screenshot at a real viewport width and read it. Open the drawers, modals, and overlays the feature might collide with, and use `elementFromPoint` to find out what is actually on top — a `z-index` comparison is meaningless across stacking contexts, and raising the number looks like a fix while changing nothing.

### Record honestly

Note which criteria you exercised and which you did not. You are not the one who ticks them — see below.

## 5. Append the Build round to the ticket

Add a section at the end of the ticket. Never edit above the divider.

```markdown
## Build — round 1 · 2026-08-06

Moved the bar out of `main-product` into a root-level render so it shares a
stacking context with the drawer. Added the no-variant price suppression.

Not addressed: the sold-out criterion — no sold-out variant exists on the
store to test against.
```

Say what you changed and why, and say plainly what you did not address and why. On a return round, answer the previous QA round item by item — an unanswered finding reads as an overlooked one.

If you found and fixed a bug that no criterion predicted, say so here. Those are the most useful lines in the file a year later, and they are also what the post-build audit reads to work out where the ticket came up short.

## 6. Keep the foundation current

If `.cortex/foundation/` exists, update it as part of this build, not as a separate chore:

- A new reusable snippet or section → append its path and its actual render signature to `components.md`.
- A new token, or a token that changed meaning → the corresponding line in `design-system.md`.
- A new event the theme emits, or a new custom element convention → `platform.md`.
- A third-party app hazard you hit → `concerns.md`.

Bump the `commit:` stamp and extend `scanned:` if you touched a path it did not cover.

These files exist so `/create-tickets` does not re-derive standing facts on every task, and they are only worth trusting if the move that changes the repo is also the move that records the change.

Skip this section entirely if `.cortex/foundation/` is absent — foundation is optional.

## 7. Record the work on the task

Add one Work Log row to the **vault task** for this session. Bump the task's frontmatter `hours` to match the Work Log total.

**Propose hours; never finalise them.** Elapsed session time is not billable time. Research you did quickly and dead ends you created for yourself are not the client's to pay for. State the number you are writing and invite correction — on the pilot the agent logged 3 hours for work the human priced at 2.

Do not write a summary onto the task. That is written once, at sign-off, from the whole ticket.

## 8. Hand off

Stop with the task at `status: review`. Print the handoff:

```
/clear
```
```
/qa <task>
```

## Guardrails

The task is a billing record. The ticket is the evidence behind it.

- **Never delete a task or a ticket.** Cancelled work is closed in place with the reason recorded.
- **Never move a task to `done`.** `review` is as far as this skill goes. Only the human accepts.
- **Never edit above the ticket's divider.** Intent, Decisions, and Criteria are frozen. Append.
- **Never tick a criterion.** Ticking is the sign-off move's job, and an agent that ticks its own work ticks everything.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Anything found after the human has reviewed** is disclosed and re-offered, never folded in silently. An approval covers the state the reviewer saw.
- **Never let the foundation files drift from what you just built.**
