from __future__ import annotations

from datetime import date

from flask import Flask, render_template, request, url_for

app = Flask(__name__)

NAV_ITEMS = [
    ("dashboard", "Executive Dashboard"),
    ("enrollment", "Employee Enrollment"),
    ("kiosk", "Biometric Entry"),
    ("attendance", "Attendance History"),
    ("payroll", "Payroll Automation"),
    ("reports", "Reports"),
]

USERS = [
    {
        "id": 1,
        "name": "Ananya Rao",
        "email": "admin@workpulse.ai",
        "role": "Admin",
        "employee_code": "WPA-001",
        "branch": "Bengaluru HQ",
        "title": "Operations Director",
    },
    {
        "id": 2,
        "name": "Rahul Mehta",
        "email": "hr@workpulse.ai",
        "role": "HR",
        "employee_code": "WPA-002",
        "branch": "Bengaluru HQ",
        "title": "People Operations Lead",
    },
    {
        "id": 3,
        "name": "Priya Sharma",
        "email": "employee@workpulse.ai",
        "role": "Employee",
        "employee_code": "WPA-003",
        "branch": "Mumbai Branch",
        "title": "Site Supervisor",
    },
]

DASHBOARD = {
    "summary": [
        {"label": "Present Today", "value": "148", "change": "+12%"},
        {"label": "Late Employees", "value": "09", "change": "-6%"},
        {"label": "Payroll Due", "value": "31", "change": "+4%"},
        {"label": "Overtime Hours", "value": "126h", "change": "+18%"},
    ],
    "attendance_breakdown": [
        {"name": "Present", "value": 78, "color": "mint"},
        {"name": "Late", "value": 12, "color": "blue"},
        {"name": "Absent", "value": 10, "color": "coral"},
    ],
    "monthly_trends": [
        {"month": "Jan", "attendance": 84},
        {"month": "Feb", "attendance": 88},
        {"month": "Mar", "attendance": 90},
        {"month": "Apr", "attendance": 92},
    ],
    "live_feed": [
        {"employee": "Priya Sharma", "branch": "Mumbai", "geo_tag": "Gate A", "mood": "Focused", "presence": "Live"},
        {"employee": "Arjun Das", "branch": "Bengaluru", "geo_tag": "HQ Lobby", "mood": "Stressed", "presence": "Flagged"},
        {"employee": "Rahul Mehta", "branch": "Bengaluru", "geo_tag": "Remote", "mood": "Calm", "presence": "Live"},
    ],
}

ATTENDANCE_HISTORY = [
    {"id": 1, "date": "2026-04-26", "mode": "Face", "geo_tag": "Mumbai Branch", "hours": "8.4", "status": "Present"},
    {"id": 2, "date": "2026-04-25", "mode": "Fingerprint", "geo_tag": "Mumbai Branch", "hours": "8.1", "status": "Present"},
    {"id": 3, "date": "2026-04-24", "mode": "Face", "geo_tag": "Mumbai Branch", "hours": "7.6", "status": "Late"},
]

PAYROLL_HISTORY = [
    {"id": 1, "month": "2026-04", "gross": "62000", "tax": "3580", "net": "58420"},
    {"id": 2, "month": "2026-03", "gross": "62000", "tax": "3510", "net": "58490"},
]

MOBILE_INSIGHTS = [
    {"label": "AI Productivity Score", "value": "82 / 100"},
    {"label": "Burnout Risk", "value": "Low"},
    {"label": "Shift Suggestion", "value": "Current schedule is healthy"},
]


def selected_user() -> dict:
    requested = request.args.get("user", "3")
    for user in USERS:
        if str(user["id"]) == requested:
            return user
    return USERS[-1]


@app.context_processor
def inject_globals() -> dict:
    return {"nav_items": NAV_ITEMS, "today_month": date.today().strftime("%Y-%m")}


@app.get("/")
def dashboard() -> str:
    active_section = request.args.get("section", "dashboard")
    theme = request.args.get("theme", "dark")
    current_user = selected_user()
    next_theme = "light" if theme == "dark" else "dark"
    return render_template(
        "dashboard.html",
        active_section=active_section,
        theme=theme,
        next_theme=next_theme,
        dashboard=DASHBOARD,
        users=USERS,
        current_user=current_user,
        attendance_history=ATTENDANCE_HISTORY,
        payroll_history=PAYROLL_HISTORY,
        monthly_summary={
            "present_days": 22,
            "late_days": 2,
            "overtime_hours": 11,
            "estimated_income": "58420.00",
            "payable_days": 22,
        },
    )


@app.get("/mobile")
def mobile() -> str:
    return render_template(
        "mobile.html",
        profile=USERS[-1],
        status="Connected",
        attendance_today={"status": "Checked in", "mode": "Face ID", "mood": "Focused"},
        salary_snapshot={"net_salary": "58420"},
        insights=MOBILE_INSIGHTS,
    )


@app.get("/desktop")
def desktop_redirect() -> str:
    return render_template("desktop_hint.html", mobile_url=url_for("mobile"), dashboard_url=url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
