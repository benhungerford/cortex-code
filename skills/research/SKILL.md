---
name: research
description: Investigate a question against primary sources in a background agent and capture the findings as a cited file. Usage:/research TT-06 <question>
disable-model-invocation: true
---

# research

Investigate a question whose answer lives outside the repo — in platform documentation, a vendor's own docs, or a specification — and leave the answer somewhere a cold session can read it.

This is one of three capture moves — alongside `grill-me` and `prototype` — invoked from an ideation session or directly against a task. All three write to the same place and are read the same way later: a later assembly step opens every `research-*.md` in the folder cold, with no memory of this conversation. `/foundation` covers standing facts about this repo; `research` covers facts that live outside it — what a platform guarantees, what a vendor's app actually does, what a specification requires. Do not use this move to re-derive something `/foundation` already answers.

## Inputs

`/research <task> <question>` writes to `.cortex/<task>/`. `/research <question>`, invoked inside an ideation session, writes to `.cortex/ideation/<effort>/`, taking the effort slug from the map rather than deriving one here. Same two-home rule as `grill-me`: with neither a task nor an ideation session to place it in, ask which before starting rather than guessing. A findings file written to the wrong folder is a findings file no later move will find.

## Spin up a background agent

Delegate the reading to a background agent so the calling session keeps working while it runs. Say plainly that this is happening — the human should not expect an immediate answer in the conversation, and should expect to be told when the finding lands. Research questions, unlike a grill, are allowed to run several at once: nothing about following a source back to itself requires the human's attention while it happens.

## Primary sources only

Every claim in a findings file traces back to the source that owns it: official documentation, the theme's own source code, a specification, or a first-party API — never a secondary write-up of any of those. A blog post explaining how a Shopify object behaves is not the source; the Shopify object's own documentation is. A forum thread describing what an app does is not the source; the app vendor's documentation, or the app's own code where it is vendored into the theme, is.

For this workflow specifically, the sources on hand are:

- **Shopify platform questions** — the Shopify dev MCP server.
- **This theme's own behaviour** — its source, read directly rather than recalled.
- **Third-party app behaviour** — the app vendor's own documentation, not a review or a support-forum answer describing it secondhand.
- **WordPress questions** — WordPress core documentation or the block-editor documentation, matched to the theme's actual WordPress version rather than assumed current.

If the question at hand does not fit one of these, find the source that owns the answer before writing anything down. Do not settle for the closest thing that turned up in a search.

## Cite everything

One file, one question, and every claim in it carries the source that backs it — a URL, or a `file:line` when the source is code in this repo or a vendored dependency. A claim without a citation is not a finding; it is a guess wearing a finding's formatting, and it is one the assembling move has to re-derive from scratch, which is the entire cost this move exists to remove. If you cannot name where a claim came from, it does not go in the file.

## The findings file

Write to `.cortex/<task>/research-NN-<slug>.md`, or `.cortex/ideation/<effort>/research-NN-<slug>.md` when invoked from a map question. `NN` is zero-padded and increments from the highest existing file already in that folder — the same numbering discipline `grill-me` uses for `grill-NN.md`. `<slug>` is a short, hyphenated summary of the question, not the whole thing.

```markdown
---
task: TT-06
question: Does the Loop widget expose a selling_plan change event?
researched: 2026-08-05
---

# Research — <question>

## Answer

<the short answer, first>

## Evidence

- <claim> — <https://source-that-owns-it>

## What this rules out

<the options this closes, and why>
```

When invoked from a map question there is no task, so replace `task:` with `map:` and `question:` — `map:` matching the question note's own `map:` key, and `question:` naming the question note.

`What this rules out` is the section that earns the file. An answer that does not change what gets built was not worth researching, and writing down what it closes is what forces that check — an answer with nothing to rule out is a sign the question was not sharp enough to need a background agent in the first place.

## Guardrails

- **Never cite a blog post, forum answer, or other secondary write-up standing in for the specification it describes.** Follow it to the specification and cite that instead.
- **Never report a fact you could not follow to its owning source.** If the trail runs out, say so in the answer rather than presenting the last thing you read as settled.
- **Never answer from memory when a source exists to check against.** What you recall about a platform's behaviour may be stale or apply to a different version than the one this theme runs.
- **Say plainly when the sources do not settle the question**, rather than producing a confident file. An honest "the docs don't say" is worth more to the assembling move than a guess dressed as a finding.
