import { useState } from "react";
import { api, type PlanResult, type Project } from "../api";

type Beat = { start: string; end: string; text: string };
const parse = (s: string) => {
  const t = s.trim();
  if (!t) return NaN;
  return t.includes(":")
    ? t.split(":").reduce((acc, p) => acc * 60 + parseFloat(p), 0)
    : parseFloat(t.replace(",", "."));
};

export function PlanTab({ project }: { project: Project }) {
  const [beats, setBeats] = useState<Beat[]>([
    { start: "0", end: "5.17", text: "" },
    { start: "5.17", end: "15.30", text: "" },
  ]);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const update = (i: number, patch: Partial<Beat>) =>
    setBeats((bs) => bs.map((b, k) => (k === i ? { ...b, ...patch } : b)));

  async function check() {
    setErr(null); setSaved(null);
    const payload = beats.map((b) => ({ start_s: parse(b.start), end_s: parse(b.end), text: b.text }));
    if (payload.some((b) => Number.isNaN(b.start_s) || Number.isNaN(b.end_s))) {
      setErr("Czas musi być liczbą (12.5) albo zapisem m:ss.s (1:02.5).");
      return;
    }
    try {
      setResult(await api.post<PlanResult>("/api/director/plan", { beats: payload }));
    } catch (e) {
      setResult(null);
      setErr((e as Error).message);
    }
  }

  const promptName = (index: number) => `shot_${String(index).padStart(2, "0")}`;

  async function savePrompt(shot: { index: number; prompt: string }) {
    const r = await api.put<{ rel_path: string }>(`/api/projects/${project.id}/prompts/${promptName(shot.index)}`, { content: shot.prompt });
    return r.rel_path;
  }

  async function saveOne(index: number) {
    if (!result) return;
    try {
      const rel = await savePrompt(result.shots[index]);
      setSaved(`Zapisano ${rel} (użyj go w zakładce H3 Extender).`);
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  async function saveAll() {
    if (!result) return;
    const todo = result.shots.filter((s) => s.prompt.trim());
    try {
      for (const s of todo) await savePrompt(s);
      setSaved(`Zapisano ${todo.length} promptów w prompts/ (shot_01…). Gotowe do użycia w H3 Extender.`);
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  const total = result?.shots.reduce((s, x) => s + x.frames, 0) ?? 0;

  return (
    <div className="stack">
      <div>
        <h2>Plan ujęć</h2>
        <p className="lead">Opisz ujęcia po kolei. Czas wpisz jako <b>12.5</b> albo <b>1:02.5</b>. Każde ujęcie dostaje
          liczbę klatek zgodną z siatką H3 (17n+5 przy 24 fps), a prompt zapisujesz jako plik w projekcie.</p>
      </div>

      <div className="card">
        <h3>Ujęcia</h3>
        <table>
          <thead><tr><th style={{ width: 40 }}>#</th><th style={{ width: 120 }}>Start (s)</th><th style={{ width: 120 }}>Koniec (s)</th><th>Opis (pozytywnie: jeden ruch kamery, bohater milczy)</th><th style={{ width: 40 }} /></tr></thead>
          <tbody>
            {beats.map((b, i) => (
              <tr key={i}>
                <td className="num">{i + 1}</td>
                <td><input value={b.start} onChange={(e) => update(i, { start: e.target.value })} /></td>
                <td><input value={b.end} onChange={(e) => update(i, { end: e.target.value })} /></td>
                <td><textarea value={b.text} onChange={(e) => update(i, { text: e.target.value })} placeholder="The gardener stands still and watches the roses…" /></td>
                <td><button className="ghost danger" onClick={() => setBeats((bs) => bs.filter((_, k) => k !== i))} title="Usuń ujęcie">✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row" style={{ marginTop: 12 }}>
          <button onClick={() => setBeats((bs) => [...bs, { start: bs.length ? bs[bs.length - 1].end : "0", end: "", text: "" }])}>+ dodaj ujęcie</button>
          <button className="primary" onClick={check}>Sprawdź plan</button>
        </div>
      </div>

      {err && <div className="alert err">{err}</div>}
      {saved && <div className="alert ok">{saved}</div>}

      {result && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ margin: 0 }}>Wynik · {result.shots.length} ujęć · {total} klatek łącznie</h3>
            <button className="primary" onClick={saveAll} disabled={!result.shots.some((s) => s.prompt.trim())}>Zapisz wszystkie prompty</button>
          </div>
          {result.warnings.length > 0 && (
            <div className="stack" style={{ marginBottom: 12 }}>
              {result.warnings.map((w, i) => <div key={i} className="alert warn">{w}</div>)}
            </div>
          )}
          <table>
            <thead><tr><th>#</th><th className="num">Czas</th><th className="num">Klatki H3</th><th>Prompt</th><th /></tr></thead>
            <tbody>
              {result.shots.map((s, i) => (
                <tr key={s.index}>
                  <td>{s.index}</td>
                  <td className="num">{s.start_s.toFixed(2)}–{s.end_s.toFixed(2)} s</td>
                  <td className="num"><span className="badge info">{s.frames} kl.</span></td>
                  <td className="mono" style={{ whiteSpace: "pre-wrap" }}>{s.prompt || <span className="hint">(pusty)</span>}</td>
                  <td><button onClick={() => saveOne(i)} disabled={!s.prompt.trim()}>Zapisz prompt</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
