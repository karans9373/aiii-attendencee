import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { bootstrap as bootstrapFallback, dashboard as dashboardFallback } from "./data";

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`;
const COLORS = ["#62f2c1", "#8db1ff", "#ff8b7b", "#ffd46a"];
const NAV_ITEMS = [
  { id: "dashboard", label: "Executive Dashboard" },
  { id: "enrollment", label: "Employee Enrollment" },
  { id: "kiosk", label: "Biometric Entry" },
  { id: "attendance", label: "Attendance History" },
  { id: "payroll", label: "Payroll Automation" },
  { id: "reports", label: "Reports" }
];

function SectionTitle({ eyebrow, title, copy }) {
  return (
    <div className="section-title">
      <span>{eyebrow}</span>
      <h2>{title}</h2>
      <p>{copy}</p>
    </div>
  );
}

function toBase64Url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function App() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [activeSection, setActiveSection] = useState("dashboard");
  const [theme, setTheme] = useState("dark");
  const [statusMessage, setStatusMessage] = useState("System connected.");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [monthLabel, setMonthLabel] = useState(new Date().toISOString().slice(0, 7));
  const [dashboard, setDashboard] = useState({
    summary: {
      presentToday: 148,
      absentToday: 17,
      lateEmployees: 9,
      payrollDue: 31,
      overtimeHours: "126h"
    },
    charts: {
      attendanceBreakdown: dashboardFallback.attendanceBreakdown,
      monthlyTrends: dashboardFallback.monthlyTrends,
      payrollDistribution: dashboardFallback.payrollDistribution
    },
    insights: dashboardFallback.productivity,
    live_feed: dashboardFallback.liveFeed
  });
  const [bootstrap, setBootstrap] = useState({
    ...bootstrapFallback,
    nextEmployeeCode: "WPA-100",
    biometrics: {
      faceRegisteredUserIds: [],
      fingerprintRegisteredUserIds: [],
      fingerprintCredentialByUserId: {}
    }
  });
  const [liveAttendance, setLiveAttendance] = useState([]);
  const [userAttendance, setUserAttendance] = useState([]);
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [monthlySummary, setMonthlySummary] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(3);
  const [newEmployee, setNewEmployee] = useState({
    full_name: "",
    email: "",
    branch: "Bengaluru HQ",
    title: "Operations Associate",
    base_salary: 35000,
    password: "Welcome@123"
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    hydrate();
    return () => stopCamera();
  }, []);

  useEffect(() => {
    if (selectedUserId) {
      hydrateUserData(selectedUserId, monthLabel);
    }
  }, [selectedUserId, monthLabel]);

  const selectedUser = useMemo(
    () => bootstrap.users.find((user) => Number(user.id) === Number(selectedUserId)),
    [bootstrap.users, selectedUserId]
  );

  const biometrics = bootstrap.biometrics || {
    faceRegisteredUserIds: [],
    fingerprintRegisteredUserIds: [],
    fingerprintCredentialByUserId: {}
  };
  const faceRegistered = biometrics.faceRegisteredUserIds?.includes(selectedUserId);
  const fingerprintRegistered = biometrics.fingerprintRegisteredUserIds?.includes(selectedUserId);

  async function hydrate() {
    try {
      const [dashboardRes, bootstrapRes, liveRes] = await Promise.all([
        fetch(`${API_BASE}/dashboard`),
        fetch(`${API_BASE}/bootstrap`),
        fetch(`${API_BASE}/attendance/live`)
      ]);
      if (dashboardRes.ok) {
        setDashboard(await dashboardRes.json());
      }
      if (bootstrapRes.ok) {
        setBootstrap(await bootstrapRes.json());
      }
      if (liveRes.ok) {
        setLiveAttendance(await liveRes.json());
      }
    } catch (error) {
      setStatusMessage(error.message || "Unable to load dashboard.");
    }
  }

  async function hydrateUserData(userId, month) {
    try {
      const [attendanceRes, payrollRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE}/attendance/user/${userId}?month_label=${month}`),
        fetch(`${API_BASE}/payroll?user_id=${userId}`),
        fetch(`${API_BASE}/reports/monthly-summary/${userId}?month_label=${month}`)
      ]);
      if (attendanceRes.ok) {
        setUserAttendance(await attendanceRes.json());
      }
      if (payrollRes.ok) {
        setPayrollRecords(await payrollRes.json());
      }
      if (summaryRes.ok) {
        setMonthlySummary(await summaryRes.json());
      }
    } catch (error) {
      setStatusMessage(error.message || "Unable to refresh selected employee data.");
    }
  }

  async function postJson(path, payload, successMessage) {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "Request failed");
      }
      setStatusMessage(data.message || successMessage);
      await hydrate();
      if (selectedUserId) {
        await hydrateUserData(selectedUserId, monthLabel);
      }
      return data;
    } catch (error) {
      setStatusMessage(error.message || "Request failed");
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function startCamera() {
    try {
      if (streamRef.current) {
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraReady(true);
      setStatusMessage("Camera opened successfully.");
    } catch (error) {
      setStatusMessage(error.message || "Unable to access camera.");
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraReady(false);
  }

  function captureFrame() {
    if (!videoRef.current) {
      throw new Error("Camera is not ready");
    }
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const context = canvas.getContext("2d");
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/png");
  }

  async function handleCreateEmployee(event) {
    event.preventDefault();
    const created = await postJson(
      "/employees",
      {
        ...newEmployee,
        employee_code: undefined,
        salary_type: "monthly",
        base_salary: Number(newEmployee.base_salary),
        daily_wage: 0
      },
      "Employee created successfully."
    );
    if (created?.id) {
      setSelectedUserId(created.id);
      setActiveSection("kiosk");
      setNewEmployee({
        full_name: "",
        email: "",
        branch: "Bengaluru HQ",
        title: "Operations Associate",
        base_salary: 35000,
        password: "Welcome@123"
      });
    }
  }

  async function handleLiveFaceRegistration() {
    try {
      if (!cameraReady) {
        await startCamera();
        return;
      }
      const image = captureFrame();
      await postJson(
        "/face/register-live",
        { user_id: Number(selectedUserId), image_data: image, sample_count: 1 },
        "Live camera face registration saved."
      );
    } catch (error) {
      setStatusMessage(error.message || "Unable to register face.");
    }
  }

  async function handleLiveFaceAttendance() {
    try {
      if (!cameraReady) {
        await startCamera();
        return;
      }
      const image = captureFrame();
      await postJson(
        "/attendance/face-live",
        { user_id: Number(selectedUserId), image_data: image, sample_count: 1 },
        "Successfully marked attendance via live camera."
      );
    } catch (error) {
      setStatusMessage(error.message || "Unable to mark face attendance.");
    }
  }

  async function handleDeviceBiometricEnrollment() {
    if (!window.PublicKeyCredential || !window.crypto?.getRandomValues) {
      setStatusMessage("This browser/device does not support platform biometric prompts.");
      return;
    }
    try {
      const challenge = crypto.getRandomValues(new Uint8Array(32));
      const userIdBytes = new TextEncoder().encode(`workpulse-${selectedUserId}`);
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge,
          rp: { name: "WorkPulse AI" },
          user: {
            id: userIdBytes,
            name: selectedUser?.email || `user-${selectedUserId}@workpulse.ai`,
            displayName: selectedUser?.name || `User ${selectedUserId}`
          },
          pubKeyCredParams: [{ type: "public-key", alg: -7 }],
          authenticatorSelection: {
            authenticatorAttachment: "platform",
            userVerification: "required"
          },
          timeout: 60000,
          attestation: "none"
        }
      });
      const credentialId = toBase64Url(credential.rawId);
      await postJson(
        "/fingerprint/enroll-device",
        { user_id: Number(selectedUserId), credential_id: credentialId, device_label: "platform-biometric" },
        "Device biometric enrolled permanently."
      );
    } catch (error) {
      setStatusMessage(error.message || "Biometric enrollment was cancelled or unsupported.");
    }
  }

  async function handleDeviceBiometricAttendance() {
    if (!window.PublicKeyCredential || !window.crypto?.getRandomValues) {
      setStatusMessage("This browser/device does not support platform biometric prompts.");
      return;
    }
    const savedCredential = biometrics.fingerprintCredentialByUserId?.[String(selectedUserId)];
    if (!savedCredential) {
      setStatusMessage("Enroll device biometric first for this employee.");
      return;
    }
    try {
      const binary = atob(savedCredential.replace(/-/g, "+").replace(/_/g, "/"));
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      await navigator.credentials.get({
        publicKey: {
          challenge: crypto.getRandomValues(new Uint8Array(32)),
          allowCredentials: [{ type: "public-key", id: bytes.buffer }],
          userVerification: "required",
          timeout: 60000
        }
      });
      await postJson(
        "/attendance/device-biometric",
        {
          user_id: Number(selectedUserId),
          credential_id: savedCredential,
          geo_tag: selectedUser?.branch || "HQ",
          device: "platform-biometric"
        },
        "Successfully marked attendance via fingerprint/device biometric."
      );
    } catch (error) {
      setStatusMessage(error.message || "Biometric verification was cancelled or unsupported.");
    }
  }

  async function handleRunPayroll() {
    await postJson("/payroll/run", { month_label: monthLabel }, `Payroll processed for ${monthLabel}.`);
  }

  async function downloadReport(path) {
    try {
      const response = await fetch(`${API_BASE}${path}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to generate report");
      }
      const link = document.createElement("a");
      link.href = `data:application/pdf;base64,${data.content_base64}`;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setStatusMessage(`${data.filename} downloaded.`);
    } catch (error) {
      setStatusMessage(error.message || "Download failed");
    }
  }

  const summaryCards = [
    { label: "Present Today", value: dashboard.summary.presentToday, change: "+12%" },
    { label: "Late Employees", value: dashboard.summary.lateEmployees, change: "-6%" },
    { label: "Payroll Due", value: dashboard.summary.payrollDue, change: "+4%" },
    { label: "Overtime Hours", value: dashboard.summary.overtimeHours, change: "+18%" }
  ];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">WP</div>
          <div>
            <h1>WorkPulse AI</h1>
            <p>Workforce Intelligence Suite</p>
          </div>
        </div>
        <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          Switch to {theme === "dark" ? "Light" : "Dark"} Theme
        </button>
        <nav>
          {NAV_ITEMS.map((item) => (
            <button key={item.id} className={activeSection === item.id ? "active" : ""} onClick={() => setActiveSection(item.id)}>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-card">
          <p>Selected employee</p>
          <strong>{selectedUser?.name || "Choose a user"}</strong>
          <span>{selectedUser?.employeeCode || bootstrap.nextEmployeeCode} • {selectedUser?.branch || "-"}</span>
        </div>
      </aside>

      <main className="content">
        <header className="hero">
          <div>
            <p className="eyebrow">Ready To Demo</p>
            <h2>{NAV_ITEMS.find((item) => item.id === activeSection)?.label}</h2>
            <p className="hero-copy">
              Real camera capture is now used from the browser. Device biometric prompts can open Windows Hello,
              fingerprint, or face verification where the machine supports it.
            </p>
          </div>
          <div className="hero-panel">
            <div>
              <span>Camera</span>
              <strong>{cameraReady ? "Open" : "Closed"}</strong>
            </div>
            <div>
              <span>Biometric Status</span>
              <strong>{fingerprintRegistered ? "Enrolled" : "Pending"}</strong>
            </div>
            <div>
              <span>System</span>
              <strong>{isSubmitting ? "Processing..." : statusMessage}</strong>
            </div>
          </div>
        </header>

        {activeSection === "dashboard" && (
          <>
            <section className="stats-grid">
              {summaryCards.map((item) => (
                <article key={item.label} className="glass-card">
                  <p>{item.label}</p>
                  <h3>{item.value}</h3>
                  <span>{item.change} vs last cycle</span>
                </article>
              ))}
            </section>
            <section className="panel-grid">
              <article className="glass-card chart-card">
                <SectionTitle eyebrow="Attendance" title="Monthly trend" copy="Executive visibility into attendance momentum." />
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={dashboard.charts.monthlyTrends}>
                    <defs>
                      <linearGradient id="attendanceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#62f2c1" stopOpacity={0.75} />
                        <stop offset="95%" stopColor="#62f2c1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="month" stroke="#94a7c6" />
                    <YAxis stroke="#94a7c6" />
                    <Tooltip />
                    <Area type="monotone" dataKey="attendance" stroke="#62f2c1" fill="url(#attendanceGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </article>
              <article className="glass-card chart-card">
                <SectionTitle eyebrow="Mix" title="Attendance breakdown" copy="Face, biometric, and flagged patterns." />
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={dashboard.charts.attendanceBreakdown} dataKey="value" innerRadius={62} outerRadius={96}>
                      {dashboard.charts.attendanceBreakdown.map((entry, index) => (
                        <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </article>
            </section>
          </>
        )}

        {activeSection === "enrollment" && (
          <section className="panel-grid">
            <article className="glass-card">
              <SectionTitle eyebrow="New Hire" title="Employee enrollment" copy="Add a permanent employee with an auto-generated unique code." />
              <form className="employee-form" onSubmit={handleCreateEmployee}>
                <label className="field">
                  <span>Full name</span>
                  <input required value={newEmployee.full_name} onChange={(event) => setNewEmployee({ ...newEmployee, full_name: event.target.value })} />
                </label>
                <label className="field">
                  <span>Email</span>
                  <input required type="email" value={newEmployee.email} onChange={(event) => setNewEmployee({ ...newEmployee, email: event.target.value })} />
                </label>
                <label className="field">
                  <span>Employee code</span>
                  <input value={bootstrap.nextEmployeeCode || ""} readOnly />
                </label>
                <label className="field">
                  <span>Branch</span>
                  <input value={newEmployee.branch} onChange={(event) => setNewEmployee({ ...newEmployee, branch: event.target.value })} />
                </label>
                <label className="field">
                  <span>Title</span>
                  <input value={newEmployee.title} onChange={(event) => setNewEmployee({ ...newEmployee, title: event.target.value })} />
                </label>
                <label className="field">
                  <span>Base salary</span>
                  <input type="number" value={newEmployee.base_salary} onChange={(event) => setNewEmployee({ ...newEmployee, base_salary: event.target.value })} />
                </label>
                <button className="primary-btn" type="submit" disabled={isSubmitting}>Create Permanent Employee</button>
              </form>
            </article>
            <article className="glass-card">
              <SectionTitle eyebrow="Directory" title="Saved employees" copy="Choose a user for live registration and attendance." />
              <div className="feed-list">
                {bootstrap.users.map((user) => (
                  <button key={user.id} className={`select-card ${Number(selectedUserId) === Number(user.id) ? "selected" : ""}`} onClick={() => setSelectedUserId(user.id)}>
                    <div>
                      <strong>{user.name}</strong>
                      <p>{user.employeeCode}</p>
                    </div>
                    <div>
                      <span>{user.branch}</span>
                      <b>{user.role}</b>
                    </div>
                  </button>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "kiosk" && (
          <>
            <section className="action-grid">
              <article className="glass-card">
                <SectionTitle eyebrow="Live Face Camera" title="Real camera registration and attendance" copy="Open camera, register face permanently, then mark attendance directly." />
                <label className="field">
                  <span>Selected employee</span>
                  <select value={selectedUserId} onChange={(event) => setSelectedUserId(Number(event.target.value))}>
                    {bootstrap.users.map((user) => (
                      <option key={user.id} value={user.id}>{user.name} • {user.employeeCode}</option>
                    ))}
                  </select>
                </label>
                <div className="camera-shell">
                  <video ref={videoRef} autoPlay playsInline muted className="camera-view" />
                </div>
                <div className="button-row">
                  <button className="primary-btn" onClick={startCamera} disabled={cameraReady || isSubmitting}>Open Real Camera</button>
                  <button className="secondary-btn" onClick={stopCamera}>Close Camera</button>
                  <button className="primary-btn" onClick={handleLiveFaceRegistration} disabled={isSubmitting}>Register Face Permanently</button>
                  <button className="secondary-btn" onClick={handleLiveFaceAttendance} disabled={isSubmitting}>Mark Face Attendance</button>
                </div>
              </article>
              <article className="glass-card">
                <SectionTitle eyebrow="Device Biometric" title="Fingerprint / Windows Hello / Face ID prompt" copy="On supported devices, this opens a real platform biometric prompt from the browser." />
                <div className="kiosk-grid">
                  <div className="kiosk-card">
                    <strong>Enrollment</strong>
                    <p>{fingerprintRegistered ? "A device biometric is already enrolled." : "Enroll a real platform biometric for this employee."}</p>
                    <button className="primary-btn" onClick={handleDeviceBiometricEnrollment} disabled={isSubmitting}>Enroll Device Biometric</button>
                  </div>
                  <div className="kiosk-card">
                    <strong>Direct Attendance</strong>
                    <p>Use fingerprint or device biometric to mark attendance directly and show success instantly.</p>
                    <button className="secondary-btn" onClick={handleDeviceBiometricAttendance} disabled={isSubmitting}>Mark Fingerprint Attendance</button>
                  </div>
                </div>
                <div className="meta-grid">
                  <div className="meta-card">
                    <strong>Face Status</strong>
                    <p>{faceRegistered ? "Registered" : "Pending"}</p>
                  </div>
                  <div className="meta-card">
                    <strong>Device Biometric</strong>
                    <p>{fingerprintRegistered ? "Enrolled" : "Pending"}</p>
                  </div>
                </div>
              </article>
            </section>
          </>
        )}

        {activeSection === "attendance" && (
          <section className="panel-grid">
            <article className="glass-card">
              <SectionTitle eyebrow="Updated Records" title="Attendance history" copy="New punches appear here after direct face or fingerprint entry." />
              <div className="feed-list">
                {userAttendance.map((item) => (
                  <div className="feed-item" key={item.id}>
                    <div>
                      <strong>{item.date}</strong>
                      <p>{item.mode} • {item.geoTag || "No geo-tag"}</p>
                    </div>
                    <div>
                      <span>{item.hoursLogged}h</span>
                      <b>{item.status}</b>
                    </div>
                  </div>
                ))}
              </div>
            </article>
            <article className="glass-card">
              <SectionTitle eyebrow="Live Feed" title="Current workforce status" copy="Fresh mark-attendance updates." />
              <div className="feed-list">
                {liveAttendance.map((item) => (
                  <div className="feed-item" key={`${item.employee}-${item.geoTag}`}>
                    <div>
                      <strong>{item.employee}</strong>
                      <p>{item.branch} • {item.geoTag}</p>
                    </div>
                    <div>
                      <span>{item.mood}</span>
                      <b>{item.presence}</b>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "payroll" && (
          <section className="panel-grid">
            <article className="glass-card">
              <SectionTitle eyebrow="Salary Engine" title="Run payroll" copy="Calculate salary from attendance and generate payslips." />
              <label className="field">
                <span>Payroll month</span>
                <input type="month" value={monthLabel} onChange={(event) => setMonthLabel(event.target.value)} />
              </label>
              <div className="button-row">
                <button className="primary-btn" onClick={handleRunPayroll} disabled={isSubmitting}>Process Monthly Payroll</button>
                {monthlySummary?.payroll?.id ? (
                  <button className="secondary-btn" onClick={() => downloadReport(`/payroll/${monthlySummary.payroll.id}/payslip`)}>Download Payslip PDF</button>
                ) : null}
              </div>
              <div className="meta-grid">
                <div className="meta-card"><strong>Present Days</strong><p>{monthlySummary?.present_days ?? 0}</p></div>
                <div className="meta-card"><strong>Estimated Income</strong><p>INR {Number(monthlySummary?.estimated_income || 0).toFixed(2)}</p></div>
                <div className="meta-card"><strong>Late Days</strong><p>{monthlySummary?.late_days ?? 0}</p></div>
                <div className="meta-card"><strong>Overtime</strong><p>{monthlySummary?.overtime_hours ?? 0}h</p></div>
              </div>
            </article>
            <article className="glass-card">
              <SectionTitle eyebrow="Processed Records" title="Payroll history" copy="Generated payroll records for the selected employee." />
              <div className="feed-list">
                {payrollRecords.map((item) => (
                  <div className="feed-item" key={item.id}>
                    <div>
                      <strong>{item.monthLabel}</strong>
                      <p>Gross INR {item.grossSalary}</p>
                    </div>
                    <div>
                      <span>Tax INR {item.taxDeduction}</span>
                      <b>Net INR {item.netSalary}</b>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </section>
        )}

        {activeSection === "reports" && (
          <section className="panel-grid">
            <article className="glass-card">
              <SectionTitle eyebrow="Monthly Reports" title="Personal employee report" copy="Download the user's attendance report and payslip as PDF." />
              <label className="field">
                <span>Report month</span>
                <input type="month" value={monthLabel} onChange={(event) => setMonthLabel(event.target.value)} />
              </label>
              <div className="button-stack">
                <button className="primary-btn" onClick={() => downloadReport(`/reports/attendance/${selectedUserId}?month_label=${monthLabel}`)}>Download Attendance PDF</button>
                {monthlySummary?.payroll?.id ? (
                  <button className="secondary-btn" onClick={() => downloadReport(`/payroll/${monthlySummary.payroll.id}/payslip`)}>Download Payslip PDF</button>
                ) : (
                  <button className="secondary-btn" onClick={handleRunPayroll}>Generate Payroll First</button>
                )}
              </div>
            </article>
            <article className="glass-card">
              <SectionTitle eyebrow="Summary" title="Selected employee snapshot" copy="Monthly attendance and income summary." />
              <div className="meta-grid">
                <div className="meta-card"><strong>Name</strong><p>{selectedUser?.name || "-"}</p></div>
                <div className="meta-card"><strong>Code</strong><p>{selectedUser?.employeeCode || "-"}</p></div>
                <div className="meta-card"><strong>Present</strong><p>{monthlySummary?.present_days ?? 0}</p></div>
                <div className="meta-card"><strong>Payable Days</strong><p>{monthlySummary?.payable_days ?? 0}</p></div>
              </div>
            </article>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
