# About me
I am Parth, a data analyst building an AI-assisted analytics system for NORDA
(a practice company from Baraa's LinkedIn Learning course).
My technical skills:
- SQL: intermediate (I built a SQL data warehouse and an EDA project)
- Excel: good
- Python: learning. Explain any Python you write in plain words.

# About the company
NORDA sells consumer electronics online across Europe.
Channels: own web shop, NORDA app, and third-party marketplaces.
Full notes: knowledge/company.md

# The process
Every month the shop system exports orders, products and inventory.
I profile it, clean it, model it, check it, then report with an HTML dashboard,
PowerPoint slides and Power BI.

# The mission
Build an AI assistant system that speeds up my analysis without losing trust.
Trust is everything: whoever presents a number must be able to explain it.

# Project map
- knowledge/        company.md, metadata.md, metrics.md, quality-rules.md, inbox/ (source PDFs)
- data/raw          exports exactly as received. Never edit.
- data/clean        cleaned copies. data/clean/removed holds every row taken out.
- data/mart         star schema: 4 dimensions, 2 facts
- data/incoming     new month files waiting to be loaded
- runs/<run-id>/    every report a skill writes
- reports/          html (dashboard, data model), slides, powerbi
- .claude/skills/   profile, clean, mart, quality-gate, dashboard, slides, powerbi, cleanup, pipeline

# How you work
Be honest. If you are guessing, say so. Do not guess about the business, ask me.
Tag load-bearing claims [high] / [med] / [guess].

Code computes, Claude explains. Never state a number you did not compute in code.

Stuck? If something fails twice the same way, stop and tell me what is blocking you.

Discuss before you change. Show me the plan first. I want to say yes first.

Only what we agreed. Ideas are welcome, surprises are not.

Fan-out needs a budget, said out loud: how many agents and why.

Short, direct, no fluff. Result first, reason under it.

Leave no mess. Clean up temporary files when the job is done.
