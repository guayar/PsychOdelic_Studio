import { useEffect, useState } from "react";
import { api, type Job, type JobEvent, type Project } from "../api";
import { kindLabel, stateLabel } from "../format";

export function JobsTab({ project }: { project: Project }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [events, setEvents] = useState<JobEvent[]>([]);

  const load = () => api.get<Job[]>(`/api/projects/${project.id}/jobs`).then(setJobs).catch(() => setJobs([]));
  useEffect(() => { load(); setOpen(null); const t = setInterval(load, 8000); return () => clearInterval(t); }, [project.id]);
  useEffect(() => { if (open) api.get<JobEvent[]>(`/api/jobs/${open}/events`).then(setEvents); }, [open]);

  return (
    <div className="stack">
      <div>
        <h2>Zadania</h2>
        <p className="lead">Każde przygotowanie komendy jest zadaniem z pełną historią zmian stanu. Stany pokazują, na jakim
          etapie jest praca. Zadania nie są uruchamiane, dopóki render nie zostanie włączony.</p>
      </div>
      {jobs.length === 0 ? (
        <div className="empty">Brak zadań. Przygotuj pierwsze ujęcie w zakładce H3 Extender lub LTX lipsync.</div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead><tr><th>Typ</th><th>Stan</th><th>Utworzono</th><th>Zaktualizowano</th><th /></tr></thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td>{kindLabel[j.kind] ?? j.kind}</td>
                  <td><span className={`badge ${j.state}`}>{stateLabel[j.state] ?? j.state}</span></td>
                  <td className="mono">{j.created_at.replace("T", " ").slice(0, 19)}</td>
                  <td className="mono">{j.updated_at.replace("T", " ").slice(0, 19)}</td>
                  <td><button onClick={() => setOpen(open === j.id ? null : j.id)}>{open === j.id ? "Zwiń" : "Historia"}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && (
        <div className="card">
          <h3>Historia zadania {open.slice(0, 8)}</h3>
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
