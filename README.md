# Spreadsheet Validation Demo

**Validate supplier-onboarding data before it is entered into another system.**

A Python command-line tool that reads an Excel supplier register, checks each row against defined data-quality rules, and produces a results workbook plus separate issue and accepted-row exports.

> **Portfolio demo:** all records, supplier details, business rules and field values are synthetic. The scenario is inspired by a general spreadsheet-to-portal data-quality problem; no employer data, code or internal workflow is included.

## At a glance

- **Input:** Excel workbook (.xlsx)
- **Checks:** required fields, formats, allowed values, ranges, GSTIN check character, cross-field consistency and duplicates
- **Outputs:** annotated results workbook, issue-level CSV and accepted-row CSV
- **Safety:** input workbook is read-only; reports are written to a separate output directory
- **Tests:** 51 automated tests
- **Runtime:** Python 3.10+

## Why this matters

A spreadsheet can look complete while containing missing identifiers, invalid contact details, inconsistent tax information or duplicate suppliers. If those issues are discovered only after manual entry into a downstream system, correction becomes slower and more expensive.

This demo uses a **validate-first** approach: identify issues before downstream entry, explain what needs correction, and separate accepted rows from rejected rows.

## How it works

1. Read the input workbook and locate its header row.
2. Normalise values only when it is safe to do so.
3. Run field-level validation rules.
4. Check relationships between fields, such as PAN and GSTIN consistency.
5. Detect duplicate supplier IDs and PAN values.
6. Classify each row and generate three output files.

| Validation area | Example |
|---|---|
| Required fields | Missing supplier contact email |
| Format | Invalid email, mobile, PIN code, PAN or GSTIN format |
| GSTIN check character | Detects a likely single-character transcription error |
| Cross-field consistency | PAN embedded in GSTIN; GSTIN state code against supplier state |
| Allowed values | Unsupported state or payment term |
| Range and date | Negative or excessive credit limit; future onboarding date |
| Duplicates | Repeated supplier ID or PAN |
| Spreadsheet hazards | Identifier stored as a number, where formatting or leading zeros may be lost |
| Workbook structure | Missing or duplicate headers stop validation |

Errors reject a row. Warnings are reported but do not reject it; for example, a positive credit limit with advance-payment terms is flagged for review.

## Sample run

The included synthetic workbook contains 21 data rows:

| Outcome | Rows |
|---|---:|
| Accepted (including one with a warning) | 6 |
| Rejected | 15 |
| Total | 21 |

These are deliberately constructed sample outcomes, not production performance metrics.

## Run locally

Requires Python 3.10 or newer.

    python -m venv .venv
    source .venv/bin/activate
    # Windows: .venv\Scripts\activate

    pip install -r requirements.txt
    python data/make_sample_data.py
    python -m validator data/sample_supplier_register.xlsx --out output/
    python -m pytest

Exit codes: 0 means all rows accepted; 1 means one or more rows rejected; 2 means the workbook could not be validated.

## Output files

| File | Purpose |
|---|---|
| Results workbook | Row-level status and errors/warnings, issue detail and summary sheets |
| Issues CSV | One record per validation issue |
| Accepted CSV | Clean rows exported locally for a hypothetical downstream handoff |

The accepted CSV is **not** sent to a real portal or system.

## Project structure

    validator/
      schema.py       Column contract and allowed values
      rules.py        Field and cross-field validation rules
      reader.py       Workbook reading, header detection and normalisation
      validate.py     Row validation and duplicate detection
      report.py       Excel and CSV report generation
      cli.py          Command-line interface
    data/
      make_sample_data.py
      sample_supplier_register.xlsx
      expected_outcomes.csv
    tests/
      test_rules.py
      test_workbook.py

## Testing and safeguards

The 51 automated tests cover individual rules, normalisation, expected sample outcomes, malformed workbook structures, command-line exit codes and report generation.

Additional safety checks verify that:
- the input workbook's SHA-256 hash is unchanged after a run;
- the validator package does not import networking libraries.

Run the tests with python -m pytest.

## What is and is not implemented

| Implemented | Not implemented |
|---|---|
| Excel input reading and validation | Connection to a live ERP, CRM or portal |
| Field, cross-field and duplicate checks | Browser or API automation |
| Excel and CSV output reports | Live PAN/GSTIN registration verification |
| CLI and automated tests | Web interface or multi-user workflow |

## Limitations and interpretation

- PAN/GSTIN checks validate format and the GSTIN check character; they do not confirm registration or legal ownership.
- The included state list is a subset and must be completed against an authoritative current list before real use.
- Email validation is pragmatic, not a complete implementation of the email standard.
- Duplicate checks use exact matching after normalisation; they do not detect fuzzy name matches.
- Ambiguous text dates are interpreted day-first (DD/MM/YYYY).
- The sample is small and synthetic; the results do not establish real-world accuracy or time savings.

## Possible next improvements

1. Configurable validation rules so operations teams can maintain allowed values without changing Python code.
2. Fuzzy duplicate suggestions for human review, without automatically merging records.
3. A simple upload-and-download interface.
4. Data-quality trend reporting across multiple files.

## Contribution and AI-use disclosure

I defined the business scenario and specified the expected validation behaviour, reporting outputs, test coverage and safe-execution requirements. The implementation was generated with AI assistance (Claude). I am reviewing the rules and behaviour and will distinguish my own verified changes from generated implementation.

## Tools and licence

Python · openpyxl · pytest · AI-assisted development

MIT License. All sample data is synthetic.
