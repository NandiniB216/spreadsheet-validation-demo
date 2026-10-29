"""The column contract for the demo workbook.

Every rule the validator applies is declared here as data, so a reviewer can
read the whole contract in one place without reading the checking code.

The domain is fictional: a supplier-onboarding register for an invented
retailer. All sample data in this repository is synthetic.
"""

from dataclasses import dataclass, field

# GST state codes for the states used in the synthetic data. This is a subset;
# extend it from the official GST state-code list before reusing elsewhere.
STATE_CODES = {
    "Delhi": "07",
    "Uttar Pradesh": "09",
    "Haryana": "06",
    "Rajasthan": "08",
    "West Bengal": "19",
    "Gujarat": "24",
    "Maharashtra": "27",
    "Karnataka": "29",
    "Kerala": "32",
    "Tamil Nadu": "33",
    "Telangana": "36",
}

PAYMENT_TERMS_DAYS = (0, 15, 30, 45, 60)
MAX_CREDIT_LIMIT_INR = 10_000_000


@dataclass(frozen=True)
class Column:
    name: str
    required: bool
    kind: str  # text | text_id | email | mobile | pincode | pan | gstin | state | date | money | choice
    description: str
    # Text IDs must never arrive as a number: a numeric cell may already have
    # lost leading zeros or been rounded, and the loss is invisible afterwards.
    choices: tuple = field(default=())


COLUMNS = (
    Column("supplier_id", True, "text_id", "Internal ID in the form SUP-0001"),
    Column("supplier_name", True, "text", "Registered business name, 2-100 characters"),
    Column("contact_email", True, "email", "Primary contact email"),
    Column("contact_mobile", True, "mobile", "10-digit Indian mobile; +91 prefix accepted"),
    Column("pan", True, "pan", "Permanent Account Number, e.g. ABCDE1234F"),
    Column("gstin", False, "gstin", "15-character GSTIN; optional for unregistered suppliers"),
    Column("state", True, "state", "State of the registered address"),
    Column("pincode", True, "pincode", "6-digit postal code"),
    Column("onboarding_date", True, "date", "Date the supplier was approved; not in the future"),
    Column("credit_limit_inr", True, "money", "Credit limit in rupees, 0 to 1,00,00,000"),
    Column("payment_terms_days", True, "choice", "One of 0, 15, 30, 45, 60",
           choices=PAYMENT_TERMS_DAYS),
)

COLUMN_NAMES = tuple(c.name for c in COLUMNS)
REQUIRED = tuple(c.name for c in COLUMNS if c.required)
BY_NAME = {c.name: c for c in COLUMNS}

# Output columns the validator appends to the results sheet.
STATUS_COLUMNS = ("validation_status", "errors", "warnings")
