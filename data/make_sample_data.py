"""Generate the synthetic sample workbook.

    python data/make_sample_data.py

Every name, email, phone number, PAN and GSTIN below is invented. Emails use
the reserved .example domain. PAN and GSTIN values are built to be
format-valid for testing only; they are not real registrations.

Each row is tagged with the outcome the validator should produce, and the
tags are written to expected_outcomes.csv so the tests (and a reader) can
check the validator against them.
"""

import csv
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validator.rules import gstin_check_character  # noqa: E402
from validator.schema import COLUMN_NAMES, STATE_CODES  # noqa: E402

HERE = Path(__file__).resolve().parent


def gstin(state, pan, entity="1"):
    body = STATE_CODES[state] + pan + entity + "Z"
    return body + gstin_check_character(body)


def row(sid, name, email, mobile, pan, gst, state, pin, onboarded, limit, terms):
    return dict(zip(COLUMN_NAMES,
                    [sid, name, email, mobile, pan, gst, state, pin, onboarded, limit, terms]))


P = {  # synthetic PANs (format-valid only)
    1: "XQZCA1001K", 2: "XQZFB1002L", 3: "XQZPC1003M", 4: "XQZCD1004N",
    5: "XQZFE1005P", 6: "XQZCF1006Q", 7: "XQZCG1007R", 8: "XQZPH1008S",
    9: "XQZCJ1009T", 10: "XQZFK1010U", 11: "XQZCL1011V", 12: "XQZCM1012W",
}

ROWS = [
    # --- rows that should be accepted -------------------------------------------------
    ("ACCEPTED", "", row("SUP-0001", "Asterwood Textiles Pvt Ltd", "accounts@asterwood.example",
                         "9999900001", P[1], gstin("Delhi", P[1]), "Delhi", "110001",
                         date(2026, 4, 6), 500000, 30)),
    ("ACCEPTED", "", row("SUP-0002", "Bluefinch Traders", "orders@bluefinch.example",
                         9999900002, P[2], gstin("Uttar Pradesh", P[2]), "Uttar Pradesh",
                         201301, date(2026, 4, 9), 250000, 45)),
    ("ACCEPTED", "mobile with +91 and spaces", row(
        "SUP-0003", "Cobalt Leaf Foods", "hello@cobaltleaf.example", "+91 99999 00003", P[3],
        None, "Haryana", "122001", "15/04/2026", "75,000", "15")),
    ("ACCEPTED", "", row("SUP-0004", "Dunmore Packaging Ltd", "ap@dunmore.example",
                         "9999900004", P[4], gstin("Maharashtra", P[4]), "Maharashtra",
                         "400001", date(2026, 5, 2), 1200000, 60)),
    ("ACCEPTED", "", row("SUP-0005", "Evergreen Agro Partners", "finance@evergreenagro.example",
                         "9999900005", P[5], gstin("Karnataka", P[5]), "karnataka",
                         "560001", date(2026, 5, 20), 300000, 30)),
    ("ACCEPTED_WITH_WARNING", "credit limit with advance terms", row(
        "SUP-0006", "Foxglove Electricals", "billing@foxglove.example", "9999900006", P[6],
        gstin("Tamil Nadu", P[6]), "Tamil Nadu", "600001", date(2026, 6, 1), 50000, 0)),
    # --- rows that should be rejected -------------------------------------------------
    ("REJECTED", "contact_email:MISSING", row(
        "SUP-0007", "Granite Hill Supplies", None, "9999900007", P[7],
        gstin("Gujarat", P[7]), "Gujarat", "380001", date(2026, 6, 3), 100000, 30)),
    ("REJECTED", "contact_email:BAD_FORMAT", row(
        "SUP-0008", "Harbourline Logistics", "ops@harbourline", "9999900008", P[8], None,
        "Kerala", "682001", date(2026, 6, 5), 150000, 30)),
    ("REJECTED", "contact_mobile:BAD_FORMAT", row(
        "SUP-0009", "Indigo Mill Works", "sales@indigomill.example", "999990009", P[9],
        gstin("Rajasthan", P[9]), "Rajasthan", "302001", date(2026, 6, 8), 90000, 15)),
    ("REJECTED", "pincode:BAD_FORMAT", row(
        "SUP-0010", "Juniper Office Supplies", "team@juniper.example", "9999900010", P[10],
        gstin("West Bengal", P[10]), "West Bengal", "070001", date(2026, 6, 10), 60000, 30)),
    ("REJECTED", "pan:BAD_FORMAT", row(
        "SUP-0011", "Kestrel Print House", "print@kestrel.example", "9999900011", "XQZC1011V",
        None, "Telangana", "500001", date(2026, 6, 12), 80000, 30)),
    ("REJECTED", "gstin:BAD_CHECKSUM", row(
        "SUP-0012", "Lumen Lighting Co", "accounts@lumen.example", "9999900012", P[12],
        gstin("Delhi", P[12])[:14] + ("A" if gstin("Delhi", P[12])[14] != "A" else "B"),
        "Delhi", "110002", date(2026, 6, 15), 200000, 45)),
    ("REJECTED", "gstin:PAN_MISMATCH", row(
        "SUP-0013", "Marigold Hygiene", "ap@marigold.example", "9999900013", "XQZCN1013X",
        gstin("Delhi", "XQZCN1013Y"), "Delhi", "110003", date(2026, 6, 18), 110000, 30)),
    ("REJECTED", "gstin:STATE_MISMATCH", row(
        "SUP-0014", "Northgate Steel", "steel@northgate.example", "9999900014", "XQZCP1014Z",
        gstin("Maharashtra", "XQZCP1014Z"), "Karnataka", "560002", date(2026, 6, 20),
        900000, 60)),
    ("REJECTED", "supplier_id:DUPLICATE_ID", row(
        "SUP-0003", "Orchid Florals", "flowers@orchid.example", "9999900015", "XQZFQ1015A",
        None, "Kerala", "682002", date(2026, 6, 22), 40000, 15)),
    ("REJECTED", "pan:DUPLICATE_PAN", row(
        "SUP-0016", "Bluefinch Traders (Noida)", "noida@bluefinch.example", "9999900016", P[2],
        None, "Uttar Pradesh", "201302", date(2026, 6, 24), 100000, 30)),
    ("REJECTED", "onboarding_date:FUTURE_DATE", row(
        "SUP-0017", "Quillstone Stationery", "q@quillstone.example", "9999900017", "XQZCR1017B",
        None, "Gujarat", "380002", date(2030, 1, 15), 30000, 30)),
    ("REJECTED", "credit_limit_inr:OUT_OF_RANGE", row(
        "SUP-0018", "Rivermint Beverages", "pay@rivermint.example", "9999900018", "XQZCS1018C",
        None, "Maharashtra", "411001", date(2026, 7, 1), 15000000, 45)),
    ("REJECTED", "payment_terms_days:UNKNOWN_VALUE", row(
        "SUP-0019", "Saffron Spice Exports", "trade@saffronspice.example", "9999900019",
        "XQZCT1019D", None, "Kerala", "682003", date(2026, 7, 3), 70000, 20)),
    ("REJECTED", "supplier_id:NUMERIC_CELL", row(
        1020, "Tidewater Marine Parts", "parts@tidewater.example", "9999900020", "XQZCU1020E",
        None, "Tamil Nadu", "600002", date(2026, 7, 6), 85000, 30)),
    ("REJECTED", "state:UNKNOWN_VALUE", row(
        "SUP-0021", "Umber Clay Ceramics", "studio@umberclay.example", "9999900021", "XQZFV1021F",
        None, "Bombay", "400002", date(2026, 7, 8), 45000, 15)),
]


def build(path=HERE / "sample_supplier_register.xlsx",
          expected_path=HERE / "expected_outcomes.csv"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Suppliers"
    ws.append(["Supplier onboarding register (SYNTHETIC DATA - fictional retailer)"])
    ws.append([])
    ws.append([*COLUMN_NAMES, "notes"])  # 'notes' is an unknown column on purpose
    expected = []
    for index, (outcome, reason, values) in enumerate(ROWS):
        if index == 6:
            ws.append([])  # a blank row the reader must skip
        ws.append([values[c] for c in COLUMN_NAMES] + [reason])
        expected.append((ws.max_row, values["supplier_id"], outcome, reason))
    wb.save(path)

    with open(expected_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["excel_row", "supplier_id", "expected_status", "expected_issue"])
        writer.writerows(expected)
    return path, expected_path


if __name__ == "__main__":
    for p in build():
        print(f"wrote {p}")
