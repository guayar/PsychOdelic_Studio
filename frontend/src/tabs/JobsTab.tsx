import { useEffect, useState } from "react";
import { api, type Job, type JobEvent, type Project } from "../api";
import { useI18n } from "../i18n";
import { kindKey, stateKey } from "../format";

const ACTIVE = new Set(["DIRECTOR_UNLOADING", "GPU_FREE_VERIFIED", "GPU_BUSY", "RENDER_QUEUED", "RENDERING", "RECOVERING", "OUTPUT_VALIDATING", "POSTPROCESSING", "DIRECTOR_RELOAD_PENDING"]);

export function JobsTab({ project }: { project: Project }) {
  const { t } = useI18n();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [events, setEvents] = useState<JobEvent[]>([]);

  const load = () => api.get<Job[]>(`/api/projects/${project.id}/jobs`).then(setJobs).catch(() => setJobs([]));
  useEffect(() => { load(); setOpen(null); const timer = setInterval(() => { if (!document.hidden) load(); }, 15000); return () => clearInterval(timer); }, [project.id]);
  useEffect(() => { if (open) api.get<JobEvent[]>(`/api/jobs/${open}/events`).then(setEvents); }, [open]);
  const [msg, setMsg] = useState<string | null>(null);

  async function removeJob(id: string) {
    if (!window.confirm(t("jobs.deleteConfirm"))) return;
    try {
      await api.del(`/api/jobs/${id}`);
      if (open === id) setOpen(null);
      setMsg(null); load();
    } catch (e) { setMsg((e as Error).message); }
  }

  async function clearAll() {
    if (!window.confirm(t("jobs.clearConfirm"))) return;
    try {
      const r = await api.post<{ deleted: number; kept_active: number }>(`/api/projects/${project.id}/jobs/clear`);
      setOpen(null);
      setMsg(t("jobs.cleared", { n: r.deleted, active: r.kept_active }));
      load();
    } catch (e) { setMsg((e as Error).message); }
  }

  return (
    <div className="stack">
      <div>
        <h2>{t("jobs.title")}</h2>
        <p className="lead">{t("jobs.lead")}</p>
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span className="hint">{msg}</span>
        <button className="ghost danger" onClick={clearAll} disabled={jobs.length === 0}>{t("jobs.clear")}</button>
      </div>
      {jobs.length === 0 ? (
        <div className="empty">{t("jobs.empty")}</div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead><tr><th>{t("jobs.colType")}</th><th>{t("jobs.colState")}</th><th>{t("jobs.colCreated")}</th><th>{t("jobs.colUpdated")}</th><th /></tr></thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td>{t(kindKey(j.kind) as "kind.raw")}</td>
                  <td><span className={`badge ${j.state}`}>{t(stateKey(j.state) as "state.PLAN_READY")}</span></td>
                  <td className="mono">{j.created_at.replace("T", " ").slice(0, 19)}</td>
                  <td className="mono">{j.updated_at.replace("T", " ").slice(0, 19)}</td>
                  <td>
                    <button onClick={() => setOpen(open === j.id ? null : j.id)}>{open === j.id ? t("jobs.hide") : t("jobs.show")}</button>{" "}
                    <button className="ghost danger" onClick={() => removeJob(j.id)} disabled={ACTIVE.has(j.state)}
                      title={ACTIVE.has(j.state) ? t("jobs.activeHint") : t("jobs.delete")}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <div className="card">
          <h3>{t("jobs.history", { id: open.slice(0, 8) })}</h3>
          <ol style={{ margin: 0, paddingLeft: 18 }}>
            {events.map((e, i) => (
              <li key={i} style={{ marginBottom: 6 }}>
                <span className="mono" style={{ color: "var(--dim)" }}>{e.at.replace("T", " ").slice(0, 19)}</span>{" "}
                <b>{e.event}</b>{" "}
                <span className="mono" style={{ color: "var(--dim)" }}>{JSON.stringify(e.detail)}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
