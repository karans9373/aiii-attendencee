import { useEffect, useState } from "react";

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`;

function App() {
  const [mobileHome, setMobileHome] = useState(null);
  const [status, setStatus] = useState("Connecting to WorkPulse AI...");

  useEffect(() => {
    async function loadHome() {
      try {
        const response = await fetch(`${API_BASE}/mobile/home/3`);
        if (response.ok) {
          setMobileHome(await response.json());
          setStatus("Connected");
        } else {
          setStatus("Using demo data");
        }
      } catch (_error) {
        setStatus("Using demo data");
      }
    }
    loadHome();
  }, []);

  const name = mobileHome?.profile?.name || "Priya Sharma";
  const title = mobileHome?.profile?.title || "Site Supervisor";
  const branch = mobileHome?.profile?.branch || "Mumbai Branch";
  const todayStatus = mobileHome?.attendance_today?.status || "Checked in";
  const todayMode = mobileHome?.attendance_today?.mode || "Face ID";
  const mood = mobileHome?.attendance_today?.mood || "Focused";
  const salary = mobileHome?.salary_snapshot?.netSalary || 58420;
  const insights = mobileHome?.insights || [
    { label: "AI Productivity Score", value: "82 / 100" },
    { label: "Burnout Risk", value: "Low" },
    { label: "Shift Suggestion", value: "Current schedule is healthy" }
  ];

  return (
    <div className="app-shell">
      <div className="phone-frame">
        <div className="topbar">
          <div>
            <p className="eyebrow">Mobile Demo</p>
            <h1>WorkPulse AI</h1>
          </div>
          <span className="status-chip">{status}</span>
        </div>

        <section className="hero-card">
          <p className="welcome">Welcome back</p>
          <h2>{name}</h2>
          <p className="meta">{branch} • {title}</p>
          <div className="hero-pill">Geo Verified</div>
        </section>

        <section className="card-grid">
          <article className="info-card highlight">
            <span>Today</span>
            <strong>{todayStatus}</strong>
            <small>{todayMode} • {mood}</small>
          </article>
          <article className="info-card">
            <span>Net Salary</span>
            <strong>₹{salary}</strong>
            <small>Latest payroll</small>
          </article>
          <article className="info-card">
            <span>Burnout Risk</span>
            <strong>{insights[1]?.value || "Low"}</strong>
            <small>AI predicted</small>
          </article>
          <article className="info-card">
            <span>Productivity</span>
            <strong>{insights[0]?.value || "82 / 100"}</strong>
            <small>Attendance-linked score</small>
          </article>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h3>Quick Actions</h3>
          </div>
          <div className="actions">
            <button>Punch In</button>
            <button>Punch Out</button>
            <button>Apply Leave</button>
            <button>Payslip</button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <h3>AI Insights</h3>
          </div>
          <div className="insight-list">
            {insights.map((item) => (
              <div className="insight-row" key={item.label}>
                <div className="dot" />
                <div>
                  <strong>{item.label}</strong>
                  <p>{item.value}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <nav className="bottom-nav">
          <a className="active">Home</a>
          <a>Attendance</a>
          <a>Salary</a>
          <a>Profile</a>
        </nav>
      </div>
    </div>
  );
}

export default App;
