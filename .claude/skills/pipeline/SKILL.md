---
name: pipeline
description: Orchestrate the whole analysis system - profile, clean, mart, quality gate, dashboard, slides, Power BI - in the right order, stopping on the first failure. Use when new data lands in data/raw or when asked to run the pipeline.
---

# Pipeline

## Steps
1. Show the user the overview (`python .claude/skills/pipeline/run_pipeline.py --list`):
   1 profile · 2 clean · 3 mart · 4 quality · 5 dashboard · 6 slides · 7 powerbi
2. Ask which to run (AskUserQuestion): **Everything (1-7)**, **Data only (1-4)**,
   **From the mart onwards (3-7)**, or a single step / range they type.
3. Run `python .claude/skills/pipeline/run_pipeline.py --steps <choice>`
   (`all`, `1-4`, `3-`, `5`, or names like `clean,mart`).
4. Report short: one line per step (PASS/FAIL), where the run folder is, what was
   published. On a FAIL, open that step's log and report in the run folder and explain the cause.

## How it behaves
- Order is fixed: each step builds on the one before.
- One folder per run: `runs/<date_time>/` holds every report, log and `run.md`.
- Stops on the first failure. Later steps never run on bad data.
- Reports are staged in `runs/<run>/reports/` and copied to `reports/` only if every
  chosen step passed, so a bad run never overwrites a good dashboard.

## Rules
- Do not change the other skills from here. This skill only calls them.
- Do not run the pipeline when the user only asked to change it.
