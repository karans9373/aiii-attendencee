import base64
from datetime import datetime
from io import BytesIO

from app.models import AttendanceLog, PayrollRecord, User


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(title: str, lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 18 Tf", "40 800 Td", f"({_escape_pdf_text(title)}) Tj", "/F1 11 Tf"]
    y = 0
    for line in lines:
        y -= 22
        content_lines.append(f"0 {y} Td")
        content_lines.append(f"({_escape_pdf_text(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj",
    ]

    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(pdf.tell())
        pdf.write(obj)
        pdf.write(b"\n")
    xref_pos = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.write(
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1")
    )
    return pdf.getvalue()


def generate_payslip_pdf(user: User, record: PayrollRecord) -> tuple[str, str, datetime]:
    buffer = BytesIO()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"Payslip-{user.employee_code}-{record.month_label}")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(40, 800, "WorkPulse AI Payslip")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(40, 770, f"Employee: {user.full_name}")
        pdf.drawString(40, 750, f"Employee Code: {user.employee_code}")
        pdf.drawString(40, 730, f"Month: {record.month_label}")
        pdf.drawString(40, 700, f"Gross Salary: INR {record.gross_salary:.2f}")
        pdf.drawString(40, 680, f"Overtime Pay: INR {record.overtime_pay:.2f}")
        pdf.drawString(40, 660, f"Bonus: INR {record.bonus:.2f}")
        pdf.drawString(40, 640, f"Late Penalty: INR {record.late_penalty:.2f}")
        pdf.drawString(40, 620, f"Leave Deduction: INR {record.leave_deduction:.2f}")
        pdf.drawString(40, 600, f"Tax Deduction: INR {record.tax_deduction:.2f}")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, 570, f"Net Salary: INR {record.net_salary:.2f}")
        pdf.showPage()
        pdf.save()
        filename = f"payslip-{user.employee_code}-{record.month_label}.pdf"
    except ImportError:
        buffer.write(
            _build_simple_pdf(
                "WorkPulse AI Payslip",
                [
                    f"Employee: {user.full_name}",
                    f"Employee Code: {user.employee_code}",
                    f"Month: {record.month_label}",
                    f"Gross Salary: INR {record.gross_salary:.2f}",
                    f"Overtime Pay: INR {record.overtime_pay:.2f}",
                    f"Bonus: INR {record.bonus:.2f}",
                    f"Late Penalty: INR {record.late_penalty:.2f}",
                    f"Leave Deduction: INR {record.leave_deduction:.2f}",
                    f"Tax Deduction: INR {record.tax_deduction:.2f}",
                    f"Net Salary: INR {record.net_salary:.2f}",
                ],
            )
        )
        filename = f"payslip-{user.employee_code}-{record.month_label}.pdf"
    generated_at = datetime.utcnow()
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return filename, encoded, generated_at


def generate_attendance_report_pdf(
    user: User,
    month_label: str,
    attendance_logs: list[AttendanceLog],
    estimated_income: float,
) -> tuple[str, str, datetime]:
    present_days = len(attendance_logs)
    late_days = len([log for log in attendance_logs if log.status == "late"])
    overtime_hours = round(sum(log.overtime_hours for log in attendance_logs), 2)
    lines = [
        f"Employee: {user.full_name}",
        f"Employee Code: {user.employee_code}",
        f"Month: {month_label}",
        f"Present Days: {present_days}",
        f"Late Days: {late_days}",
        f"Overtime Hours: {overtime_hours}",
        f"Estimated Income: INR {estimated_income:.2f}",
    ]
    for index, log in enumerate(attendance_logs[:10], start=1):
        lines.append(
            f"{index}. {log.punch_in.strftime('%Y-%m-%d')} | {log.mode} | {log.status} | {log.hours_logged:.1f}h"
        )

    pdf_bytes = _build_simple_pdf("WorkPulse AI Monthly Attendance Report", lines)
    generated_at = datetime.utcnow()
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    filename = f"attendance-report-{user.employee_code}-{month_label}.pdf"
    return filename, encoded, generated_at
