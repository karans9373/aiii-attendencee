# WorkPulse AI

WorkPulse AI is a production-style workforce intelligence platform with:

- `backend/`: FastAPI API for attendance, payroll, analytics, AI insights, and auth
- `web/`: React admin + HR dashboard
- `mobile/`: React Native employee app for mobile attendance and self-service

## Product Positioning

This repository is structured like a sellable SaaS MVP:

- Face recognition attendance flow with liveness simulation
- Fingerprint attendance simulation
- Payroll automation and rules engine
- HR analytics with AI-style insight modules
- Role-based authentication
- Mobile-ready employee experience
- Hosting-ready docs and environment templates

## Architecture

- Backend: FastAPI + SQLAlchemy + JWT
- Database: PostgreSQL-ready, SQLite fallback for local demo
- Web: React + Vite + Recharts
- Mobile: Expo / React Native

## Run Locally

### Backend

1. Create a virtual environment
2. Install dependencies from `backend/requirements.txt`
3. Copy `backend/.env.example` to `.env`
4. Run:

```bash
uvicorn app.main:app --reload --app-dir backend
```

### Web

1. Install dependencies in `web/`
2. Run:

```bash
npm run dev
```

### Mobile

1. Install dependencies in `mobile/`
2. Run:

```bash
npm run start
```

## Suggested Hosting

- Backend: Render, Railway, Fly.io, or an EC2/Docker VM
- Web: Vercel or Netlify
- Database: Neon, Supabase Postgres, Railway Postgres, or RDS
- Mobile: Expo EAS build for Android APK / Play Store deployment

## Selling Angle

At a `20k INR` budget, this should be positioned as:

- `Admin web dashboard` for HR and operations
- `Employee mobile app` for attendance, leaves, payslips, and insights
- `AI-powered attendance and payroll suite` with enterprise styling

## Demo Credentials

- Admin: `admin@workpulse.ai` / `Admin@123`
- HR: `hr@workpulse.ai` / `Hr@12345`
- Employee: `employee@workpulse.ai` / `Emp@12345`
