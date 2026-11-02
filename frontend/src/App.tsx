import { useEffect, useState, useCallback } from "react";
import { api, type Project, type Status } from "./api";
import { useI18n, type Key } from "./i18n";
import { PlanTab } from "./tabs/PlanTab";
import { H3Tab } from "./tabs/H3Tab";
import { LtxTab } from "./tabs/LtxTab";
import { JobsTab } from "./tabs/JobsTab";
import { ReviewTab } from "./tabs/ReviewTab";
import { TimelineTab } from "./tabs/TimelineTab";
import { StatusTab } from "./tabs/StatusTab";

type TabId = "plan" | "h3" | "ltx" | "jobs" | "review" | "timeline" | "status";
const TABS: { id: TabId; key: Key }[] = [
  { id: "plan", key: "nav.plan" }, { id: "h3", key: "nav.h3" }, { id: "ltx", key: "nav.ltx" },
  { id: "jobs", key: "nav.jobs" }, { id: "review", key: "nav.review" }, { id: "timeline", key: "nav.timeline" },
  { id: "status", key: "nav.status" },
];

export function App() {
  const { t, lang, setLang } = useI18n();
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
    try { setStatus(await api.get<Status>("/api/system/status")); } catch { setStatus(null); }
  }, []);

  useEffect(() => {
    loadProjects().catch((e: Error) => setError(e.message));
    loadStatus();
    const timer = setInterval(loadStatus, 15000);
    return () => clearInterval(timer);
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
      const msg = (e as Error).message;
      setError(msg.includes("już istnieje") ? t("projects.duplicate") : msg);
    }
  }

  const project = projects.find((p) => p.id === selected) ?? null;
  const renderOn = Boolean(status?.render_enabled);
  const vramOk = status?.vram.status === "POTWIERDZONE_TESTEM";
  const llmOk = status?.llm.runtime === "ollama" && status.llm.status === "POTWIERDZONE_TESTEM";

  return (
    <div className="app">
      <aside className="side">
        <div className="brand">
          <div className="dot" />
          <div>
            <b>PsychOdelic Studio</b>
            <small>{t("app.local")}</small>
          </div>
        </div>
        <div className="stack">
          <span className="hint">{t("projects.title")}</span>
          {projects.length === 0 && <div className="hint">{t("projects.empty")}</div>}
          {projects.map((p) => (
            <button key={p.id} className={`proj ${p.id === selected ? "sel" : ""}`} onClick={() => setSelected(p.id)}>
              <div>{p.name}</div>
              <div className="meta">{t("projects.meta", { jobs: p.jobs ?? 0, variants: p.variants ?? 0 })}</div>
            </button>
          ))}
        </div>
        <div className="stack" style={{ marginTop: "auto" }}>
          <label>
            <span>{t("projects.new")}</span>
            <input value={newName} placeholder={t("projects.placeholder")}
              onChange={(e) => setNewName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && createProject()} />
          </label>
          <button className="primary" onClick={createProject} disabled={!newName.trim()}>{t("projects.create")}</button>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div className="title">{project ? project.name : t("projects.pick")}</div>
          <div className="chips">
            <span className={`chip ${renderOn ? "ok" : "off"}`} title={status?.note}>
              {renderOn ? t("chip.render.on") : t("chip.render.off")}
            </span>
            <span className={`chip ${vramOk ? "ok" : "warn"}`}>{vramOk ? t("chip.vram.ok") : t("chip.vram.no")}</span>
            <span className={`chip ${llmOk ? "ok" : "off"}`}>{llmOk ? t("chip.llm.ok") : t("chip.llm.rule")}</span>
            <div className="lang" role="group" aria-label={t("lang.label")}>
              <button className={lang === "pl" ? "on" : ""} onClick={() => setLang("pl")} aria-pressed={lang === "pl"}>{t("lang.pl")}</button>
              <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")} aria-pressed={lang === "en"}>{t("lang.en")}</button>
            </div>
          </div>
        </div>

        {error && <div style={{ padding: "10px 22px" }}><div className="alert err">{error}</div></div>}

        <nav className="tabs">
          {TABS.map((x) => (
            <button key={x.id} className={`tab ${tab === x.id ? "on" : ""}`} onClick={() => setTab(x.id)}>{t(x.key)}</button>
          ))}
        </nav>

        <div className="content">
          {!project && tab !== "status" && <div className="empty">{t("projects.needOne")}</div>}
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
