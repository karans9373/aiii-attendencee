from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.core.security import hash_password
from app.db import get_db
from app.models import (
    AttendanceLog,
    AuditLog,
    Department,
    FaceProfile,
    FingerprintProfile,
    LeaveRequest,
    Notification,
    PayrollRecord,
    User,
)
from app.schemas import (
    AttendancePunchRequest,
    DashboardResponse,
    DeviceBiometricEnrollmentRequest,
    DeviceBiometricVerifyRequest,
    EmployeeCreateRequest,
    FaceCaptureRequest,
    FaceRegistrationRequest,
    FingerEnrollmentRequest,
    GenericResponse,
    LeaveCreateRequest,
    LoginRequest,
    MobileHomeResponse,
    MonthlyUserSummaryResponse,
    PayrollRunRequest,
    ReportExportResponse,
    TokenResponse,
)
from app.services.ai_insights import (
    burnout_risk,
    fraud_detector,
    mood_detection_simulation,
    productivity_score,
    shift_optimization_suggestion,
    suspicious_punch_pattern,
)
from app.services.payroll import calculate_payroll_for_month
from app.services.reports import generate_attendance_report_pdf, generate_payslip_pdf

router = APIRouter(prefix="/api")
STORAGE_ROOT = Path(__file__).resolve().parent.parent / "storage"
FACES_DIR = STORAGE_ROOT / "faces"
FACES_DIR.mkdir(parents=True, exist_ok=True)


@router.get("")
def api_root():
    return {
        "product": "WorkPulse AI",
        "status": "running",
        "docs": "/docs",
        "availableModules": [
            "employees",
            "attendance",
            "face-recognition",
            "fingerprint",
            "payroll",
            "analytics",
        ],
    }


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
        "employeeCode": user.employee_code,
        "departmentId": user.department_id,
        "branch": user.branch,
        "title": user.title,
        "salaryType": user.salary_type,
        "baseSalary": user.base_salary,
        "dailyWage": user.daily_wage,
        "shiftName": user.shift_name,
    }


def _next_employee_code(db: Session) -> str:
    users = db.scalars(select(User)).all()
    numeric_parts = []
    for user in users:
        code = user.employee_code or ""
        if code.startswith("WPA-"):
            suffix = code.split("WPA-")[-1]
            if suffix.isdigit():
                numeric_parts.append(int(suffix))
    next_value = (max(numeric_parts) + 1) if numeric_parts else 1
    return f"WPA-{next_value:03d}"


def _month_logs_for_user(logs: list[AttendanceLog], month_label: str) -> list[AttendanceLog]:
    return [log for log in logs if log.punch_in.strftime("%Y-%m") == month_label]


def _payroll_to_dict(item: PayrollRecord) -> dict:
    return {
        "id": item.id,
        "userId": item.user_id,
        "monthLabel": item.month_label,
        "grossSalary": item.gross_salary,
        "overtimePay": item.overtime_pay,
        "bonus": item.bonus,
        "latePenalty": item.late_penalty,
        "leaveDeduction": item.leave_deduction,
        "taxDeduction": item.tax_deduction,
        "netSalary": item.net_salary,
        "status": item.status,
    }


def _save_data_url_image(image_data: str, target: Path) -> None:
    if "," not in image_data:
        raise HTTPException(status_code=400, detail="Invalid image payload")
    _, encoded = image_data.split(",", 1)
    target.write_bytes(base64.b64decode(encoded))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id), {"role": user.role, "email": user.email})
    return TokenResponse(access_token=token, user=_serialize_user(user))


@router.get("/bootstrap")
def bootstrap(db: Session = Depends(get_db)):
    users = db.scalars(select(User)).all()
    departments = db.scalars(select(Department)).all()
    notifications = db.scalars(select(Notification)).all()
    face_profiles = db.scalars(select(FaceProfile)).all()
    fingerprint_profiles = db.scalars(select(FingerprintProfile)).all()
    faces = {item.user_id for item in face_profiles}
    fingerprints = {item.user_id for item in fingerprint_profiles}
    return {
        "users": [_serialize_user(user) for user in users],
        "departments": [
            {"id": item.id, "name": item.name, "branch": item.branch, "headcount": item.headcount}
            for item in departments
        ],
        "notifications": [
            {"id": item.id, "title": item.title, "message": item.message, "level": item.level}
            for item in notifications
        ],
        "nextEmployeeCode": _next_employee_code(db),
        "biometrics": {
            "faceRegisteredUserIds": list(faces),
            "fingerprintRegisteredUserIds": list(fingerprints),
            "fingerprintCredentialByUserId": {
                str(item.user_id): item.template_key for item in fingerprint_profiles if item.template_key
            },
        },
    }


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.role == "employee")).all()
    logs = db.scalars(select(AttendanceLog)).all()
    payroll = db.scalars(select(PayrollRecord)).all()
    departments = db.scalars(select(Department)).all()

    present_today = len([log for log in logs if log.punch_in.date() == datetime.utcnow().date()])
    late_count = len([log for log in logs if log.status == "late"])
    overtime_total = round(sum(log.overtime_hours for log in logs), 1)
    payroll_due = len([user for user in users if user.id not in [item.user_id for item in payroll]])

    chart_attendance = [
        {"name": "Present", "value": max(1, len(logs) - late_count)},
        {"name": "Late", "value": late_count},
        {"name": "Flagged", "value": len([log for log in logs if log.fraud_flag])},
    ]
    monthly_trends = [
        {"month": "Jan", "attendance": 84, "payroll": 6.7},
        {"month": "Feb", "attendance": 87, "payroll": 6.9},
        {"month": "Mar", "attendance": 89, "payroll": 7.3},
        {"month": "Apr", "attendance": 92, "payroll": 7.5},
    ]
    heatmap = [
        {
            "department": dept.name,
            "utilization": min(96, 64 + dept.headcount),
            "risk": "medium" if dept.headcount > 10 else "low",
        }
        for dept in departments
    ]

    insights = []
    for user in users:
        user_logs = [log for log in logs if log.user_id == user.id]
        attendance_ratio = min(1.0, len(user_logs) / 22)
        hours = sum(log.hours_logged for log in user_logs) / max(1, len(user_logs))
        overtime = sum(log.overtime_hours for log in user_logs)
        insights.append(
            {
                "user": user.full_name,
                "productivityScore": productivity_score(hours, overtime, attendance_ratio),
                "burnoutRisk": burnout_risk(hours, overtime, sum(log.late_minutes for log in user_logs)),
                "fraudSummary": fraud_detector([log.status for log in user_logs], [log.late_minutes for log in user_logs]),
            }
        )

    live_feed = [
        {
            "employee": user.full_name,
            "mode": logs[idx].mode if idx < len(logs) else "face",
            "branch": user.branch,
            "status": "On-site" if idx % 2 == 0 else "Remote",
            "mood": logs[idx].mood if idx < len(logs) else "calm",
        }
        for idx, user in enumerate(users)
    ]

    return DashboardResponse(
        summary={
            "presentToday": present_today,
            "absentToday": max(0, len(users) - present_today),
            "lateEmployees": late_count,
            "payrollDue": payroll_due,
            "overtimeHours": overtime_total,
        },
        charts={
            "attendanceBreakdown": chart_attendance,
            "monthlyTrends": monthly_trends,
            "departmentHeatmap": heatmap,
            "payrollDistribution": [
                {"name": "Engineering", "value": 4.3},
                {"name": "People Ops", "value": 1.7},
                {"name": "Field Ops", "value": 2.1},
            ],
            "productivity": [
                {"name": "Ananya", "score": 94},
                {"name": "Rahul", "score": 87},
                {"name": "Priya", "score": 82},
                {"name": "Arjun", "score": 90},
            ],
        },
        insights=insights,
        live_feed=live_feed,
    )


@router.get("/employees")
def get_employees(db: Session = Depends(get_db)):
    users = db.scalars(select(User)).all()
    return [_serialize_user(user) for user in users]


@router.get("/employees/next-code")
def get_next_employee_code(db: Session = Depends(get_db)):
    return {"employeeCode": _next_employee_code(db)}


@router.post("/employees")
def create_employee(payload: EmployeeCreateRequest, db: Session = Depends(get_db)):
    existing_email = db.scalar(select(User).where(User.email == payload.email))
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    employee_code = payload.employee_code or _next_employee_code(db)
    existing_code = db.scalar(select(User).where(User.employee_code == employee_code))
    if existing_code:
        employee_code = _next_employee_code(db)

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        employee_code=employee_code,
        department_id=payload.department_id,
        branch=payload.branch,
        title=payload.title,
        salary_type=payload.salary_type,
        base_salary=payload.base_salary,
        daily_wage=payload.daily_wage,
        shift_name=payload.shift_name,
        remote_allowed=payload.remote_allowed,
    )
    db.add(user)
    db.flush()
    db.add(
        AuditLog(
            actor_email="admin@workpulse.ai",
            action=f"Created employee {user.full_name}",
            entity="employee",
        )
    )
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.get("/attendance/live")
def live_attendance(db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.role == "employee")).all()
    logs = db.scalars(select(AttendanceLog)).all()
    items = []
    for user in users:
        user_logs = [log for log in logs if log.user_id == user.id]
        devices = [log.device for log in user_logs]
        geo_tags = [log.geo_tag or "" for log in user_logs]
        items.append(
            {
                "employee": user.full_name,
                "branch": user.branch,
                "lastMode": user_logs[0].mode if user_logs else "face",
                "presence": "present" if user_logs else "unknown",
                "mood": user_logs[0].mood if user_logs else "calm",
                "fraudFlag": suspicious_punch_pattern(devices, geo_tags),
                "geoTag": user_logs[0].geo_tag if user_logs else user.branch,
            }
        )
    return items


@router.get("/attendance/user/{user_id}")
def user_attendance(user_id: int, month_label: str | None = None, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logs = db.scalars(select(AttendanceLog).where(AttendanceLog.user_id == user_id)).all()
    if month_label:
        logs = _month_logs_for_user(logs, month_label)
    return [
        {
            "id": log.id,
            "date": log.punch_in.strftime("%Y-%m-%d"),
            "mode": log.mode,
            "status": log.status,
            "hoursLogged": log.hours_logged,
            "lateMinutes": log.late_minutes,
            "overtimeHours": log.overtime_hours,
            "mood": log.mood,
            "geoTag": log.geo_tag,
        }
        for log in sorted(logs, key=lambda item: item.punch_in, reverse=True)
    ]


@router.post("/attendance/punch", response_model=GenericResponse)
def punch(payload: AttendancePunchRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    liveness_score = 0.98 if payload.mode == "face" else 0.93
    late_minutes = 14 if datetime.utcnow().hour >= 10 else 0
    mood = mood_detection_simulation(liveness_score, late_minutes)
    log = AttendanceLog(
        user_id=user.id,
        mode=payload.mode,
        punch_in=datetime.utcnow(),
        punch_out=None,
        hours_logged=0,
        status="late" if late_minutes else "present",
        late_minutes=late_minutes,
        overtime_hours=0,
        geo_tag=payload.geo_tag,
        mood=mood,
        liveness_score=liveness_score,
        fraud_flag=False,
        device=payload.device,
    )
    db.add(log)
    db.add(AuditLog(actor_email=user.email, action=f"Marked attendance via {payload.mode}", entity="attendance"))
    db.commit()
    return GenericResponse(message=f"Attendance punched via {payload.mode} with mood {mood}.")


@router.post("/attendance/face-live", response_model=GenericResponse)
def punch_face_live(payload: FaceCaptureRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.scalar(select(FaceProfile).where(FaceProfile.user_id == payload.user_id))
    if not existing:
        raise HTTPException(status_code=400, detail="Register face first for this employee")

    image_path = FACES_DIR / f"{user.employee_code}-latest-attendance.png"
    _save_data_url_image(payload.image_data, image_path)
    db.add(
        AttendanceLog(
            user_id=user.id,
            mode="face",
            punch_in=datetime.utcnow(),
            punch_out=None,
            hours_logged=0,
            status="present",
            late_minutes=0,
            overtime_hours=0,
            geo_tag=user.branch,
            mood="focused",
            liveness_score=0.98,
            fraud_flag=False,
            device="live-camera",
        )
    )
    db.add(AuditLog(actor_email=user.email, action="Marked attendance via live camera", entity="attendance"))
    db.commit()
    return GenericResponse(message="Successfully marked attendance via live camera.")


@router.post("/attendance/device-biometric", response_model=GenericResponse)
def punch_device_biometric(payload: DeviceBiometricVerifyRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.scalar(select(FingerprintProfile).where(FingerprintProfile.user_id == payload.user_id))
    if not existing or existing.template_key != payload.credential_id:
        raise HTTPException(status_code=400, detail="No matching enrolled device biometric found")

    db.add(
        AttendanceLog(
            user_id=user.id,
            mode="fingerprint",
            punch_in=datetime.utcnow(),
            punch_out=None,
            hours_logged=0,
            status="present",
            late_minutes=0,
            overtime_hours=0,
            geo_tag=payload.geo_tag or user.branch,
            mood="focused",
            liveness_score=0.99,
            fraud_flag=False,
            device=payload.device,
        )
    )
    db.add(AuditLog(actor_email=user.email, action="Marked attendance via device biometric", entity="attendance"))
    db.commit()
    return GenericResponse(message="Successfully marked attendance via fingerprint/device biometric.")


@router.post("/face/register", response_model=GenericResponse)
def register_face(payload: FaceRegistrationRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(FaceProfile).where(FaceProfile.user_id == payload.user_id))
    if existing:
        existing.sample_count = payload.sample_count
    else:
        db.add(FaceProfile(user_id=payload.user_id, embedding_key=f"face-user-{payload.user_id}", sample_count=payload.sample_count))
    db.commit()
    return GenericResponse(message="Face profile registered successfully.")


@router.post("/face/register-live", response_model=GenericResponse)
def register_face_live(payload: FaceCaptureRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_path = FACES_DIR / f"{user.employee_code}-register.png"
    _save_data_url_image(payload.image_data, image_path)

    existing = db.scalar(select(FaceProfile).where(FaceProfile.user_id == payload.user_id))
    if existing:
        existing.sample_count = max(existing.sample_count, payload.sample_count)
        existing.embedding_key = str(image_path)
        existing.last_registered_at = datetime.utcnow()
    else:
        db.add(
            FaceProfile(
                user_id=payload.user_id,
                embedding_key=str(image_path),
                sample_count=payload.sample_count,
            )
        )
    db.add(AuditLog(actor_email=user.email, action="Registered live face capture", entity="face_profile"))
    db.commit()
    return GenericResponse(message="Live camera face registration saved permanently.")


@router.post("/fingerprint/enroll", response_model=GenericResponse)
def enroll_fingerprint(payload: FingerEnrollmentRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(FingerprintProfile).where(FingerprintProfile.user_id == payload.user_id))
    if existing:
        existing.simulated_quality = payload.simulated_quality
    else:
        db.add(
            FingerprintProfile(
                user_id=payload.user_id,
                template_key=f"fp-user-{payload.user_id}",
                simulated_quality=payload.simulated_quality,
            )
        )
    db.commit()
    return GenericResponse(message="Fingerprint profile enrolled successfully.")


@router.post("/fingerprint/enroll-device", response_model=GenericResponse)
def enroll_device_biometric(payload: DeviceBiometricEnrollmentRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.scalar(select(FingerprintProfile).where(FingerprintProfile.user_id == payload.user_id))
    if existing:
        existing.template_key = payload.credential_id
        existing.simulated_quality = 0.99
    else:
        db.add(
            FingerprintProfile(
                user_id=payload.user_id,
                template_key=payload.credential_id,
                simulated_quality=0.99,
            )
        )
    db.add(
        AuditLog(
            actor_email=user.email,
            action=f"Enrolled device biometric via {payload.device_label}",
            entity="fingerprint_profile",
        )
    )
    db.commit()
    return GenericResponse(message="Device biometric enrolled and saved permanently.")


@router.post("/leave", response_model=GenericResponse)
def create_leave(payload: LeaveCreateRequest, db: Session = Depends(get_db)):
    db.add(
        LeaveRequest(
            user_id=payload.user_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
            status="pending",
        )
    )
    db.commit()
    return GenericResponse(message="Leave request submitted.")


@router.get("/leave")
def list_leave_requests(db: Session = Depends(get_db)):
    leaves = db.scalars(select(LeaveRequest)).all()
    return [
        {
            "id": item.id,
            "userId": item.user_id,
            "leaveType": item.leave_type,
            "startDate": item.start_date.isoformat(),
            "endDate": item.end_date.isoformat(),
            "reason": item.reason,
            "status": item.status,
        }
        for item in leaves
    ]


@router.post("/payroll/run")
def run_payroll(payload: PayrollRunRequest, db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.role == "employee")).all()
    attendance_logs = db.scalars(select(AttendanceLog)).all()
    records = calculate_payroll_for_month(users, attendance_logs, payload.month_label)
    for record in records:
        db.add(record)
    db.commit()
    return {"processed": len(records), "month": payload.month_label}


@router.get("/payroll")
def list_payroll(user_id: int | None = None, db: Session = Depends(get_db)):
    query = select(PayrollRecord)
    if user_id:
        query = query.where(PayrollRecord.user_id == user_id)
    records = db.scalars(query).all()
    return [_payroll_to_dict(item) for item in records]


@router.get("/payroll/{record_id}/payslip", response_model=ReportExportResponse)
def get_payslip(record_id: int, db: Session = Depends(get_db)):
    record = db.get(PayrollRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    user = db.get(User, record.user_id)
    filename, content_base64, generated_at = generate_payslip_pdf(user, record)
    return ReportExportResponse(filename=filename, content_base64=content_base64, generated_at=generated_at)


@router.get("/reports/attendance/{user_id}", response_model=ReportExportResponse)
def get_attendance_report(user_id: int, month_label: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logs = db.scalars(select(AttendanceLog).where(AttendanceLog.user_id == user_id)).all()
    month_logs = _month_logs_for_user(logs, month_label)
    if user.salary_type == "monthly":
        estimated_income = user.base_salary
    else:
        estimated_income = len(month_logs) * user.daily_wage
    filename, content_base64, generated_at = generate_attendance_report_pdf(
        user, month_label, month_logs, estimated_income
    )
    return ReportExportResponse(filename=filename, content_base64=content_base64, generated_at=generated_at)


@router.get("/reports/monthly-summary/{user_id}", response_model=MonthlyUserSummaryResponse)
def monthly_summary(user_id: int, month_label: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logs = db.scalars(select(AttendanceLog).where(AttendanceLog.user_id == user_id)).all()
    month_logs = _month_logs_for_user(logs, month_label)
    present_days = len(month_logs)
    late_days = len([log for log in month_logs if log.status == "late"])
    overtime_hours = round(sum(log.overtime_hours for log in month_logs), 2)
    payable_days = float(present_days)

    payroll = db.scalar(
        select(PayrollRecord).where(
            PayrollRecord.user_id == user_id,
            PayrollRecord.month_label == month_label,
        )
    )
    if payroll:
        estimated_income = payroll.net_salary
    elif user.salary_type == "monthly":
        estimated_income = user.base_salary
    else:
        estimated_income = present_days * user.daily_wage

    return MonthlyUserSummaryResponse(
        employee=_serialize_user(user),
        month_label=month_label,
        present_days=present_days,
        late_days=late_days,
        overtime_hours=overtime_hours,
        payable_days=payable_days,
        estimated_income=estimated_income,
        payroll=_payroll_to_dict(payroll) if payroll else None,
    )


@router.get("/mobile/home/{user_id}", response_model=MobileHomeResponse)
def mobile_home(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logs = db.scalars(select(AttendanceLog).where(AttendanceLog.user_id == user_id)).all()
    payroll_record = db.scalars(select(PayrollRecord).where(PayrollRecord.user_id == user_id)).first()
    today_log = next((log for log in logs if log.punch_in.date() == datetime.utcnow().date()), None)

    attendance_ratio = min(1.0, len(logs) / 22)
    avg_hours = sum(log.hours_logged for log in logs) / max(1, len(logs))
    overtime = sum(log.overtime_hours for log in logs)

    return MobileHomeResponse(
        profile=_serialize_user(user),
        attendance_today={
            "status": today_log.status if today_log else "not punched",
            "mode": today_log.mode if today_log else "pending",
            "mood": today_log.mood if today_log else "calm",
            "geoTag": today_log.geo_tag if today_log else user.branch,
        },
        salary_snapshot={
            "month": payroll_record.month_label if payroll_record else "Pending",
            "netSalary": payroll_record.net_salary if payroll_record else 0,
            "bonus": payroll_record.bonus if payroll_record else 0,
        },
        insights=[
            {
                "label": "AI Productivity Score",
                "value": productivity_score(avg_hours, overtime, attendance_ratio),
            },
            {
                "label": "Burnout Risk",
                "value": burnout_risk(avg_hours, overtime, sum(log.late_minutes for log in logs)),
            },
            {
                "label": "Shift Suggestion",
                "value": shift_optimization_suggestion(user.title, avg_hours, 1 - attendance_ratio),
            },
        ],
        upcoming=[
            {"title": "Leave Request Pending", "subtitle": "People Ops approval expected by tomorrow"},
            {"title": "Payroll Window", "subtitle": "Payslip unlocks on the 30th"},
        ],
    )


@router.get("/reports/executive")
def executive_report(db: Session = Depends(get_db)):
    departments = db.scalars(select(Department)).all()
    return {
        "leaderboard": [
            {"name": "Arjun Das", "score": 90},
            {"name": "Priya Sharma", "score": 82},
            {"name": "Rahul Mehta", "score": 87},
        ],
        "presenceMap": [
            {"city": "Bengaluru", "employees": 19},
            {"city": "Mumbai", "employees": 12},
            {"city": "Hyderabad", "employees": 4},
        ],
        "departmentComparison": [
            {"department": dept.name, "performance": 78 + idx * 5, "attendance": 82 + idx * 4}
            for idx, dept in enumerate(departments)
        ],
        "voiceAssistantPrompts": [
            "Who is at burnout risk this week?",
            "Show payroll anomalies for this month.",
            "Compare overtime across departments.",
        ],
    }
