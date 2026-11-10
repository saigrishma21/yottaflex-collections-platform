"""Unit tests for Contact Scheduler and Compliance detection."""

import pytest
from datetime import datetime, time
from decimal import Decimal
from backend.app.models.entities import ContactPreference, ContactAttempt
from backend.app.services.contact_scheduler import validate_contact_schedule
from backend.app.services.compliance import scan_compliance_violations
from backend.app.database import SessionLocal


def test_dnc_contact_blocked():
    """Verify customer on Do Not Call register is blocked."""
    pref = ContactPreference(
        preference_id="PREF-001",
        customer_id="CUST-001",
        preferred_channel="PHONE",
        contact_start_time="09:00:00",
        contact_end_time="18:00:00",
        do_not_call=True,
        contact_allowed=False,
    )
    res = validate_contact_schedule(pref, datetime(2026, 10, 20, 11, 0, 0))
    assert res["allowed"] is False
    assert res["status"] == "BLOCKED_DNC"


def test_outside_window_blocked():
    """Verify attempt at 21:30 is blocked when allowed window is 09:00 to 18:00."""
    pref = ContactPreference(
        preference_id="PREF-002",
        customer_id="CUST-002",
        preferred_channel="PHONE",
        contact_start_time="09:00:00",
        contact_end_time="18:00:00",
        do_not_call=False,
        contact_allowed=True,
    )
    # Attempt at 21:30 (night)
    res = validate_contact_schedule(pref, datetime(2026, 10, 20, 21, 30, 0))
    assert res["allowed"] is False
    assert res["status"] == "BLOCKED_OUTSIDE_WINDOW"


def test_compliant_window_allowed():
    """Verify attempt at 14:00 is allowed."""
    pref = ContactPreference(
        preference_id="PREF-003",
        customer_id="CUST-003",
        preferred_channel="PHONE",
        contact_start_time="09:00:00",
        contact_end_time="18:00:00",
        do_not_call=False,
        contact_allowed=True,
    )
    res = validate_contact_schedule(pref, datetime(2026, 10, 20, 14, 0, 0))
    assert res["allowed"] is True
    assert res["status"] == "SCHEDULED"


def test_compliance_scanner_identifies_injected_anomalies():
    """Verify that scan_compliance_violations catches all 5 injected negative scenarios in the DB."""
    db = SessionLocal()
    try:
        violations = scan_compliance_violations(db)
        assert len(violations) > 0

        violation_codes = {v["violation_code"] for v in violations}
        assert "ERR_PAID_IN_COLLECTION" in violation_codes
        assert "ERR_OUTSIDE_CONTACT_WINDOW" in violation_codes
        assert "ERR_WRONG_PAYMENT_ALLOCATION" in violation_codes
        assert "ERR_PROMISE_EXCEEDS_ARREARS" in violation_codes
        assert "ERR_DISPUTED_TREATED_CONFIRMED" in violation_codes
    finally:
        db.close()
