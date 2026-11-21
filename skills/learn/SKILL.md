---
name: learn
description: Fold Ben's marks on reviewed /auto review notes back into his decision profile — confirms, corrections, new rules, site facts — after he approves the changes. Usage:/learn
disable-model-invocation: true
---

# learn

Close the loop `/auto` opens. A run guesses how Ben would decide; he marks each guess right or wrong on the review note; this move turns those marks into a better profile.

It is the only move that writes to the profile. `/auto` reads it and never changes it. That split is deliberate: the profile changes only when Ben has looked at a run and said what was wrong, never because a run decided something on its own.

**Ben is here for this one.** It is not unattended. Nothing is written until he approves the proposed changes, the same way `/create-tasks` waits for approval of the set.

## Paths

The vault path comes from the `<cortex-session>` block, or `get_boot_context` from `cortex-vault` where there is no block.

- Profile: `<vault>/Work/Personal/Cortex Code/Cortex Code Auto/Ben Decision Profile.md`
- Ledger: `<vault>/Work/Personal/Cortex Code/Cortex Code Auto/Profile Learning Log.md` (create it on first use, format in `ledger.md`)
- Ticket gaps: `<vault>/Knowledge Base/ticket-gaps.md` (create it on first use)

## 1. Find the notes

Search the vault's `Work/TBL/` for notes with `source: auto` and `status: reviewed` in their frontmatter. Those are review notes Ben has finished marking. Skip `unreviewed` (he hasn't marked it) and `learned` (already folded in).

None found → say so in one line and stop. If there are `unreviewed` ones, name them, so Ben knows what is waiting on him.

Read the profile in full before reading any note. Note its `version:`.

## 2. Read each mark

A review note has three kinds of guess. Read each one and sort it into exactly one outcome.

**`## Check these first` and `## Also guessed`** (checkbox items):

| What Ben left | Outcome |
|---|---|
| `- [x]`, *Your answer* empty | **right** |
| `- [x]`, *Your answer* filled | **right, with a nuance** — read it as a refinement of the rule, not a correction |
| `- [ ]`, *Your answer* filled | **wrong** — his words are the real answer |
| `- [ ]`, *Your answer* empty | **unmarked** — skip it. Never count it as right or wrong |

**`## Decided with confidence`** and **`## Calls the run made about the work itself`** (no checkboxes): a line Ben added under an item makes that item **wrong** (or a nuance, if it agrees and adds). An item with nothing under it is **not flagged**. That is weaker than a tick, because he may only have skimmed it. Count it separately and never use it to strengthen a rule. Items in *Decided with confidence* are `high`; calls about the work carry no confidence and stay out of calibration.

For every guess, take from the note: the question, what the run chose, the confidence (`high` / `medium` / `low`), and the `basis`. A basis is one of:

- a rule ID such as `A8` (or several),
- a profile section: `section 3` (a taste call), `section 4` (a past reversal), `section 5` (a site fact),
- a research file, or nothing.

The note's `profile:` version goes in the ledger header only. It tells a later reader which rules the run had.

If a mark can't be read (a ticked box with an answer that contradicts the tick, or an answer that doesn't say what the right call was), **don't guess**. List it under *Need you* in the proposal.

## 3. Decide what each outcome changes

Work out every change before writing any of them.

Evidence lines use the **review note's date**, not today's. Write them in the rule's existing evidence style: `<note date> <brief title> (auto, <confidence>) — confirmed.` or `— "<his words>"`.

**Right**, and the basis is a rule → add the case as evidence to that rule and raise its `Strength` by 1. Where the strength isn't a single number ("1–2", a phrase), leave it and append `+1 (<note date>)`.

**Right**, and the basis is section 3 → add the case as one more example under that taste call. No strength; taste calls stay asked.

**Right**, and the basis is anything else → no profile change. It still goes in the ledger.

**Right, with a nuance** → add Ben's words to the rule as evidence. If they narrow the rule (a scope, an exception), edit the rule's text to say so. Don't raise its strength.

**Wrong** → first ask what kind of wrong it is. Take the first that fits:

1. **The run had the answer and missed it.** The design, the brief, the repo, or profile section 5 already said what Ben wrote (a value in the frame, a fact already listed). The profile isn't wrong; the run read badly. → No profile change. List it in the proposal under *Run misses*, naming which helper should have caught it, so the `/auto` helper brief can be fixed.
2. **A fact about one site.** Something true or false about the site that you could check by looking: which form plugin, which video host, who owns a section, what a page doesn't have. → Add it to the profile's **section 5** under that site, dated, in Ben's words. Also list it in the proposal as *add to the foundation*, naming the repo (from the vault's `.claude/cortex/registry.json`) and the foundation file it belongs in (`.cortex/foundation/concerns.md` for ownership and third-party apps, `components.md` for what exists). Don't write to the repo yourself; a repo with uncommitted changes fails `/auto`'s intake check.
3. **A rule that was wrong for this case.** The basis names a rule (or a section 4 reversal whose lesson a rule carries) and Ben's answer goes against it. → Add his words to that rule as counter-evidence. Then either narrow the rule so it no longer covers this case, or, if the case shows the rule is wrong in general, rewrite it. Log the change in **section 4** the way its entries already read: `**<rule ID> <short name>.** <what it said> → <what it says now>. <why, with his words>.` Never quietly delete evidence.
4. **A taste call** (basis is section 3, or the question is one of its kinds). → Don't make it a rule. Add the case as one more example under that section 3 item.
5. **A gap: no rule applied.** A preference: a way of choosing that could have gone either way. → Write a new rule in the category it fits (A–L), with the next free ID in that category, `Strength: 1`, his words as the evidence, and `*(v<new version>)*` after the rule text, the way v2 marks its additions. `Scope:` uses the names the profile already uses ("TBL site", "TWW", "global"); pick the site unless his words make it general ("we never…" on one site is that site's scope, not global).

**A wrong answer can also confirm something.** If Ben's words say what to do and an existing rule already says it ("color change only on hover" and a hover rule), add the case to that rule as evidence too.

When two marks touch the same rule, combine them into one change.

**Recurring questions.** Read the ledger. A question that has now been asked in **two or more** reviewed runs, on different briefs, and that Ben answered the same way each time, is a question the brief should have asked up front. Add it to `ticket-gaps.md` with the briefs it came from. A question he answered differently each time is a taste call. Propose adding it to section 3 instead.

**Calibration.** From the ledger plus this batch, total the right/wrong counts for each confidence level, across every learned note. Leave out unmarked and not-flagged items. Compare against section 0's thresholds and the back-test (high ≥ 76%, medium ≥ 69%). If a level has **at least 10 marks** and has fallen below its number, say so in the proposal and suggest a change (for example: "medium is at 52% over 14 marks; treat medium as low until it recovers"). **Never change section 0 yourself.** That is Ben's rule; propose it, and write it only if he approves that line.

## 4. Propose

Show Ben one plain list before writing anything. Plain words. Every item names the rule in words, not just its ID.

```
From <N> review notes (<brief titles>), <R> right, <W> wrong, <U> unmarked.

Stronger:
- A8 "leave finished work alone" — 2 more confirmations

Changed:
- C4 "autoplay off by default" — narrowed: not for hero video (your words: "…")

New:
- F7 "<rule>" — from <brief>: "<his answer>"

Site facts:
- TBL site: <fact> — also add to tigerblood's .cortex/foundation/concerns.md

Run misses (no profile change; fix the helper):
- "<question>" — the frame says square; research helper should have measured it

Not counted:
- 1 unmarked (<question>), 2 not flagged

Ticket gaps:
- "<question>" — asked on <brief>, <brief>

Calibration:
- high 9/10 · medium 6/9 · low 2/7. No change suggested.

Need you:
- <brief> — "<question>": ticked, but your answer says the opposite. Which is it?
```

Then ask once: **apply all, or tell me what to drop or change.** Wait for the answer. Apply only what he approves. Resolve *Need you* items from his reply; any he leaves unanswered stay out, and that note stays `reviewed`.

## 5. Write

In this order, so a failure halfway leaves nothing marked done that wasn't:

1. **Profile.** Apply the approved changes. Bump `version:` by 1 and `updated:`. Add one line to **section 6** (version history): date, how many review notes, what changed in a sentence. Update the version line at the top of the file to match.
2. **Ticket gaps.** Append approved items.
3. **Ledger.** Append one section per note, format in `ledger.md`. Every guess goes in, unmarked ones included, so later recurrence and calibration counts can be checked by hand.
4. **Review notes.** Set each fully-folded note to `status: learned`, add `learned_into: v<new version>`, and set `updated:` to now. A note with unresolved *Need you* items stays `reviewed`.
5. **Vault log.** Log each file write to `<vault>/_changelog.txt` per the vault's changelog rules (`UPDATED` for the profile and notes, `CREATED` for a new ledger or ticket-gaps file). In the Cortex Code Auto project's `Changelog.md`, add under a `## <today> — profile v<N>` heading, newest first: `- **Decision:** Profile v<N> from <count> review notes — <one line>.`

## 6. Report

Two or three lines: the new profile version, what changed in it, and which notes are now `learned`. If calibration suggested a section 0 change Ben declined, say it is still open.

## Guardrails

- **Nothing is written before approval.** Not the profile, not the ledger, not a note's status.
- **Ben's words are quoted, not paraphrased,** wherever they become evidence or a rule. A run paraphrasing him is how the profile drifts away from him.
- **Never remove evidence.** Rules get narrowed, rewritten, or marked superseded in section 4; their history stays.
- **Never strengthen a rule from a not-flagged item.** Silence is not a tick.
- **One pass, one version.** However many notes, a pass bumps the version once.
- **Facts go to section 5, not rules.** A fact written as a preference gets applied to the wrong site.
