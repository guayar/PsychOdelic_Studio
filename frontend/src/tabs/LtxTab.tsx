import { useEffect, useState } from "react";
import { api, type Command, type PrepareResult, type Project, type PromptFile } from "../api";
import { CommandView } from "./CommandView";

export function LtxTab({ project }: { project: Project }) {
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
  const [prepared, setPrepared] = useState<{ command: Command } | null>(null);

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
      setMsg({ kind: "ok", text: "Przygotowano. Komenda poniżej NIE została uruchomiona." });
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    } finally { setBusy(false); }
  }

  return (
    <div className="stack">
      <div>
        <h2>LTX lipsync</h2>
        <p className="lead">Scena z mową: ogon poprzedniego klipu, wycinek audio z master WAV i prompt. Zgodnie z zasadą
          projektu audio pochodzi z oryginalnego pliku, a wynik trafia do zakładki Przegląd.</p>
      </div>
      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}
      <div className="card">
        <div className="grid2">
          <label><span>Ogon (plik w ComfyUI input)</span><input value={tail} onChange={(e) => setTail(e.target.value)} placeholder="oug_cu_rose_tight_tail.mp4" /></label>
          <label><span>Klatki ogona</span><input value={tailFrames} onChange={(e) => setTailFrames(e.target.value)} /></label>
          <label><span>Audio (plik wav w ComfyUI input)</span><input value={audio} onChange={(e) => setAudio(e.target.value)} placeholder="oug_lip_rose1.wav" /></label>
          <label><span>Klatki audio (24 kl./s)</span><input value={audioFrames} onChange={(e) => setAudioFrames(e.target.value)} placeholder="np. 141" /></label>
          <label><span>Prompt</span>
            <select value={promptName} onChange={(e) => setPromptName(e.target.value)}>
              {prompts.length === 0 && <option value="">(brak promptów)</option>}
              {prompts.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
            </select>
          </label>
          <label><span>Przesunięcie audio (klatki)</span><input value={audioShift} onChange={(e) => setAudioShift(e.target.value)} /></label>
          <label><span>Seed</span><input value={seed} onChange={(e) => setSeed(e.target.value)} /></label>
          <label><span>Prefiks wyniku</span><input value={prefix} onChange={(e) => setPrefix(e.target.value)} /></label>
        </div>
        <div className="row end" style={{ marginTop: 14 }}>
          <button className="primary" onClick={prepare} disabled={busy || !promptName || !tail || !audio}>
            {busy ? "Przygotowuję…" : "Przygotuj komendę (bez renderu)"}
          </button>
        </div>
      </div>
      {prepared && <div className="card"><h3>Gotowa komenda</h3><CommandView command={prepared.command} /></div>}
    </div>
  );
}
