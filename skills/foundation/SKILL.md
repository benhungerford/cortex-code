---
name: foundation
description: Scan the repo and write the four standing-fact files under .cortex/foundation/ that every ticket would otherwise re-derive. Usage:/foundation
disable-model-invocation: true
---

# foundation

`/create-tickets` researches the repo on every task. Which snippet renders a button, what the class convention is, which app owns the price element — most of what it finds on task nine is the same as what it found on task one, and it is paid for nine times. `/foundation` pays for it once and writes down what it found, so later moves read a file instead of re-deriving the repo.

## Inputs

`/foundation` takes no argument.

**Resolving the vault project.** Prefer what Cortex boot already resolved — the `<cortex-session>` block in context names the vault path and the active project, and at L3 it is fully resolved before the first message. With no block, call `find_project_by_cwd` from `cortex-vault`. Read `docs/agents/issue-tracker.md` only when neither resolves. From a resolved project both paths follow by convention: tasks are `<project>/Tasks/`, tickets are `<repo root>/.cortex/`. If a binding file names a different project than boot resolved, stop and say both — silently preferring either is how a stale binding gets worse instead of better. If nothing resolves, stop and say this repo has not been registered with Cortex; `/cortex-register-repo` is the move that binds it.

**The scan root is not always the repo root.** The vault binding belongs to the checkout as a whole, and it resolves from the repo root. What you scan may sit well below it — a WordPress theme inside a `wp-content` tree has its git root several levels above `themes/<theme>/`, and platform detection run at the git root finds no WordPress markers and takes the wrong branch. Detect the platform where the theme actually lives, and say which directory you scanned as well as which branch you took.

Then detect the platform before scanning anything else. A `config/settings_schema.json` alongside `layout/theme.liquid` means Shopify. A `style.css` carrying a theme header, or a `theme.json`, means WordPress. State which branch you took and what you matched on before doing any further reading — the rest of the scan depends on it, and a wrong guess here produces a shaped-for-the-wrong-platform file that looks complete and is not.

## Preconditions

Foundation reads a repo that has something in it. On a new Horizon build there is nothing to scan on day one — no sections, no snippets, no tokens beyond the scaffold — so this move runs after bootstrap, not before it. If the repo is effectively empty, say so and stop. Do not write four near-empty files just to have written them; a later move that trusts `components.md` and finds nothing there because there was nothing to find is fine, but a later move that trusts it and finds nothing there because the scan gave up early is a silent gap, and nobody will know to double-check.

## The four files

| File | Holds |
|---|---|
| `design-system.md` | Tokens with their definition sites, declared-but-dead among them, type scale, spacing, breakpoints, class convention and its counter-examples |
| `components.md` | Every reusable snippet and section: path, actual render signature, available variants |
| `platform.md` | Template and section architecture, custom-element conventions, and the events the theme emits |
| `concerns.md` | Third-party app surface, vendored CSS, do-not-touch areas, half-finished attempts |

Write all four to `.cortex/foundation/design-system.md`, `.cortex/foundation/components.md`, `.cortex/foundation/platform.md`, and `.cortex/foundation/concerns.md`. These four paths are a contract other moves read directly — do not rename them, nest them further, or split one into two.

## Provenance

Every one of the four files opens with this frontmatter:

```yaml
---
generated: 2026-08-05
commit: a1b2c3d
platform: shopify
scanned:
  - assets/*.css
  - snippets/
  - sections/
---
```

`commit` is the short SHA of `HEAD` at generation time — get it fresh for each file, in case the scan spans a commit boundary. `scanned` is the glob list you actually walked for that file, not the list you intended to walk. A later staleness check intersects changed paths against this list to decide whether a file is worth re-running, and an aspirational entry — a path you meant to cover but didn't reach — makes that check lie: it will wave through a change that should have flagged the file as stale.

## Evidence rules

Every claim carries a `file:line` citation. Anything inferred rather than directly observed is marked `(inferred)` and says what it was inferred from. This is the same discipline `qa` applies when it refuses to tick an item it did not see happen — a document later moves trust without re-checking cannot afford to be generous with itself. If you cannot point at the line that supports a claim, the claim does not go in the file. A shorter file that is entirely true is worth more than a fuller one that is half guessed.

## What each file must contain

**`design-system.md`** — every design token, where it is defined, and whether anything still uses it. A token declared in the tokens file but never referenced anywhere else is declared-but-dead, and it is worth naming as such, because a build session that reaches for it in good faith is about to add a fifth definition of the same spacing value instead of removing the fourth. Record the type scale, the spacing scale, the breakpoints, and the class-naming convention in force — then record where the repo breaks its own convention, because those counter-examples are exactly the files a build is likely to copy from next.

**`components.md`** — every reusable snippet and section, its path, and its variants. The render signature must be the actual one read out of the snippet's `{{ }}` and `{% liquid %}` parameter usage, not a guess from the file's name — write it as it would be called, `{% render 'button', label: ..., url: ..., style: ... %}`, with every parameter the snippet actually reads. The entire point of this file is that a build reaches for the existing snippet instead of hand-rolling an `<a class="btn">`, and a signature guessed from `button.liquid` sounding like it takes a label is worse than no entry at all, because it will be trusted and it will be wrong.

**`platform.md`** — template and section architecture, custom-element conventions, and the events the theme emits, named exactly as they are dispatched. This is what a build listens to instead of polling a DOM node for a change nobody promised to signal. If a cart drawer dispatches `cart:updated` on `document`, that is the line this file exists to hold.

**`concerns.md`** — the third-party app surface: which app injects markup or styles, and where. This is not a lesser file than the other three. On the pilot, a subscription app rendered its `selling_plan` input inside the product form, and finding that one fact before any code was written changed the architecture of the whole feature — a sticky add-to-cart bar with its own form would have silently converted subscribers into one-time buyers, looked completely correct, and shipped. That is what this file is for: catching the thing a build would otherwise discover the expensive way, mid-implementation, or not at all. Also record vendored CSS, areas marked or understood as do-not-touch, and any half-finished attempt at the thing you are looking at — a dead feature flag, an abandoned second cart drawer, a commented-out include. A build that does not know an attempt already failed here is liable to repeat it.

## Shopify

Read `config/settings_schema.json` for the settings surface, `assets/*.css` for tokens and the class convention, `snippets/` and `sections/` for components and their signatures, `templates/*.json` for the section-to-template wiring, and the theme's JS entry point for custom elements and emitted events. A Shopify-shaped `components.md` — snippet paths, `{% render %}` signatures — describes a Liquid repo. Do not produce one of these for a WordPress repo and call it partial; it is not partial, it is the wrong file, because nothing in it corresponds to anything WordPress actually has.

## WordPress

Read `theme.json` for tokens and supported settings, `style.css` for the theme header and any hand-rolled custom properties, `functions.php` for enqueued stylesheets and registered blocks or patterns, and the block or pattern directory for components and their attributes. The four files describe different objects on this platform than they do on Shopify — there is no `settings_schema.json` and no sections, there is a block library and a `theme.json`. Write what this repo actually has, in this repo's own terms, rather than reaching for the Shopify vocabulary because it is what you scanned last time.

## Guardrails

- Never write a claim you cannot cite with `file:line`.
- Never guess a render signature from a snippet's or block's name. Read the parameters it actually uses.
- Never overwrite a file with fewer facts than it already had. A re-run that loses detail is a regression, not a refresh — later builds append to these files as they go, so re-runs of `/foundation` itself are additive unless the thing a section describes has genuinely changed underneath it.
- Never scan a repo that resolves to no vault project. Point at `/cortex-register-repo` rather than at a missing file.
- Never let a platform guess stand unstated. Say what you matched on, and which directory you matched it in, before you scan.
