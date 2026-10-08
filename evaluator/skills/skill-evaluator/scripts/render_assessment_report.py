#!/usr/bin/env python3
"""
Scores a profile-based assessment and writes one scoring sheet (Excel + Markdown) plus JSON.

Inputs:
  --plan            evals/eval_plan.json        (from build_plan_from_profile.py)
  --result          assessment_result.json      (from agents/manual-qa-assessment-judge.md)
  --human           human_decisions.json        (optional; the human's call on advisory flags)
  --submission-dir  root folder of the trainee's submission (optional; lets the script
                    check that every evidence ref points at a file that exists)
  --out-dir         report/

Scoring (the judge reports counts of errors, never points; this script does the maths):
  criterion points = max_points - penalty_per_error x errors, floored at 0
  a criterion marked na scores full max_points (the trainee is not penalised for a
  criterion that does not apply to them) and is flagged in the report
  group total = sum of its criteria; total = sum of groups
  PASS when total >= pass_threshold

Advisory flags (criteria with `advisory`, e.g. C6 severity deviation): the judge only
records them. A flag costs nothing until a human decides:
  human_decisions.json = {"C6-severity:BUG-02": {"decision": "fail", "errors": 1}}
  decision "fail" adds `errors` (default 1) to that criterion; "pass" adds nothing.
While any flag has no decision, the report status is "provisional", not final.

Evidence refs: every error's `where` must be a path relative to the submission root plus an
optional locator:  path[:line] | path!Sheet!Cell | path#Heading
  skills/Test-Case-Generation/SKILL.md:17
  outputs/tc-list.xlsx!TC List!F7
  chat-transcript.md#Turn 2
A `where` with no file path is shown as "(no file ref)", and with --submission-dir a path
that does not exist is shown as "(ref not found)". Both are also listed under Notes.

Outputs: assessment_scoring_sheet.xlsx (the table), assessment_report.md, assessment_report.json

Usage:
    python scripts/render_assessment_report.py --plan evals/eval_plan.json \
        --result L1/1/run-1/assessment_result.json --out-dir report/ \
        [--human decisions.json] [--submission-dir path/to/submission]
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

QUOTE_MAX = 90
HEADERS = ["Category", "Sub-Category", "Evaluation Criteria", "Max", "Points", "Errors",
           "Evidence/Notes", "Meets target?"]
WIDTHS = [22, 30, 48, 8, 9, 9, 70, 18]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def ref_path(where):
    """The file-path part of an evidence ref, or None when there is none."""
    p = re.split(r"[:!#]", where or "", maxsplit=1)[0].strip()
    return p if re.search(r"\.[A-Za-z0-9]+$|/", p) else None


def short(text, n=QUOTE_MAX):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def check_ref(where, sub_dir):
    """Returns (display, problem or None)."""
    path = ref_path(where)
    if path is None:
        return f"{where} (no file ref)", "no file ref"
    if sub_dir is not None and not (sub_dir / path).exists():
        return f"{where} (ref not found)", "ref not found"
    return where, None


def col_letter(i):
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i]


STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="4"><font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
    '<font><b/><sz val="16"/><color rgb="FF1F5C99"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
    '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/></patternFill></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFE7E6E6"/></patternFill></fill></fills>'
    '<borders count="2"><border/><border><left style="thin"/><right style="thin"/><top style="thin"/><bottom style="thin"/></border></borders>'
    '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
    '<cellXfs count="6">'
    '<xf fontId="0" fillId="0" borderId="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
    '<xf fontId="1" fillId="2" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
    '<xf fontId="2" fillId="0" borderId="0" applyFont="1"/>'
    '<xf fontId="0" fillId="3" borderId="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
    '<xf fontId="3" fillId="4" borderId="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
    '<xf fontId="0" fillId="0" borderId="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="top"/></xf>'
    '</cellXfs></styleSheet>'
)
S_CELL, S_HEAD, S_TITLE, S_EVID, S_SUB, S_NUM = range(6)


def write_xlsx(path, title, subtitle, table):
    """table: list of rows; each row is a list of (value, style) for the 8 columns."""
    def cell(r, c, v, s):
        ref = f"{col_letter(c)}{r}"
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return f'<c r="{ref}" s="{s}"><v>{v}</v></c>'
        return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'

    rows = [f'<row r="1">{cell(1, 0, title, S_TITLE)}</row>',
            f'<row r="2">{cell(2, 0, subtitle, S_CELL)}</row>',
            '<row r="4" ht="32" customHeight="1">' + "".join(cell(4, i, h, S_HEAD) for i, h in enumerate(HEADERS)) + "</row>"]
    for n, row in enumerate(table, start=5):
        rows.append(f'<row r="{n}">' + "".join(cell(n, i, v, s) for i, (v, s) in enumerate(row)) + "</row>")
    cols = "<cols>" + "".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>' for i, w in enumerate(WIDTHS)) + "</cols>"
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetViews><sheetView workbookViewId="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
             f'{cols}<sheetData>{"".join(rows)}</sheetData></worksheet>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Scoring Sheet" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", STYLES)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--human")
    ap.add_argument("--submission-dir", type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    a = ap.parse_args()

    plan, result = load(a.plan), load(a.result)
    human = load(a.human) if a.human else {}
    asm = plan["scope"]["assessment"]
    graded = result.get("criteria", {})

    missing = [c["id"] for c in asm["criteria"] if c["id"] not in graded]
    if missing:
        print(f"error: result has no entry for criteria {missing}", file=sys.stderr)
        return 1

    flags = result.get("advisory_flags", [])
    known_adv = {adv["id"] for c in asm["criteria"] for adv in c.get("advisory", [])}
    for f in flags:
        if f.get("id") not in known_adv:
            print(f"error: advisory flag id {f.get('id')!r} is not defined in the plan", file=sys.stderr)
            return 1
    flag_keys = {f"{f['id']}:{f.get('ref', '')}": f for f in flags}
    stale = sorted(set(human) - set(flag_keys))
    pending = sorted(k for k in flag_keys if k not in human)

    rows, notes = [], []
    for c in asm["criteria"]:
        g = graded[c["id"]]
        na = bool(g.get("na"))
        adv_ids = {x["id"] for x in c.get("advisory", [])}
        my_flags = {k: f for k, f in flag_keys.items() if f["id"] in adv_ids}
        adv_fail = sum(human[k].get("errors", 1) for k in my_flags if human.get(k, {}).get("decision") == "fail")
        errors = len(g.get("errors", []))
        points = c["max_points"] if na else max(0, c["max_points"] - c["penalty_per_error"] * (errors + adv_fail))
        if na and not c.get("na_when"):
            notes.append(f"{c['id']} was graded N/A but the criterion defines no N/A condition -- check the judge's reasoning.")

        evidence = []
        for e in g.get("errors", []):
            shown, problem = check_ref(e.get("where", ""), a.submission_dir)
            if problem:
                notes.append(f"{c['id']}: evidence ref {problem}: {e.get('where')!r}")
            evidence.append(f"- {shown} -- \"{short(e.get('quote', ''))}\"")
        for k, f in my_flags.items():
            d = human.get(k)
            state = "human: fail" if d and d["decision"] == "fail" else "human: pass" if d else "PENDING human decision"
            evidence.append(f"- flag {k} ({state}) -- {short(f.get('detail', ''))}")
        if na:
            evidence.append(f"- N/A: {short(g.get('note', ''))}")
        meets = ("N/A" if na else "Pending human" if any(k in pending for k in my_flags)
                 else "Yes" if points == c["max_points"] else "No")
        rows.append({"id": c["id"], "group": c["group"], "name": c["name"], "criteria": c["pass_when"],
                     "max": c["max_points"], "errors": errors, "human_errors": adv_fail, "na": na,
                     "points": points, "evidence": evidence, "meets": meets})
    if stale:
        notes.append(f"human decisions with no matching flag (ignored): {stale}")

    group_rows = []
    for gr in asm["groups"]:
        group_rows.append({"id": gr["id"], "name": gr["name"], "max": gr["max_points"],
                           "points": sum(r["points"] for r in rows if r["group"] == gr["id"])})
    total = sum(g["points"] for g in group_rows)
    max_total = sum(g["max"] for g in group_rows)
    verdict = "PASS" if total >= asm["pass_threshold"] else "FAIL"
    status = "provisional" if pending else "final"

    report = {"status": status, "verdict": verdict, "total": total, "max_total": max_total,
              "pass_threshold": asm["pass_threshold"], "groups": group_rows, "criteria": rows,
              "pending_human_flags": pending, "criteria_sha256": asm["criteria_sha256"],
              "baseline_sha256": asm["baseline_sha256"], "notes": notes}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / "assessment_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- the scoring sheet (same layout idea as the course's Excel scoring sheet) ---
    table = []
    for gr in group_rows:
        for r in (x for x in rows if x["group"] == gr["id"]):
            table.append([(f"{gr['id']} {gr['name']}", S_CELL), (f"{r['id']} {r['name']}", S_CELL),
                          (r["criteria"], S_CELL), (r["max"], S_NUM), (r["points"], S_NUM),
                          ("N/A" if r["na"] else r["errors"] + r["human_errors"], S_NUM),
                          ("\n".join(r["evidence"]) or "No deduction", S_EVID), (r["meets"], S_NUM)])
        table.append([(f"{gr['id']} {gr['name']}", S_SUB), ("Subtotal", S_SUB), ("", S_SUB), (gr["max"], S_SUB),
                      (gr["points"], S_SUB), ("", S_SUB), ("", S_SUB), ("", S_SUB)])
    table.append([("TOTAL", S_SUB), (f"Target: pass at {asm['pass_threshold']}", S_SUB), (f"{verdict} ({status})", S_SUB),
                  (max_total, S_SUB), (total, S_SUB), ("", S_SUB), ("", S_SUB), (verdict, S_SUB)])
    title = f"Scoring Sheet - {plan['skill_name']}"
    subtitle = f"Status: {status}. Pass threshold: {asm['pass_threshold']} of {max_total}. Evidence refs: path[:line] | path!Sheet!Cell | path#Heading."
    write_xlsx(a.out_dir / "assessment_scoring_sheet.xlsx", title, subtitle, table)

    # --- Markdown copy of the same table ---
    def cellmd(t):
        return str(t).replace("|", "\\|").replace("\n", "<br>")
    md = [f"# Scoring Sheet - {plan['skill_name']}", "",
          f"**{total} / {max_total}: {verdict}** (pass at {asm['pass_threshold']}) -- status: {status}", ""]
    if pending:
        md += [f"Provisional: {len(pending)} advisory flag(s) await a human decision and cost nothing yet: "
               + ", ".join(pending), ""]
    md += ["| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
    for row in table:
        md.append("| " + " | ".join(cellmd(v) for v, _ in row) + " |")
    if notes:
        md += ["", "## Notes"] + [f"- {n}" for n in notes]
    (a.out_dir / "assessment_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{verdict} {total}/{max_total} status={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
