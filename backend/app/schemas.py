from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmployeeCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "employee"
    employee_code: str | None = None
    department_id: int | None = None
    branch: str = "HQ"
    title: str = "Associate"
    salary_type: str = "monthly"
    base_salary: float = 0
    daily_wage: float = 0
    shift_name: str = "General"
    remote_allowed: bool = True
    password: str = "Welcome@123"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class AttendancePunchRequest(BaseModel):
    user_id: int
    mode: str
    geo_tag: str | None = None
    device: str = "mobile"


class LeaveCreateRequest(BaseModel):
    user_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str


class FaceRegistrationRequest(BaseModel):
    user_id: int
    sample_count: int = 8


class FaceCaptureRequest(BaseModel):
    user_id: int
    image_data: str
    sample_count: int = 1


class FingerEnrollmentRequest(BaseModel):
    user_id: int
    simulated_quality: float = 0.92


class DeviceBiometricEnrollmentRequest(BaseModel):
    user_id: int
    credential_id: str
    device_label: str = "platform-biometric"


class DeviceBiometricVerifyRequest(BaseModel):
    user_id: int
    credential_id: str
    geo_tag: str | None = None
    device: str = "device-biometric"


class PayrollRunRequest(BaseModel):
    month_label: str


class GenericResponse(BaseModel):
    message: str


class DashboardResponse(BaseModel):
    summary: dict[str, Any]
    charts: dict[str, Any]
    insights: list[dict[str, Any]]
    live_feed: list[dict[str, Any]]


class MobileHomeResponse(BaseModel):
    profile: dict[str, Any]
    attendance_today: dict[str, Any]
    salary_snapshot: dict[str, Any]
    insights: list[dict[str, Any]]
    upcoming: list[dict[str, Any]]


class ReportExportResponse(BaseModel):
    filename: str
    content_base64: str
    generated_at: datetime


class MonthlyUserSummaryResponse(BaseModel):
    employee: dict[str, Any]
    month_label: str
    present_days: int
    late_days: int
    overtime_hours: float
    payable_days: float
    estimated_income: float
    payroll: dict[str, Any] | None = None
