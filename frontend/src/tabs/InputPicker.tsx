import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useI18n } from "../i18n";

type Item = { name: string; kind: string; size: number };
type Listing = { exists: boolean; root: string; items: Item[] };

// Przegladarka ComfyUI/input (tylko odczyt): wybor pliku zamiast wpisywania nazwy.
export function InputPicker({ onPick, kinds, label }: { onPick: (name: string) => void; kinds?: string[]; label?: string }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [data, setData] = useState<Listing | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    api.get<Listing>(`/api/comfy/input?q=${encodeURIComponent(q)}`)
      .then((r) => { setData(r); setErr(null); })
      .catch((e) => setErr((e as Error).message));
  }, [open, q]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const items = useMemo(() => (data?.items ?? []).filter((i) => !kinds || kinds.includes(i.kind)), [data, kinds]);

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
            <input autoFocus value={q} placeholder={t("pick.search")} onChange={(e) => setQ(e.target.value)} style={{ width: "100%", margin: "10px 0" }} />
            {err && <div className="alert err">{err}</div>}
            {data && !data.exists && <div className="alert warn">{t("pick.missing", { path: data.root })}</div>}
            {data?.exists && items.length === 0 && <div className="hint">{t("pick.empty")}</div>}
            <div className="picker-grid">
              {items.map((it) => (
                <button key={it.name} type="button" className="picker-item" title={it.name}
                  onClick={() => { onPick(it.name); setOpen(false); }}>
                  {it.kind === "image"
                    ? <img loading="lazy" alt="" src={`/api/comfy/input/file?name=${encodeURIComponent(it.name)}`} />
                    : <div className="picker-kind">{it.kind}</div>}
                  <div className="picker-name">{it.name}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
