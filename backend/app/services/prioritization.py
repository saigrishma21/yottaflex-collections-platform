"""Prioritization Engine: Computes explainable multi-factor collection priority scores.
Produces meaningful continuous variation based on DPD (40%), Balance (35%), and Risk (25%).
"""

from decimal import Decimal
from typing import Dict, Any


def score_collection_account(
    total_arrears: Decimal,
    days_past_due: int,
    risk_segment: str = "MEDIUM",
    loan_status: str = "ACTIVE",
    dispute_status: str = "NONE",
    is_hardship: bool = False,
    principal_amount: Decimal = None,
) -> Dict[str, Any]:
    """Calculate an explainable collection priority score and tier with full factor attribution.

    Continuous Multi-Factor Weights:
      - Days Past Due (DPD): 40% (delinquency urgency)
      - Outstanding Balance: 35% (financial exposure)
      - Customer Risk Profile: 25% (underwriting credit tier)
    """
    # 1. Statutory Exclusions
    if total_arrears <= Decimal("0.00") or loan_status == "PAID_OFF":
        return {
            "priority_score": Decimal("0.00"),
            "priority_level": "LOW",
            "eligible": False,
            "exclusion_reason": "PAID_OFF_ZERO_ARREARS",
            "action": "EXCLUDE_FROM_COLLECTIONS",
            "factors": [],
            "decision_summary": "Account has zero overdue arrears or is marked paid off.",
        }

    if dispute_status == "OPEN":
        return {
            "priority_score": Decimal("0.00"),
            "priority_level": "LOW",
            "eligible": False,
            "exclusion_reason": "DISPUTED_DEBT",
            "action": "ROUTE_DISPUTE_REVIEW",
            "factors": [],
            "decision_summary": "Active consumer dispute pending. Collection outreach is legally stayed.",
        }

    # 2. Continuous DPD Normalization (0 - 100)
    # Piecewise continuous curve avoiding hard clamping at 90 days
    dpd = max(0, days_past_due)
    if dpd <= 30:
        s_dpd = (dpd / 30.0) * 35.0
    elif dpd <= 90:
        s_dpd = 35.0 + ((dpd - 30) / 60.0) * 35.0
    elif dpd <= 270:
        s_dpd = 70.0 + ((dpd - 90) / 180.0) * 25.0
    else:
        s_dpd = 95.0 + min(5.0, ((dpd - 270) / 90.0) * 5.0)

    # 3. Continuous Balance Normalization (0 - 100)
    # Piecewise curve scaling smoothly across retail micro to high-ticket loans
    bal_float = float(total_arrears)
    if bal_float <= 20000:
        s_balance = (bal_float / 20000.0) * 30.0
    elif bal_float <= 80000:
        s_balance = 30.0 + ((bal_float - 20000.0) / 60000.0) * 35.0
    elif bal_float <= 300000:
        s_balance = 65.0 + ((bal_float - 80000.0) / 220000.0) * 25.0
    else:
        s_balance = 90.0 + min(10.0, ((bal_float - 300000.0) / 700000.0) * 10.0)

    # 4. Continuous Risk Normalization (0 - 100)
    # Incorporates base credit segment plus arrears-to-principal exposure ratio
    risk_seg = (risk_segment or "MEDIUM").upper()
    if principal_amount and float(principal_amount) > 0:
        exposure_ratio = min(1.0, bal_float / float(principal_amount))
    else:
        exposure_ratio = 0.5

    if risk_seg == "HIGH":
        s_risk = 80.0 + (exposure_ratio * 18.0)
    elif risk_seg == "MEDIUM":
        s_risk = 45.0 + (exposure_ratio * 20.0)
    else:  # LOW
        s_risk = 15.0 + (exposure_ratio * 20.0)

    # 5. Weighted Composite Calculation (DPD: 40%, Balance: 35%, Risk: 25%)
    c_dpd = s_dpd * 0.40
    c_balance = s_balance * 0.35
    c_risk = s_risk * 0.25
    raw_score = c_dpd + c_balance + c_risk

    # Hardship adjustment if under restructuring
    if is_hardship:
        raw_score = min(raw_score, 45.0)

    priority_score = Decimal(str(round(raw_score, 2)))

    # 6. Tier Mapping
    if priority_score >= 80.0:
        priority_level = "CRITICAL"
    elif priority_score >= 60.0:
        priority_level = "HIGH"
    elif priority_score >= 40.0:
        priority_level = "MEDIUM"
    else:
        priority_level = "LOW"

    factors = [
        {
            "factor_name": "Days Past Due (Delinquency Age)",
            "raw_value": f"{days_past_due} Days",
            "normalized_score": round(s_dpd, 1),
            "weight": 0.40,
            "weighted_contribution": round(c_dpd, 2),
        },
        {
            "factor_name": "Outstanding Balance Arrears",
            "raw_value": f"₹{bal_float:,.2f}",
            "normalized_score": round(s_balance, 1),
            "weight": 0.35,
            "weighted_contribution": round(c_balance, 2),
        },
        {
            "factor_name": "Customer Risk Profile",
            "raw_value": f"{risk_seg} (Exposure: {int(exposure_ratio * 100)}%)",
            "normalized_score": round(s_risk, 1),
            "weight": 0.25,
            "weighted_contribution": round(c_risk, 2),
        },
    ]

    summary = (
        f"{priority_level} priority: {days_past_due} DPD with ₹{bal_float:,.2f} arrears "
        f"on {risk_seg} risk profile."
    )

    return {
        "priority_score": priority_score,
        "priority_level": priority_level,
        "eligible": True,
        "exclusion_reason": None,
        "action": "SCHEDULE_OUTREACH",
        "factors": factors,
        "decision_summary": summary,
    }
