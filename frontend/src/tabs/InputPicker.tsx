import { useEffect, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

type Entry = { name: string; kind: string; path: string; size: number };
type Listing = { path: string; parent: string | null; entries: Entry[] };

// Przegladarka plikow z dowolnego katalogu. Wybrany plik spoza ComfyUI/input jest kopiowany do ComfyUI/input.
export function InputPicker({ onPick, kinds, label }: { onPick: (name: string) => void; kinds?: string[]; label?: string }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [dir, setDir] = useState<string>("");
  const [q, setQ] = useState("");
  const [data, setData] = useState<Listing | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    api.get<Listing>(`/api/fs/list?path=${encodeURIComponent(dir)}`)
      .then((r) => { setData(r); setErr(null); })
      .catch((e) => { setErr((e as Error).message); setData(null); });
  }, [open, dir]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  async function choose(e: Entry) {
    setBusy(true);
    try {
      const r = await api.post<{ name: string }>("/api/fs/import", { path: e.path });
      onPick(r.name);
      setOpen(false);
    } catch (ex) { setErr((ex as Error).message); }
    finally { setBusy(false); }
  }

  const needle = q.trim().toLowerCase();
  const visible = (data?.entries ?? []).filter((e) =>
    e.kind === "dir" || ((!kinds || kinds.includes(e.kind)) && (!needle || e.name.toLowerCase().includes(needle))));

  return (
    <>
      <button type="button" className="ghost" onClick={() => setOpen(true)}>{label ?? t("pick.open")}</button>
      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal picker" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h3 style={{ margin: 0 }}>{t("pick.title")}</h3>
              <button className="ghost" onClick={() => setOpen(false)}>✕</button>
            </div>
            <div className="row" style={{ margin: "8px 0", gap: 6 }}>
              <button className="ghost" disabled={!data?.parent} onClick={() => data?.parent && setDir(data.parent)}>{t("pick.up")}</button>
              <code className="mono" style={{ fontSize: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{data?.path ?? dir}</code>
            </div>
            <input autoFocus value={q} placeholder={t("pick.search")} onChange={(e) => setQ(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
            <div className="hint" style={{ marginBottom: 8 }}>{t("pick.hint")}</div>
            {err && <div className="alert err">{err}</div>}
            {busy && <div className="hint">{t("pick.importing")}</div>}
            <div className="picker-grid">
              {visible.map((e) => (
                e.kind === "dir"
                  ? <button key={e.path} type="button" className="picker-item" onClick={() => setDir(e.path)} title={e.name}>
                      <div className="picker-kind">📁</div><div className="picker-name">{e.name}</div>
                    </button>
                  : <button key={e.path} type="button" className="picker-item" disabled={busy} title={e.name} onClick={() => choose(e)}>
                      {e.kind === "image"
                        ? <img loading="lazy" alt="" src={`/api/fs/file?path=${encodeURIComponent(e.path)}`} />
                        : <div className="picker-kind">{e.kind}</div>}
                      <div className="picker-name">{e.name}</div>
                    </button>
              ))}
              {data && visible.length === 0 && <div className="hint">{t("pick.empty")}</div>}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
