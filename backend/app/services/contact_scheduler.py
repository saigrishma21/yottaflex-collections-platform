"""Contact Scheduler & Compliance Guard: Enforces fair communication practices.
Timezone-aware permissible window validation and cross-account frequency caps.
"""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from backend.app.models.entities import ContactPreference, ContactAttempt


def parse_time_str(time_str: str) -> time:
    """Safely parse time string like '09:00:00' or '09:00' to time object."""
    parts = [int(p) for p in time_str.split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1], 0)
    return time(parts[0], parts[1], parts[2])


def get_borrower_local_time(
    dt: datetime,
    borrower_tz_str: Optional[str] = None,
    source_tz_str: Optional[str] = None,
) -> datetime:
    """Convert a scheduled datetime to the customer's stored local timezone."""
    if not borrower_tz_str:
        return dt
    try:
        target_tz = ZoneInfo(borrower_tz_str)
        if dt.tzinfo is not None:
            # Timezone-aware: convert directly to target timezone
            return dt.astimezone(target_tz)
        elif source_tz_str:
            src_tz = ZoneInfo(source_tz_str)
            return dt.replace(tzinfo=src_tz).astimezone(target_tz)
        else:
            return dt
    except Exception:
        return dt


def validate_contact_schedule(
    preference: ContactPreference,
    scheduled_datetime: datetime,
    recent_attempts: List[ContactAttempt] = None,
    max_weekly_attempts: int = 3,
    contact_channel: Optional[str] = None,
    source_timezone: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate whether an outreach attempt complies with preferences, timezones, and regulatory constraints."""
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

    # 2. Timezone-Aware Permissible Window Check
    borrower_tz = getattr(preference, "timezone", None)
    local_dt = get_borrower_local_time(
        scheduled_datetime,
        borrower_tz_str=borrower_tz,
        source_tz_str=source_timezone,
    )

    start_t = parse_time_str(preference.contact_start_time)
    end_t = parse_time_str(preference.contact_end_time)
    attempt_time = local_dt.time()

    if attempt_time < start_t or attempt_time > end_t:
        tz_label = f" ({borrower_tz})" if borrower_tz else ""
        return {
            "allowed": False,
            "status": "BLOCKED_OUTSIDE_WINDOW",
            "reason": (
                f"Scheduled local time ({attempt_time.strftime('%H:%M:%S')}{tz_label}) falls outside "
                f"permissible contact window ({start_t.strftime('%H:%M:%S')} to {end_t.strftime('%H:%M:%S')})."
            ),
            "preferred_channel": preference.preferred_channel,
        }

    # 3. Weekly Frequency Limits Check (e.g. max 3 voice contacts in rolling 7 days across borrower accounts)
    # Evaluates the actual proposed contact channel (defaults to preferred_channel if omitted)
    channel_to_eval = (contact_channel or preference.preferred_channel or "PHONE").upper()
    seven_days_ago = local_dt.replace(tzinfo=None) - timedelta(days=7)
    voice_attempts_7d = [
        att for att in recent_attempts
        if att.contact_time >= seven_days_ago and att.contact_channel.upper() == "PHONE"
    ]

    if channel_to_eval == "PHONE" and len(voice_attempts_7d) >= max_weekly_attempts:
        return {
            "allowed": False,
            "status": "BLOCKED_FREQUENCY_LIMIT",
            "reason": (
                f"Maximum rolling 7-day voice contact limit ({max_weekly_attempts}) "
                f"reached for borrower across all credit accounts."
            ),
            "preferred_channel": preference.preferred_channel,
        }

    # All checks satisfied
    return {
        "allowed": True,
        "status": "SCHEDULED",
        "reason": "Outreach complies with permissible contact hours and regulatory frequency caps.",
        "preferred_channel": preference.preferred_channel,
    }

