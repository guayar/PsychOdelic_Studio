import { useEffect, useState } from "react";
import { api, type PlanResult, type Project } from "../api";
import { useI18n } from "../i18n";
import { DirectorPanel } from "./DirectorPanel";

type Beat = { start: string; end: string; text: string };
const parse = (s: string) => {
  const t = s.trim();
  if (!t) return NaN;
  return t.includes(":") ? t.split(":").reduce((acc, p) => acc * 60 + parseFloat(p), 0) : parseFloat(t.replace(",", "."));
};

export function PlanTab({ project }: { project: Project }) {
  const { t } = useI18n();
  // Szkic ujec zyje w przegladarce per projekt: nie znika przy przejsciu na inna zakladke.
  const draftKey = `psy.plan.${project.id}`;
  const [beats, setBeats] = useState<Beat[]>(() => {
    try {
      const raw = localStorage.getItem(draftKey);
      if (raw) { const parsed = JSON.parse(raw); if (Array.isArray(parsed) && parsed.length) return parsed; }
    } catch { /* brak dostepu do localStorage: zwykly stan w pamieci */ }
    return [{ start: "0", end: "5.17", text: "" }, { start: "5.17", end: "15.30", text: "" }];
  });
  useEffect(() => {
    try { localStorage.setItem(draftKey, JSON.stringify(beats)); } catch { /* ignoruj */ }
  }, [beats, draftKey]);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  const update = (i: number, patch: Partial<Beat>) => setBeats((bs) => bs.map((b, k) => (k === i ? { ...b, ...patch } : b)));

  async function check() {
    setErr(null); setSaved(null);
    const payload = beats.map((b) => ({ start_s: parse(b.start), end_s: parse(b.end), text: b.text }));
    if (payload.some((b) => Number.isNaN(b.start_s) || Number.isNaN(b.end_s))) { setErr(t("plan.badTime")); return; }
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
    try { setSaved(t("plan.savedOne", { path: await savePrompt(result.shots[index]) })); }
    catch (e) { setErr((e as Error).message); }
  }
  async function saveAll() {
    if (!result) return;
    const todo = result.shots.filter((s) => s.prompt.trim());
    try {
      for (const s of todo) await savePrompt(s);
      setSaved(t("plan.savedAll", { n: todo.length }));
    } catch (e) { setErr((e as Error).message); }
  }

  const total = result?.shots.reduce((s, x) => s + x.frames, 0) ?? 0;

  return (
    <div className="stack">
      <DirectorPanel projectId={project.id} />
      <div>
        <h2>{t("plan.title")}</h2>
        <p className="lead">{t("plan.lead")}</p>
      </div>

      <div className="card">
        <h3>{t("plan.shots")}</h3>
        <table>
          <thead><tr><th style={{ width: 40 }}>{t("plan.colNo")}</th><th style={{ width: 120 }}>{t("plan.colStart")}</th><th style={{ width: 120 }}>{t("plan.colEnd")}</th><th>{t("plan.colText")}</th><th style={{ width: 40 }} /></tr></thead>
          <tbody>
            {beats.map((b, i) => (
              <tr key={i}>
                <td className="num">{i + 1}</td>
                <td><input value={b.start} onChange={(e) => update(i, { start: e.target.value })} /></td>
                <td><input value={b.end} onChange={(e) => update(i, { end: e.target.value })} /></td>
                <td><textarea value={b.text} onChange={(e) => update(i, { text: e.target.value })} placeholder={t("plan.placeholder")} /></td>
                <td><button className="ghost danger" onClick={() => setBeats((bs) => bs.filter((_, k) => k !== i))} title={t("plan.removeShot")}>✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row" style={{ marginTop: 12 }}>
          <button onClick={() => setBeats((bs) => [...bs, { start: bs.length ? bs[bs.length - 1].end : "0", end: "", text: "" }])}>{t("plan.add")}</button>
          <button className="primary" onClick={check}>{t("plan.check")}</button>
        </div>
      </div>

      {err && <div className="alert err">{err}</div>}
      {saved && <div className="alert ok">{saved}</div>}

      {result && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ margin: 0 }}>{t("plan.result", { shots: result.shots.length, frames: total })}</h3>
            <button className="primary" onClick={saveAll} disabled={!result.shots.some((s) => s.prompt.trim())}>{t("plan.saveAll")}</button>
          </div>
          {result.warnings.length > 0 && (
            <div className="stack" style={{ marginBottom: 12 }}>
              {result.warnings.map((w, i) => <div key={i} className="alert warn">{w}</div>)}
            </div>
          )}
          <table>
            <thead><tr><th>{t("plan.colNo")}</th><th className="num">{t("plan.colTime")}</th><th className="num">{t("plan.colFrames")}</th><th>{t("plan.colPrompt")}</th><th /></tr></thead>
            <tbody>
              {result.shots.map((s, i) => (
                <tr key={s.index}>
                  <td>{s.index}</td>
                  <td className="num">{s.start_s.toFixed(2)}–{s.end_s.toFixed(2)} s</td>
                  <td className="num"><span className="badge info">{s.frames} kl.</span></td>
                  <td className="mono" style={{ whiteSpace: "pre-wrap" }}>{s.prompt || <span className="hint">{t("plan.emptyPrompt")}</span>}</td>
                  <td><button onClick={() => saveOne(i)} disabled={!s.prompt.trim()}>{t("plan.savePrompt")}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
