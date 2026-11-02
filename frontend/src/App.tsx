import { useEffect, useState, useCallback } from "react";
import { api, type Project, type Status } from "./api";
import { PlanTab } from "./tabs/PlanTab";
import { H3Tab } from "./tabs/H3Tab";
import { LtxTab } from "./tabs/LtxTab";
import { JobsTab } from "./tabs/JobsTab";
import { ReviewTab } from "./tabs/ReviewTab";
import { TimelineTab } from "./tabs/TimelineTab";
import { StatusTab } from "./tabs/StatusTab";

type TabId = "plan" | "h3" | "ltx" | "jobs" | "review" | "timeline" | "status";
const TABS: { id: TabId; label: string }[] = [
  { id: "plan", label: "Plan ujęć" },
  { id: "h3", label: "H3 Extender" },
  { id: "ltx", label: "LTX lipsync" },
  { id: "jobs", label: "Zadania" },
  { id: "review", label: "Przegląd" },
  { id: "timeline", label: "Oś montażowa" },
  { id: "status", label: "Stan systemu" },
];

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("plan");
  const [status, setStatus] = useState<Status | null>(null);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    const list = await api.get<Project[]>("/api/projects-summary");
    setProjects(list);
    setSelected((cur) => cur ?? (list[0]?.id ?? null));
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      setStatus(await api.get<Status>("/api/system/status"));
    } catch {
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    loadProjects().catch((e: Error) => setError(e.message));
    loadStatus();
    const t = setInterval(loadStatus, 15000);
    return () => clearInterval(t);
  }, [loadProjects, loadStatus]);

  async function createProject() {
    const name = newName.trim();
    if (!name) return;
    try {
      const p = await api.post<Project>("/api/projects", { name });
      setNewName("");
      await loadProjects();
      setSelected(p.id);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const project = projects.find((p) => p.id === selected) ?? null;

  return (
    <div className="app">
      <aside className="side">
        <div className="brand">
          <div className="dot" />
          <div>
            <b>PsychOdelic Studio</b>
            <small>lokalnie · 127.0.0.1</small>
          </div>
        </div>
        <div className="stack">
          <span className="hint">Projekty</span>
          {projects.length === 0 && <div className="hint">Brak projektów. Utwórz pierwszy poniżej.</div>}
          {projects.map((p) => (
            <button key={p.id} className={`proj ${p.id === selected ? "sel" : ""}`} onClick={() => setSelected(p.id)}>
              <div>{p.name}</div>
              <div className="meta">zadania: {p.jobs ?? 0} · warianty: {p.variants ?? 0}</div>
            </button>
          ))}
        </div>
        <div className="stack" style={{ marginTop: "auto" }}>
          <label>
            <span>Nowy projekt</span>
            <input value={newName} placeholder="np. Once Upon a Garden"
              onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && createProject()} />
          </label>
          <button className="primary" onClick={createProject} disabled={!newName.trim()}>Utwórz projekt</button>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div className="title">{project ? project.name : "Wybierz projekt"}</div>
          <div className="chips">
            <span className={`chip ${status?.render_enabled ? "ok" : "off"}`} title={status?.note}>
              Render GPU: {status ? (status.render_enabled ? "włączony" : "wyłączony") : "?"}
            </span>
            <span className={`chip ${status?.vram.status === "POTWIERDZONE_TESTEM" ? "ok" : "warn"}`}>
              VRAM: {status?.vram.status === "POTWIERDZONE_TESTEM" ? "odczytany" : "niezweryfikowany"}
            </span>
            <span className={`chip ${status?.llm.status === "POTWIERDZONE_TESTEM" ? "ok" : "off"}`}>
              Model lokalny: {status?.llm.runtime === "ollama" && status.llm.status === "POTWIERDZONE_TESTEM" ? "działa" : "tryb regułowy"}
            </span>
          </div>
        </div>

        {error && <div style={{ padding: "10px 22px" }}><div className="alert err">{error}</div></div>}

        <nav className="tabs">
          {TABS.map((t) => (
            <button key={t.id} className={`tab ${tab === t.id ? "on" : ""}`} onClick={() => setTab(t.id)}>{t.label}</button>
          ))}
        </nav>

        <div className="content">
          {!project && tab !== "status" && (
            <div className="empty">Utwórz projekt po lewej, aby zacząć planowanie ujęć.</div>
          )}
          {project && tab === "plan" && <PlanTab project={project} />}
          {project && tab === "h3" && <H3Tab project={project} />}
          {project && tab === "ltx" && <LtxTab project={project} />}
          {project && tab === "jobs" && <JobsTab project={project} />}
          {project && tab === "review" && <ReviewTab project={project} />}
          {project && tab === "timeline" && <TimelineTab project={project} />}
          {tab === "status" && <StatusTab status={status} onRefresh={loadStatus} />}
        </div>
      </main>
    </div>
  );
}
