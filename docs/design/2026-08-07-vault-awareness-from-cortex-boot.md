# Vault awareness from Cortex boot

*2026-08-07 — implemented. Raised by Ben while running `/foundation` on the TBL Staging WordPress repo, where the move stopped on a missing binding file even though Claude Cortex had already resolved the repo to its vault project earlier in the same session.*

## The problem

Every move that touches the vault gates on a per-repo file:

> If `docs/agents/issue-tracker.md` does not exist, stop and say so — this repo has not been bound to a vault project.
> — `skills/foundation/SKILL.md`

`create-tickets`, `create-tasks`, `build`, `qa`, and `ideation` carry the same dependency. The file names two things: the project's vault `Tasks/` folder, and the repo's `.cortex/` ticket path.

But the plugin already lists `cortex-vault` as a requirement, and describes it as the thing "for resolving a repo to its vault project" (`README.md:69`). That resolution genuinely happens — the `claude-cortex` session-start hook runs `hooks/lib/boot-context.py`, walks the working directory up to a registered repo, and injects a `<cortex-session>` block naming the vault path, the activation level, and the resolved project before the model reads the first user message. At L3 the project is fully resolved and in context.

So the binding is known and the plugin asks for it again in a file. Two consequences:

1. **A correctly-registered repo still fails the precondition.** Nothing about registering a repo with `cortex-register-repo` produces `docs/agents/issue-tracker.md`, so every repo needs a second, manual, hand-authored binding step that duplicates information Cortex already holds.
2. **The two bindings can disagree.** Nothing reconciles the file against what `find_project_by_cwd` returns. A repo moved between vault projects updates in one place and goes stale in the other, silently, and the moves trust the file.

## What is wanted

Cortex Code should take its vault binding from the Cortex boot context when one is available, and fall back to `docs/agents/issue-tracker.md` only when it is not.

## How the open questions were settled

- **Where the resolution reads from.** A four-step order, written the same way into every move: the `<cortex-session>` block already in context first, because boot has usually done the work and reading it is free; `find_project_by_cwd` from `cortex-vault` when there is no block, which covers the shell-less surfaces where the hook cannot run; `docs/agents/issue-tracker.md` last; and a stop if none of the three resolves. The move calls the tool itself only in the second case — nothing re-derives what boot already put in context.
- **What the file carried that boot does not: nothing.** Both paths follow by convention from a resolved project — tasks at `<project>/Tasks/`, tickets at `<repo root>/.cortex/` — which is what the model doc's own tree already showed. The file is redundant rather than load-bearing, and it survives as a fallback for repos that already have one, not as something anything produces.
- **On disagreement, stop.** A binding file naming a different project than boot resolved is surfaced with both named, and the human resolves it. This is the case the whole change exists to catch, so preferring either silently would have been the one outcome worse than the original bug.
- **The failure message points at `/cortex-register-repo`.** "This repo has not been registered with Cortex" rather than "has not been bound to a vault project," because registering is the step that actually establishes the binding and the old wording pointed at a file nobody was told to write.
- **Repo root and scan root are separated, in `/foundation` only.** The vault binding resolves from the repo root; platform detection runs where the theme actually lives. `/foundation` now says which directory it scanned as well as which platform branch it took, so the WordPress-inside-`wp-content` case stops silently taking the wrong branch. No other move needed this — they resolve a project and read `.cortex/`, neither of which cares where the theme sits.

## What was changed

All six moves repeated the precondition in their own words, so this was not one edit. The resolution rule is now written verbatim into each of them rather than factored into a shared file: every move in this plugin starts cold with its own file as the only input, so a reference another skill would have to also open buys nothing. The cost is that a future change to the rule is six edits again, which is the honest trade for keeping each move self-contained.

- `skills/foundation/SKILL.md` — resolution rule, scan-root separation, two guardrails reworded
- `skills/create-tickets/SKILL.md` — resolution rule, and the task read from the resolved folder
- `skills/create-tasks/SKILL.md` — resolution rule under `Where they are written`
- `skills/build/SKILL.md` — resolution rule replacing the hard stop on the missing file
- `skills/qa/SKILL.md` — resolution rule in `Read the ticket`
- `skills/ideation/SKILL.md` — resolution rule, with the no-repo-yet case named
- `README.md` — Requirements now asks for a registered repo, not a hand-authored file
