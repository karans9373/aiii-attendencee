from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api import router
from app.core.config import get_settings
from app.db import Base, SessionLocal, engine
from app.services.seed import seed_database

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health():
    return {"status": "ok", "product": settings.app_name}


@app.get("/")
def root():
    if settings.frontend_url:
        return RedirectResponse(url=settings.frontend_url, status_code=307)
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>WorkPulse AI</title>
            <style>
              :root {
                color-scheme: dark;
                --bg: #05070b;
                --panel: #0f1724;
                --border: rgba(69, 143, 255, 0.22);
                --text: #f5f9ff;
                --muted: #8ea2c0;
                --blue: #458fff;
              }
              * { box-sizing: border-box; }
              body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: var(--bg);
                color: var(--text);
                min-height: 100vh;
                display: grid;
                place-items: center;
                padding: 24px;
              }
              .wrap {
                width: min(980px, 100%);
                display: grid;
                gap: 24px;
              }
              .hero, .panel {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 28px;
                padding: 28px;
              }
              .eyebrow {
                color: var(--blue);
                text-transform: uppercase;
                letter-spacing: .14em;
                font-size: 12px;
              }
              h1 {
                font-size: clamp(2rem, 5vw, 4rem);
                margin: 12px 0;
              }
              p {
                color: var(--muted);
                line-height: 1.7;
                margin: 0;
              }
              .actions {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 22px;
              }
              a {
                text-decoration: none;
              }
              .btn {
                display: inline-block;
                padding: 14px 18px;
                border-radius: 16px;
                font-weight: 700;
              }
              .btn-primary {
                background: linear-gradient(135deg, #2f80ed, #5aa2ff);
                color: white;
              }
              .btn-secondary {
                border: 1px solid var(--border);
                background: rgba(69, 143, 255, 0.08);
                color: var(--text);
              }
              .grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 18px;
              }
              .card {
                background: rgba(255,255,255,0.02);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 18px;
              }
              .card strong {
                display: block;
                margin-bottom: 8px;
              }
              @media (max-width: 800px) {
                .grid { grid-template-columns: 1fr; }
              }
            </style>
          </head>
          <body>
            <div class="wrap">
              <section class="hero">
                <div class="eyebrow">Workforce Intelligence Platform</div>
                <h1>WorkPulse AI</h1>
                <p>
                  AI attendance, live face capture, payroll automation, HR analytics,
                  and biometric-ready employee workflows in one production-style platform.
                </p>
                <div class="actions">
                  <a class="btn btn-primary" href="/docs">Open API Docs</a>
                  <a class="btn btn-secondary" href="/api">Open API Root</a>
                  <a class="btn btn-secondary" href="/health">Health Check</a>
                </div>
              </section>

              <section class="panel">
                <div class="grid">
                  <div class="card">
                    <strong>Face Attendance</strong>
                    <p>Real browser camera flow with permanent face registration support.</p>
                  </div>
                  <div class="card">
                    <strong>Payroll Engine</strong>
                    <p>Monthly attendance summaries, income calculations, and payslip exports.</p>
                  </div>
                  <div class="card">
                    <strong>HR Dashboard</strong>
                    <p>Executive reporting, biometric workflows, and employee enrollment flow.</p>
                  </div>
                </div>
              </section>
            </div>
          </body>
        </html>
        """
    )


app.include_router(router)
