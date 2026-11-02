import { useEffect, useState } from "react";
import { api, type Project, type Variant } from "../api";

export function ReviewTab({ project }: { project: Project }) {
  const [variants, setVariants] = useState<Variant[]>([]);
  const [path, setPath] = useState("");
  const [kind, setKind] = useState("new_only");
  const [frames, setFrames] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const load = () => api.get<Variant[]>(`/api/projects/${project.id}/variants`).then(setVariants).catch(() => setVariants([]));
  useEffect(() => { load(); setMsg(null); }, [project.id]);

  async function register() {
    try {
      await api.post(`/api/projects/${project.id}/variants`, {
        kind, rel_path: path.trim(), frames: frames ? Number(frames) : null, fps: 24,
      });
      setPath(""); setFrames("");
      setMsg({ kind: "ok", text: "Wariant dodany do przeglądu." });
      load();
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function review(v: Variant, decision: "accepted" | "rejected") {
    try {
      await api.post(`/api/variants/${v.id}/review`, { decision, note: notes[v.id] ?? "" });
      setMsg({ kind: "ok", text: decision === "accepted" ? "Zaakceptowano. Plik pozostaje na dysku." : "Odrzucono. Plik pozostaje na dysku (nic nie jest kasowane)." });
      load();
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  const pending = variants.filter((v) => v.review_status === "pending");
  const done = variants.filter((v) => v.review_status !== "pending");

  return (
    <div className="stack">
      <div>
        <h2>Przegląd ujęć</h2>
        <p className="lead">Tu decydujesz o jakości. Akceptacja i odrzucenie zapisują decyzję i notatkę. <b>Żadna
          decyzja nie kasuje plików</b>: odrzucone ujęcia zostają do ewentualnego powrotu.</p>
      </div>

      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}

      <div className="card">
        <h3>Dodaj wynik do przeglądu</h3>
        <div className="grid3">
          <label><span>Plik względem projektu</span><input value={path} placeholder="renders/OUG_v3b_1_new_only.mp4" onChange={(e) => setPath(e.target.value)} /></label>
          <label><span>Rodzaj</span>
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="new_only">nowe klatki</option><option value="cumulative">kumulacyjny</option>
              <option value="raw">surowy</option><option value="preview">podgląd</option>
              <option value="audio_slice">wycinek audio</option><option value="other">inny</option>
            </select>
          </label>
          <label><span>Liczba klatek</span><input value={frames} onChange={(e) => setFrames(e.target.value)} /></label>
        </div>
        <div className="row end" style={{ marginTop: 12 }}>
          <button onClick={register} disabled={!path.trim()}>Dodaj do przeglądu</button>
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 10 }}>Do oceny · {pending.length}</h3>
        {pending.length === 0 && <div className="empty">Nic nie czeka na ocenę.</div>}
        {pending.map((v) => (
          <div className="review-card" key={v.id}>
            <div>
              <div className="row"><span className="badge pending">{v.kind ?? "—"}</span>
                <span className="mono" style={{ color: "var(--dim)" }}>{v.frames ?? "?"} kl. · {v.fps ?? "?"} fps</span></div>
              <div className="path" style={{ marginTop: 6 }}>{v.abs_path}</div>
              <input style={{ marginTop: 8 }} placeholder="Notatka (np. „zbyt miękko na szwie”)" value={notes[v.id] ?? ""}
                onChange={(e) => setNotes((n) => ({ ...n, [v.id]: e.target.value }))} />
            </div>
            <div className="stack">
              <button className="primary" onClick={() => review(v, "accepted")}>Akceptuj</button>
              <button onClick={() => review(v, "rejected")}>Odrzuć</button>
            </div>
          </div>
        ))}
      </div>

      {done.length > 0 && (
        <div>
          <h3 style={{ marginBottom: 10 }}>Zdecydowane · {done.length}</h3>
          {done.map((v) => (
            <div className="review-card" key={v.id} style={{ opacity: v.review_status === "rejected" ? 0.7 : 1 }}>
              <div>
                <div className="row"><span className={`badge ${v.review_status}`}>{v.review_status === "accepted" ? "zaakceptowany" : "odrzucony"}</span>
                  <span className="mono" style={{ color: "var(--dim)" }}>{v.kind ?? "—"}</span></div>
                <div className="path" style={{ marginTop: 6 }}>{v.abs_path}</div>
              </div>
              <span />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
