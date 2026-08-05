---
name: create-tickets
description: Assemble one or more build tickets from the task, its capture folder, and the foundation files — routing back when something is missing. Usage:/create-tickets TT-06
disable-model-invocation: true
---

# ticket

Write the file a cold build session will work from.

Everything downstream is only as good as this. `/build` reads the ticket and nothing else; `/qa` walks the criteria this move wrote. A vague ticket does not produce a vague build — it produces a confident build of the wrong thing, and the cost surfaces two rounds later as findings tagged `found by QA`.

So this move is allowed to be expensive. It is the one place in the workflow where thoroughness is cheaper than speed.

## Inputs

`/ticket <task>` — e.g. `/ticket TT-06`. Optional, and it is normal to hand it more than the ID.

**With no argument:** read the vault `Tasks/` folder named by `docs/agents/issue-tracker.md`, list every task at `todo` that has no ticket in `.cortex/` yet, and ask which. Do not pick one silently.

**If the named task does not exist in the vault:** stop. The plugin reads tasks; it does not invent them — a task is a billing record and it comes from Obsidian or Monday. Say what is missing and what its frontmatter needs. If the human then asks you to create it, do so from what is on hand and show it to them before continuing. Never create one as a side effect of being asked for a ticket.

**If a ticket already exists for this task:** stop and say so. Above the divider is frozen once written. If the work has genuinely changed, that is a new ticket on the same task, numbered after the existing one.

## 1. Route on what you were handed

Whatever came with the command tells you which capture avenues to run. This is a routing decision, not a menu to present.

| What you were handed | What to run |
|---|---|
| A Figma URL | Pull design context — tokens, spacing, breakpoints, component names. Name the frame you read. |
| A live URL, or a described bug | Fetch and inspect the rendered page. Reproduce it before describing it. |
| A paragraph of the human's own detail | Take it as intent, then confirm every factual claim in it against the code. People misremember their own repos. |
| A Pastel link | Pull the comments as findings. Each becomes a criterion or an explicit out-of-scope note. |
| A screenshot | Read it, then find the corresponding markup. A screenshot tells you what is wrong, never why. |
| Nothing but a task ID | Research the repo, then grill. There is nothing else to go on. |

Several of these can apply at once. Run all that do.

## 2. Research the repo. Always.

This runs regardless of what else you were handed, and it runs *before* you ask the human anything.

On the pilot this is what earned the whole move. Research found that `{% form 'product' %}` wrapped every block on the product page and that the Loop Subscriptions widget rendered its `selling_plan` input inside that same form. That one fact changed the architecture before a line was written — a sticky bar with its own form would have silently converted subscribers into one-time buyers, looked completely correct, and shipped. Three of the ticket's criteria existed only because of it.

What to establish, every time:

- **Which files actually render the thing.** Not which files sound like they do.
- **What the platform already gives you.** Events the theme emits, JSON it publishes, elements that already do the job. Building a second one of something is how you lose a hidden input some app owns.
- **What third-party apps are in the path.** These are the most common source of bugs that survive review. If an app can change state, assume you will not be told about it.
- **Whether the thing is uniform.** On the pilot, 38 of 38 live products rendered the same section, which is why one implementation covered every case. That was verified, not assumed — six alternate templates existed and none were assigned.
- **What is already there.** Half-finished attempts, dead gates, and settings that look relevant and are not.

Say what you checked and what you found, with file and line references. A claim in a ticket that cannot be traced to a file is a claim `/build` will have to re-derive.

### Side trips

Three, each returning here. They are not stages — nothing downstream knows one was taken.

- **prototype** — when the answer has to be seen rather than described.
- **research** — when the facts live outside the repo.
- **wayfinder** — when the destination itself is foggy and the question is what to build, not how.

## 3. Then ask

Only what research could not settle. A question the repo already answers spends the human's attention and teaches them the questions are not worth answering carefully.

Good questions at this stage are about intent, priorities, and trade-offs the code cannot express: which behaviour is correct when two are defensible, what happens in the case nobody has decided about, whether an edge case is worth handling at all.

Ask them one at a time. Write each answer into the ticket as you get it — not at the end, when you are summarising and will smooth it into something more agreeable than what was said.

## 4. Decide whether it is one sitting

If what you have described is more than one build session's worth of work, say so and propose a split. This is part of the job, not something to wait to be asked for.

A homepage with five sections is one task and five tickets. Each ticket is independently buildable and independently verifiable. The hours still land on the one task.

Propose the split with a one-line description of each ticket and the order. The human approves it. Then write them as `01-<slug>.md`, `02-<slug>.md`, and so on in `.cortex/<task>/`.

Signs it needs splitting: more than roughly a dozen criteria, more than one page or template, or a build step that has to finish before the next one can even be described.

## 5. Write the ticket

`.cortex/<task>/ticket.md`, or the numbered files if you split. Everything you write now sits above the divider and is frozen the moment you hand off.

```markdown
---
task: TT-06
ticket: 01
created: 2026-08-06
---

# TT-06 — Sticky add-to-cart on mobile PDP

## Intent

What the work is and why it exists. The problem in the shopper's terms, then
the fix in the developer's. Include how to reproduce it.

### What the repo says

Findings with file and line references. The hazards you found, and what each
one rules out.

## Decisions taken at ticket

- Bar proxies to the real submit button rather than posting its own request.
- Mobile only. Desktop is unchanged.

## Acceptance criteria

- [ ] ...

## How this gets verified

The environment, and the fallback if it is unavailable.

---
```

The `---` at the end is the divider. Everything below it belongs to `/build` and `/qa`.

### Writing criteria

Criteria are the definition of done, and they are also what the audit measures this ticket against later. Write each one so that a person in a browser can say *what they saw*.

- **Observable, not architectural.** "The cart line comes back with `selling_plan` set and a price of $18.70" can be ticked. "The bar uses the existing form" cannot — it is a decision, and it belongs in Decisions.
- **One thing each.** A criterion joined by "and" produces a half-tick nobody can record.
- **Name the conditions.** Which viewport width, which variant, which state. A criterion that does not say where to stand cannot be failed honestly.
- **Encode the hazards you found.** If research turned up a third-party app, a stacking context, or an async write, there is a criterion for it. These are the ones that pay for the research.
- **Include the states nobody demonstrates.** Sold out, no variant selected, empty cart, one item, the longest product title on the store.

Then read them back and ask: *if every one of these were ticked, could the screen still be wrong?* On the pilot the answer was yes — every criterion was satisfiable in a state where the bar showed $22.00 and the cart charged $18.70. If the answer is yes, there is a criterion missing.

## 6. Record the scoping time

Add a Work Log row to the **vault task** for this session, marked as scoping.

Whether scoping is billable to the client or overhead is unsettled — flag the row rather than deciding it. State the time, say it is scoping, and let the human place it.

**Propose the number; never finalise it.** Research you did quickly is not the client's to pay for.

## 7. The completeness gate

**Do not print the handoff until every question you asked and every finding you surfaced is in the ticket.**

After the `/clear` there is no transcript. Anything that exists only in this conversation is gone, and the build session will rediscover it the expensive way or not at all.

Before handing off, check:

- Every answer the human gave is written down, in their terms rather than your summary of them.
- Every repo finding is in "What the repo says", with its file reference.
- Every hazard has either a criterion or an explicit out-of-scope line.
- Every decision made in conversation is in Decisions.
- "How this gets verified" names a real environment, and says what to do when it is unavailable.

Then set the task to `status: todo` and print:

```
/clear
```
```
/build <task>
```

## Guardrails

- **Never write a ticket without researching the repo first**, however clear the request seems. The clear ones are where the unexamined assumption hides.
- **Never ask what the repo can answer.**
- **Never invent a task.** The plugin reads them; Obsidian and Monday create them.
- **Never overwrite an existing ticket.** Above the divider is written once. Changed work is a new ticket.
- **Never write a criterion you could not observe in a browser.** If it cannot be observed, it is a decision, and it goes in Decisions where nobody will be tempted to tick it.
- **Never invent or adjust `rate`, `billed`, or `invoice`.**
- **Never hand off with an unanswered question still in the conversation.** Either it is in the ticket or it is not settled.
