"use client";

import { BriefcaseBusiness, FileUp, LogIn, MessageSquare, Send, UserRound } from "lucide-react";
import { useMemo, useState } from "react";

type ChatMessage = {
  role: string;
  content: string;
};

type Dashboard = {
  profile: Record<string, unknown>;
  skill_graph: {
    fit_score?: number;
    readiness_level?: string;
    strengths?: string[];
    skill_gaps?: string[];
  };
  learning_path: {
    steps?: Array<{ week: number; focus: string; objective: string; practice: string }>;
  };
  report: {
    headline?: string;
    next_actions?: string[];
  };
  jobs: Array<{
    id: string;
    title: string;
    organization: string;
    location: string;
    apply_url: string;
    source: string;
  }>;
  chat_history: ChatMessage[];
};

const emptyDashboard: Dashboard = {
  profile: {},
  skill_graph: {},
  learning_path: {},
  report: {},
  jobs: [],
  chat_history: []
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8081";

export default function Home() {
  const [token, setToken] = useState("demo-user");
  const [resumeText, setResumeText] = useState("");
  const [targetRole, setTargetRole] = useState("data analyst");
  const [location, setLocation] = useState("Texas");
  const [message, setMessage] = useState("What should I do next to become job-ready?");
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard);
  const [status, setStatus] = useState("Ready");

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  async function demoLogin() {
    const response = await fetch(`${apiBase}/auth/demo-login`, { method: "POST" });
    const user = await response.json();
    setToken(user.user_id);
    setStatus(`Signed in as ${user.email}`);
  }

  async function uploadResume() {
    const file = new File([resumeText], "resume.txt", { type: "text/plain" });
    const body = new FormData();
    body.append("file", file);
    const response = await fetch(`${apiBase}/api/resumes`, {
      method: "POST",
      headers: authHeader,
      body
    });
    if (!response.ok) {
      setStatus(await response.text());
      return;
    }
    const result = await response.json();
    setStatus(`Uploaded ${result.filename}`);
  }

  async function sendChat() {
    setStatus("Running agents...");
    const response = await fetch(`${apiBase}/api/chat`, {
      method: "POST",
      headers: { ...authHeader, "Content-Type": "application/json" },
      body: JSON.stringify({ message, resume_text: resumeText, target_role: targetRole, location })
    });
    if (!response.ok) {
      setStatus(await response.text());
      return;
    }
    setDashboard(await response.json());
    setStatus("Agent workflow complete");
  }

  const gaps = dashboard.skill_graph.skill_gaps || [];
  const strengths = dashboard.skill_graph.strengths || [];

  return (
    <main className="shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">SkillBridge AI</p>
          <h1>Career readiness cockpit</h1>
        </div>
        <button className="primary" onClick={demoLogin}>
          <LogIn size={18} />
          Demo login
        </button>
        <label>
          Target role
          <input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} />
        </label>
        <label>
          Location
          <input value={location} onChange={(event) => setLocation(event.target.value)} />
        </label>
        <label>
          Resume text
          <textarea
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            placeholder="Paste resume text for the POC..."
          />
        </label>
        <button onClick={uploadResume}>
          <FileUp size={18} />
          Upload resume
        </button>
        <p className="status">{status}</p>
      </aside>

      <section className="workspace">
        <div className="toolbar">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h2>{dashboard.report.headline || "Resume-guided job plan"}</h2>
          </div>
          <div className="score">
            <span>{Math.round((dashboard.skill_graph.fit_score || 0) * 100)}%</span>
            <small>{dashboard.skill_graph.readiness_level || "not analyzed"}</small>
          </div>
        </div>

        <section className="grid">
          <div className="panel">
            <h3>
              <UserRound size={18} />
              Skill profile
            </h3>
            <div className="chips">
              {strengths.map((skill) => (
                <span className="chip good" key={skill}>{skill}</span>
              ))}
              {gaps.map((skill) => (
                <span className="chip warn" key={skill}>{skill}</span>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>
              <MessageSquare size={18} />
              Agent chat
            </h3>
            <div className="chat">
              {dashboard.chat_history.map((item, index) => (
                <p className={item.role === "assistant" ? "assistant" : "user"} key={index}>
                  {item.content}
                </p>
              ))}
            </div>
            <div className="composer">
              <input value={message} onChange={(event) => setMessage(event.target.value)} />
              <button aria-label="Send message" onClick={sendChat}>
                <Send size={18} />
              </button>
            </div>
          </div>

          <div className="panel">
            <h3>
              <BriefcaseBusiness size={18} />
              USAJOBS matches
            </h3>
            <div className="jobs">
              {dashboard.jobs.map((job) => (
                <a className="job" href={job.apply_url} key={job.id} rel="noreferrer" target="_blank">
                  <strong>{job.title}</strong>
                  <span>{job.organization}</span>
                  <small>{job.location} · {job.source}</small>
                </a>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>Learning path</h3>
            <ol className="steps">
              {(dashboard.learning_path.steps || []).map((step) => (
                <li key={`${step.week}-${step.focus}`}>
                  <strong>Week {step.week}: {step.focus}</strong>
                  <span>{step.objective}</span>
                </li>
              ))}
            </ol>
          </div>
        </section>
      </section>
    </main>
  );
}

