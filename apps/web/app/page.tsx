"use client";

import {
  Activity,
  AlertCircle,
  BriefcaseBusiness,
  CheckCircle2,
  FileUp,
  LogIn,
  MessageSquare,
  Send,
  UserRound
} from "lucide-react";
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

type StatusEvent = {
  event: string;
  message: string;
  step_id?: string;
  agent?: string;
  status?: string;
  data?: Dashboard | { steps?: Array<{ id: string; label: string; agent: string; reason: string }> };
};

type Diagnostic = {
  label: string;
  status: "pending" | "success" | "error" | "info";
  detail: string;
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
  const [uploadStatus, setUploadStatus] = useState<Diagnostic>({
    label: "Resume upload",
    status: "info",
    detail: "No resume uploaded yet"
  });
  const [chatStatus, setChatStatus] = useState<Diagnostic>({
    label: "Agent workflow",
    status: "info",
    detail: "Waiting for a chat request"
  });
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [events, setEvents] = useState<StatusEvent[]>([]);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  async function demoLogin() {
    setDiagnostics((current) => [
      { label: "Demo login", status: "pending", detail: "Calling /auth/demo-login" },
      ...current
    ]);
    try {
      const response = await fetch(`${apiBase}/auth/demo-login`, { method: "POST" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const user = await response.json();
      setToken(user.user_id);
      setStatus(`Signed in as ${user.email}`);
      addDiagnostic("Demo login", "success", `Signed in as ${user.email}`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Login failed";
      setStatus(detail);
      addDiagnostic("Demo login", "error", detail);
    }
  }

  async function uploadResume(): Promise<boolean> {
    if (!resumeText.trim()) {
      const detail = "Paste resume text before uploading.";
      setUploadStatus({ label: "Resume upload", status: "error", detail });
      addDiagnostic("Resume upload", "error", detail);
      return false;
    }
    setIsUploading(true);
    setUploadStatus({ label: "Resume upload", status: "pending", detail: "Uploading resume text..." });
    addDiagnostic("Resume upload", "pending", `POST ${apiBase}/api/resumes`);
    const file = new File([resumeText], "resume.txt", { type: "text/plain" });
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(`${apiBase}/api/resumes`, {
        method: "POST",
        headers: authHeader,
        body
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const result = await response.json();
      const detail = `Uploaded ${result.filename} (${result.resume_id})`;
      setUploadStatus({ label: "Resume upload", status: "success", detail });
      setStatus(detail);
      addDiagnostic("Resume upload", "success", detail);
      return true;
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Resume upload failed";
      setUploadStatus({ label: "Resume upload", status: "error", detail });
      setStatus(detail);
      addDiagnostic("Resume upload", "error", detail);
      return false;
    } finally {
      setIsUploading(false);
    }
  }

  async function sendChat() {
    if (isChatting) {
      return;
    }
    setStatus("Planning agent workflow...");
    setChatStatus({ label: "Agent workflow", status: "pending", detail: "Preparing chat request..." });
    setEvents([]);
    if (resumeText.trim()) {
      const uploaded = await uploadResume();
      if (!uploaded) {
        setChatStatus({
          label: "Agent workflow",
          status: "error",
          detail: "Chat stopped because resume upload failed."
        });
        return;
      }
    }
    setIsChatting(true);
    addDiagnostic("SSE stream", "pending", "Opening /api/chat/events");
    const params = new URLSearchParams({
      message,
      target_role: targetRole,
      location,
      user_id: token
    });
    const source = new EventSource(`${apiBase}/api/chat/events?${params.toString()}`);
    let completed = false;

    source.addEventListener("plan", (event) => {
      const parsed = JSON.parse((event as MessageEvent).data) as StatusEvent;
      setEvents((current) => [...current, parsed]);
      setStatus("Main agent created a plan");
      setChatStatus({ label: "Agent workflow", status: "pending", detail: parsed.message });
      addDiagnostic("Main agent plan", "success", parsed.message);
    });
    source.addEventListener("status", (event) => {
      const parsed = JSON.parse((event as MessageEvent).data) as StatusEvent;
      setEvents((current) => [...current, parsed]);
      setStatus(parsed.message);
      setChatStatus({ label: "Agent workflow", status: "pending", detail: parsed.message });
    });
    source.addEventListener("complete", (event) => {
      const parsed = JSON.parse((event as MessageEvent).data) as StatusEvent;
      completed = true;
      setEvents((current) => [...current, parsed]);
      setDashboard(parsed.data as Dashboard);
      setStatus("Agent workflow complete");
      setChatStatus({ label: "Agent workflow", status: "success", detail: "Dashboard updated." });
      addDiagnostic("SSE stream", "success", "Received complete event and dashboard data.");
      setIsChatting(false);
      source.close();
    });
    source.addEventListener("error", (event) => {
      if ("data" in event && event.data) {
        const parsed = JSON.parse((event as MessageEvent).data) as StatusEvent;
        setEvents((current) => [...current, parsed]);
        setStatus(parsed.message);
        setChatStatus({ label: "Agent workflow", status: "error", detail: parsed.message });
        addDiagnostic("SSE stream", "error", parsed.message);
      } else {
        const detail = completed
          ? "Workflow stream closed after completion."
          : "Workflow stream interrupted before completion. Check web-api Cloud Run logs.";
        setStatus(detail);
        setChatStatus({
          label: "Agent workflow",
          status: completed ? "success" : "error",
          detail
        });
        addDiagnostic("SSE stream", completed ? "success" : "error", detail);
      }
      setIsChatting(false);
      source.close();
    });
  }

  function addDiagnostic(label: string, statusValue: Diagnostic["status"], detail: string) {
    setDiagnostics((current) => [
      { label, status: statusValue, detail },
      ...current.filter((item) => !(item.label === label && item.detail === detail))
    ].slice(0, 8));
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
        <button disabled={isUploading} onClick={uploadResume}>
          <FileUp size={18} />
          {isUploading ? "Uploading..." : "Upload resume"}
        </button>
        <StatusCard item={uploadStatus} />
        <StatusCard item={chatStatus} />
        <p className="status">Current: {status}</p>
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
              <button aria-label="Send message" disabled={isChatting} onClick={sendChat}>
                <Send size={18} />
              </button>
            </div>
          </div>

          <div className="panel">
            <h3>
              <Activity size={18} />
              Agent status
            </h3>
            <div className="timeline">
              {events.length === 0 && <p className="empty">No agent events yet.</p>}
              {events.map((item, index) => (
                <div className="event" key={`${item.event}-${item.step_id || index}`}>
                  <strong>{item.agent || item.event}</strong>
                  <span>{item.message}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>
              <AlertCircle size={18} />
              Diagnostics
            </h3>
            <div className="diagnostics">
              {diagnostics.length === 0 && <p className="empty">No API calls yet.</p>}
              {diagnostics.map((item, index) => (
                <StatusCard item={item} key={`${item.label}-${index}`} compact />
              ))}
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

function StatusCard({ item, compact = false }: { item: Diagnostic; compact?: boolean }) {
  return (
    <div className={`status-card ${item.status} ${compact ? "compact" : ""}`}>
      {item.status === "success" ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
      <div>
        <strong>{item.label}</strong>
        <span>{item.detail}</span>
      </div>
    </div>
  );
}
