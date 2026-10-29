"""Command line entry point.

    python -m validator data/sample_supplier_register.xlsx --out output/

Exit codes: 0 every row accepted, 1 one or more rows rejected,
2 the file could not be validated (missing columns, unreadable file).
"""

import argparse
import sys

from .reader import StructureError, read_workbook
from .report import summary_lines, write_results
from .validate import validate_rows


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="validator",
        description="Validate a supplier-onboarding workbook and report rejected rows. "
                    "Read-only on the input; writes reports to --out; makes no network calls.")
    parser.add_argument("workbook", help="path to the .xlsx file to validate")
    parser.add_argument("--sheet", help="sheet name (default: first sheet)")
    parser.add_argument("--out", default="output", help="folder for the reports (default: output)")
    args = parser.parse_args(argv)

    try:
        workbook = read_workbook(args.workbook, sheet_name=args.sheet)
    except StructureError as exc:
        print(f"STRUCTURE ERROR: {exc}", file=sys.stderr)
        return 2

    result = validate_rows(workbook)
    paths = write_results(result, args.out)

    for metric, value in summary_lines(result):
        print(f"{metric:<20} {value}")
    if result.rejected:
        print("\nRejected rows:")
        for r in result.rejected:
            codes = ", ".join(f"{i.column}:{i.code}" for i in r.errors)
            print(f"  row {r.row.excel_row:<4} {codes}")
    print("\nReports written:")
    for name, path in paths.items():
        print(f"  {name:<9} {path}")
    return 1 if result.rejected else 0


if __name__ == "__main__":
    sys.exit(main())
