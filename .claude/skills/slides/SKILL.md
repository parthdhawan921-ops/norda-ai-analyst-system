---
name: slides
description: Answer the monthly ad hoc review questions (was every part up, what ran out and what it cost, what to reorder) and build the PowerPoint deck in the locked style from data/mart. Use when asked for the December/monthly review or meeting slides.
---

# Slides (monthly review deck)

## Steps
1. Make sure the quality gate passed. If not, stop.
2. Read the questions in `knowledge/inbox/december-questions.pdf` (or the new request).
3. Run `python .claude/skills/slides/slides.py --month 2025-12`
   (pipeline passes `--out <run folder>/reports/december-review.pptx` to stage it)
4. Answer the three questions in the chat in 3 short lines, using the numbers the script
   printed and the deck. Tag estimates [med] or [guess].

## Deck (locked style)
1. Title with the headline  2. The short answer (one card per question)
3. Q1 was every part up: change by category + what is hiding (basket size, discount, country, channel)
4. Q2 what ran out and what it cost: revenue history of the sold-out models + cost range
5. Q3 what to order: products under 1 month of cover + suggested order
6. Before anyone asks: presenter prep, not for the screen

White background, blue for data, orange/red only for the problem. One message per slide,
title = the answer. This is a story for a meeting, not a dashboard.

## Rules
- Every number comes from `analyse()` in slides.py. Never type a number into a slide.
- New question? Add the calculation to `analyse()` first, then a slide.
- Cost of stock-outs is an estimate: show the method and the range, never one exact figure.
