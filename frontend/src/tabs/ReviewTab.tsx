import { useEffect, useRef, useState } from "react";
import { api, type Project, type Variant } from "../api";
import { useI18n } from "../i18n";
import { kindKey } from "../format";
import { InputPicker } from "./InputPicker";

const KINDS = ["new_only", "cumulative", "raw", "preview", "audio_slice", "other"] as const;

// Podglad wyniku: obraz, wideo albo audio. Sterowanie: stop, -5 s, odtwarzaj/pauza, +5 s (kontrolki natywne zostaja).
function MediaPreview({ projectId, path, autoPlay }: { projectId: string; path: string; autoPlay?: boolean }) {
  const { t } = useI18n();
  const el = useRef<HTMLMediaElement>(null);
  if (!path) return null;
  const src = `/api/projects/${projectId}/media?path=${encodeURIComponent(path)}`;
  const ext = (path.trim().replace(/\.+$/, "").toLowerCase().split(".").pop() ?? "");
  const isImage = ["png", "jpg", "jpeg", "webp"].includes(ext);
  const isVideo = ["mp4", "mov", "webm"].includes(ext);
  const isAudio = ["wav", "mp3", "flac"].includes(ext);
  if (isImage) return <img src={src} alt="" style={{ width: "100%", borderRadius: 8, marginTop: 8 }} />;
  if (!isVideo && !isAudio) return null;
  const m = () => el.current;
  const stop = () => { const x = m(); if (x) { x.pause(); x.currentTime = 0; } };
  const jump = (d: number) => { const x = m(); if (x) x.currentTime = Math.max(0, Math.min(x.duration || 0, x.currentTime + d)); };
  const toggle = () => { const x = m(); if (x) { if (x.paused) x.play().catch(() => {}); else x.pause(); } };
  const mediaProps = { ref: el as React.RefObject<HTMLVideoElement>, src, controls: true, autoPlay, preload: "metadata" as const };
  return (
    <div>
      {isVideo
        ? <video {...mediaProps} playsInline style={{ width: "100%", maxHeight: 360, background: "#000", borderRadius: 8, marginTop: 8 }} />
        : <audio {...mediaProps} style={{ width: "100%", marginTop: 8 }} />}
      <div className="row" style={{ marginTop: 8, gap: 6 }}>
        <button className="ghost" onClick={stop} title={t("player.stop")}>⏹ {t("player.stop")}</button>
        <button className="ghost" onClick={() => jump(-1)} title={t("player.back5")}>⏪ −1 s</button>
        <button className="primary" onClick={toggle} title={t("player.toggle")}>⏯</button>
        <button className="ghost" onClick={() => jump(1)} title={t("player.fwd5")}>⏩ +1 s</button>
        {isVideo && <>
          <button className="ghost" onClick={() => jump(-1 / 24)} title="-1 klatka (1/24 s)">◀ −1 kl.</button>
          <button className="ghost" onClick={() => jump(1 / 24)} title="+1 klatka (1/24 s)">+1 kl. ▶</button>
        </>}
      </div>
    </div>
  );
}

export function ReviewTab({ project }: { project: Project }) {
  const { t } = useI18n();
  const [variants, setVariants] = useState<Variant[]>([]);
  const [path, setPath] = useState("");
  const [kind, setKind] = useState<(typeof KINDS)[number]>("new_only");
  const [frames, setFrames] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const load = () => api.get<Variant[]>(`/api/projects/${project.id}/variants`).then(setVariants).catch(() => setVariants([]));
  useEffect(() => { load(); setMsg(null); }, [project.id]);

  async function register() {
    try {
      await api.post(`/api/projects/${project.id}/variants`, { kind, rel_path: path.trim(), frames: frames ? Number(frames) : null, fps: 24 });
      setPath(""); setFrames("");
      setMsg({ kind: "ok", text: t("review.registered") });
      load();
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function removeVariant(id: string) {
    if (!window.confirm(t("review.removeConfirm"))) return;
    try { await api.del(`/api/variants/${id}`); load(); }
    catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function clearRejected() {
    if (!window.confirm(t("review.clearConfirm"))) return;
    try { await api.post(`/api/projects/${project.id}/variants/clear-rejected`); load(); }
    catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  async function review(v: Variant, decision: "accepted" | "rejected") {
    try {
      await api.post(`/api/variants/${v.id}/review`, { decision, note: notes[v.id] ?? "" });
      setMsg({ kind: "ok", text: decision === "accepted" ? t("review.acceptedMsg") : t("review.rejectedMsg") });
      load();
    } catch (e) { setMsg({ kind: "err", text: (e as Error).message }); }
  }

  const [playing, setPlaying] = useState<string | null>(null);
  const pending = variants.filter((v) => v.review_status === "pending");
  const done = variants.filter((v) => v.review_status !== "pending");

  return (
    <div className="stack">
      <div>
        <h2>{t("review.title")}</h2>
        <p className="lead">{t("review.lead")}</p>
      </div>

      {msg && <div className={`alert ${msg.kind}`}>{msg.text}</div>}

      <div className="card">
        <h3>{t("review.add")}</h3>
        <div className="grid3">
          <label><span>{t("review.path")}</span><input value={path} placeholder="renders/shot_01_final.mp4" onChange={(e) => setPath(e.target.value)} /></label><InputPicker kinds={["video", "image"]} projectId={project.id} label={t("pick.openAny")} onPick={setPath} />
          <label><span>{t("review.kind")}</span>
            <select value={kind} onChange={(e) => setKind(e.target.value as (typeof KINDS)[number])}>
              {KINDS.map((k) => <option key={k} value={k}>{t(kindKey(k) as "kind.raw")}</option>)}
            </select>
          </label>
          <label><span>{t("review.frames")}</span><input value={frames} onChange={(e) => setFrames(e.target.value)} /></label>
        </div>
        <div className="row end" style={{ marginTop: 12 }}>
          <button onClick={register} disabled={!path.trim()}>{t("review.register")}</button>
        </div>
      </div>

      <div>
        {playing && (
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="mono" style={{ color: "var(--dim)", fontSize: 12 }}>{playing}</span>
              <button className="ghost" onClick={() => setPlaying(null)}>{t("review.playerClose")}</button>
            </div>
            <MediaPreview projectId={project.id} path={playing} autoPlay />
          </div>
        )}
        <h3 style={{ marginBottom: 10 }}>{t("review.pending", { n: pending.length })}</h3>
        {pending.length === 0 && <div className="empty">{t("review.none")}</div>}
        {pending.map((v) => (
          <div className="review-card" key={v.id}>
            <div>
              <div className="row"><span className="badge pending">{v.kind ? t(kindKey(v.kind) as "kind.raw") : "—"}</span>
                <span className="mono" style={{ color: "var(--dim)" }}>{v.frames ?? "?"} kl. · {v.fps ?? "?"} fps</span></div>
              <div className="path" style={{ marginTop: 6 }}>{v.abs_path}</div>
              <div className="row" style={{ marginTop: 8 }}><button className="ghost" onClick={() => setPlaying(v.abs_path ?? null)}>▶ {t("review.play")}</button></div>
              <input style={{ marginTop: 8 }} placeholder={t("review.note")} value={notes[v.id] ?? ""}
                onChange={(e) => setNotes((n) => ({ ...n, [v.id]: e.target.value }))} />
            </div>
            <div className="stack">
              <button className="primary" onClick={() => review(v, "accepted")}>{t("review.accept")}</button>
              <button onClick={() => review(v, "rejected")}>{t("review.reject")}</button>
            </div>
          </div>
        ))}
      </div>

      {done.length > 0 && (
        <div>
          <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
            <h3 style={{ margin: 0 }}>{t("review.done", { n: done.length })}</h3>
            {done.some((v) => v.review_status === "rejected") && (
              <button className="ghost danger" onClick={clearRejected}>{t("review.clearRejected")}</button>
            )}
          </div>
          {done.map((v) => (
            <div className="review-card" key={v.id} style={{ opacity: v.review_status === "rejected" ? 0.7 : 1 }}>
              {v.review_status === "rejected" && <div className="row" style={{ justifyContent: "flex-end" }}><button className="ghost danger" onClick={() => removeVariant(v.id)}>✕ {t("review.remove")}</button></div>}
              <div>
                <div className="row">
                  <span className={`badge ${v.review_status}`}>{v.review_status === "accepted" ? t("review.statusAccepted") : t("review.statusRejected")}</span>
                  <span className="mono" style={{ color: "var(--dim)" }}>{v.kind ? t(kindKey(v.kind) as "kind.raw") : "—"}</span>
                </div>
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
