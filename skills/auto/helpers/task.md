# Helper — task

You are one step of an unattended Cortex Code run. You start cold. Everything you need is on disk; everything you decide goes on disk. Nobody will read your conversation.

## Your job

Turn the brief into **one** task in the vault project's `Tasks/` folder.

Read `skills/create-tasks/SKILL.md` in the Cortex Code plugin and follow it — the task file's frontmatter, the slug rules, the collision check — with these overrides. They replace that skill's human checkpoints; nothing else in it is relaxed.

## Overrides

- **The brief is the input.** create-tasks accepts "a brief handed in directly". The brief at `<brief path>` is it.
- **Exactly one task.** Do not propose a set. If the brief reads as several deliverables, still write one task, and record `split_note:` in your return so the main agent can put it on the review note.
- **Approval is replaced by a record.** Do not wait for approval. Write the task, then record what you would have shown in the proposal table (title, slug, scope line) in your return.
- **Title** is the brief's `# heading`. Slug it per create-tasks.
- **Slug collision** — an existing `.cortex/<slug>/` or a task with that slug. Do not append a suffix. Lengthen the title with the most specific word from the brief's `## What` (the page or section name) and re-slug. Record the original and the chosen name in your return.
- **Extra frontmatter**, after create-tasks' own block: `autopilot: true` and `brief: "_Briefs/<brief file name>"` (a plain path: the vault keeps wikilinks out of frontmatter). Add a `[[_Briefs/<brief file name without .md>]]` link in the task body too.
- **No hours, rate, or estimate.** Unchanged from create-tasks — and this is TBL work, so billing fields stay at their defaults.

## Return (under 8 lines)

```
task: <vault path of the task file>
slug: <slug>
scope: <the scope line>
split_note: <none | why this might be more than one deliverable>
collision: <none | original → chosen>
```
