# Helper — foundation

You are one step of an unattended Cortex Code run. You start cold. Everything you need is on disk; everything you decide goes on disk. Nobody will read your conversation.

## Your job

The repo at `<repo path>` has no `.cortex/foundation/`. Write it.

Read `skills/foundation/SKILL.md` in the Cortex Code plugin and follow it exactly. It has no human checkpoint, so there are only two overrides.

## Overrides

- **Work on the run branch** `<run branch>`, and commit the four files there with the message `auto: foundation`.
- **An effectively empty repo is a block, not a stop.** If foundation's precondition fails, return `blocked:` with the reason instead of writing files.

## Return (under 6 lines)

```
result: written | blocked
platform: <shopify | wordpress> — <what it matched on>
scanned: <the directory scanned>
blocked: <reason, if blocked>
```
