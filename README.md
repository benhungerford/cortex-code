# Cortex Code

The build half of a client workflow that runs on tickets stored in an Obsidian vault.

Cortex owns the vault. Cortex Code owns the repo. The ticket is the handoff.

## What this is for

Shopify Liquid and WordPress PHP theme work, where there is no test runner and no type checker, so red-green is unavailable and the browser is the feedback loop.

This plugin is deliberately small. It ships only what upstream cannot do:

| Move | Covered by |
|---|---|
| Brief | [`mattpocock-skills`](https://github.com/mattpocock/skills) — `grill-me` → `to-spec` → `to-tickets` |
| Per-repo setup | `setup-matt-pocock-skills` |
| **Build** | **this plugin** |
| **Sign off** | **this plugin** *(not written yet)* |

Upstream's `implement` is eight lines that delegate to `tdd`, typechecking, and a test suite. In a theme repo, none of those exist. Upstream's `qa` is deprecated, and was conversational bug intake rather than sign-off.

## Requirements

- [`mattpocock-skills`](https://github.com/mattpocock/skills) installed
- The [`cortex-vault`](https://github.com/benhungerford/claude-cortex) MCP server, for resolving a repo to its vault project
- A `docs/agents/issue-tracker.md` in each repo, pointing at that project's ticket folder. `setup-matt-pocock-skills` writes this when you choose the **Other** tracker option and describe the vault layout.

## Usage

```
/build TT-06
```

The ticket ID is the only argument — repo path, vault project, ticket folder, and stage are all derived.

Each move ends by clearing context and printing the next command. A move boundary is a context boundary: every move starts cold with the ticket as its only input, which is what forces the ticket to be complete.

## The ticket is a billing record

Its frontmatter feeds an invoice roll-up. That drives the guardrails:

- Never delete a ticket — cancelled work is closed in place with the reason in the Receipt
- Never move a ticket to `done` — `review` is as far as an agent goes
- Never tick a criterion — an agent that ticks its own work ticks everything
- Never invent hours; propose them and invite correction
- Never rewrite Intent or Decisions on a ticket in flight

## Why the browser

On the first ticket run through this workflow, browser verification caught four bugs that read as correct code:

- An `IntersectionObserver` that never fires on a jump-scroll, because IO only fires on transitions
- A sticky bar showing $22.00 while the cart charged $18.70, because a subscription app renders its own price and never updates the theme's
- A one-shot price sync that raced the same app's asynchronous property write, failing intermittently
- A bar drawing on top of a cart drawer with a `z-index` eleven times higher, because it sat in a different stacking context

None of these break a test. All of them break a customer.

## Status

`0.1.0` — `build` only. `qa` is next.

MIT.
