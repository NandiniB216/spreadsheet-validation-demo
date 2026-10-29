"""Write the results workbook, the rejected-row CSV and the accepted-row export.

Everything is written to a new output folder. Nothing is sent anywhere: the
"accepted" export is a local CSV standing in for a downstream system.
"""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .schema import COLUMN_NAMES, STATUS_COLUMNS

_RED = PatternFill("solid", fgColor="F8D7DA")
_GREEN = PatternFill("solid", fgColor="D4EDDA")
_BOLD = Font(bold=True)


def _fmt(issues):
    return "; ".join(f"{i.column}: {i.code} - {i.message}" for i in issues)


def _cell(value):
    return value if value is not None else ""


def write_results(result, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = result.workbook.path.stem
    paths = {
        "results": out_dir / f"{stem}-results.xlsx",
        "issues": out_dir / f"{stem}-issues.csv",
        "accepted": out_dir / f"{stem}-accepted.csv",
    }

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["excel_row", *COLUMN_NAMES, *STATUS_COLUMNS])
    for cell in ws[1]:
        cell.font = _BOLD
    for r in result.results:
        ws.append([r.row.excel_row, *(_cell(r.row.raw.get(c)) for c in COLUMN_NAMES),
                   r.status, _fmt(r.errors), _fmt(r.warnings)])
        ws.cell(row=ws.max_row, column=len(COLUMN_NAMES) + 2).fill = \
            _RED if r.errors else _GREEN

    issues_ws = wb.create_sheet("Issues")
    issues_ws.append(["excel_row", "severity", "column", "code", "message", "value"])
    for cell in issues_ws[1]:
        cell.font = _BOLD
    issue_rows = []
    for r in result.results:
        for issue in r.errors + r.warnings:
            line = [r.row.excel_row, issue.severity, issue.column, issue.code, issue.message,
                    str(_cell(r.row.raw.get(issue.column)))]
            issues_ws.append(line)
            issue_rows.append(line)

    summary = wb.create_sheet("Summary")
    summary.append(["Metric", "Value"])
    for cell in summary[1]:
        cell.font = _BOLD
    for metric, value in summary_lines(result):
        summary.append([metric, value])
    summary.append([])
    summary.append(["severity", "column", "code", "count"])
    for (severity, column, code), count in result.issue_counts().items():
        summary.append([severity, column, code, count])

    wb.save(paths["results"])

    with open(paths["issues"], "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["excel_row", "severity", "column", "code", "message", "value"])
        writer.writerows(issue_rows)

    with open(paths["accepted"], "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMN_NAMES)
        for r in result.accepted:
            writer.writerow([_export(r.row.values[c]) for c in COLUMN_NAMES])

    return paths


def _export(value):
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def summary_lines(result):
    total = len(result.results)
    accepted = len(result.accepted)
    rejected = len(result.rejected)
    warned = sum(1 for r in result.results if r.warnings)
    return [
        ("Input file", result.workbook.path.name),
        ("Sheet", result.workbook.sheet_name),
        ("Header row", result.workbook.header_row),
        ("Data rows read", total),
        ("Accepted", accepted),
        ("Rejected", rejected),
        ("Rows with warnings", warned),
        ("Structure warnings", "; ".join(result.workbook.structure_warnings) or "none"),
    ]
