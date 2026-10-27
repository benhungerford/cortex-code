---
name: auto
description: Run one brief from _Briefs/ end to end without Ben — task, research, self-grill, tickets, build loop, QA as Ben — and ping him at review. Usage:/auto homepage-hero
disable-model-invocation: true
---

# auto

Run a brief through the whole Cortex Code workflow unattended, and stop at `review`.

Every other move in this plugin has a point where it waits for Ben: grill-me waits for answers, create-tasks for approval of the set, create-tickets for approval of a split, build for a run mode, prototype for a verdict, qa for acceptance. This move runs the same moves with each of those waits replaced by something written down — a decision taken from Ben's profile, tagged with how sure it was, and listed on a review note he reads afterwards. **Nothing is decided silently.** A run that guessed and said so is useful; a run that guessed and didn't is worse than no run.

You are the **main agent**. You hold the brief, the status, and file paths — never the work itself. Every step runs as a fresh helper (an `Agent` call) that reads its inputs from disk, writes its outputs to disk, and reports back in a few lines. That is what lets one session run all day: your context grows by a few lines per step, not by a repo's worth of reading. It is also the existing plugin rule that every move starts cold from its file, applied without a `/clear`.

**Helpers cannot start their own helpers.** Any step that would normally spawn an agent — build's checker, research's background reader, grill-me's fact-finding sub-agent — has that part done inline by the helper, or done by you. The build loop is the one that matters: you run it.

## Inputs

`/auto <brief>` — the brief's file name in `<vault>/_Briefs/`, matched by prefix. With no argument, list every brief at `status: ready` and take the oldest by `created`; say which you took. A hand run is **slot 0**.

`/auto --pickup <slot>` — the scheduled form (slots 1–3, one scheduled task each). Run, from this skill's folder:

```bash
python3 claim.py --vault "<vault>" --slot <slot>
```

It takes the oldest ready brief, flips it to `running` with `run_started` and `run_slot`, and prints JSON. It holds a lock while it does this, so two slots firing together never take the same brief.

- `"claimed": null` → nothing to do. Say the `reason` in one line and stop. **No notification**; an empty check every 15 minutes is not news.
- `"stale"` lists briefs still `running` more than 8 hours after they started. A run that long has probably died. Name them in your one line. Don't touch them; Ben decides.
- A claimed brief → carry on from Intake with that brief.

Up to 3 runs at once in total (`claim.py --max-total`), on any mix of sites. Briefs on the same site **plan in parallel and take turns on the site** — see *Site turns* below.

The vault path comes from the `<cortex-session>` block, or `get_boot_context` from `cortex-vault` where there is no block.

Read, once, before starting:

- The brief.
- `<vault>/Work/Personal/Cortex Code/Cortex Code Auto/Ben Decision Profile.md` — the profile. You don't apply it; helpers do. Read section 0 so you know the confidence rules you are enforcing.
- `helpers/*.md` in this skill's folder — one brief per step, each the prompt you give that step's helper.

## Guardrails that hold for the whole run

These sit on top of every guardrail in every move this skill runs. Nothing here relaxes those.

- **Never move a task to `done`.** `review` is as far as a run goes. Only Ben accepts.
- **Never tick a criterion.** The checker's observation is the only thing that clears one.
- **Never push, deploy, or upload.** Work stays on the run's branch, committed locally. (Deploy timing is open — OQ-07 in the project hub. Until it closes, a run ends with a branch, not a release.)
- **Never touch a launched site.** The intake check below is not optional and is re-run if a run resumes.
- **Never write hours or estimates** on the task. Timing goes on the brief, as run time, never as billable time.
- **Every guess goes on the review note.** If a helper took a decision Ben would normally take, it is on the list with its confidence, its basis, and what changes if it is wrong.
- **One brief is one task.** A brief that reads as two deliverables is still run as one task with more than one ticket; say so on the review note.

## 1. Intake

Validate before anything is created. Any failure here **blocks** the run: set `status: blocked`, write the reason under the brief's `## Run log`, notify (section 7), and stop. Do not start "the parts that work".

1. **Status is `ready`.** Not `draft`, not `running` (another run has it). The one exception: a pickup's own claim, which is `running` with this run's `run_slot`.
2. **Project resolves.** `project:` is a full vault path to a TBL project that exists and has a Project Context hub. Look it up in `<vault>/.claude/cortex/registry.json` and confirm it has at least one entry in `repo_paths`, and that the repo is a git repo (`git rev-parse` succeeds). No repo, no run. Sites the registry lists as `repo_kind: worktree` are plain folders synced over SFTP; they block with "no git repo — the SFTP baseline isn't set up" until it is.
3. **Required sections are filled.** `## What` and `## Designs` contain something other than the template's placeholder text.
4. **The site is unlaunched.** From the brief's `## Where` URL, or the project hub's staging URL:
   - **Shopify** — the storefront redirects to `/password`. One request, no retries.
   - **WordPress** — a WP Engine staging host, or a production host whose `robots.txt` disallows `/` or whose homepage carries `noindex`. One request each, no retries.
   - Can't tell → blocked, with what you saw. Never assume unlaunched.
5. **Repo is clean.** `git status` in the repo shows no uncommitted changes. Somebody's work in progress is not yours to build on top of.

Then:

- Set `status: running` and `run_started:` (`YYYY-MM-DDTHH:mm`, local) on the brief, unless the pickup's claim already did.
- Create the run's own copy of the code, on its own branch, cut from the repo's current branch:

  ```bash
  git -C "<repo>" worktree add ~/.cortex-auto/worktrees/<registry id>/<brief-slug> -b auto/<brief-slug>
  ```

  **From here on, "the repo" means this worktree.** Give its path to every helper as the repo path. The main checkout is never written by a run, so Ben can keep working in it and other runs can't collide with it. Say the worktree path and the branch it was cut from in the run log.
- **Port.** Any local server a helper starts (`shopify theme dev`, a local WordPress) uses port `9300 + slot`, so runs on different sites never fight over one. Pass it to every helper with the repo path.
- Start the run log (section 8).

## 2. The pipeline

Run these in order. Each row is one helper unless it says otherwise. Before each step, write its start line to the run log; after it, its end line and the helper's one-line result.

| # | Step | Helper brief | Skip when |
|---|---|---|---|
| 1 | Task | `helpers/task.md` | Never |
| 2 | Foundation | `helpers/foundation.md` | `.cortex/foundation/` already exists |
| 3 | Research | `helpers/research.md` — one helper per question, run in parallel | Never; there is always at least the design-vs-repo question |
| 4 | Self-grill | `helpers/self-grill.md` | Never |
| 5 | Prototype | `helpers/prototype.md` — one per question the grill routed | The grill routed nothing |
| 6 | Tickets | `helpers/tickets.md` | Never |
| 7 | Build loop | Section 3 below — you run it | Never |
| 8 | QA as Ben | `helpers/qa-as-ben.md` | Never |
| 9 | Wrap | Sections 5–7 below — you do it | Never |

Use `subagent_type: general-purpose` for every helper except the checker. Give each helper: the vault path, the repo path, the brief path, the task slug once step 1 has set it, the run branch, and its helper brief **verbatim**. Never paraphrase a helper brief; the overrides in it are the contract.

**Route-backs.** The tickets helper may come back saying the capture folder has a hole and naming the move that fills it — the same route-back create-tickets makes to a human. Run that move's helper (research, self-grill, or prototype) on just that hole, then run the tickets helper again. **At most two route-backs per run.** A third means the brief is missing something no helper can supply: block the run and say what.

### Site turns

Steps 1–4 and 6 only read and write files in the run's own worktree, so every brief on a site can do them at once. **Prototype, the build loop and QA as Ben drive the site in a browser**, and two runs doing that on one site at once would trip over each other's preview and the bot check. Those steps take the site's turn first:

```bash
python3 site_turn.py take --vault "<vault>" --site "<brief's project:>" --brief "_Briefs/<brief>.md" --step <prototype|build> --wait 540
```

- **Granted** (exit 0) → go ahead.
- **Not yet** (exit 3) → it waited 9 minutes and you are `position` N in the queue behind `held_by`. Run the same command again. Turns go in the order runs asked, and a turn held by a run that is no longer `running` is freed by itself, so you never clear one by hand.
- **Six hours waiting in total** → block the run: `waiting for <site> since <time>, behind <held_by>`. Something upstream has stuck.

Give the turn back as soon as the steps that need it are done:

```bash
python3 site_turn.py give --vault "<vault>" --site "<brief's project:>" --brief "_Briefs/<brief>.md"
```

| Take before | Give back after |
|---|---|
| Step 5, prototype (and any prototype route-back) | The last prototype helper returns |
| Step 7, the build loop | QA as Ben finishes, or a halt |

Build and QA share one turn, so another run can't slip in between a QA send-back and its fix. Close out (section 6) always gives the turn back, whatever happened; giving back a turn you don't hold does nothing.

Time spent waiting goes in the run log on its own line and in the brief's `queued_minutes:`. It is neither build time nor blocked time.

## 3. The build loop

You run this, because build's checker is a separate agent and a helper cannot spawn one. It is build's own loop (build `SKILL.md`, section 4) with the roles split across agents. Read build's section 4 and its Exit conditions before the first round.

For each ticket, in number order (build's **all, sequentially** mode — the recommended one; never parallel in a run):

1. **Builder.** A helper with `helpers/builder.md`. On the first round it implements the ticket. On later rounds it gets the checker's last failure list verbatim and fixes those items only. It commits on the run branch each round and returns the files it changed, one line each.
2. **Checker.** An `Agent` with `subagent_type: Explore`, synchronous, given `helpers/checker.md` plus everything build section 4 says a checker gets — criteria verbatim, unresolved QA items verbatim, what changed this round (from the builder's return), the URLs, the browser rules verbatim. **Never** pass on the builder's own claims about what works.
3. **Judge the round yourself** against build's exit conditions:
   - Every item pass or blocked → the ticket clears. Go to 4.
   - Same item failing two rounds running with the checker's observation unchanged → **stall**. Halt the whole loop.
   - Checker reports bot protection, or the environment won't stand up → **halt** the whole loop.
   - Builder reports the fix would need something above the divider → **halt**.
   - Otherwise → next round, back to 1.
4. **Write-up.** One final builder helper, told to append the single Build round (build section 5) and do the foundation upkeep (build section 6). It writes; you don't.

Keep, per ticket, only: round count, the last verdict list's counts, and anything blocked. That is what goes in the run log.

**A halt** leaves every cleared ticket's work committed, holds the task at `in-progress`, and goes straight to the review note (section 5) and close out (section 6), with the run marked blocked. The guesses made before the halt still need checking. Do not run QA on a half-built task.

## 4. QA as Ben

When every ticket clears, run `helpers/qa-as-ben.md`. It walks the built pages the way Ben's review does (his `K` rules, plus section 3 taste calls) and appends a QA round to each ticket with its findings tagged `found by QA (auto)`.

- **Findings come back** → send back to the build loop (section 3) with those items as unresolved QA items. Then QA again.
- **At most two QA send-backs per run.** After the second, stop sending back; whatever is still open goes on the review note as a known issue. Ben's review is the real QA; this one exists to make his shorter.
- **Nothing found** → the task moves to `review`. QA as Ben never accepts.

## 5. The review note

Write it to the project's `Notes/` folder as `<YYYY-MM-DD> Auto Review — <brief title>.md`, in the format in `review-note.md`. It is the most important thing a run produces: it is how Ben checks the run's guesses and how the profile learns.

Collect its contents from disk, not from memory: every `[auto · <confidence>]` item in the run's `grill-*.md` files, every prototype verdict marked provisional, every split and slug call the task and tickets helpers recorded, every blocked criterion, and every known issue from section 4.

Link it from the brief, the task, and the project's `Notes/_MOC.md`.

## 6. Close out

- Site turn: run `site_turn.py give` (section 2, *Site turns*), even on a block or halt.
- Brief: `status: review` (or `blocked`), `run_ended:`, `blocked_minutes:` and `queued_minutes:` (section 8), and the review note linked under `## Run log`.
- Task: `status: review` (or `in-progress` on a halt), with `brief:` pointing back at the brief.
- Repo: the run branch is committed and **not pushed**. Name it in the run log. Leave the worktree in place for Ben's review; he removes it (`git worktree remove`) when he's merged or dropped the branch.
- Stop any local server the run started, so its port is free for the next run.

## 7. Notify

Send one `PushNotification`. One line, under 200 characters, leading with what Ben would act on.

- **Done:** `<brief title> ready for review: <N> guesses to check (<H> high-risk), <T> tickets built.`
- **Blocked:** `<brief title> blocked at <step>: <reason>. Run log in the brief.`

The notification belongs to this session, so opening it opens this session — that is why the blocked message names the step and not a file path.

## 8. Run log and timing

Format in `run-log.md`. Write it as you go, never reconstructed at the end: a run that dies mid-step should leave a log that says where.

`blocked_minutes` is time the run spent unable to proceed for reasons outside the work — an environment that wouldn't stand up and was retried, a bot-protection cool-down. It is kept apart so a slow environment doesn't read as a slow build. A run that ends blocked counts nothing after the block.

`queued_minutes` is time spent waiting for the site's turn behind another brief. It is kept apart for the same reason: a queue is not a slow build.

## 9. When something goes wrong that this file doesn't cover

Block, don't improvise. Write what happened and what you would have needed into the run log, notify, and stop. An unattended run that improvises is making a decision Ben never sees.
