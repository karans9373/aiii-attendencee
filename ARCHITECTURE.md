# WorkPulse AI Delivery Notes

## What is included

- FastAPI backend with persistent relational schema
- Role-based JWT login
- Attendance endpoints for face, fingerprint, and hybrid punch-in
- Payroll engine with attendance-linked salary generation
- Executive dashboard data endpoints
- Mobile employee API
- React web admin experience
- React Native mobile app shell
- Seed data and demo credentials

## How to sell this for 20k+

Pitch it as:

- `Admin control panel`: HR analytics, payroll, shifts, leave approvals, reports
- `Employee mobile app`: attendance, payslips, leave, remote punch, personal insights
- `AI differentiators`: fraud detection, burnout risk, mood signal, productivity score, staffing suggestions

## Hosting stack

- Backend API:
  - Render web service or Railway
  - Use `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
- Database:
  - Managed PostgreSQL on Neon / Supabase / Railway
- Web frontend:
  - Vercel or Netlify
- Mobile:
  - Expo build pipeline for APK

## Next production upgrades

- Replace simulated recognition with actual OpenCV / `face_recognition` processing worker
- Add Redis and Celery for video/image jobs
- Add S3-compatible media storage
- Add real push notifications
- Add multi-tenant organization table
- Add tests, CI pipeline, and Docker Compose
