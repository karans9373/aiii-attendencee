from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    branch: Mapped[str] = mapped_column(String(120))
    headcount: Mapped[int] = mapped_column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(140))
    email: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), index=True)
    employee_code: Mapped[str] = mapped_column(String(40), unique=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    branch: Mapped[str] = mapped_column(String(120), default="HQ")
    title: Mapped[str] = mapped_column(String(120), default="Associate")
    salary_type: Mapped[str] = mapped_column(String(20), default="monthly")
    base_salary: Mapped[float] = mapped_column(Float, default=0)
    daily_wage: Mapped[float] = mapped_column(Float, default=0)
    shift_name: Mapped[str] = mapped_column(String(80), default="General")
    remote_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_on: Mapped[date] = mapped_column(Date, default=date.today)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    department = relationship("Department")


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(30))
    punch_in: Mapped[datetime] = mapped_column(DateTime)
    punch_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hours_logged: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="present")
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0)
    geo_tag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mood: Mapped[str | None] = mapped_column(String(40), nullable=True)
    liveness_score: Mapped[float] = mapped_column(Float, default=0.96)
    fraud_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    device: Mapped[str] = mapped_column(String(80), default="web-kiosk")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    leave_type: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    month_label: Mapped[str] = mapped_column(String(30), index=True)
    working_days: Mapped[int] = mapped_column(Integer)
    payable_days: Mapped[float] = mapped_column(Float)
    gross_salary: Mapped[float] = mapped_column(Float)
    overtime_pay: Mapped[float] = mapped_column(Float)
    bonus: Mapped[float] = mapped_column(Float, default=0)
    leave_deduction: Mapped[float] = mapped_column(Float, default=0)
    late_penalty: Mapped[float] = mapped_column(Float, default=0)
    tax_deduction: Mapped[float] = mapped_column(Float, default=0)
    net_salary: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="processed")


class FaceProfile(Base):
    __tablename__ = "face_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    embedding_key: Mapped[str] = mapped_column(String(120))
    sample_count: Mapped[int] = mapped_column(Integer, default=5)
    last_registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    anti_spoof_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class FingerprintProfile(Base):
    __tablename__ = "fingerprint_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    template_key: Mapped[str] = mapped_column(String(120))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    simulated_quality: Mapped[float] = mapped_column(Float, default=0.92)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_email: Mapped[str] = mapped_column(String(140))
    action: Mapped[str] = mapped_column(String(200))
    entity: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(40), default="all")
    level: Mapped[str] = mapped_column(String(20), default="info")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
