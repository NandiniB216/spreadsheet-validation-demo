from datetime import date

import pytest

from validator.reader import normalise_cell
from validator.rules import check_cross_field, check_field, gstin_check_character

TODAY = date(2026, 10, 1)


def codes(issues):
    return [i.code for i in issues]


def make_gstin(state_code, pan):
    body = state_code + pan + "1Z"
    return body + gstin_check_character(body)


@pytest.mark.parametrize("value", ["accounts@asterwood.example", "a.b+c@sub.domain.example"])
def test_valid_emails_pass(value):
    assert check_field("contact_email", value) == []


@pytest.mark.parametrize("value", ["ops@harbourline", "no-at-sign.example", "a@b@c.example"])
def test_invalid_emails_fail(value):
    assert codes(check_field("contact_email", value)) == ["BAD_FORMAT"]


def test_missing_required_field_is_reported():
    assert codes(check_field("contact_email", None)) == ["MISSING"]


def test_missing_optional_field_is_fine():
    assert check_field("gstin", None) == []


@pytest.mark.parametrize("raw,expected", [
    (9999900002, "9999900002"),          # number cell
    (9999900002.0, "9999900002"),        # float cell from Excel
    ("+91 99999 00003", "9999900003"),
    ("919999900004", "9999900004"),
    ("09999900005", "9999900005"),
    ("99999-00006", "9999900006"),
])
def test_mobile_normalisation(raw, expected):
    value, issues = normalise_cell("contact_mobile", raw)
    assert value == expected and issues == []
    assert check_field("contact_mobile", value) == []


@pytest.mark.parametrize("value", ["999990009", "5999900001", "99999000011"])
def test_bad_mobiles_fail(value):
    assert codes(check_field("contact_mobile", value)) == ["BAD_FORMAT"]


def test_pincode_cannot_start_with_zero():
    assert codes(check_field("pincode", "070001")) == ["BAD_FORMAT"]
    assert check_field("pincode", "110001") == []


def test_numeric_pincode_cell_is_accepted():
    value, issues = normalise_cell("pincode", 201301)
    assert value == "201301" and issues == []


def test_fractional_pincode_is_not_silently_rounded():
    value, _ = normalise_cell("pincode", 110001.5)
    assert codes(check_field("pincode", value)) == ["BAD_FORMAT"]


def test_identifier_stored_as_number_is_flagged():
    value, issues = normalise_cell("supplier_id", 1020)
    assert codes(issues) == ["NUMERIC_CELL"]
    assert codes(check_field("supplier_id", value)) == ["BAD_FORMAT"]


@pytest.mark.parametrize("value,ok", [
    ("XQZCA1001K", True),
    ("XQZC1011V", False),     # too short
    ("XQZXA1001K", False),    # 4th character is not a valid entity type
    ("12345ABCDE", False),
])
def test_pan_format(value, ok):
    assert (check_field("pan", value) == []) is ok


def test_gstin_checksum_round_trip():
    good = make_gstin("07", "XQZCA1001K")
    assert check_field("gstin", good) == []
    typo = good[:14] + ("A" if good[14] != "A" else "B")
    assert codes(check_field("gstin", typo)) == ["BAD_CHECKSUM"]


def test_gstin_must_contain_the_pan():
    row = {"pan": "XQZCN1013X", "gstin": make_gstin("07", "XQZCN1013Y"), "state": "Delhi"}
    assert codes(check_cross_field(row)) == ["PAN_MISMATCH"]


def test_gstin_state_code_must_match_state():
    row = {"pan": "XQZCP1014Z", "gstin": make_gstin("27", "XQZCP1014Z"), "state": "Karnataka"}
    assert codes(check_cross_field(row)) == ["STATE_MISMATCH"]


def test_future_date_rejected_and_past_date_accepted():
    assert codes(check_field("onboarding_date", date(2030, 1, 15), today=TODAY)) == ["FUTURE_DATE"]
    assert check_field("onboarding_date", date(2026, 4, 6), today=TODAY) == []


@pytest.mark.parametrize("raw,expected", [
    ("15/04/2026", date(2026, 4, 15)),
    ("2026-04-15", date(2026, 4, 15)),
    ("15-04-2026", date(2026, 4, 15)),
])
def test_text_dates_are_parsed(raw, expected):
    value, _ = normalise_cell("onboarding_date", raw)
    assert value == expected


def test_unparseable_date_is_reported():
    value, _ = normalise_cell("onboarding_date", "next Tuesday")
    assert codes(check_field("onboarding_date", value, today=TODAY)) == ["BAD_DATE"]


@pytest.mark.parametrize("raw,expected", [("75,000", 75000), ("₹ 1,20,000", 120000), (5e5, 5e5)])
def test_money_normalisation(raw, expected):
    value, _ = normalise_cell("credit_limit_inr", raw)
    assert value == expected and check_field("credit_limit_inr", value) == []


@pytest.mark.parametrize("value,code", [(-1, "OUT_OF_RANGE"), (15_000_000, "OUT_OF_RANGE"),
                                        ("lots", "NOT_A_NUMBER")])
def test_money_out_of_range(value, code):
    assert codes(check_field("credit_limit_inr", value)) == [code]


def test_payment_terms_must_be_an_allowed_value():
    assert codes(check_field("payment_terms_days", 20)) == ["UNKNOWN_VALUE"]
    value, _ = normalise_cell("payment_terms_days", "30")
    assert check_field("payment_terms_days", value) == []


def test_advance_terms_with_credit_is_only_a_warning():
    issues = check_cross_field({"credit_limit_inr": 50000, "payment_terms_days": 0})
    assert [(i.code, i.severity) for i in issues] == [("TERMS_CONFLICT", "warning")]
