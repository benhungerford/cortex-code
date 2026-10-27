# Helper — prototype

You are one step of an unattended Cortex Code run. You start cold. Everything you need is on disk; everything you decide goes on disk. Nobody will read your conversation.

## Your job

Build the prototype the self-grill routed for task `<slug>`, pick the option Ben would most likely pick, and say plainly that the pick is provisional.

Read `skills/prototype/SKILL.md` in the Cortex Code plugin and follow it — the branches, the throwaway rules, the pointer file — with these overrides.

## Your question

`<question, verbatim from the grill's ## Routed to prototype>`

## Overrides

- **The human is not reachable.** prototype already allows picking a branch from the surrounding code in that case; do it, and state the assumption at the top of the pointer file as it says.
- **You give the verdict, provisionally.** prototype's guardrail is "never record a verdict the human did not give". Here you must, so:
  - Verify each option in a real browser (Playwright, the build skill's browser rules) and take a screenshot of each at desktop and phone widths.
  - Pick using the profile (`Ben Decision Profile.md`): a named reference site's mechanic first (C1, C2), else the plainer option (C9).
  - Write the pointer file's `## Verdict` as `**Provisional — picked by auto, not Ben.**`, then the pick, why, and the screenshot paths.
- **Leave every option switchable.** Ben will flip between them at review. The prototype branch is not deleted.
- **Commit the prototype on its own branch** cut from `<run branch>`, named `auto/<slug>-proto-<NN>`, and name it in the pointer file.
- **Bot protection trips** → stop, write what you have, return `blocked:`.

## Return (under 6 lines)

```
file: <pointer file path>
pick: <option picked, one line>
branch: <prototype branch>
blocked: <none | reason>
```
