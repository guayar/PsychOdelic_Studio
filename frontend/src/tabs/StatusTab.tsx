import { useEffect, useState } from "react";
import { api, type Status } from "../api";
import { useI18n, type Key } from "../i18n";
import { fmtBytes } from "../format";

type Doctor = { items: { name: string; status: string; detail: string }[]; summary: Record<string, number> };
type ComfyItem = { kind: string; name: string; status: "FOUND" | "MISSING"; source: string; action: string };
type ComfyCheck = { profile: string; title: string; reachable: boolean; detail?: string; items: ComfyItem[];
  summary: { FOUND: number; MISSING: number; ready: boolean } | null };

const badgeClass = (s: string) => (s === "POTWIERDZONE_TESTEM" ? "ok" : s.startsWith("TECHNICZNIE") || s === "NIEZWERYFIKOWANE" ? "warn" : "err");
const statusKey = (s: string): Key =>
  s === "POTWIERDZONE_TESTEM" ? "status.potwierdzone" : s === "NIEZWERYFIKOWANE" || s.startsWith("TECHNICZNIE") ? "status.niezweryfikowane" : "status.niedostepne";

export function StatusTab({ status, onRefresh }: { status: Status | null; onRefresh: () => void }) {
  const { t } = useI18n();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [comfy, setComfy] = useState<ComfyCheck | null>(null);
  const [comfyBusy, setComfyBusy] = useState(false);

  useEffect(() => { api.get<Doctor>("/api/doctor").then(setDoctor).catch(() => setDoctor(null)); }, []);

  async function checkComfy() {
    setComfyBusy(true);
    try { setComfy(await api.get<ComfyCheck>("/api/comfy/check/h3_extender")); }
    catch { setComfy(null); }
    finally { setComfyBusy(false); }
  }

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h2>{t("status.title")}</h2>
          <p className="lead">{t("status.lead")}</p>
        </div>
        <button onClick={onRefresh}>{t("common.refresh")}</button>
      </div>

      {status && <div className="alert info">{t("status.render")}</div>}

      <div className="grid2">
        <div className="card">
          <h3>{t("status.gpu")}</h3>
          {!status && <div className="hint">{t("common.noData")}</div>}
          {status && <>
            <div className="row"><span className={`badge ${badgeClass(status.vram.status)}`}>{t(statusKey(status.vram.status))}</span></div>
            {status.vram.gpus?.map((g) => (
              <div key={g.gpu} className="mono" style={{ marginTop: 10 }}>{t("status.vramGpu", { n: g.gpu, used: fmtBytes(g.used_b), total: fmtBytes(g.total_b) })}</div>
            ))}
            {status.vram.detail && <div className="hint" style={{ marginTop: 8 }}>{status.vram.detail}</div>}
          </>}
        </div>
        <div className="card">
          <h3>{t("status.llm")}</h3>
          {!status && <div className="hint">{t("common.noData")}</div>}
          {status && <>
            <div className="row">
              <span className={`badge ${badgeClass(status.llm.status)}`}>{status.llm.runtime === "ollama" ? "Ollama" : (t("chip.llm.rule"))}</span>
              <span className="hint">{t(statusKey(status.llm.status))}</span>
            </div>
            {status.llm.models && <div className="mono" style={{ marginTop: 10 }}>{t("status.models", { list: status.llm.models.join(", ") || t("common.none") })}</div>}
            {status.llm.detail && <div className="hint" style={{ marginTop: 8 }}>{status.llm.detail}</div>}
            <p className="hint" style={{ marginTop: 10 }}>{t("status.note.llm")}</p>
          </>}
        </div>
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>{t("status.comfy")}</h3>
          <button onClick={checkComfy} disabled={comfyBusy}>{comfyBusy ? t("common.loading") : t("status.comfyCheck")}</button>
        </div>
        {!comfy && <p className="hint" style={{ marginTop: 10 }}>{t("status.comfyUnreachable")}</p>}
        {comfy && !comfy.reachable && <div className="alert warn" style={{ marginTop: 10 }}>{t("status.comfyUnreachable")}</div>}
        {comfy && comfy.reachable && comfy.summary && (
          <>
            <div className="row" style={{ marginTop: 10 }}>
              <span className={`badge ${comfy.summary.ready ? "ok" : "warn"}`}>{comfy.summary.ready ? t("status.ready") : t("status.missing")}</span>
              <span className="hint">{comfy.title} · {comfy.summary.FOUND} / {comfy.summary.FOUND + comfy.summary.MISSING}</span>
            </div>
            <table style={{ marginTop: 10 }}>
              <thead><tr><th>{t("status.colItem")}</th><th>{t("status.colStatus")}</th><th>{t("status.colSource")}</th><th>{t("status.colAction")}</th></tr></thead>
              <tbody>
                {comfy.items.map((it) => (
                  <tr key={it.kind + it.name}>
                    <td className="mono">{it.name}</td>
                    <td><span className={`badge ${it.status === "FOUND" ? "ok" : "err"}`}>{t(`badge.${it.status}`)}</span></td>
                    <td className="hint">{it.source}</td>
                    <td className="hint">{it.action || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      <div className="card">
        <h3>{t("status.doctor")}</h3>
        {!doctor && <div className="hint">{t("common.loading")}</div>}
        {doctor && (
          <table>
            <thead><tr><th>{t("status.colItem")}</th><th>{t("status.colStatus")}</th><th>{t("status.colDetail")}</th></tr></thead>
            <tbody>
              {doctor.items.map((it) => (
                <tr key={it.name}>
                  <td>{it.name}</td>
                  <td><span className={`badge ${badgeClass(it.status)}`}>{t(statusKey(it.status))}</span></td>
                  <td className="mono" style={{ color: "var(--dim)" }}>{it.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
