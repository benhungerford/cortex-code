# Review note format

The review note is how Ben checks a run's guesses, and how the profile learns. Write it for someone who just walked in: plain words, no ticket numbers without a name beside them, the riskiest thing first.

File: `<project>/Notes/<YYYY-MM-DD> Auto Review — <brief title>.md`

```markdown
---
type: qa-note
source: auto
brief: "_Briefs/<brief>.md"        # plain paths: the vault keeps wikilinks out of frontmatter
task: "<vault path of the task file>"
status: unreviewed          # unreviewed → reviewed (Ben sets it) → learned (/learn sets it)
profile: v<N>
created: <YYYY-MM-DDTHH:mm>
updated: <YYYY-MM-DDTHH:mm>
tags:
  - "#type/qa-note"
  - "#source/internal"
---

# Auto Review — <brief title>

**Brief:** [[_Briefs/<brief>]] · **Task:** [[<task file name>]]

**Result:** <ready for review | blocked at <step>> · **Branch:** `<run branch>` (not pushed) · **Run time:** <h:mm> (+ <m> min blocked)

## Check these first

The guesses most likely to cost rework if wrong. Every `low` guess and every `## Ask me before` item, ordered by the size of its `if wrong:`.

- [ ] **<question>** — guessed: <answer>. <one line on why>. *If wrong:* <rework>. `low` · <basis>
  - Worth prototyping first: <what to compare>   ← only when the grill marked it
  - Your answer: 

## Also guessed

Every `medium` guess, same shape.

## Decided with confidence

Every `high` guess, one line each, no checkbox. Skim it; flag anything wrong by adding a line under it.

## Calls the run made about the work itself

- **Split:** <one task, N tickets — one line each> 
- **Name:** <slug collision, if any>
- **Taste flags from QA as Ben:** <one per line>

## Not done

- <blocked criteria, known issues after two QA send-backs, anything never reached on a halt — each with its reason>

## How to review

1. Tick each guess that was right. For a wrong one, write the real answer after *Your answer:*. Your words, not a correction of mine.
2. Set `status: reviewed`.
3. Then run `/qa <task>` as usual. Your answers here are not acceptance.
4. When you have a few reviewed notes, run `/learn` to fold your answers into the profile.

---
*Related:* [[_MOC]] · [[<project> — Project Context]]
```

## Why it is shaped this way

- **Riskiest first,** because review time is limited and a wrong `low` guess costs more than a wrong `high` one. The back-test showed `low` guesses right only 23% of the time.
- **Checkboxes on guesses, not on outcomes.** Ben is grading the profile here, not the build. `/qa` grades the build.
- **"Your answer" in his own words,** because those words become profile rules. A ticked box says the profile was right; a written answer is a new rule or a correction to one.
- **`status: reviewed`** is how `/learn` finds the notes whose answers are ready to fold into the profile. It sets `learned` once they are in.
