# Run log format

The run log lives under the brief's `## Run log` heading. Write each line as the thing happens — never reconstructed at the end, so a run that dies mid-step still says where it died.

```markdown
## Run log

- **Run** started 2026-10-28 09:02 · branch `auto/homepage-hero` from `main` · profile v2
- 09:02 → 09:03 · **Intake** · ok · Shopify, password page on
- 09:03 → 09:05 · **Task** · `homepage-hero`, one task
- 09:05 → 09:05 · **Foundation** · skipped, exists
- 09:05 → 09:21 · **Research** · 3 questions in parallel · 1 unreachable: Figma node 1:234 (permission)
- 09:21 → 09:34 · **Self-grill** · 31 answered (4 brief, 12 high, 11 medium, 4 low) · 1 to prototype
- 09:34 → 10:02 · **Prototype** · expand mechanics · picked B (provisional)
- 10:02 → 10:19 · **Tickets** · 3 tickets · 0 route-backs
- 10:19 → 11:48 · **Build** · 01 cleared in 3 rounds · 02 cleared in 5 · 03 cleared in 2, 1 blocked
- 11:48 → 12:05 · **QA as Ben** · round 1: 2 send-backs · round 2: clean · 1 taste flag
- 12:05 → 12:20 · **Build** (QA send-back) · 02 cleared in 2 rounds
- 12:20 → 12:22 · **Wrap** · [[2026-10-28 Auto Review — Homepage hero]]
- **Run** ended 12:22 · review · 3:20 total · 6 min blocked (environment retry at 10:40)
```

## Rules

- **Times are local, `HH:mm`.** The date sits on the first line only, unless the run crosses midnight.
- **One line per step.** Parallel helpers in one step share a line.
- **Blocked time** gets its own note on the line where it happened, and its minutes add to `blocked_minutes:` in the brief's frontmatter. Count waiting on things outside the work only: an environment retry, a bot-protection cool-down. Slow builds are not blocked time.
- **A halt** ends the log with `**Run** ended HH:mm · blocked at <step> · <reason>`.
- **`run_started` / `run_ended`** in the frontmatter match the first and last lines.

The step durations are the agency's build-time numbers. Keep them honest: a step's time is from its helper's start to its result, not to whenever you got round to logging it.
