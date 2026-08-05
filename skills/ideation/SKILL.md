---
name: ideation
description: Chart a foggy effort as a map of questions in the vault, then resolve them one per session until the way to the destination is clear. Usage:/ideation
disable-model-invocation: true
---

# ideation

A loose idea has arrived, too big for one session and wrapped in fog: the way to the destination is not visible yet. Ideation charts that way as a map, then works its questions one at a time until nothing is left to decide. It is about finding the way, not charging at the destination.

## Vocabulary

Say the collision plainly, because a reader arriving from wayfinding will expect the other word. These are **questions**, not tickets. A question resolves into a decision and then closes. A ticket, in this plugin, is a build session: append-only, and it does not close until the work ships. Nothing below uses "ticket" to mean a map child, and nothing should.

## Plan, don't do

Ideation produces decisions, not deliverables. Each question resolves a decision, and the map is done when nothing is left to decide before someone goes and builds. The pull to just do the work — to fix the thing instead of deciding how it should work — is the signal you have reached the edge of the map, not an invitation to keep going. The response to that pull is `/create-tasks`, not building.

## The map

A note in the active vault project, resolved through `docs/agents/issue-tracker.md`. It is an index, not a store: a decision lives in exactly one place, its question, and the map gists and links rather than restating what the question already says. The body, verbatim:

```markdown
## Destination

<what reaching the end of this map looks like — the spec, decision, or change
this effort is finding its way to. One or two lines; every session orients to
it before choosing a question.>

## Notes

<domain; skills every session should consult; standing preferences>

## Decisions so far

- [[<closed question>]] — <one-line gist of the answer>

## Not yet specified

<in-scope fog that cannot be phrased sharply yet; graduates as the frontier advances>

## Out of scope

<work ruled beyond the destination; closed, never graduates>
```

## Questions

Child notes of the map. Each carries a type — `research`, `prototype`, `grilling`, or `task` — and a `blocked_by:` frontmatter list, since Obsidian has no native dependency edge to lean on. The frontmatter, verbatim:

```yaml
---
type: question
map: "<map note name>"
question_type: grilling
blocked_by: []
status: open
---
```

The **frontier** is the set of open questions with no unclosed blocker. There is no claim or assignee mechanic here. Upstream assigns a question to a developer before work starts so concurrent sessions don't collide on the same one — that solves a coordination problem this workflow does not have, because it is one person, one session at a time. Nothing is ever claimed because nothing is ever contended. An open question with no unclosed blocker is takeable, and that is the whole rule; if you find yourself adding a claim field back, the problem it would solve doesn't exist here.

## Question types

Four, and the type names which move resolves the question:

- **research** — a fact a decision is waiting on, resolved by `/research` as a background agent. The only type that may run in parallel with others, since following a source back to itself doesn't need the human's attention while it happens.
- **prototype** — resolved by `/prototype`, for whenever "how should it look" or "how should it behave" is the actual question.
- **grilling** — resolved by `/grill-me`. The default case: a decision only the human can make, walked one question at a time.
- **task** — manual work that has to happen before a decision can be made at all: signing up for a service so its API can be judged, provisioning access, getting the client to send the promised assets. There is nothing to decide here, but the discussion is blocked until it's done. It's the one type that *does* rather than decides, and it earns its place on the map by unblocking a decision that would otherwise stall. It resolves when the work is done, and its answer records what was done and any facts later questions depend on.

## Fog of war

The map is deliberately incomplete. Beyond the live questions is the fog: decisions you can already tell are coming but cannot yet pin down. Resolving a question clears the fog immediately ahead of it, the way a decision made now narrows what the next one even has to consider.

The test for fog-versus-question is whether you can *state* the question precisely right now, not whether you can answer it. Sharp enough to phrase means it's a question — even if it's blocked and sits off the frontier. Not sharp enough to phrase means it stays in `Not yet specified`. Do not pre-slice the fog into question-sized pieces before it's sharp; a map full of vaguely-worded questions is worse than an honest patch of fog, because it looks like progress that hasn't happened.

## Out of scope

Fog gathers only toward the destination, so work that sits beyond the destination is out of scope, not fog. When resolving a question reveals that it actually sits past the destination, close it and leave one line in `Out of scope` with the gist and the reason it doesn't belong. It stays out of `Decisions so far`, which records the route actually walked toward the destination, not the detours ruled out along the way.

## Where artifacts live

`.cortex/ideation/<effort>/`. The three capture moves already know this — `grill-me`, `research`, and `prototype` each write their own files there when invoked from a map question, and this file does not restate their naming patterns.

Ideation frequently runs the week a project is won, before a repo exists to hold a `.cortex/` folder at all. This is a normal case, not an edge one — a client hands over a loose idea long before there's anything to check out. When there is no repo yet, the map holds those artifacts inline instead, and they move to `.cortex/ideation/<effort>/` once a repo exists to receive them. Blocking ideation on a missing repo would just push the work back into a chat window that dies with the session, which is the exact failure this move exists to end.

## Charting a map

1. **Name the destination.** Grill to pin down what this map is finding its way to. The destination fixes the scope, so it gets settled before anything else — every question added later is judged against it.
2. **Map the frontier.** Grill again, breadth-first, fanning out across the space rather than going deep on whichever thread looks most interesting. If this surfaces no fog at all, the way is already clear and the effort fits in one session: say so and stop, because it doesn't need a map.
3. **Create the map** with `Destination` and `Notes` filled in, `Decisions so far` empty, and the fog sketched into `Not yet specified`.
4. **Create the questions** you can specify now, then wire `blocked_by` in a second pass once every question that depends on another exists to be pointed at.
5. **Fire the research questions** as background agents, in parallel.
6. **Stop.** Charting is one session's work and resolves nothing by hand — that's what working the map is for.

## Working a map

1. Load the map, not every question body — the map is the index for a reason.
2. Choose a question: the one named, or the first on the frontier.
3. Resolve it with the move its type names, zooming into related or closed questions on demand rather than loading them all up front.
4. Record the resolution on the question itself, close it, and append the one-line gist to `Decisions so far`.
5. Add any newly surfaced questions, and graduate any fog the answer made specifiable — clearing each graduated patch out of `Not yet specified` so it lives only as its new question, not in both places. If the answer reveals that a question actually sits beyond the destination, rule it out of scope rather than resolving it as if it belonged.

One question per session, research excepted.

## Handoff

When the map has no open questions, print:

```
/clear
```
```
/create-tasks
```

## Guardrails

- **Never resolve more than one question per session**, research excepted — research questions may run several at once as background agents.
- **Never answer a grilling or prototype question on the human's behalf.** Those decisions are the human's; a question resolved by guessing what they'd say defeats the reason the map exists.
- **Never restate a decision on the map that its question already holds.** The map gists and links; the question is where the decision actually lives.
- **Never write a task.** That's `/create-tasks`, and only with sign-off — ideation stops at `Decisions so far`.
- **Never let fog past the destination sit in `Not yet specified`.** If it's beyond the destination, it belongs in `Out of scope`, not waiting to graduate into a question that will never be asked.
