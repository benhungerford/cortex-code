---
name: build
description: Implement a vault ticket against its criteria and verify it in a real browser. For theme work with no test runner. Usage:/build TT-06
disable-model-invocation: true
---

# build

Implement the work described by a ticket, then prove it works by looking at it.

This exists because the usual build loop assumes a test runner and a type checker. Shopify Liquid and WordPress PHP have neither, so red-green is unavailable and the browser is the feedback loop instead. That is not a downgrade — on the pilot ticket the browser caught four real bugs, none of which a test suite would plausibly have caught, and in every case the code read correctly.

## Inputs

`/build <ticket>` — e.g. `/build TT-06`. The ticket ID is the only argument. Everything else is derived.

## 1. Read the ticket. It is the contract.

Find the ticket via `docs/agents/issue-tracker.md` in this repo, which names the vault folder its tickets live in. Resolve the ID by prefix match on filename. If that file does not exist, stop and say so — this repo has not been bound to a vault project.

**Intent and Decisions are settled.** They came out of a brief that researched the repo and asked the human about the parts research could not settle. Do not relitigate them, do not improve them, and do not quietly build something adjacent. If the work genuinely cannot be done as described, stop and say why — that is a conversation, not a decision you get to make.

**Criteria are the definition of done.** Read them before writing anything, because they usually encode a hazard the ticket found. On the pilot, three criteria existed only because the brief discovered a subscription app inside the product form.

Set `status: in-progress` if it is not already.

## 2. Orient before editing

Read the files the ticket names. Confirm they still say what the ticket claims — a brief written a week ago describes a repo that may have moved.

Branch before touching anything if you are on the default branch.

## 3. Implement

Follow the ticket's stated approach. Prefer the platform's own data and events over anything you invent:

- If the theme already emits an event for a state change, listen to it rather than polling or re-deriving.
- If the platform publishes structured data on the page, read it rather than scraping rendered markup.
- If an element already exists that does the thing, drive that element rather than duplicating its behaviour. Duplicating a form is how you silently lose a hidden input that some app owns.

## 4. Verify in the browser

This is the part that earns its keep. Work through the Criteria one at a time.

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

## 5. Record the work

Add one Work Log row for this session. Bump the frontmatter `hours` to match the Work Log total.

**Propose hours; never finalise them.** Elapsed session time is not billable time. Research you did quickly and dead ends you created for yourself are not the client's to pay for. State the number you are writing and invite correction — on the pilot the agent logged 3 hours for work the human priced at 2.

Write the Receipt as the record of what actually shipped: what was built, what was verified and how, and every bug found and fixed along the way. Bugs found during the build belong in the Receipt — they are the most useful thing in it later.

## 6. Hand off

Stop at `status: review`. Print the handoff:

```
/clear
```
```
/qa <ticket>
```

## Guardrails

The ticket is a billing record, not a scratch file.

- **Never delete a ticket.** Cancelled work is closed in place with the reason in the Receipt.
- **Never move a ticket to `done`.** `review` is as far as this skill goes. Only the human accepts.
- **Never tick a criterion.** Ticking is the sign-off move's job, and an agent that ticks its own work ticks everything.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never rewrite Intent or Decisions** on a ticket in flight.
- **Anything found after the human has reviewed** is disclosed and re-offered, never folded in silently. An approval covers the state the reviewer saw.
