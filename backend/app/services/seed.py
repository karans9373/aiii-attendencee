from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    AttendanceLog,
    AuditLog,
    Department,
    FaceProfile,
    FingerprintProfile,
    LeaveRequest,
    Notification,
    User,
)


def seed_database(db: Session) -> None:
    existing_user = db.scalar(select(User).limit(1))
    if existing_user:
        return

    engineering = Department(name="Engineering", branch="Bengaluru", headcount=18)
    hr = Department(name="People Operations", branch="Bengaluru", headcount=5)
    field = Department(name="Field Ops", branch="Mumbai", headcount=12)
    db.add_all([engineering, hr, field])
    db.flush()

    users = [
        User(
            full_name="Ananya Rao",
            email="admin@workpulse.ai",
            password_hash=hash_password("Admin@123"),
            role="admin",
            employee_code="WPA-001",
            department_id=engineering.id,
            branch="Bengaluru HQ",
            title="Operations Director",
            salary_type="monthly",
            base_salary=135000,
            shift_name="Leadership",
        ),
        User(
            full_name="Rahul Mehta",
            email="hr@workpulse.ai",
            password_hash=hash_password("Hr@12345"),
            role="hr",
            employee_code="WPA-014",
            department_id=hr.id,
            branch="Bengaluru HQ",
            title="HR Manager",
            salary_type="monthly",
            base_salary=82000,
            shift_name="General",
        ),
        User(
            full_name="Priya Sharma",
            email="employee@workpulse.ai",
            password_hash=hash_password("Emp@12345"),
            role="employee",
            employee_code="WPA-028",
            department_id=field.id,
            branch="Mumbai Branch",
            title="Site Supervisor",
            salary_type="monthly",
            base_salary=54000,
            shift_name="Morning",
        ),
        User(
            full_name="Arjun Das",
            email="arjun@workpulse.ai",
            password_hash=hash_password("Emp@12345"),
            role="employee",
            employee_code="WPA-031",
            department_id=engineering.id,
            branch="Bengaluru HQ",
            title="ML Engineer",
            salary_type="monthly",
            base_salary=92000,
            shift_name="Flex",
        ),
    ]
    db.add_all(users)
    db.flush()

    for user in users[2:]:
        db.add(
            FaceProfile(
                user_id=user.id,
                embedding_key=f"face-{user.employee_code.lower()}",
                sample_count=12,
            )
        )
        db.add(
            FingerprintProfile(
                user_id=user.id,
                template_key=f"fp-{user.employee_code.lower()}",
                simulated_quality=0.94,
            )
        )

    now = datetime.utcnow()
    attendance_logs = []
    for offset in range(1, 13):
        day = now - timedelta(days=offset)
        attendance_logs.extend(
            [
                AttendanceLog(
                    user_id=users[2].id,
                    mode="face",
                    punch_in=day.replace(hour=9, minute=10),
                    punch_out=day.replace(hour=18, minute=45),
                    hours_logged=8.9,
                    status="present" if offset % 5 else "late",
                    late_minutes=12 if offset % 5 == 0 else 0,
                    overtime_hours=0.8 if offset % 2 == 0 else 0.2,
                    geo_tag="Mumbai Office",
                    mood="focused",
                    liveness_score=0.98,
                    fraud_flag=False,
                    device="mobile-app",
                ),
                AttendanceLog(
                    user_id=users[3].id,
                    mode="fingerprint",
                    punch_in=day.replace(hour=10, minute=5),
                    punch_out=day.replace(hour=20, minute=10),
                    hours_logged=10.1,
                    status="late" if offset % 4 == 0 else "present",
                    late_minutes=21 if offset % 4 == 0 else 0,
                    overtime_hours=1.6,
                    geo_tag="Bengaluru HQ",
                    mood="stressed" if offset % 4 == 0 else "calm",
                    liveness_score=0.95,
                    fraud_flag=offset % 6 == 0,
                    device="smart-kiosk",
                ),
            ]
        )

    db.add_all(attendance_logs)
    db.add_all(
        [
            LeaveRequest(
                user_id=users[2].id,
                leave_type="Casual Leave",
                start_date=date.today() + timedelta(days=2),
                end_date=date.today() + timedelta(days=3),
                reason="Family travel",
                status="pending",
            ),
            Notification(
                title="Payroll cutoff reminder",
                message="Approve attendance correction requests before month-end payroll run.",
                audience="admin",
                level="warning",
            ),
            Notification(
                title="High overtime alert",
                message="Engineering team crossed the safe overtime threshold this week.",
                audience="hr",
                level="critical",
            ),
            AuditLog(
                actor_email="system@workpulse.ai",
                action="Initial seed data prepared for demo tenant",
                entity="bootstrap",
            ),
        ]
    )
    db.commit()
