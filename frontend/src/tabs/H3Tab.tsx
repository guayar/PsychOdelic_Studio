import { useEffect, useState } from "react";
import { api, type Command, type Project, type PrepareResult, type PromptFile } from "../api";
import { CommandView } from "./CommandView";

const MAX_REFS = 9;

export function H3Tab({ project }: { project: Project }) {
  const [prompts, setPrompts] = useState<PromptFile[]>([]);
  const [promptName, setPromptName] = useState("");
  const [promptText, setPromptText] = useState("");
  const [dirty, setDirty] = useState(false);
  const [prefix, setPrefix] = useState("OUG/v3b_1");
  const [seed, setSeed] = useState("1234");
  const [refs, setRefs] = useState<string[]>([]);
  const [refInput, setRefInput] = useState("");
  const [cont, setCont] = useState("");
  const [durs, setDurs] = useState("7.5");
  const [runmode, setRunmode] = useState("full_batch");
  const [validated, setValidated] = useState("0");
  const [fullres, setFullres] = useState(true);
  const [refine, setRefine] = useState(false);
  const [ctrl, setCtrl] = useState("");
  const [ctrlFrames, setCtrlFrames] = useState("");
  const [ctrlStrength, setCtrlStrength] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err" | "info"; text: string } | null>(null);
  const [prepared, setPrepared] = useState<PrepareResult | null>(null);

  async function reloadPrompts() {
    const list = await api.get<PromptFile[]>(`/api/projects/${project.id}/prompts`);
    setPrompts(list);
    setPromptName((cur) => cur || (list[0]?.name ?? ""));
  }
  useEffect(() => { setPrepared(null); setMsg(null); reloadPrompts().catch((e: Error) => setMsg({ kind: "err", text: e.message })); }, [project.id]);

  useEffect(() => {
    if (!promptName) { setPromptText(""); return; }
    api.get<{ content: string }>(`/api/projects/${project.id}/prompts/${promptName.replace(/\.txt$/, "")}`)
      .then((r) => { setPromptText(r.content); setDirty(false); })
      .catch(() => setPromptText(""));
  }, [promptName, project.id]);

  const stem = promptName.replace(/\.txt$/, "");
  const promptRel = stem ? `prompts/${stem}.txt` : "";

  async function savePrompt() {
    if (!stem) return;
    const r = await api.put<{ rel_path: string }>(`/api/projects/${project.id}/prompts/${stem}`, { content: promptText });
    setDirty(false);
    setMsg({ kind: "ok", text: `Zapisano ${r.rel_path}` });
  }

  function addRef() {
    const v = refInput.trim();
    if (!v) return;
    if (refs.length >= MAX_REFS) { setMsg({ kind: "err", text: `Limit H3: ${MAX_REFS} referencji obrazów.` }); return; }
    setRefs((r) => [...r, v]);
    setRefInput("");
  }

  async function prepare() {
    setBusy(true); setMsg(null); setPrepared(null);
    try {
      if (dirty) await savePrompt();
      const body = {
        prefix, seed: Number(seed), prompt_files: [promptRel], refs,
        cont: cont.trim() || null,
        durs: durs.split(",").map((x) => x.trim()).filter(Boolean).map(Number),
        runmode, validated: Number(validated), fullres, refine,
        ctrl: ctrl.trim() || null,
        ctrl_frames: ctrlFrames ? Number(ctrlFrames) : null,
        ctrl_strength: ctrlStrength ? Number(ctrlStrength) : null,
      };
      const res = await api.post<PrepareResult>(`/api/projects/${project.id}/h3/prepare`, body);
      setPrepared(res);
      setMsg({ kind: "ok", text: "Przygotowano. Komenda poniżej NIE została uruchomiona." });
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  const refsFull = refs.length >= MAX_REFS;
  return (
    <div className="stack">
      <div>
        <h2>H3 Extender</h2>
        <p className="lead">Przygotuj przedłużenie ujęcia. Aplikacja zbuduje dokładną komendę produkcyjnego skryptu
          <code> gen_extender_refine.py</code> i sprawdzi wejścia. <b>Nic nie jest renderowane</b>, dopóki nie włączysz
          renderu w ustawieniach (obecnie wyłączony).</p>
      </div>

      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}

      <div className="split">
        <div className="card">
          <h3>Prompt</h3>
          <div className="stack">
            <label>
              <span>Plik promptu w projekcie</span>
              <select value={promptName} onChange={(e) => setPromptName(e.target.value)}>
                {prompts.length === 0 && <option value="">(brak — utwórz w Planie ujęć)</option>}
                {prompts.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
              </select>
            </label>
            <label>
              <span>Treść (pozytywnie, jeden ruch kamery, bohater milczy)</span>
              <textarea value={promptText} rows={9}
                onChange={(e) => { setPromptText(e.target.value); setDirty(true); }} />
            </label>
            <div className="row end">
              <span className="hint">{dirty ? "niezapisane zmiany" : "zapisane"}</span>
              <button onClick={savePrompt} disabled={!stem || !dirty}>Zapisz prompt</button>
            </div>
          </div>
        </div>

        <div className="card">
          <h3>Ustawienia</h3>
          <div className="grid2">
            <label><span>Prefiks wyniku</span><input value={prefix} onChange={(e) => setPrefix(e.target.value)} /></label>
            <label><span>Seed</span><input value={seed} onChange={(e) => setSeed(e.target.value)} /></label>
            <label><span>Kontynuacja (CONT, plik w ComfyUI input)</span><input value={cont} placeholder="np. oug_v3a_2.mp4" onChange={(e) => setCont(e.target.value)} /></label>
            <label><span>Długości segmentów (s, po przecinku)</span><input value={durs} onChange={(e) => setDurs(e.target.value)} /><span className="hint">H3 wymaga siatki 17n+5 przy 24 fps.</span></label>
            <label><span>Tryb (RUNMODE)</span>
              <select value={runmode} onChange={(e) => setRunmode(e.target.value)}>
                <option value="full_batch">full_batch</option>
                <option value="clip_by_clip">clip_by_clip</option>
              </select>
            </label>
            <label><span>Zatwierdzone segmenty (VALIDATED)</span><input value={validated} onChange={(e) => setValidated(e.target.value)} /></label>
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <label className="row" style={{ gap: 6 }}><input type="checkbox" style={{ width: "auto" }} checked={fullres} onChange={(e) => setFullres(e.target.checked)} /><span>Pełna rozdzielczość 1344×768</span></label>
            <label className="row" style={{ gap: 6 }}><input type="checkbox" style={{ width: "auto" }} checked={refine} onChange={(e) => setRefine(e.target.checked)} /><span>Refine (dopracowanie)</span></label>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Referencje obrazów</h3>
          <span className={`counter ${refsFull ? "full" : ""}`}>{refs.length} / {MAX_REFS}</span>
        </div>
        <p className="hint" style={{ margin: "6px 0 12px" }}>Kolejność = numer <code>&lt;Picture N&gt;</code> w prompcie. Pliki muszą leżeć w ComfyUI input.</p>
        <div className="row">
          <input style={{ flex: 1, minWidth: 260 }} value={refInput} disabled={refsFull} placeholder={refsFull ? "Limit osiągnięty — usuń pozycję" : "np. oug_gsheet2.png"}
            onChange={(e) => setRefInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addRef()} />
          <button onClick={addRef} disabled={refsFull || !refInput.trim()}>Dodaj referencję</button>
        </div>
        <div>
          {refs.map((r, i) => (
            <div className="refitem" key={`${r}-${i}`}>
              <span><span className="idx">{i + 1}</span><code>{r}</code></span>
              <button className="ghost danger" onClick={() => setRefs((rs) => rs.filter((_, k) => k !== i))}>usuń</button>
            </div>
          ))}
        </div>
      </div>

      <details className="card">
        <summary style={{ cursor: "pointer", color: "var(--dim)" }}>Sterowanie (ControlNet) — opcjonalne</summary>
        <div className="grid3" style={{ marginTop: 12 }}>
          <label><span>Obraz sterujący (CTRL)</span><input value={ctrl} onChange={(e) => setCtrl(e.target.value)} placeholder="np. oug_hall_new.png" /></label>
          <label><span>Liczba klatek sterowania</span><input value={ctrlFrames} onChange={(e) => setCtrlFrames(e.target.value)} /></label>
          <label><span>Siła (0–10)</span><input value={ctrlStrength} onChange={(e) => setCtrlStrength(e.target.value)} /></label>
        </div>
      </details>

      <div className="row end">
        <button className="primary" onClick={prepare} disabled={busy || !promptRel}>
          {busy ? "Przygotowuję…" : "Przygotuj komendę (bez renderu)"}
        </button>
      </div>

      {prepared && (
        <div className="card">
          <h3>Gotowa komenda · zadanie {prepared.job.id.slice(0, 8)} · stan: {prepared.job.state}</h3>
          <CommandView command={prepared.command as Command} />
        </div>
      )}
    </div>
  );
}
