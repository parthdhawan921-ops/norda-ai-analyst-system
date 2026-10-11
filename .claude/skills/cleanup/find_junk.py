"""List housekeeping candidates. It only REPORTS - it never deletes or moves.

  1. junk: temp files, caches, test leftovers, empty files outside data/
  2. wrong folder: CSVs outside data/, reports outside reports/, knowledge outside knowledge/
  3. skill health: every skill has SKILL.md with name + description, name = folder name
  4. old runs: run folders beyond the newest 10

Run:  python .claude/skills/cleanup/find_junk.py
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
JUNK = re.compile(r"(\.tmp$|\.bak$|~\$|^~|\.pyc$|^tmp_|^test_|^scratch|\.log$)", re.I)
SKIP = {".git"}

def rel(p): return str(p.relative_to(ROOT)).replace("\\", "/")

junk, wrong, skills, runs = [], [], [], []
for p in ROOT.rglob("*"):
    if any(part in SKIP for part in p.parts) or not p.is_file():
        continue
    r = rel(p)
    if r.startswith("runs/"):
        continue
    if "__pycache__" in p.parts or JUNK.search(p.name):
        junk.append(r)
    elif p.stat().st_size == 0 and not r.startswith("data/"):
        junk.append(r + "  (empty)")
    top = r.split("/")[0]
    if p.suffix.lower() == ".csv" and top != "data":
        wrong.append(f"{r}  -> data/")
    if p.suffix.lower() in (".pptx", ".html") and top not in ("reports", ".claude"):
        wrong.append(f"{r}  -> reports/")
    if p.suffix.lower() == ".pdf" and top != "knowledge":
        wrong.append(f"{r}  -> knowledge/inbox/")
for d in sorted((ROOT / ".claude" / "skills").iterdir()):
    if not d.is_dir():
        continue
    md = d / "SKILL.md"
    if not md.exists():
        skills.append(f"{d.name}: no SKILL.md"); continue
    head = md.read_text(encoding="utf-8").split("---")
    fm = head[1] if len(head) > 2 else ""
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    if not name or name.group(1).strip() != d.name:
        skills.append(f"{d.name}: frontmatter name does not match folder")
    if not re.search(r"^description:\s*\S", fm, re.M):
        skills.append(f"{d.name}: missing description")
    for sec in ("## Steps", "## Rules"):
        if sec not in md.read_text(encoding="utf-8"):
            skills.append(f"{d.name}: missing section '{sec}'")
run_dirs = sorted([d for d in (ROOT / "runs").iterdir() if d.is_dir()], reverse=True) if (ROOT / "runs").exists() else []
runs = [rel(d) for d in run_dirs[10:]]

for title, items in [("1 Junk", junk), ("2 Wrong folder", wrong), ("3 Skill health", skills), ("4 Old runs (beyond newest 10)", runs)]:
    print(f"## {title}: {len(items)}")
    for i in items:
        print(f"- {i}")
