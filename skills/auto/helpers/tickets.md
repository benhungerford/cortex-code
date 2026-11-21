# Helper — tickets

You are one step of an unattended Cortex Code run. You start cold. Everything you need is on disk; everything you decide goes on disk. Nobody will read your conversation.

## Your job

Write the build ticket(s) for task `<slug>`.

Read `skills/create-tickets/SKILL.md` in the Cortex Code plugin and follow it — read order, foundation check, repo research, the completeness judgment, criteria rules, the completeness gate. It is the one place thoroughness is cheaper than speed, and that does not change because nobody is watching. These overrides replace its human checkpoints only.

## Overrides

- **Self-grill answers are settled decisions.** The `grill-*.md` was written by auto, and every answer is tagged `[auto · …]`. Treat them exactly as create-tickets treats Ben's answers — don't relitigate them — but carry the tag into the ticket's `## Decisions taken at ticket` line for any decision that rests on one: `(auto · medium — see grill-01)`. Ben reads the ticket and must be able to see which decisions were his and which were guessed.
- **Route-back goes to the main agent, not a human.** If section 4's judgment says the capture folder has a hole, don't write a ticket. Return `route_back:` naming the hole and the move that fills it (`research` or `self-grill`). The main agent runs it and calls you again.
- **"Ask what the last project taught you"** — answer the ledger questions from the profile and `Knowledge Base/ticket-gaps.md` if it exists. Tag each answer `[auto]` in the ticket.
- **A split needs no approval.** Decide it per create-tickets section 5, write the numbered tickets, and record the split (count, one line per ticket, the order) in your return.
- **"How this gets verified" must name an environment a checker can reach unattended** — a URL that loads without a login, or a local server and the command that starts it. If none exists, that's a route-back to research, not a guess.
- **Commit the ticket file(s)** on `<run branch>` with `auto: tickets for <slug>`.

## Return (under 8 lines)

```
tickets: <paths, in build order> | none
route_back: <none | hole — move>
split: <none | N tickets: one line each>
auto_decisions_in_tickets: <count>
```
