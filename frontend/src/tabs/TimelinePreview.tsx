import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

export type PreviewClip = { clip_id: string; source_path: string; inF: number; outF: number; start: number };

const FPS = 24;
const tc = (frames: number) => {
  const safe = Math.max(0, Math.floor(frames));
  const s = Math.floor(safe / FPS), f = safe % FPS;
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60, f].map((n) => String(n).padStart(2, "0")).join(":");
};

// Podglad osi: odtwarza klipy wideo w kolejnosci osi. Audio master WAV nie jest jeszcze odtwarzane.
export function TimelinePreview({ projectId, clips, total }: { projectId: string; clips: PreviewClip[]; total: number }) {
  const { t } = useI18n();
  const videoRef = useRef<HTMLVideoElement>(null);
  const wantRef = useRef(0);
  const keyRef = useRef("");
  const posRef = useRef(0);
  const [pos, setPos] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [check, setCheck] = useState<{ src: string; ok: boolean } | null>(null);

  const sorted = useMemo(() => [...clips].sort((a, b) => a.start - b.start), [clips]);
  const clipAt = (f: number) => sorted.find((c) => f >= c.start && f < c.start + (c.outF - c.inF)) ?? null;
  const current = clipAt(pos);
  const key = current ? `${current.clip_id}:${current.start}:${current.source_path}` : "";
  const src = current ? `/api/projects/${projectId}/media?path=${encodeURIComponent(current.source_path)}` : "";

  function seek(f: number) { posRef.current = f; setPos(f); }

  // Plik sprawdzany przed odtwarzaniem: brak pliku to komunikat w podgladzie, a nie blad w konsoli.
  useEffect(() => {
    if (!src) return;
    let cancelled = false;
    const q = `/api/projects/${projectId}/media/check?path=${encodeURIComponent(current ? current.source_path : "")}`;
    api.get<{ exists: boolean }>(q)
      .then((r) => { if (!cancelled) setCheck({ src, ok: r.exists }); })
      .catch(() => { if (!cancelled) setCheck({ src, ok: false }); });
    return () => { cancelled = true; };
  }, [src, projectId]);
  const ready = !!current && !!check && check.src === src && check.ok;
  const missing = !!current && !!check && check.src === src && !check.ok;

  // Zegar osi: podczas odtwarzania przesuwa pozycje w klatkach (24 fps).
  useEffect(() => {
    if (!playing) return;
    let last = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      const np = posRef.current + dt * FPS;
      if (np >= total) { seek(total); setPlaying(false); return; }
      seek(np);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, total]);

  // Sterowanie wideo: zmiana klipu ustawia nowe zrodlo, dryf jest korygowany.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (!ready || !current) { v.pause(); keyRef.current = ""; return; }
    const want = (current.inF + (pos - current.start)) / FPS;
    wantRef.current = want;
    if (keyRef.current !== key) {
      keyRef.current = key;
      v.src = src;
    } else if (Math.abs(v.currentTime - want) > 0.25 && v.readyState >= 1) {
      v.currentTime = want;
    }
    if (playing) v.play().catch(() => setPlaying(false));
    else v.pause();
  }, [pos, playing, key, src, ready]);

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>{t("tl.preview")}</h3>
        <span className="hint">{tc(pos)} / {tc(total)}</span>
      </div>
      <div className="video-screen">
        {ready
          ? <video ref={videoRef} preload="auto" playsInline onLoadedMetadata={() => { if (videoRef.current) videoRef.current.currentTime = wantRef.current; }} />
          : missing
            ? <div className="hint" style={{ padding: 40, textAlign: "center" }}>{t("tl.fileMissing", { path: current?.source_path ?? "" })}</div>
            : <div className="hint" style={{ padding: 40 }}>{current ? t("common.loading") : t("tl.noClipHere")}</div>}
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <button onClick={() => { setPlaying(false); seek(0); }}>{t("tl.rewind")}</button>
        <button className="primary" onClick={() => setPlaying((p) => !p)} disabled={total === 0}>
          {playing ? t("tl.pause") : t("tl.play")}
        </button>
        <input type="range" min={0} max={Math.max(total, 1)} step={1} value={Math.floor(pos)} style={{ flex: 1, minWidth: 200 }}
          onChange={(e) => { setPlaying(false); seek(Number(e.target.value)); }} />
      </div>
      <p className="hint" style={{ marginTop: 8 }}>{t("tl.previewNote")}</p>
    </div>
  );
}
