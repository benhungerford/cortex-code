---
name: grill-me
description: A relentless one-question-at-a-time interview that settles what research cannot, written down as it goes. Usage:/grill-me TT-06
disable-model-invocation: true
---

# grill-me

A relentless interview that reaches shared understanding on a plan, decision, or idea, and writes the result somewhere a cold session can read it.

This is one of three capture moves — alongside `research` and `prototype` — invoked from an ideation session or directly against a task. All three write to the same place and are read the same way later: a later assembly step opens every `grill-*.md` in the folder cold, with no memory of this conversation. What is not in the file did not happen. That is why the discipline below matters more here than in most skills — the whole value of a grill is that the human's own answers ended up on disk, not a paraphrase of them.

## Inputs

`/grill-me <task>` writes to `.cortex/<task>/`. `/grill-me` with no argument, invoked inside an ideation session, writes to `.cortex/ideation/<effort>/`, taking the effort slug from the map rather than deriving one here. With neither a task nor an ideation session to place it in, ask which before starting. Do not guess a home — a transcript written to the wrong folder is a transcript no later move will find.

## How to grill

Walk down each branch of the decision tree, resolving dependencies between decisions one at a time rather than jumping ahead to whatever seems most interesting.

For each question, give your recommended answer and the reason for it. A grill without a recommendation makes the human do the thinking this move exists to save them.

**One question per message.** Asking several at once is bewildering, and it produces one answer to the easiest of them while the rest go unaddressed.

If a *fact* can be found in the filesystem, the repo, or a tool, look it up rather than asking. The *decisions* are the human's — put each one to them and wait. A grill that asks what the repo already answers is spending the human's attention on a question they shouldn't have to field.

Do not act on any of it until the human confirms shared understanding has been reached. The grill produces a transcript, not code and not a plan executed mid-interview.

A branch can end two ways once it has been asked: the human answers, and the answer plus your reasoning for having recommended it goes to `Settled`; or the human is not ready to decide, and the question goes to `Still open` along with what it blocks. If the human says a whole line of questioning no longer applies, that verdict is itself the answer — write it to `Settled` rather than treating the branch as never having been asked.

## Write as you go

Append each answer to the transcript file as it is given, in the human's own terms rather than your summary of them. Not at the end, when you are summarising and will smooth what was said into something more agreeable. This mirrors the rule already in the `create-tickets` move, and it is the reason the transcript is worth reading cold: a later session gets what the human actually said, not what you thought they meant.

## The transcript

Write to `.cortex/<task>/grill-NN.md` when a task is named, or `.cortex/ideation/<effort>/grill-NN.md` when invoked from a map question. `NN` is zero-padded and increments from the highest existing file already in that folder.

```markdown
---
task: TT-06
grilled: 2026-08-05
---

# Grill — TT-06

## Settled

- **<question>** — <the answer, in their words>

## Still open

- <question the human deferred, and what it blocks>
```

When invoked from a map question there is no task, so replace `task:` with `map:` and `question:` — the map note's name and the question this resolves — matching the question frontmatter `/ideation` writes.

`Still open` is not a failure state. A question the human deliberately deferred is information a later assembly step needs; an empty `Still open` on a grill that ended early is a lie.

## Guardrails

- **Never answer your own question and record it as settled.** An agent that grills itself has broken the whole point of the move — the transcript exists because the human's own words were captured, not because a plausible-sounding answer was.
- **Never ask what the repo answers.** Look it up.
- **Never write a decision the human did not make.**
- **Never finish while a question you asked is unanswered.** Every question you put to the human lands in `Settled` or `Still open` before you stop — nothing is left hanging only in the conversation.
