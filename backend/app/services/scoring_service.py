"""Lead scoring (section 12). Fixed point table for now — apply per activity
as it's logged, clamped to [0, 100].

ponytail: rules are a hardcoded dict, not per-organization configurable yet.
Upgrade path: move ACTIVITY_SCORE_DELTA into an org-level settings table (or
a `lead_scoring_rules` table) once a customer actually asks to tune it.
"""
ACTIVITY_SCORE_DELTA: dict[str, int] = {
    "budget_confirmed": 15,
    "timeline_under_30_days": 20,
    "responded": 10,
    "visit_requested": 25,
    "property_shortlisted": 15,
    "financing_approved": 15,
    "no_response_30_days": -10,
}


def score_delta_for_activity(activity_type: str) -> int:
    return ACTIVITY_SCORE_DELTA.get(activity_type, 0)


def apply_score_delta(current_score: int, activity_type: str) -> int:
    delta = score_delta_for_activity(activity_type)
    return max(0, min(100, current_score + delta))
