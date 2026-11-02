import { useEffect, useState } from "react";
import { api, type Status } from "../api";
import { useI18n } from "../i18n";

type Target = "scene" | "ltx";

// Qwen jako AI Director: propozycja planu. Nic nie zapisuje, dopoki nie klikniesz "Wyslij".
export function DirectorPanel({ projectId }: { projectId: string }) {
  const { t } = useI18n();
  const [model, setModel] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [brief, setBrief] = useState("");
  const [out, setOut] = useState("");
  const [busy, setBusy] = useState(false);
  const [target, setTarget] = useState<Target>("scene");
  const [name, setName] = useState("shot_01");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    api.get<{ settings: { director_model: string } }>("/api/settings")
      .then((r) => setModel(r.settings.director_model)).catch(() => {});
    api.get<Status>("/api/system/status")
      .then((s) => setModels(s.llm.models ?? [])).catch(() => setModels([]));
  }, []);

  async function saveModel(v: string) {
    setModel(v);
    try { await api.put("/api/settings", { director_model: v }); setMsg(null); }
    catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function ask() {
    setBusy(true); setMsg(null);
    try {
      const r = await api.post<{ text: string }>("/api/director/llm-plan", { brief, project_id: projectId });
      setOut(r.text);
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
    finally { setBusy(false); }
  }

  function switchTarget(v: Target) {
    setTarget(v);
    setName(v === "scene" ? "shot_01" : "lip_01");
  }

  async function send() {
    const n = name.trim();
    if (!n || !out.trim()) return;
    try {
      const r = await api.put<{ rel_path: string }>(`/api/projects/${projectId}/prompts/${encodeURIComponent(n)}`, { content: out });
      setMsg({ kind: "ok", text: t("dir.sent", { path: r.rel_path }) });
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>{t("dir.title")}</h3>
        <label className="row" style={{ gap: 6 }}>
          <span className="hint">{t("dir.model")}</span>
          <select value={model} onChange={(e) => saveModel(e.target.value)} disabled={models.length === 0}>
            <option value="">{models.length === 0 ? t("dir.noModels") : t("dir.pick")}</option>
            {models.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
      </div>
      <p className="hint" style={{ margin: "6px 0 10px" }}>{t("dir.lead")}</p>

      <textarea rows={3} value={brief} placeholder={t("dir.briefPh")} onChange={(e) => setBrief(e.target.value)} />
      <div className="row" style={{ marginTop: 8 }}>
        <button className="primary" onClick={ask} disabled={busy || !brief.trim() || !model}>
          {busy ? t("dir.asking") : t("dir.ask")}
        </button>
      </div>

      {out && <>
        <textarea rows={8} value={out} onChange={(e) => setOut(e.target.value)} style={{ marginTop: 10 }} />
        <div className="row" style={{ marginTop: 8, flexWrap: "wrap" }}>
          <label className="row" style={{ gap: 6 }}>
            <span className="hint">{t("dir.target")}</span>
            <select value={target} onChange={(e) => switchTarget(e.target.value as Target)}>
              <option value="scene">{t("dir.toScene")}</option>
              <option value="ltx">{t("dir.toLtx")}</option>
            </select>
          </label>
          <label className="row" style={{ gap: 6 }}>
            <span className="hint">{t("dir.name")}</span>
            <input value={name} onChange={(e) => setName(e.target.value)} style={{ width: 180 }} />
          </label>
          <button onClick={send} disabled={!name.trim()}>{t("dir.send")}</button>
        </div>
      </>}

      {msg && <div className={`alert ${msg.kind}`} style={{ marginTop: 10 }}>{msg.text}</div>}
    </div>
  );
}
