# Spreadsheet Validation Demo

Checks a supplier-onboarding spreadsheet row by row **before** anyone keys it into another system, and tells you exactly which rows are wrong and why.

Synthetic data only. No network calls. The input file is never modified.

> **Before publishing — delete this box once true.** This repository was drafted with AI assistance (Claude). Keep the "My contribution" section only after you have read every file, run the tests yourself and can explain each rule in an interview.

---

## The problem

Teams often receive onboarding data in Excel and enter it into a portal or ERP by hand or with an automation script. Errors in the sheet — a nine-digit phone number, a GSTIN with a typo, the same supplier listed twice, an ID that Excel silently turned into a number — are cheap to fix in the spreadsheet and expensive to fix after a record has been created downstream.

This project shows a **validate-first** approach: run every rule against the whole file, accept the clean rows, and return a clear rejected-row report the sender can act on.

The problem is one I met during my internship (spreadsheet data feeding a web portal). **No company code, data, field list or workflow is used here.** The domain, columns, rules and records are invented for this demo.

## What it does

```
input.xlsx ──► find header row ──► normalise each cell ──► field rules ──► cross-field rules ──► duplicate checks
                                                                                                     │
               output/<name>-results.xlsx  (every row + status + errors)  ◄──────────────────────────┤
               output/<name>-issues.csv    (one line per problem)         ◄──────────────────────────┤
               output/<name>-accepted.csv  (clean rows only, local file)  ◄──────────────────────────┘
```

| Check | Example of what it catches |
|---|---|
| Required fields | Missing contact email |
| Format | Email without a domain, 9-digit mobile, pincode starting with 0, malformed PAN |
| GSTIN check character | A one-character typo in a GSTIN (mod-36 check digit) |
| Cross-field | GSTIN does not contain the PAN; GSTIN state code does not match the state |
| Allowed values | Unknown state, payment terms of 20 days when only 0/15/30/45/60 are allowed |
| Range | Credit limit below 0 or above ₹1 crore; onboarding date in the future |
| Duplicates | Same supplier ID twice; same PAN under two supplier IDs (first occurrence kept) |
| Spreadsheet hazards | An identifier stored as a *number* (leading zeros or formatting may already be lost) |
| Structure | Missing or duplicate column headers stop the run with exit code 2 |

Warnings (for example, a credit limit with advance-payment terms) are reported but do not reject the row.

Normalisation is deliberate and limited: `+91 99999 00003` becomes `9999900003`, `"75,000"` becomes `75000`, `15/04/2026` becomes a date, and header names are matched regardless of case and spacing. Anything that cannot be normalised safely is reported, never guessed.

## Run it

Requires Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python data/make_sample_data.py                         # regenerates the synthetic workbook
python -m validator data/sample_supplier_register.xlsx --out output/
python -m pytest                                        # 51 tests
```

Exit codes: `0` all rows accepted · `1` some rows rejected · `2` file could not be validated.

Sample run on the included workbook (21 data rows): **6 accepted** (one with a warning), **15 rejected**, each rejection deliberately exercising a different rule. `data/expected_outcomes.csv` lists the intended result for every row, and a test checks the validator against it.

## Project layout

```
validator/
  schema.py    column contract: names, required/optional, kinds, allowed values
  rules.py     field and cross-field rules, GSTIN check character
  reader.py    read-only workbook reader: header detection, cell normalisation
  validate.py  row validation and duplicate detection
  report.py    results workbook, issues CSV, accepted-rows CSV
  cli.py       command line entry point
data/
  make_sample_data.py      builds the synthetic workbook and expected outcomes
tests/
  test_rules.py            rule-by-rule tests
  test_workbook.py         end-to-end tests, safety tests
```

## Testing

51 automated tests cover:

- each rule with valid and invalid values;
- normalisation of phone numbers, dates, money and numeric cells;
- the sample workbook against its documented expected outcomes;
- structural failures (missing column, duplicate header, non-Excel file);
- the CLI's exit codes and report files;
- **safety**: the input file's SHA-256 hash is unchanged after a run, and a static check fails the build if any module imports a networking library.

## Implemented vs. not implemented

| Implemented | Not implemented (deliberately) |
|---|---|
| Validation, normalisation, duplicate detection | Writing to any real system, API or portal |
| Results workbook, issues CSV, accepted-rows CSV | Browser automation |
| Command line tool with exit codes | Web interface |
| Automated tests | Live PAN/GSTIN verification against government services |

## Limitations

- Format and check-character validation proves a PAN or GSTIN is *well-formed*, not that it is *registered* or belongs to the supplier.
- The state list is a subset of Indian states and union territories; extend it from the official GST state-code list before reuse.
- The email rule is pragmatic, not RFC-complete.
- Duplicate detection is exact-match after normalisation; it will not catch "Bluefinch Traders" vs "Blue Finch Traders".
- Dates in ambiguous text formats are read as day-first (`DD/MM/YYYY`).

## Possible improvements

- Fuzzy matching on supplier names to flag likely duplicates for human review.
- A configurable rules file (YAML) so business users can change allowed values without code changes.
- A small web page for drag-and-drop validation.
- Data-quality trend reporting across files (which rules fail most often, from which senders).

## My contribution

**[CONFIRM BEFORE PUBLISHING — keep only what is true]**

- Defined the problem and the validation requirements from experience with spreadsheet-to-portal data entry.
- Built the project with AI assistance (Claude), then reviewed the rules, ran the test suite and checked the reports against the expected outcomes.
- [FILL IN anything you changed or added yourself]

## Tools

Python · openpyxl · pytest · AI-assisted development (Claude)

## Licence

MIT — see `LICENSE`. All data is synthetic.
