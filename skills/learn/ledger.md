# Ledger format

The ledger is every guess `/learn` has read, with how it came out. It is the memory recurrence and calibration are counted from, so it is append-only and keeps unmarked guesses too.

File: `<vault>/Work/Personal/Cortex Code/Cortex Code Auto/Profile Learning Log.md`

Create it with this header the first time:

```markdown
---
type: reference
project: "Cortex Code Auto"
client: "Cortex Code"
tags:
  - "#type/reference"
  - "#domain/devops"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# Profile Learning Log

Every guess from every review note `/learn` has folded into [[Ben Decision Profile]], newest last. Written by `/learn`; don't edit by hand.

---
*Related:* [[_MOC]] · [[Cortex Code Auto — Project Context]]
```

Then, per note, insert above the footer:

```markdown
## <YYYY-MM-DD> — <brief title> → v<new version>

Note: [[<review note file name>]] · run on profile v<N> · <site>

| Question | Chose | Conf | Basis | Outcome | Change |
|---|---|---|---|---|---|
| Hover on the card arrow | color only | medium | K4, C9 | right | K4 +1 |
| Contact form | hand-built | low | research | wrong: "it's Formidable" | section 5 fact |
| Section order | page order | high | A1 | not flagged | — |
| Carousel autoplay | off | low | — | unmarked | — |
```

## Rules

- **Outcome** is one of `right`, `right + nuance`, `wrong: "<his words, short>"`, `not flagged`, `unmarked`, or `need you`.
- **Question** is the review note's wording, unchanged, so the same question asked on two briefs can be matched by eye as well as by `/learn`.
- **Change** names what moved in the profile, or `—`.
- Bump `updated:` on every write.
