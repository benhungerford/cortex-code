---
name: prototype
description: Build throwaway code that answers a design or behaviour question — UI variants on one route, or real theme state driven in a browser. Usage:/prototype TT-06
disable-model-invocation: true
---

# prototype

Throwaway code that answers a question. The question decides the shape.

This is the last of three capture moves — alongside `grill-me` and `research` — invoked from an ideation session or directly against a task. The other two leave words on disk: a transcript, a cited answer. This one leaves code, and that changes what the write target has to hold. The real output is a branch, not a file. `.cortex/` gets only a pointer to it, recording the question, the verdict, and where the code lives, so a later assembly step can find the branch without any memory of this session.

## Inputs

`/prototype <task> <question>` writes its pointer file to `.cortex/<task>/`. `/prototype <question>`, invoked inside an ideation session, writes to `.cortex/ideation/<effort>/`. Same rule as its siblings: with neither a task nor an ideation session to place it in, ask which before starting rather than guessing. A pointer file in the wrong folder points nowhere a later move will look, and a prototype without a pointer is a branch nobody will ever find again.

## Pick a branch

Two, and getting it wrong wastes the whole prototype:

- *What should this look like?* → the **UI** branch.
- *Does this behave right?* → the **behaviour** branch.

If the question is genuinely ambiguous and the human is not reachable, pick from the surrounding code — a template or section means UI, a script or state interaction means behaviour — and state the assumption at the top of the prototype.

## UI branch

Several radically different takes on one throwaway template, switchable by a query parameter, with a floating switcher so the human can flip between them without editing a URL by hand. Follow whatever routing or template convention the theme already uses; do not invent a new top-level structure. Radically different is the requirement — three variations on one idea answer nothing.

## Behaviour branch

A throwaway route that exercises the real theme JS in a real browser: cart drawer, variant selection, price sync, whatever the question is about. Render the full relevant state on screen after every action so the human can see what changed.

This departs from the conventional logic prototype, which builds an interactive terminal application driving a state machine. There is no runtime for that in a theme repo. More importantly, the browser is this workflow's entire feedback loop, and a terminal state machine cannot reproduce what only a browser produces. On the pilot, four bugs that read as correct code were caught only there: an `IntersectionObserver` that never fired on a jump-scroll, a sticky bar showing a price the cart did not charge, a one-shot sync racing an app's asynchronous property write, and a stacking-context collision that a `z-index` comparison could not see. None of those are visible in a REPL — they only exist as frames that fail to paint, requests the UI misreports, and elements stacked wrong on a rendered page. A logic prototype that does not run in a browser cannot answer the questions that actually bite here; it can only answer the ones a terminal happens to be able to see, which on this workflow is rarely the question that was asked.

## Rules for both branches

1. Throwaway from day one and clearly marked as such. Locate it next to what it prototypes so the context is obvious, and name it so a casual reader can see it is not production.
2. One command to run it. The human must be able to start it without thinking.
3. No persistence. State lives in memory.
4. No polish. No tests, no error handling beyond what makes it runnable, no abstractions.
5. Surface the state. Print or render everything relevant after every action or variant switch.
6. Capture it when done. Fold the validated decision into the real work, commit the prototype to a throwaway branch off the default branch, and leave the pointer file.

## The pointer file

The code is the real output, and it never reaches the default branch. The file below is only a pointer to where that code lives — it does not stand in for the branch, and it is not itself the deliverable the way a `grill-me` transcript or a `research` finding is.

Write to `.cortex/<task>/prototype-NN-<slug>.md`, or `.cortex/ideation/<effort>/prototype-NN-<slug>.md` when invoked from a map question. `NN` is zero-padded and increments from the highest existing file already in that folder — the same numbering discipline `grill-me` and `research` use for their own files. `<slug>` is a short, hyphenated summary of the question, not the whole thing.

```markdown
---
task: TT-06
prototyped: 2026-08-05
branch: prototype/sticky-bar-variants
---

# Prototype — <question>

## Verdict

<what was decided, and what the human said when they saw it>

## What it ruled out

<the options this closed>
```

`## Verdict` records a reaction, not an inference — the entire point of a prototype is that a human looked at running code and said something back, and that something is what belongs here, in their words. `## What it ruled out` carries the same discipline as `research`'s equivalent section: the options this closed are what makes the branch worth having sat on for however long it took to build. A verdict with nothing ruled out is a sign the prototype answered a question nobody was actually undecided about.

## Guardrails

- **Never leave prototype code on the default branch.** It is throwaway by definition, and the default branch is not a place throwaway code sits "for now."
- **Never let a prototype grow error handling or tests.** The moment it needs those, it has stopped being a question and started being a feature — and features go through `/create-tickets` and `/build`, not this move.
- **Never record a verdict the human did not give.** The UI and behaviour branches both exist to be reacted to; a prototype nobody looked at has no verdict, and a pointer file written before anyone saw the code is a guess wearing a verdict's formatting.
- **Never keep a prototype alive as production code because it worked.** Working is not the same as built to last. Fold the validated decision into the real work instead of promoting the shortcut itself.
