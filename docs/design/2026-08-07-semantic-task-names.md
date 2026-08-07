# Semantic task names

*2026-08-07 — implemented. Raised by Ben: tasks should be named for what they are, not numbered. The "Why Regenerative" page should be a task called `Why Regenerative`.*

## The problem

Every move in the plugin demonstrates the task argument as an ID:

```
/create-tickets TT-06
/grill-me TT-06
/build TT-06
/qa TT-06
```

And `create-tasks` writes that ID into the frontmatter it calls verbatim, twice — once as the `task:` key and once inside the `cortex:` path:

```yaml
task: TT-06
cortex: .cortex/TT-06/
```

So a task called *Why Regenerative* becomes `TT-06`, and the name of the thing being built survives only in the note's title and the scope line.

Two reasons that is wrong.

**The ID carries no information.** `TT-06` tells you nothing about what it is. Every read of it — in a folder listing, in a `task:` key inside a grill transcript, in a handoff line printed at the end of a move — requires a lookup to recover the meaning that a name would have carried for free. The plugin's whole design premise is that each move starts cold with its file as the only input, which makes every un-self-describing identifier a cost paid on every cold start.

**Tasks pulled from Monday arrive named.** Monday items have names, not numbers. A task pulled straight from a board is already called *Why Regenerative*, and minting a `TT-06` to sit in front of it invents a second identity for a thing that already had one — and one that nothing on the Monday side will ever recognize.

## The model already does this

The task and ticket model shows both shapes in the same tree, and only one of them has an ID:

```
Vault
  Work/<cat>/<client>/<project>/Tasks/
    AC-01 — Currency selector flag bloat.md
    Homepage.md

Repo
  .cortex/
    AC-01/
      ticket.md
    homepage/
      01-hero.md
```

`Homepage` has no ID, and its capture folder is `homepage/`. Its neighbour has `AC-01` bolted to the front of a name that was already doing the work. The naming was never consistent — this decision picks the half that was already there and drops the other.

## What is wanted

Tasks are named for what they are. The ID is dropped, not made optional — an identifier scheme that applies to some tasks and not others is the inconsistency above, preserved.

## What makes this safe

The ID's one load-bearing job is being a stable, collision-free filesystem key: `.cortex/<task>/` is a real path, and `task:` in every grill, research, prototype, and ticket file is a join key pointing at it. A display title cannot do that job, because a display title can be reworded.

A slug can, and the mechanism for it is already written:

> `cortex:` is the pointer to the capture folder that `/create-tickets` will write into. Write it now, before that folder exists — the pointer is the contract, and the folder catches up to it.
> — `skills/create-tasks/SKILL.md`

So: **the slug is the key, the title is display.** `create-tasks` derives the slug from the approved title once, at creation, and writes it into `cortex:`. Every downstream move resolves the capture folder by reading that frontmatter value — never by re-slugging the title at read time. Re-deriving it on each read is what would make a rename break the join, and it is the single thing this design must not do.

That gives renaming for free. Retitle the task in Obsidian, or let Monday's item name drift, and `.cortex/why-regenerative/` and every `task: why-regenerative` key underneath it stay pointed at each other.

## The one real cost

Two tasks with the same name collide. A `Homepage` in Q1 and a `Homepage` in Q3 for the same project both want `.cortex/homepage/`, and the second one lands in the first one's capture folder.

IDs never collide; slugs can. The mitigation is that `create-tasks` already proposes the whole set as a table and writes nothing until the human approves it — so the collision surfaces at the moment the name is chosen, in front of the person who can rename it. That check has to be added: before writing, `create-tasks` looks for an existing `.cortex/<slug>/` or an existing task with that slug, and if it finds one, says so and asks for a distinguishing name rather than picking a suffix itself. An auto-appended `-2` would recreate the meaningless identifier this change exists to remove.

## How the open questions were settled

- **Slug length.** Slug the title, not the scope line — three or four words. Where a full slug would make an unusable path, cut at the first phrase that still identifies the work and show the cut in the proposal table, so the human sees what the folder will be called before it is written rather than discovering it later.
- **`parent:` is unchanged.** It was already the grouping mechanism and nothing resolves through it, so the ID prefix was never doing that job — it only looked like it was. Nine independently-named audit tasks sharing `parent: "Q3 audit"` group exactly as nine `AC-` tasks did.
- **Prefix match holds, with a new stop.** `/build why-reg` still finds `why-regenerative`, but names collide on prefixes far more readily than sequential IDs did, so every move that resolves a task now lists the matches and asks when more than one hits. Taking the first match is how you build the wrong thing.

## What was changed

- `skills/create-tasks/SKILL.md` — a `Name the task for what it is` section, the slug column in the proposal table, the collision check, the reworked frontmatter block, two guardrails
- `skills/create-tickets/SKILL.md` — usage, prefix-match rule, the task read, ticket frontmatter and H1
- `skills/build/SKILL.md` — usage, prefix-match rule, capture folder read from `cortex:`
- `skills/qa/SKILL.md` — usage, prefix-match rule, capture folder read from `cortex:`
- `skills/grill-me/SKILL.md` — usage, write target, transcript frontmatter and heading
- `skills/research/SKILL.md` — usage, write target, findings frontmatter
- `skills/prototype/SKILL.md` — usage, write target, pointer frontmatter
- `README.md` — the moves section now describes naming and the slug-as-key rule

## Affected files

Seven skills demonstrate or write the ID, and the model doc defines it:

- `skills/create-tasks/SKILL.md` — writes `task:` and `cortex:`; needs the slug derivation and the collision check
- `skills/create-tickets/SKILL.md` — usage, inputs, ticket frontmatter, ticket H1
- `skills/build/SKILL.md` — usage, inputs, "resolve the task ID by prefix match"
- `skills/qa/SKILL.md` — usage, inputs
- `skills/grill-me/SKILL.md` — usage, inputs, frontmatter, transcript H1
- `skills/research/SKILL.md` — usage, frontmatter
- `skills/prototype/SKILL.md` — usage, frontmatter
- `docs/design/2026-08-04-task-and-ticket-model.md` — the `Where things live` tree and the Move 0 frontmatter block

`foundation` and `ideation` are untouched — neither references a task ID.
