---
name: cleanup
description: Housekeeping for the project - find junk files, files in the wrong folder, skills that break the common format, and old run folders; review with the user before touching anything. Use weekly/monthly or when asked to clean the house.
---

# Cleanup (housekeeping)

## Steps
1. Run `python .claude/skills/cleanup/find_junk.py` (it only reports).
2. Also look yourself for anything the script cannot judge: duplicate scripts, stale
   notes, knowledge that belongs in knowledge/.
3. Show the user ONE numbered list in 4 groups: junk · wrong folder · skill health · old runs.
   Say what you would do with each item. Budget: no agents, do it in this chat.
4. Wait for approval per group ("OK for 1, 2, 3 but not 4"). Then act only on approved items.
5. Report what changed.

## Standards every skill follows
- Folder name = `name:` in SKILL.md frontmatter, plus a one-line `description:`.
- Sections: a short intro, `## Steps`, `## Rules` (others optional).
- Scripts live next to SKILL.md, find the project root via CLAUDE.md, write reports to
  the run folder (`--run-dir` / env `RUN_DIR`), and exit 1 on failure.

## Rules
- Never delete anything in data/raw, knowledge/inbox or reports/powerbi without an explicit yes.
- Prefer moving to a `_to_delete/` folder over deleting.
