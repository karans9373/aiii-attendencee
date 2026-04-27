export const dashboard = {
  summary: [
    { label: "Present Today", value: "148", change: "+12%" },
    { label: "Late Employees", value: "09", change: "-6%" },
    { label: "Payroll Due", value: "31", change: "+4%" },
    { label: "Overtime Hours", value: "126h", change: "+18%" }
  ],
  attendanceBreakdown: [
    { name: "Present", value: 78 },
    { name: "Late", value: 12 },
    { name: "Absent", value: 10 }
  ],
  monthlyTrends: [
    { month: "Jan", attendance: 84, payroll: 6.7 },
    { month: "Feb", attendance: 88, payroll: 6.9 },
    { month: "Mar", attendance: 90, payroll: 7.1 },
    { month: "Apr", attendance: 92, payroll: 7.4 }
  ],
  payrollDistribution: [
    { name: "Engineering", value: 4.3 },
    { name: "People Ops", value: 1.8 },
    { name: "Field Ops", value: 2.2 }
  ],
  productivity: [
    { name: "Ananya", score: 94 },
    { name: "Rahul", score: 87 },
    { name: "Priya", score: 82 },
    { name: "Arjun", score: 90 }
  ],
  heatmap: [
    { department: "Engineering", utilization: 88, risk: "Medium" },
    { department: "People Ops", utilization: 76, risk: "Low" },
    { department: "Field Ops", utilization: 92, risk: "High" }
  ],
  liveFeed: [
    { employee: "Priya Sharma", mode: "Face", branch: "Mumbai", mood: "Focused", status: "Live" },
    { employee: "Arjun Das", mode: "Fingerprint", branch: "Bengaluru", mood: "Stressed", status: "Flagged" },
    { employee: "Rahul Mehta", mode: "Remote", branch: "Bengaluru", mood: "Calm", status: "Live" }
  ],
  wowFeatures: [
    "AI Productivity Score",
    "Burnout Risk Predictor",
    "Payroll Anomaly Detector",
    "Voice Assistant for HR",
    "Attendance Fraud Detection"
  ]
};

export const bootstrap = {
  users: [
    { id: 1, name: "Ananya Rao", role: "admin", branch: "Bengaluru HQ" },
    { id: 2, name: "Rahul Mehta", role: "hr", branch: "Bengaluru HQ" },
    { id: 3, name: "Priya Sharma", role: "employee", branch: "Mumbai Branch" }
  ],
  notifications: [
    { id: 1, title: "Payroll cutoff reminder", message: "Approve corrections before final salary processing.", level: "warning" },
    { id: 2, title: "High overtime alert", message: "Engineering crossed safe overtime threshold this week.", level: "critical" }
  ]
};
