import { useEffect, useState } from "react";
import { api, type PrepareResult, type Project, type PromptFile } from "../api";
import { useI18n } from "../i18n";
import { CommandView } from "./CommandView";

export function LtxTab({ project }: { project: Project }) {
  const { t } = useI18n();
  const [prompts, setPrompts] = useState<PromptFile[]>([]);
  const [promptName, setPromptName] = useState("");
  const [tail, setTail] = useState("");
  const [tailFrames, setTailFrames] = useState("24");
  const [audio, setAudio] = useState("");
  const [audioFrames, setAudioFrames] = useState("");
  const [audioShift, setAudioShift] = useState("0");
  const [seed, setSeed] = useState("1");
  const [prefix, setPrefix] = useState("OUG/lip_1");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [prepared, setPrepared] = useState<{ command: PrepareResult["command"] } | null>(null);

  useEffect(() => {
    api.get<PromptFile[]>(`/api/projects/${project.id}/prompts`).then((list) => {
      setPrompts(list);
      setPromptName(list[0]?.name ?? "");
    }).catch(() => setPrompts([]));
    setPrepared(null);
  }, [project.id]);

  async function prepare() {
    setBusy(true); setMsg(null); setPrepared(null);
    try {
      const res = await api.post<PrepareResult>(`/api/projects/${project.id}/ltx/prepare`, {
        tail: tail.trim(), tail_frames: Number(tailFrames), audio: audio.trim(), audio_frames: Number(audioFrames),
        prompt_file: `prompts/${promptName.replace(/\.txt$/, "")}.txt`, seed: Number(seed), prefix,
        audio_shift: Number(audioShift),
      });
      setPrepared(res);
      setMsg({ kind: "ok", text: t("h3.prepared") });
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    } finally { setBusy(false); }
  }

  return (
    <div className="stack">
      <div>
        <h2>{t("ltx.title")}</h2>
        <p className="lead">{t("ltx.lead")}</p>
      </div>
      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}
      <div className="card">
        <div className="grid2">
          <label><span>{t("ltx.tail")}</span><input value={tail} onChange={(e) => setTail(e.target.value)} placeholder="oug_cu_rose_tight_tail.mp4" /></label>
          <label><span>{t("ltx.tailFrames")}</span><input value={tailFrames} onChange={(e) => setTailFrames(e.target.value)} /></label>
          <label><span>{t("ltx.audio")}</span><input value={audio} onChange={(e) => setAudio(e.target.value)} placeholder="oug_lip_rose1.wav" /></label>
          <label><span>{t("ltx.audioFrames")}</span><input value={audioFrames} onChange={(e) => setAudioFrames(e.target.value)} placeholder="141" /></label>
          <label><span>{t("ltx.prompt")}</span>
            <select value={promptName} onChange={(e) => setPromptName(e.target.value)}>
              {prompts.length === 0 && <option value="">{t("ltx.noPrompts")}</option>}
              {prompts.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
            </select>
          </label>
          <label><span>{t("ltx.audioShift")}</span><input value={audioShift} onChange={(e) => setAudioShift(e.target.value)} /></label>
          <label><span>{t("ltx.seed")}</span><input value={seed} onChange={(e) => setSeed(e.target.value)} /></label>
          <label><span>{t("ltx.prefix")}</span><input value={prefix} onChange={(e) => setPrefix(e.target.value)} /></label>
        </div>
        <div className="row end" style={{ marginTop: 14 }}>
          <button className="primary" onClick={prepare} disabled={busy || !promptName || !tail || !audio}>
            {busy ? t("h3.preparing") : t("h3.prepare")}
          </button>
        </div>
      </div>
      {prepared && <div className="card"><h3>{t("cmd.title")}</h3><CommandView command={prepared.command} /></div>}
    </div>
  );
}
