# The task and ticket model

*2026-08-04 — design agreed, not yet implemented. Supersedes the single-file ticket model that `0.2.0` shipped against.*

## What changed

`0.2.0` has one durable object: a ticket in the vault that is simultaneously the spec, the agent's brief, the QA checklist, and the billing record. That worked on the pilot and it does not survive contact with the rest of the work.

Two pressures broke it.

**The billing unit and the build unit are not the same size.** An agency homepage is one thing you bill and five things you build — hero, testimonials, footer CTA, and so on, each a full session's worth of prompt. A site audit is the reverse: one thing you were asked to do and nine things you bill separately. One file cannot be both without either splitting the invoice or bloating the prompt.

**The billing record and the build prompt want opposite things.** The invoice wants to stay short, stable, and readable by the client. The build prompt wants to be long, ugly, and complete — full Figma dumps, repo findings, third-party app hazards, and every way a previous attempt went wrong. Keeping both in one file means one of them is always being compromised for the other.

So the object splits in two, along the line of who reads it.

## The model

**A task is the billing unit.** It lives in the vault, or arrives from Monday and is mirrored there. It carries hours, rate, billing state, and a short client-readable summary of what shipped. It is what you would show the client. Tasks never nest.

**A ticket is one build session.** It lives in the repo, under `.cortex/`, and it is the only input a cold `/build` gets. It carries intent, decisions, acceptance criteria, and then every QA and build round appended beneath them. It is never deleted, because the post-build audit reads it.

**A grouping label is a string.** `parent: "Q3 audit"` in a task's frontmatter, and nothing more. It groups a view; it is not a container. Nothing resolves through it, nothing rolls up to it, and no move ever has to work out whether it is looking at a leaf or a branch.

One task has one or more tickets. Usually one. When the work is more than a single sitting, the `/ticket` move says so and writes several.

### The two shapes this covers

A site audit is nine independent tasks that share `parent: "Q3 audit"`. Each has its own hours and its own ticket.

A homepage rebuild is one task with five tickets. Hours land on the homepage; the sections are how you get through it. Each ticket produces one Work Log row on the task, which is the mechanism the pilot already ran — that ticket had several rows and one total.

### Where things live

```
Vault
  Work/<cat>/<client>/<project>/Tasks/
    AC-01 — Currency selector flag bloat.md      ← task: hours, rate, summary
    Homepage.md                                   ← task: hours, rate, summary

Repo
  .cortex/
    AC-01/
      ticket.md                                   ← intent, criteria, QA rounds
    homepage/
      01-hero.md
      02-testimonials.md
      03-footer-cta.md
  docs/agents/issue-tracker.md                    ← binds this repo to the vault project
```

The vault `Specs/` folder becomes `Tasks/`. Specs are the one thing that definitively does not live there — an upstream `to-spec` scratch spec is disposable and stays in `.scratch/`.

## The moves

Three commands. Every move ends by clearing context and printing the next one, because a move boundary is a context boundary: each move starts cold with its file as the only input, which is what forces that file to be complete.

### Move 0 — the task exists

Not a plugin job. You create it in Obsidian, or it arrives from Monday. The plugin reads tasks; it never invents them. This keeps the roster small and keeps the plugin from having an opinion about how the week is run.

```yaml
---
type: freelance-task
task: AC-01
client: Acme Coffee
project: Shopify Website Build
parent: "Q3 audit"        # grouping label, optional
status: todo              # todo | in-progress | review | done
estimate_low: 1
estimate_high: 2
hours: 0
rate: 100
billed: false
invoice: ""
---
```

The body is a paragraph of what it is, a Work Log table, and — once the work lands — three or four sentences of what shipped. No criteria. No bug list. Those are the ticket's job, and duplicating them across two files guarantees they drift.

### Move 1 — `/ticket <task>`

Writes the ticket. This is the move that decides how good everything downstream is, so it is the one that gets to be expensive.

It routes on what is handed to it alongside the task:

| Input | What runs |
|---|---|
| a Figma URL | pull design context, tokens, measurements |
| a live URL or a described bug | fetch and inspect the rendered page |
| a paragraph of your own detail | repo research, then confirm the claims against the code |
| a Pastel link | pull the comments as findings |
| nothing but a task name | grill, because there is nothing else to go on |

Repo research always runs regardless of input. On the pilot it found the `{% form 'product' %}` wrapper and the Loop Subscriptions widget inside it, which changed the architecture before a line was written — a bar with its own form would have silently converted subscribers to one-time buyers, looked correct, and shipped. Research first, ask second, is not a style preference; it is what makes the questions worth asking.

`prototype` remains available as a side trip when the answer has to be seen rather than described. Nothing downstream knows one was taken.

**Splitting is part of the job.** If what you have described is more than one sitting, the move says so and writes numbered tickets rather than one long one. It proposes the split; you approve it.

**The completeness gate:** the move may not print its handoff until every question asked and every finding surfaced is in the file. After the `/clear` there is no transcript to recover them from. This is the rule that makes the whole workflow depend on ticket quality rather than on conversational memory.

### Move 2 — `/build <task>`

Reads the ticket and nothing else. Implements. Proves it in a real browser.

The browser rules are unchanged from `0.2.0` and are the pilot's findings, not a preference: use a real rendering browser rather than an embedded pane, batch every assertion for a page state into one `evaluate`, capture the request rather than the appearance for anything transactional, and suspect anything a third-party app owns.

Writes one Work Log row on the **task** and proposes hours. Sets the task to `in-progress`. Stops at `review`. Never ticks anything, never touches `rate`, `billed`, or `invoice`.

On a task with several tickets, `/build <task>` picks the next unfinished ticket and announces which one it took before doing anything. `/build homepage 02` overrides.

### Move 3 — `/qa <task>`

Starts cold and reads the ticket. Walks the criteria in a browser. Ticks only what it observed this session and can say it saw; annotates every untick with why.

**QA also writes its own items.** It is not limited to the criteria the ticket authored. It looks at the thing, and anything wrong is a finding whether or not a criterion covered it. On the pilot every written criterion was satisfiable in a state where the bar displayed $22.00 and the cart charged $18.70.

**Every QA item records its origin.** This is what makes the audit work.

| Origin | Meaning |
|---|---|
| `from criteria` | The ticket predicted this check |
| `found by QA` | The ticket did not; QA found it by looking |
| `from Pastel` | The client raised it |
| `from Ben` | You raised it |

A ticket whose QA items are all `from criteria` was a good ticket. A ticket carrying a lot of `found by QA` was underspecified technically. A ticket carrying a lot of `from Pastel` missed the client's expectations. Those are different failures with different fixes, and the tag is what lets the audit tell them apart.

**Pastel is not a separate skill.** A Pastel comment is a QA item with a different origin. It enters here, appends to the ticket, and goes back to `/build` like any other failure. This removes the fourth skill the old roster planned for.

On failure: write it into the ticket, set the task to `in-progress`, hand back to `/build`. Never fix what you find — QA that repairs its own findings has no independent record of what was wrong.

On acceptance: write the short summary onto the task. If tickets remain, the task stays `in-progress` and the next ticket starts. If that was the last, the task goes `done` with `billed: false`, because invoicing is a separate act.

## The ticket file

Append-only. Nothing above the line is ever edited — the existing "never rewrite Intent or Decisions" guardrail, generalised. Everything after is added in dated rounds.

```markdown
---
task: AC-01
ticket: 01
created: 2026-08-04
---

# AC-01 — Currency selector flag bloat

## Intent
...

## Decisions taken at ticket
...

## Acceptance criteria
- [ ] ...

## How this gets verified
...

---

## QA — round 1 · 2026-08-06

- [x] Bar price matches cart on subscription select — *saw $18.70 in both* · from criteria
- [ ] Sold-out variant disables the button — *never exercised; no sold-out variant on the store* · from criteria
- [ ] **Fails.** Bar draws under the cart drawer at 390px — *`elementFromPoint` returned the drawer overlay; separate stacking context, so z-index is irrelevant* · found by QA
- [ ] **Fails.** Client wants the price hidden when no variant is chosen · from Pastel

## Build — round 1 · 2026-08-06

Moved the bar out of `main-product` into a root-level render so it shares a
stacking context with the drawer. Added the no-variant price suppression.
Did not address the sold-out criterion — still no sold-out variant to test against.

## QA — round 2 · 2026-08-07
...
```

Unticked is a normal outcome. A ticket that closes with several unticked criteria and an honest note on each is worth more than one with sixteen ticks that cannot be substantiated. The unticked ones are also the to-do list for whoever picks it up on a real device.

## Resolution

Nothing is memorised. `find_project_by_cwd` resolves the repo to its vault project; `docs/agents/issue-tracker.md` names the `Tasks/` folder; the task's `status` decides start-versus-resume.

**It knows, it shows, you confirm.** A zero-argument command asks you to trust a resolution you cannot see and gives you nothing to correct when it picks wrong — which is why `/work` was dropped on 2026-08-03. But refusing to look things up is the opposite error. So:

```
/ticket
→ Acme Coffee — 8 tasks ready. AC-01 currency selector, AC-02 homepage
  image weights, AC-08 structured data… which one?

/ticket AC-01
→ skips the ask
```

This gives the "what should I pick up next" lookup without a fourth command, and settles OQ-06 — `work` does not survive.

## Guardrails

The task is a billing record. The ticket is the evidence behind it.

- **Never delete either.** Cancelled work closes in place with the reason recorded.
- **Never move a task to `done`** without explicit human acceptance.
- **Never tick a criterion you did not observe** in that QA session, in a browser. The test is whether you can say what you saw. Deductions do not tick boxes.
- **Never invent or adjust** `rate`, `billed`, or `invoice`.
- **Never rewrite Intent, Decisions, or Criteria.** If QA proves a decision wrong, that is an appended finding, not an edit.
- **Never fix what QA finds.** Hand it back to `/build`.
- **Never finalise hours.** Elapsed session time is not billable time. Propose the number and invite correction — on the pilot the agent logged 3 hours for work priced at 2.
- **Anything found after human review is disclosed and re-offered**, never folded in silently. An approval covers the state the reviewer saw.

## The audit — later, not v1

`/audit <project>` reads the kept tickets across a finished project and reports where the tickets came up short: which hazards went unpredicted, which viewports went unchecked, which client expectations were missed. The origin tags are the data.

This is the reason tickets stay in the repo rather than being deleted with the code that consumed them, and it is deliberately post-project work — not something to do while the build is live.

## What this supersedes

- `^dec-2026-08-03-10` said specs are disposable and tickets are permanent, with tickets in the vault. Still true about specs; tickets now live in the repo and are still permanent.
- The `0.2.0` `build` and `qa` skills are written against the single-file model and need rewriting against this one. Their browser rules, hour rules, and tick discipline transfer unchanged — the file layout underneath them does not.
- The planned `pastel` skill is cancelled. It is an origin tag.

## Rename scope

One pass, so two meanings are never alive at once:

- plugin `README.md`
- `skills/build/SKILL.md` and `skills/qa/SKILL.md`, bodies and `description` fields
- the vault project hub's decisions and open questions
- `docs/agents/issue-tracker.md` in each bound repo
- vault `Specs/` → `Tasks/`

Existing ticket files stay where they are and become tasks. They shed their criteria to repo tickets as each is picked up, rather than in a migration.

## Open

- **Does `/qa` dispatch a subagent, or is the `/clear` enough?** The clear already gives QA a cold start with the ticket as its only input. A dispatched subagent would additionally not see the conversation in which it was invoked. Stronger, and not obviously necessary.
- **Is the `/ticket` move billable to the client, or overhead?** Carried over from OQ-05, and it now applies to a move that is deliberately more expensive than it was. The pilot brief took 0.5 hr of real scoping that materially changed the build, and was logged as billable.
- **How far can `/build` run unattended?** Carried over from OQ-03. Build can scaffold, implement, and self-correct alone. Verification is the wall — sustained automated requests against `shopify theme dev` trip Cloudflare bot detection, which does not clear, and working around bot protection is not an option. Open part: whether batching all assertions into very few page loads keeps it under the threshold.
