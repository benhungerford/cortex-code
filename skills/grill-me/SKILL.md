---
name: grill-me
description: A relentless interview that works the design tree in rounds, asking the whole frontier at once and writing the answers down as they come. Usage:/grill-me TT-06
disable-model-invocation: true
---

# grill-me

A relentless interview that reaches shared understanding on a plan, decision, or idea, and writes the result somewhere a cold session can read it.

This is one of three capture moves — alongside `research` and `prototype` — invoked from an ideation session or directly against a task. All three write to the same place and are read the same way later: a later assembly step opens every `grill-*.md` in the folder cold, with no memory of this conversation. What is not in the file did not happen. That is why the discipline below matters more here than in most skills — the whole value of a grill is that the human's own answers ended up on disk, not a paraphrase of them.

## Inputs

`/grill-me <task>` writes to `.cortex/<task>/`. `/grill-me` with no argument, invoked inside an ideation session, writes to `.cortex/ideation/<effort>/`, taking the effort slug from the map rather than deriving one here. With neither a task nor an ideation session to place it in, ask which before starting. Do not guess a home — a transcript written to the wrong folder is a transcript no later move will find.

## How to grill

Map the work as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask *now* without guessing at answers you have not heard yet. Ask the whole frontier in one round, then wait. A question whose answer depends on another question still open in this round belongs to a *later* round, not this one.

Format each question like this:

```
❓ **Q1** - **<question title>**: <question body, which may run to several paragraphs and may lay out choices>

➡️ <your recommended answer>
```

Every question carries a recommended answer and the reason for it. A grill without recommendations makes the human do the thinking this move exists to save them.

Each round of answers reshapes the tree — settled decisions push the frontier outward and unblock the questions that depended on them. Recompute the frontier and ask the next round.

The session is done when the frontier is empty: every branch of the tree visited, nothing left silently assumed. Do not act on any of it until the human confirms shared understanding has been reached. The grill produces a transcript, not code and not a plan executed mid-interview.

## Finding facts is your job, not theirs

When a frontier question turns on a fact in this repo, or one reachable by tool, dispatch a sub-agent to find it rather than asking. Do not block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report — ask the rest of the frontier now.

A fact that needs a primary source — vendor documentation, platform behaviour, anything a claim would have to be cited to — belongs to `/research`, not here. Route it there and let the question it blocks wait for the findings file. A source chased down mid-grill lands in a transcript uncited, and `/create-tickets` is told a cited finding is among the most valuable things in the capture folder.

The *decisions* are the human's. Put each one to them and wait. A grill that asks what the repo already answers is spending the human's attention on a question they should not have to field.

A question ends two ways once it has been asked: the human answers, and the answer plus your reasoning for having recommended it goes to `Settled`; or the human is not ready to decide, and it goes to `Still open` along with what it blocks. If the human says a whole line of questioning no longer applies, that verdict is itself the answer — write it to `Settled` rather than treating the branch as never having been asked.

## Write as you go

Append each round to the transcript as that round closes, in the human's own terms rather than your summary of them. Not at the end, when you are summarising and will smooth what was said into something more agreeable. This mirrors the rule already in the `create-tickets` move, and it is the reason the transcript is worth reading cold: a later session gets what the human actually said, not what you thought they meant.

Batching makes this matter more, not less. A round of eight answers is where paraphrase creeps in.

## The transcript

Write to `.cortex/<task>/grill-NN.md` when a task is named, or `.cortex/ideation/<effort>/grill-NN.md` when invoked from a map question. `NN` is zero-padded and increments from the highest existing file already in that folder.

```markdown
---
task: TT-06
grilled: 2026-08-05
---

# Grill — TT-06

## Settled

### Round 1

- **<question title>** — <the answer, in their words>

### Round 2

- **<question title>** — <the answer, in their words>

## Still open

- <question the human deferred, and what it blocks>
```

When invoked from a map question there is no task, so replace `task:` with `map:` and `question:` — `map:` matching the question note's own `map:` key, and `question:` naming the question note.

Rounds are kept because they record the order decisions were actually made in, which is what a later session needs to tell a settled foundation from something built on top of it. `Still open` is not grouped by round — a deferred question belongs to the whole grill, not the round that happened to surface it.

`Still open` is not a failure state. A question the human deliberately deferred is information a later assembly step needs; an empty `Still open` on a grill that ended early is a lie.

## Guardrails

- **Never answer your own question and record it as settled.** An agent that grills itself has broken the whole point of the move — the transcript exists because the human's own words were captured, not because a plausible-sounding answer was.
- **Never ask a question whose prerequisite is still open in this round.** That is guessing at an answer you have not heard, and it is what the rounds exist to prevent.
- **Never ask what the repo answers.** Dispatch a sub-agent and look it up.
- **Never chase a primary source mid-grill.** That is `/research`, and the difference is a citation.
- **Never write a decision the human did not make.**
- **Never finish while a question you asked is unanswered.** Every question you put to the human lands in `Settled` or `Still open` before you stop — nothing is left hanging only in the conversation.
- **Never stop with the frontier non-empty** unless the human ends the session. An unvisited branch is a decision made silently.
