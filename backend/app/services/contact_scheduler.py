"""Contact Scheduler & Compliance Guard: Enforces fair communication practices.
"""

from datetime import datetime, time, timedelta
from typing import Dict, Any, List
from backend.app.models.entities import ContactPreference, ContactAttempt


def parse_time_str(time_str: str) -> time:
    """Safely parse time string like '09:00:00' or '09:00' to time object."""
    parts = [int(p) for p in time_str.split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1], 0)
    return time(parts[0], parts[1], parts[2])


def validate_contact_schedule(
    preference: ContactPreference,
    scheduled_datetime: datetime,
    recent_attempts: List[ContactAttempt] = None,
    max_weekly_attempts: int = 3,
) -> Dict[str, Any]:
    """Validate whether an outreach attempt complies with preferences and regulatory constraints."""
    if recent_attempts is None:
        recent_attempts = []

    # 1. Statutory Do Not Call & Consent Check
    if preference.do_not_call or not preference.contact_allowed:
        return {
            "allowed": False,
            "status": "BLOCKED_DNC",
            "reason": "Borrower is on statutory Do Not Call register or has revoked contact consent.",
            "preferred_channel": preference.preferred_channel,
        }

    # 2. Permissible Window Check
    start_t = parse_time_str(preference.contact_start_time)
    end_t = parse_time_str(preference.contact_end_time)
    attempt_time = scheduled_datetime.time()

    if attempt_time < start_t or attempt_time > end_t:
        return {
            "allowed": False,
            "status": "BLOCKED_OUTSIDE_WINDOW",
            "reason": (
                f"Scheduled time ({attempt_time.strftime('%H:%M:%S')}) falls outside "
                f"permissible contact window ({start_t.strftime('%H:%M:%S')} to {end_t.strftime('%H:%M:%S')})."
            ),
            "preferred_channel": preference.preferred_channel,
        }

    # 3. Weekly Frequency Limits Check (e.g. max 3 phone contacts in rolling 7 days)
    seven_days_ago = scheduled_datetime - timedelta(days=7)
    voice_attempts_7d = [
        att for att in recent_attempts
        if att.contact_time >= seven_days_ago and att.contact_channel == "PHONE"
    ]

    if preference.preferred_channel == "PHONE" and len(voice_attempts_7d) >= max_weekly_attempts:
        return {
            "allowed": False,
            "status": "BLOCKED_FREQUENCY_LIMIT",
            "reason": f"Maximum rolling 7-day voice contact limit ({max_weekly_attempts}) reached for borrower.",
            "preferred_channel": preference.preferred_channel,
        }

    # All checks satisfied
    return {
        "allowed": True,
        "status": "SCHEDULED",
        "reason": "Outreach complies with permissible contact hours and regulatory frequency caps.",
        "preferred_channel": preference.preferred_channel,
    }
