import { useEffect, useMemo, useState } from "react";
import { api, type Clip, type Project } from "../api";

type Row = { clip_id: string; source_path: string; source_in: string; source_out: string; timeline_start: string };
const toRow = (c: Clip): Row => ({ clip_id: c.clip_id, source_path: c.source_path, source_in: String(c.source_in),
  source_out: String(c.source_out), timeline_start: String(c.timeline_start) });
// Ten sam format co backend (frames_to_timecode): hh:mm:ss:ff przy 24 fps.
const tc = (frames: number, fps = 24) => {
  const safe = Math.max(0, Math.floor(frames));
  const s = Math.floor(safe / fps), f = safe % fps;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return [h, m, sec, f].map((n) => String(n).padStart(2, "0")).join(":");
};

export function TimelineTab({ project }: { project: Project }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [exported, setExported] = useState<string | null>(null);

  const load = () => api.get<{ clips: Clip[] }>(`/api/projects/${project.id}/timeline`)
    .then((r) => setRows(r.clips.map(toRow))).catch(() => setRows([]));
  useEffect(() => { load(); setExported(null); setMsg(null); }, [project.id]);

  const parsed = useMemo(() => rows.map((r) => ({
    ...r, a: Number(r.timeline_start), inF: Number(r.source_in), outF: Number(r.source_out),
  })), [rows]);
  const localErrors = useMemo(() => {
    const errs: string[] = [];
    parsed.forEach((r) => {
      if (!r.source_path.trim()) errs.push(`${r.clip_id || "klip"}: brak pliku`);
      if (!(r.outF > r.inF)) errs.push(`${r.clip_id || "klip"}: koniec (wyłączny) musi być po początku`);
    });
    const sorted = [...parsed].sort((x, y) => x.a - y.a);
    sorted.forEach((r, i) => {
      const prev = sorted[i - 1];
      if (prev && r.a < prev.a + (prev.outF - prev.inF)) errs.push(`${prev.clip_id} i ${r.clip_id} nakładają się na osi`);
    });
    return errs;
  }, [parsed]);
  const total = Math.max(0, ...parsed.map((r) => r.a + (r.outF - r.inF)));
  // Klipy nakladajace sie ida na osobne sciezki (lanes), zeby bylo widac konflikt.
  const drawn = useMemo(() => {
    const ends: number[] = [];
    return [...parsed]
      .filter((r) => r.outF > r.inF)
      .sort((x, y) => x.a - y.a)
      .map((r, key) => {
        const len = r.outF - r.inF;
        let lane = ends.findIndex((e) => e <= r.a);
        if (lane === -1) { lane = ends.length; ends.push(r.a + len); } else { ends[lane] = r.a + len; }
        return { ...r, key, lane, len };
      });
  }, [parsed]);
  const lanes = Math.max(1, ...drawn.map((r) => r.lane + 1));

  const upd = (i: number, patch: Partial<Row>) => setRows((rs) => rs.map((r, k) => (k === i ? { ...r, ...patch } : r)));
  const addRow = () => setRows((rs) => [...rs, {
    clip_id: `klip_${rs.length + 1}`, source_path: "", source_in: "0", source_out: "124",
    timeline_start: String(rs.reduce((m, r) => Math.max(m, Number(r.timeline_start) + Number(r.source_out) - Number(r.source_in)), 0)),
  }]);

  async function save() {
    if (localErrors.length) { setMsg({ kind: "err", text: localErrors[0] }); return; }
    try {
      await api.put(`/api/projects/${project.id}/timeline`, { clips: rows.map((r) => ({
        clip_id: r.clip_id, source_path: r.source_path, source_in: Number(r.source_in),
        source_out: Number(r.source_out), timeline_start: Number(r.timeline_start) })) });
      setMsg({ kind: "ok", text: "Oś zapisana." });
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function doExport(format: "csv" | "json") {
    try {
      const r = await api.get<{ content: string | object }>(`/api/projects/${project.id}/timeline/export?format=${format}`);
      setExported(typeof r.content === "string" ? r.content : JSON.stringify(r.content, null, 2));
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  return (
    <div className="stack">
      <div>
        <h2>Oś montażowa</h2>
        <p className="lead">Ułóż zatwierdzone klipy w czasie utworu. Zakres źródła <code>[początek, koniec)</code>: koniec jest
          wyłączny, a klatki liczone są w FPS osi (24). Ścieżka audio zawsze pochodzi z oryginalnego master WAV.</p>
      </div>
      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}

      <div className="card">
        <div className="timeline-bar" style={{ height: lanes * 30 + 8 }}>
          {drawn.map((r) => (
            <div key={r.key} className="seg" title={`${r.clip_id}: ${tc(r.a)} → ${tc(r.a + r.len)}`}
              style={{ left: `${total ? (r.a / total) * 100 : 0}%`, width: `${total ? (r.len / total) * 100 : 0}%`,
                top: 4 + r.lane * 30, height: 24 }}>
              {r.clip_id}
            </div>
          ))}
        </div>
        <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
          <span className="hint">Długość osi: {total} kl. · koniec {tc(total)}</span>
          <span className="hint">{localErrors.length ? `${localErrors.length} do poprawy` : "układ poprawny"}</span>
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Klip</th><th>Plik źródłowy</th><th className="num">Wejście</th><th className="num">Wyjście (wył.)</th><th className="num">Start na osi</th><th /></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={6} className="hint" style={{ textAlign: "center", padding: 22 }}>Brak klipów. Dodaj pierwszy.</td></tr>}
            {rows.map((r, i) => (
              <tr key={i}>
                <td><input value={r.clip_id} onChange={(e) => upd(i, { clip_id: e.target.value })} style={{ width: 120 }} /></td>
                <td><input value={r.source_path} placeholder="renders/…mp4" onChange={(e) => upd(i, { source_path: e.target.value })} /></td>
                <td className="num"><input value={r.source_in} onChange={(e) => upd(i, { source_in: e.target.value })} style={{ width: 90, textAlign: "right" }} /></td>
                <td className="num"><input value={r.source_out} onChange={(e) => upd(i, { source_out: e.target.value })} style={{ width: 90, textAlign: "right" }} /></td>
                <td className="num"><input value={r.timeline_start} onChange={(e) => upd(i, { timeline_start: e.target.value })} style={{ width: 90, textAlign: "right" }} /><div className="hint">{tc(Number(r.timeline_start) || 0)}</div></td>
                <td><button className="ghost danger" onClick={() => setRows((rs) => rs.filter((_, k) => k !== i))}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {localErrors.map((e, i) => <div key={i} className="alert warn">{e}</div>)}

      <div className="row">
        <button onClick={addRow}>+ dodaj klip</button>
        <button className="primary" onClick={save} disabled={localErrors.length > 0}>Zapisz oś</button>
        <button onClick={() => doExport("csv")}>Eksport CSV</button>
        <button onClick={() => doExport("json")}>Eksport JSON</button>
      </div>

      {exported && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>Eksport</h3>
            <button onClick={() => navigator.clipboard?.writeText(exported)}>Kopiuj</button>
          </div>
          <pre className="cmd" style={{ marginTop: 10 }}>{exported}</pre>
        </div>
      )}
    </div>
  );
}
