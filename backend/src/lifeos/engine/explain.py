"""Human-readable recommendation explanations."""

from __future__ import annotations

from lifeos.schemas.results import ScoreBreakdown


def explain_breakdown(b: ScoreBreakdown) -> str:
    """Turn a score breakdown into a short human-readable rationale."""
    reasons: list[str] = []

    if b.slack_minutes is not None and b.slack_minutes < 12 * 60:
        if b.slack_minutes < 0:
            reasons.append("already infeasible — act now")
        else:
            hours = b.slack_minutes / 60
            reasons.append(f"only {hours:.0f}h slack before deadline")

    if b.urgency >= 0.6:
        reasons.append("urgent deadline")
    elif b.importance >= 0.75:
        reasons.append("high-stakes goal")

    if b.goal_alignment >= 0.9:
        reasons.append("directly advances a top goal")
    elif b.goal_alignment <= 0.3:
        reasons.append("weak goal link")

    if b.balance_boost >= 0.05:
        reasons.append("area is underserved — balance nudge")

    if b.time_cost >= 0.5:
        reasons.append("good leverage per hour")

    if not reasons:
        reasons.append("best balance of urgency and importance")

    return "; ".join(reasons[:3])


def overload_label(severity: str) -> str:
    labels = {
        "green": "OK — capacity looks manageable",
        "yellow": "TIGHT — schedule conflicts detected",
        "red": "OVERLOADED — deadlines at risk",
    }
    return labels.get(severity, severity)
