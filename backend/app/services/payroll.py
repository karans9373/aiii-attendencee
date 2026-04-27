from __future__ import annotations

from collections import defaultdict

from app.models import AttendanceLog, PayrollRecord, User


def calculate_payroll_for_month(users: list[User], attendance_logs: list[AttendanceLog], month_label: str) -> list[PayrollRecord]:
    grouped_logs = defaultdict(list)
    for log in attendance_logs:
        grouped_logs[log.user_id].append(log)

    records: list[PayrollRecord] = []
    for user in users:
        logs = grouped_logs.get(user.id, [])
        working_days = 22
        present_days = len(logs)
        overtime_hours = sum(item.overtime_hours for item in logs)
        late_penalty = sum(item.late_minutes for item in logs) * 2.5
        leave_deduction = max(0, working_days - present_days) * (
            (user.base_salary / working_days) if user.salary_type == "monthly" and user.base_salary else user.daily_wage
        )

        if user.salary_type == "daily":
            gross_salary = present_days * user.daily_wage
        else:
            gross_salary = user.base_salary

        overtime_pay = overtime_hours * max((user.base_salary / 176) if user.base_salary else user.daily_wage / 8, 120)
        bonus = 3000 if overtime_hours > 18 else 1000 if overtime_hours > 10 else 0
        tax_deduction = gross_salary * 0.07
        net_salary = gross_salary + overtime_pay + bonus - leave_deduction - late_penalty - tax_deduction

        records.append(
            PayrollRecord(
                user_id=user.id,
                month_label=month_label,
                working_days=working_days,
                payable_days=present_days,
                gross_salary=round(gross_salary, 2),
                overtime_pay=round(overtime_pay, 2),
                bonus=round(bonus, 2),
                leave_deduction=round(leave_deduction, 2),
                late_penalty=round(late_penalty, 2),
                tax_deduction=round(tax_deduction, 2),
                net_salary=round(net_salary, 2),
                status="processed",
            )
        )
    return records
