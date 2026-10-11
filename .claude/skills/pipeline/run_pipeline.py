"""Run the whole analysis system in order, or only the steps you choose.

  1 profile    profile + check the raw data        (.claude/skills/profile)
  2 clean      raw -> clean                          (.claude/skills/clean)
  3 mart       clean -> star schema                  (.claude/skills/mart)
  4 quality    quality gate across all layers        (.claude/skills/quality-gate)
  5 dashboard  interactive HTML dashboard            (.claude/skills/dashboard)
  6 slides     December review deck                  (.claude/skills/slides)
  7 powerbi    Power BI semantic model (TMDL)        (.claude/skills/powerbi)

Every run gets its own folder runs/<date_time>/ with each step's report.
If a step fails, the pipeline STOPS: later steps never run on bad data.
Reports are STAGED: the dashboard and deck are written into the run folder
first and copied to reports/ only when every chosen step passed.

Run:  python .claude/skills/pipeline/run_pipeline.py --steps all
      python .claude/skills/pipeline/run_pipeline.py --steps 1-2     (profile + clean)
      python .claude/skills/pipeline/run_pipeline.py --steps 3-      (mart onwards)
      python .claude/skills/pipeline/run_pipeline.py --list
"""
import argparse, datetime as dt, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "CLAUDE.md").exists())
SK = ROOT / ".claude" / "skills"

STEPS = [  # (number, name, description, list of commands; {run} = run folder)
    (1, "profile", "profile + check the raw data", [[SK / "profile" / "profile.py"], [SK / "profile" / "check.py"]]),
    (2, "clean", "raw -> clean", [[SK / "clean" / "clean.py"]]),
    (3, "mart", "clean -> star schema", [[SK / "mart" / "build_mart.py"]]),
    (4, "quality", "quality gate", [[SK / "quality-gate" / "quality.py"]]),
    (5, "dashboard", "interactive HTML dashboard", [[SK / "dashboard" / "dashboard.py", "--out", "{run}/reports/dashboard.html"]]),
    (6, "slides", "December review deck", [[SK / "slides" / "slides.py", "--out", "{run}/reports/december-review.pptx"]]),
    (7, "powerbi", "Power BI model (TMDL)", [[SK / "powerbi" / "build_pbi.py"]]),
]
PUBLISH = {"dashboard.html": ROOT / "reports" / "html" / "dashboard.html",
           "december-review.pptx": ROOT / "reports" / "slides" / "december-review.pptx"}


def parse_steps(spec):
    if spec in ("all", ""):
        return [s[0] for s in STEPS]
    chosen = set()
    for part in spec.split(","):
        part = part.strip()
        names = {s[1]: s[0] for s in STEPS}
        if part in names:
            chosen.add(names[part]); continue
        if "-" in part:
            a, b = part.split("-")
            chosen.update(range(int(a or 1), int(b or len(STEPS)) + 1))
        else:
            chosen.add(int(part))
    bad = [c for c in chosen if c < 1 or c > len(STEPS)]
    if bad:
        raise SystemExit(f"pipeline: unknown step(s) {bad}")
    return sorted(chosen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", default="all")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        for n, name, desc, _ in STEPS:
            print(f"  {n}  {name:<10} {desc}")
        return
    chosen = parse_steps(args.steps)
    run = ROOT / "runs" / dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    (run / "reports").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, RUN_DIR=str(run), PYTHONIOENCODING="utf-8")
    log, ok_all = [], True
    print(f"pipeline: run folder {run.relative_to(ROOT)}; steps {chosen}")
    for n, name, desc, cmds in STEPS:
        if n not in chosen:
            continue
        t0 = time.time()
        status, tail = "PASS", ""
        for cmd in cmds:
            full = [sys.executable] + [str(c).replace("{run}", str(run)) for c in cmd]
            if "--out" not in cmd and name not in ("powerbi",):
                full += ["--run-dir", str(run)]
            p = subprocess.run(full, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
            (run / f"{n}_{name}.log").open("a", encoding="utf-8").write(p.stdout + p.stderr)
            tail = (p.stdout.strip().splitlines() or [""])[-1]
            if p.returncode != 0:
                status = "FAIL"
                tail = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or ["no output"])[-1]
                break
        secs = time.time() - t0
        log.append((n, name, status, secs, tail))
        print(f"  {n} {name:<10} {status}  {secs:5.1f}s  {tail}")
        if status == "FAIL":
            ok_all = False
            print(f"pipeline: STOPPED at step {n} ({name}). See {run.relative_to(ROOT)}/{n}_{name}.log")
            break
    published = []
    if ok_all:
        for fname, dest in PUBLISH.items():
            src = run / "reports" / fname
            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                published.append(str(dest.relative_to(ROOT)))
    md = [f"# Pipeline run {run.name}", "", f"Steps chosen: {', '.join(map(str, chosen))}  ",
          f"Result: **{'PASS' if ok_all else 'STOPPED ON FAILURE'}**", "",
          "| step | name | result | seconds | last line |", "|---|---|---|---:|---|"] + \
         [f"| {n} | {name} | {st} | {s:.1f} | {t} |" for n, name, st, s, t in log]
    md += ["", "Published to reports/: " + (", ".join(published) if published else
           ("nothing (no report step chosen)" if ok_all else "nothing - staged reports stay in this run folder"))]
    (run / "run.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"pipeline: {'PASS' if ok_all else 'FAIL'}; summary {run.relative_to(ROOT)}/run.md")
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
