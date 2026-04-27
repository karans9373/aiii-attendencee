from __future__ import annotations

from collections import Counter
from statistics import mean


def productivity_score(hours_logged: float, overtime_hours: float, attendance_ratio: float) -> int:
    score = 55 + attendance_ratio * 25 + min(hours_logged, 9) * 2.2 + overtime_hours * 1.5
    return max(45, min(98, int(score)))


def burnout_risk(hours_logged: float, overtime_hours: float, late_minutes: int) -> str:
    risk_index = hours_logged * 0.8 + overtime_hours * 2.5 + late_minutes * 0.04
    if risk_index >= 18:
        return "high"
    if risk_index >= 11:
        return "medium"
    return "low"


def mood_detection_simulation(liveness_score: float, late_minutes: int) -> str:
    if late_minutes > 20:
        return "stressed"
    if liveness_score > 0.97:
        return "focused"
    return "calm"


def suspicious_punch_pattern(device_names: list[str], geo_tags: list[str]) -> bool:
    device_count = len(Counter(device_names))
    geo_count = len(Counter([item for item in geo_tags if item]))
    return device_count > 2 or geo_count > 2


def shift_optimization_suggestion(department_name: str, avg_hours: float, absence_ratio: float) -> str:
    if absence_ratio > 0.18:
        return f"{department_name}: add one swing-shift backup to stabilize absenteeism."
    if avg_hours > 9.2:
        return f"{department_name}: split peak workload across staggered shifts to cut overtime."
    return f"{department_name}: current staffing is healthy, maintain present shift structure."


def fraud_detector(statuses: list[str], late_minutes: list[int]) -> str:
    if statuses.count("late") >= 4 and mean(late_minutes or [0]) > 18:
        return "Repeated late entries suggest buddy punching or shift misuse."
    return "No major attendance fraud pattern detected."
