"""Row-level and file-level validation."""

from collections import defaultdict
from dataclasses import dataclass, field

from .reader import Row, Workbook
from .rules import Issue, check_cross_field, check_field
from .schema import COLUMN_NAMES


@dataclass
class RowResult:
    row: Row
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def status(self):
        return "REJECTED" if self.errors else "ACCEPTED"


@dataclass
class ValidationResult:
    workbook: Workbook
    results: list

    @property
    def accepted(self):
        return [r for r in self.results if r.status == "ACCEPTED"]

    @property
    def rejected(self):
        return [r for r in self.results if r.status == "REJECTED"]

    def issue_counts(self):
        counts = defaultdict(int)
        for r in self.results:
            for issue in r.errors + r.warnings:
                counts[(issue.severity, issue.column, issue.code)] += 1
        return dict(sorted(counts.items()))


def _split(issues):
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    return errors, warnings


def validate_rows(workbook, today=None):
    results = []
    for row in workbook.rows:
        issues = list(row.issues)
        for column in COLUMN_NAMES:
            issues.extend(check_field(column, row.values[column], today=today))
        issues.extend(check_cross_field(row.values))
        errors, warnings = _split(issues)
        results.append(RowResult(row=row, errors=errors, warnings=warnings))

    _flag_duplicates(results, "supplier_id", "DUPLICATE_ID",
                     "supplier_id already used on row {first}")
    _flag_duplicates(results, "pan", "DUPLICATE_PAN",
                     "same PAN as row {first}; possible duplicate supplier")
    return ValidationResult(workbook=workbook, results=results)


def _flag_duplicates(results, column, code, template):
    """Reject the second and later rows that repeat a value; keep the first."""
    first_seen = {}
    for result in results:
        value = result.row.values.get(column)
        if not value:
            continue
        if value in first_seen:
            result.errors.append(Issue(column, code,
                                       template.format(first=first_seen[value])))
        else:
            first_seen[value] = result.row.excel_row
