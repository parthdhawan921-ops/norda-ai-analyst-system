---
name: profile
description: Profile the raw shop export in data/raw and gate it with pass/fail checks. Use when new data arrives or when asked to profile, inspect or check the raw data.
---

# Profile

Understand the raw data and list its problems. Never changes data/raw.

## Steps
1. Pick the run folder: `runs/<YYYY-MM-DD>` unless the pipeline gave one (env `RUN_DIR`).
2. Run `python .claude/skills/profile/profile.py --run-dir <run folder>`
   - writes `<run folder>/profile.md` (findings table + per-column profile)
   - refreshes `knowledge/metadata.md`
3. Run `python .claude/skills/profile/check.py --run-dir <run folder>`
   - writes `<run folder>/check.md`; exit code 1 means a check failed
4. Tell the user, short: pass/fail count, the high-severity findings, anything new
   compared with the last run. Tag claims [high]/[med]/[guess].

## Rules
- Numbers come from the scripts, never from your own arithmetic.
- An unknown country, channel, brand or category is a FAIL: ask the user before
  adding it to `baseline.json`.
- Volume drop: the latest month must have at least 50% of the usual monthly lines.
- No cleaning here. That is the `clean` skill.
