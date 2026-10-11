---
name: quality-gate
description: Run the trust layer - automatic checks built from knowledge/quality-rules.md (code computes, two roads, trace 10 orders, always-true facts) across raw, clean and mart. Use after /mart and before any report.
---

# Quality gate

## Steps
1. Run folder: `runs/<YYYY-MM-DD>` unless the pipeline gave one (env `RUN_DIR`).
2. Run `python .claude/skills/quality-gate/quality.py --run-dir <run folder>`
   (add `--seed N` to repeat the same 10 traced orders)
3. Exit code 1 = at least one check failed. Do NOT build reports on top of a failed gate.
4. Report short: pass count per rule, every FAIL with its detail, the key numbers.
   Explain what a failure means in business words. Tag claims [high]/[med]/[guess].

## The four rules (knowledge/quality-rules.md)
1. Code computes, Claude understands: every stored number is recomputed in code.
2. Two roads, one number: revenue, orders, units, stock, top product and stock-outs are
   each computed two or three independent ways (mart, clean, raw).
3. Trace orders: 10 random orders followed raw -> clean -> mart (seed is in the report).
4. Always true: every month has sales, no empty files, no negative revenue,
   December is the biggest month of 2025.

## Rules
- Never loosen a tolerance to make a check pass. Find the cause first and tell the user.
- A new finding the user agrees is a rule: add it to knowledge/quality-rules.md and here.
