#!/usr/bin/env python3
"""Content integrity validator for Degrees of Film. READ-ONLY (opens files for
reading only; never writes, never touches the network, never reads curation/.env).

Run from the repo root:
    python .claude/skills/degreesoffilm-diagnostics-and-tooling/scripts/validate_content.py

Checks (one PASS/FAIL line per group, house test style, non-zero exit on FAIL):
  manifest-structure   parses, entries have all fields, sorted by date, dates+ids unique
  puzzle-files         every manifest entry's file exists and parses as JSON
  id-consistency       each puzzle file's "id" matches its manifest entry's "id"
  images               every referenced image (tier images[] + per-rung image) exists
  decode               every obfuscated answer/caption/manifest-title decodes cleanly
  rung-shape           every rung has >=1 answer; rung 1 is the Film rung
  ledger-crosscheck    ledger <-> manifest 1:1 by puzzle id; ledger film ids unique
                       (reality as of 2026-07-03: hand-authored puzzle 001 IS in the
                       ledger — TMDB id 6977, puzzle 1 — so the check is strict 1:1)
  quotes-vs-ledger     WARN class: docs/app.js home-screen QUOTES must not name a
                       film that is in the ledger (owner's spoiler discipline).
                       WARN does not fail the run unless --strict is passed.
  decoy-coverage       INFO: rungs with decoys / total, per puzzle
  runway               INFO: consecutive stocked days starting today

Exit codes: 0 = all groups pass (warnings allowed), 1 = any FAIL,
            1 also on WARN if --strict. Flags: --strict, --today YYYY-MM-DD.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# Repo root derived from this file's own path (scripts/ -> skill/ -> skills/ ->
# .claude/ -> root), so the script works from any cwd.
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "curation"))
import cipher  # noqa: E402  (curation/cipher.py — stdlib only)

PUZZLES_DIR = ROOT / "docs" / "puzzles"
MANIFEST_PATH = PUZZLES_DIR / "manifest.json"
LEDGER_PATH = ROOT / "curation" / "used_films.json"
APP_JS_PATH = ROOT / "docs" / "app.js"

try:  # Unicode film titles on Windows' cp1252 stdout (same trick as the test suites)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FAILS = 0
WARNS = 0
GROUPS_PASSED = 0


def report(group, problems, warn=False, info=None):
    """Print one PASS/FAIL/WARN line for a check group (+ indented details)."""
    global FAILS, WARNS, GROUPS_PASSED
    if problems:
        tag = "WARN" if warn else "FAIL"
        if warn:
            WARNS += 1
        else:
            FAILS += 1
        print(f"{tag}  {group}: {len(problems)} problem(s)")
        for p in problems:
            print(f"        - {p}")
    else:
        GROUPS_PASSED += 1
        print(f"PASS  {group}{': ' + info if info else ''}")


def try_decode(s):
    """(ok, decoded_or_error). Plaintext passthrough counts as ok (by design)."""
    try:
        return True, cipher.deobfuscate(s)
    except Exception as e:  # bad base64 / bad utf-8 after XOR = corrupt blob
        return False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser(description="Read-only content integrity validator.")
    ap.add_argument("--strict", action="store_true",
                    help="treat WARN-class findings (quotes-vs-ledger) as failures")
    ap.add_argument("--today", default=None, metavar="YYYY-MM-DD",
                    help="override 'today' for the runway report (deterministic runs)")
    args = ap.parse_args()
    today = args.today or datetime.date.today().isoformat()

    # ---- manifest-structure -------------------------------------------------
    problems = []
    manifest = []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not isinstance(manifest, list):
            problems.append("manifest is not a JSON list")
            manifest = []
    except Exception as e:
        problems.append(f"manifest failed to parse: {e}")
    for i, e in enumerate(manifest):
        missing = [f for f in ("date", "id", "file", "title", "accent") if f not in e]
        if missing:
            problems.append(f"entry #{i} missing fields: {missing}")
    dates = [e.get("date") for e in manifest]
    ids = [e.get("id") for e in manifest]
    if dates != sorted(dates):
        problems.append("entries are not sorted by date")
    if len(set(dates)) != len(dates):
        problems.append(f"duplicate dates: {sorted({d for d in dates if dates.count(d) > 1})}")
    if len(set(ids)) != len(ids):
        problems.append(f"duplicate ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    report("manifest-structure", problems,
           info=f"{len(manifest)} entries, sorted, dates+ids unique")

    # ---- puzzle-files -------------------------------------------------------
    problems, puzzles = [], {}   # id -> parsed puzzle
    for e in manifest:
        path = PUZZLES_DIR / e.get("file", "")
        if not path.is_file():
            problems.append(f"{e.get('file')} (dated {e.get('date')}) does not exist")
            continue
        try:
            puzzles[e.get("id")] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as ex:
            problems.append(f"{e.get('file')} failed to parse: {ex}")
    report("puzzle-files", problems, info=f"all {len(puzzles)} files exist and parse")

    # ---- id-consistency -----------------------------------------------------
    problems = [f"{e.get('file')}: file id={puzzles[e.get('id')].get('id')} "
                f"!= manifest id={e.get('id')}"
                for e in manifest
                if e.get("id") in puzzles and puzzles[e.get("id")].get("id") != e.get("id")]
    report("id-consistency", problems, info="every file id matches its manifest entry")

    # ---- images -------------------------------------------------------------
    problems, n_imgs = [], 0
    for pid, pz in sorted(puzzles.items()):
        refs = list(pz.get("images", []))
        refs += [r["image"] for r in pz.get("rungs", []) if r.get("image")]
        for rel in refs:
            n_imgs += 1
            if not (PUZZLES_DIR / rel).is_file():
                problems.append(f"puzzle {pid}: missing {rel}")
    report("images", problems, info=f"all {n_imgs} referenced images exist on disk")

    # ---- decode -------------------------------------------------------------
    problems, n_strings = [], 0
    for e in manifest:
        n_strings += 1
        ok, out = try_decode(e.get("title"))
        if not ok:
            problems.append(f"manifest title for id {e.get('id')}: {out}")
        elif isinstance(out, str) and not out.strip():
            problems.append(f"manifest title for id {e.get('id')} decodes to empty")
    for pid, pz in sorted(puzzles.items()):
        for ri, r in enumerate(pz.get("rungs", []), start=1):
            for a in r.get("answers", []):
                n_strings += 1
                ok, out = try_decode(a)
                if not ok:
                    problems.append(f"puzzle {pid} rung {ri} answer: {out}")
                elif isinstance(out, str) and not out.strip():
                    problems.append(f"puzzle {pid} rung {ri}: answer decodes to empty")
            if r.get("caption"):
                n_strings += 1
                ok, out = try_decode(r["caption"])
                if not ok:
                    problems.append(f"puzzle {pid} rung {ri} caption: {out}")
    report("decode", problems, info=f"{n_strings} obfuscated strings decode cleanly")

    # ---- rung-shape ---------------------------------------------------------
    problems = []
    for pid, pz in sorted(puzzles.items()):
        rungs = pz.get("rungs", [])
        if not rungs:
            problems.append(f"puzzle {pid}: no rungs at all")
            continue
        if rungs[0].get("role") != "Film":
            problems.append(f"puzzle {pid}: rung 1 role is "
                            f"{rungs[0].get('role')!r}, expected 'Film'")
        for ri, r in enumerate(rungs, start=1):
            if not r.get("answers"):
                problems.append(f"puzzle {pid} rung {ri} ({r.get('role')}): no answers")
    report("rung-shape", problems, info="every rung has answers; Film rung is first")

    # ---- ledger-crosscheck --------------------------------------------------
    problems, ledger = [], []
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        problems.append(f"ledger failed to parse: {e}")
    led_puzzles = [rec.get("puzzle") for rec in ledger]
    led_ids = [rec.get("id") for rec in ledger]
    if len(set(led_ids)) != len(led_ids):
        problems.append("duplicate TMDB film ids in the ledger (never-repeat broken)")
    man_ids = {e.get("id") for e in manifest}
    for e in manifest:
        if e.get("id") not in led_puzzles:
            problems.append(f"manifest id {e.get('id')} has no ledger record "
                            f"(film not marked used)")
    for rec in ledger:
        if rec.get("puzzle") not in man_ids:
            problems.append(f"ledger film {rec.get('title')!r} points at puzzle "
                            f"{rec.get('puzzle')} which is not in the manifest")
    report("ledger-crosscheck", problems,
           info=f"{len(ledger)} ledger records <-> {len(manifest)} manifest entries, 1:1")

    # ---- quotes-vs-ledger (WARN class) --------------------------------------
    # Owner's spoiler rule: home-screen QUOTES must be from films NOT in the puzzle
    # set. Parse the QUOTES array in docs/app.js and compare film names to ledger
    # titles. WARN, not FAIL: it can't corrupt data, but it leaks answers.
    problems, quote_films = [], []
    try:
        src = APP_JS_PATH.read_text(encoding="utf-8")
        m = re.search(r"const QUOTES = \[(.*?)\];", src, re.S)
        quote_films = re.findall(r",\s*'([^']+)'\s*\]", m.group(1)) if m else []
        if not quote_films:
            problems.append("could not parse the QUOTES array out of docs/app.js")
        led_titles = {(rec.get("title") or "").casefold(): rec for rec in ledger}
        for film in quote_films:
            rec = led_titles.get(film.casefold())
            if rec:
                problems.append(f"QUOTES names {film!r} — it is puzzle "
                                f"{rec.get('puzzle')} in the ledger (spoiler)")
    except Exception as e:
        problems.append(f"quotes check errored: {e}")
    report("quotes-vs-ledger", problems, warn=True,
           info=f"none of the {len(quote_films)} quote films are in the ledger")

    # ---- decoy-coverage (INFO) ----------------------------------------------
    for pid, pz in sorted(puzzles.items()):
        rungs = pz.get("rungs", [])
        with_decoys = sum(1 for r in rungs if r.get("decoys"))
        print(f"INFO  decoy-coverage: puzzle {pid}: {with_decoys}/{len(rungs)} "
              f"rungs have decoys")

    # ---- runway (INFO) ------------------------------------------------------
    stocked = {e.get("date") for e in manifest}
    d = datetime.date.fromisoformat(today)
    runway = 0
    while d.isoformat() in stocked:
        runway += 1
        d += datetime.timedelta(days=1)
    print(f"INFO  runway: {runway} consecutive stocked day(s) from {today}"
          + (" — TODAY HAS NO PUZZLE (daily will repeat)" if runway == 0 else ""))

    # ---- summary ------------------------------------------------------------
    fails = FAILS + (WARNS if args.strict else 0)
    print(f"\n{GROUPS_PASSED} group(s) passed, {FAILS} failed, {WARNS} warning(s)"
          + (" [--strict: warnings count as failures]" if args.strict else ""))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
