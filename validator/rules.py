"""Field-level rules.

Each check takes an already-normalised value and returns a list of Issue
objects (empty when the value passes). Checks never raise on bad data: a bad
value is a finding to report, not a crash.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

from .schema import BY_NAME, MAX_CREDIT_LIMIT_INR, STATE_CODES


@dataclass(frozen=True)
class Issue:
    column: str
    code: str
    message: str
    severity: str = "error"  # error rejects the row; warning does not


SUPPLIER_ID_RE = re.compile(r"^SUP-\d{4}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
PINCODE_RE = re.compile(r"^[1-9]\d{5}$")
PAN_RE = re.compile(r"^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$")
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

_GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_check_character(first_14: str) -> str:
    """Return the 15th (check) character for the first 14 characters of a GSTIN.

    Mod-36 scheme: each character's value is multiplied by alternating
    factors 1 and 2; the quotient and remainder of each product by 36 are
    summed; the check value makes the total a multiple of 36.
    """
    total = 0
    for position, char in enumerate(first_14):
        product = _GSTIN_CHARSET.index(char) * (1 if position % 2 == 0 else 2)
        total += product // 36 + product % 36
    return _GSTIN_CHARSET[(36 - total % 36) % 36]


def _required(column, value):
    if value is None or value == "":
        return [Issue(column, "MISSING", f"{column} is required")]
    return []


def check_text_id(column, value):
    if not SUPPLIER_ID_RE.match(value):
        return [Issue(column, "BAD_FORMAT", f"'{value}' is not in the form SUP-0001")]
    return []


def check_text(column, value):
    if not 2 <= len(value) <= 100:
        return [Issue(column, "BAD_LENGTH", "must be 2 to 100 characters")]
    return []


def check_email(column, value):
    if not EMAIL_RE.match(value):
        return [Issue(column, "BAD_FORMAT", f"'{value}' is not a valid email address")]
    return []


def check_mobile(column, value):
    if not MOBILE_RE.match(value):
        return [Issue(column, "BAD_FORMAT",
                      "must be 10 digits starting with 6-9 (after removing +91)")]
    return []


def check_pincode(column, value):
    if not PINCODE_RE.match(value):
        return [Issue(column, "BAD_FORMAT", "must be 6 digits and cannot start with 0")]
    return []


def check_pan(column, value):
    if not PAN_RE.match(value):
        return [Issue(column, "BAD_FORMAT", f"'{value}' is not a valid PAN format")]
    return []


def check_gstin(column, value):
    if not GSTIN_RE.match(value):
        return [Issue(column, "BAD_FORMAT", f"'{value}' is not a valid GSTIN format")]
    expected = gstin_check_character(value[:14])
    if value[14] != expected:
        return [Issue(column, "BAD_CHECKSUM",
                      f"check character is '{value[14]}', expected '{expected}' (likely a typo)")]
    return []


def check_state(column, value):
    if value not in STATE_CODES:
        return [Issue(column, "UNKNOWN_VALUE", f"'{value}' is not in the allowed state list")]
    return []


def check_date(column, value, today=None):
    today = today or date.today()
    if not isinstance(value, date):
        return [Issue(column, "BAD_DATE", f"'{value}' is not a date (use YYYY-MM-DD)")]
    if value > today:
        return [Issue(column, "FUTURE_DATE", f"{value.isoformat()} is in the future")]
    return []


def check_money(column, value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return [Issue(column, "NOT_A_NUMBER", f"'{value}' is not a number")]
    if value < 0 or value > MAX_CREDIT_LIMIT_INR:
        return [Issue(column, "OUT_OF_RANGE", f"{value:,} is outside 0 to {MAX_CREDIT_LIMIT_INR:,}")]
    return []


def check_choice(column, value):
    allowed = BY_NAME[column].choices
    if value not in allowed:
        return [Issue(column, "UNKNOWN_VALUE",
                      f"'{value}' is not one of {', '.join(str(a) for a in allowed)}")]
    return []


CHECKS = {
    "text_id": check_text_id,
    "text": check_text,
    "email": check_email,
    "mobile": check_mobile,
    "pincode": check_pincode,
    "pan": check_pan,
    "gstin": check_gstin,
    "state": check_state,
    "date": check_date,
    "money": check_money,
    "choice": check_choice,
}


def check_field(column, value, today=None):
    """Run the required-check and the kind-specific check for one cell."""
    spec = BY_NAME[column]
    if value is None or value == "":
        return _required(column, value) if spec.required else []
    if spec.kind == "date":
        return check_date(column, value, today=today)
    return CHECKS[spec.kind](column, value)


def check_cross_field(row):
    """Rules that need more than one column of the same row."""
    issues = []
    pan, gstin, state = row.get("pan"), row.get("gstin"), row.get("state")
    if gstin and pan and GSTIN_RE.match(gstin) and gstin[2:12] != pan:
        issues.append(Issue("gstin", "PAN_MISMATCH",
                            "characters 3-12 of the GSTIN must equal the PAN"))
    if gstin and state in STATE_CODES and GSTIN_RE.match(gstin) \
            and gstin[:2] != STATE_CODES[state]:
        issues.append(Issue("gstin", "STATE_MISMATCH",
                            f"GSTIN state code {gstin[:2]} does not match {state} "
                            f"({STATE_CODES[state]})"))
    if row.get("credit_limit_inr") not in (None, "") and row.get("payment_terms_days") == 0 \
            and isinstance(row.get("credit_limit_inr"), (int, float)) \
            and row["credit_limit_inr"] > 0:
        issues.append(Issue("credit_limit_inr", "TERMS_CONFLICT",
                            "a credit limit above 0 with 0-day (advance) terms is unusual; "
                            "confirm with finance", severity="warning"))
    return issues


def parse_date(value):
    """Turn a cell value into a date, or return it unchanged if it cannot be."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return value
