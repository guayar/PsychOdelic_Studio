import { useEffect, useState } from "react";
import { api, type Status } from "../api";
import { fmtBytes } from "../format";

type Doctor = { items: { name: string; status: string; detail: string }[]; summary: Record<string, number> };

const badge = (s: string) => (s === "POTWIERDZONE_TESTEM" ? "ok" : s.startsWith("TECHNICZNIE") || s === "NIEZWERYFIKOWANE" ? "warn" : "err");
const label = (s: string) => ({ POTWIERDZONE_TESTEM: "potwierdzone", TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE: "niezweryfikowane",
  NIEDOSTEPNE_LUB_WYMAGA_ZMIANY: "niedostępne", NIEZWERYFIKOWANE: "niezweryfikowane" } as Record<string, string>)[s] ?? s;

export function StatusTab({ status, onRefresh }: { status: Status | null; onRefresh: () => void }) {
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  useEffect(() => { api.get<Doctor>("/api/doctor").then(setDoctor).catch(() => setDoctor(null)); }, []);

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h2>Stan systemu</h2>
          <p className="lead">Tylko odczyt: co aplikacja wie o tym komputerze. Niepotwierdzone wartości są oznaczone, a nie
            udawane.</p>
        </div>
        <button onClick={onRefresh}>Odśwież</button>
      </div>

      {status && (
        <div className="alert info">{status.note}</div>
      )}

      <div className="grid2">
        <div className="card">
          <h3>Karta graficzna (VRAM)</h3>
          {!status && <div className="hint">Brak danych.</div>}
          {status && <>
            <div className="row"><span className={`badge ${badge(status.vram.status)}`}>{label(status.vram.status)}</span></div>
            {status.vram.gpus?.map((g) => (
              <div key={g.gpu} className="mono" style={{ marginTop: 10 }}>
                GPU {g.gpu}: {fmtBytes(g.used_b)} / {fmtBytes(g.total_b)} w użyciu
              </div>
            ))}
            {status.vram.detail && <div className="hint" style={{ marginTop: 8 }}>{status.vram.detail}</div>}
          </>}
        </div>
        <div className="card">
          <h3>Model lokalny (Director)</h3>
          {!status && <div className="hint">Brak danych.</div>}
          {status && <>
            <div className="row"><span className={`badge ${badge(status.llm.status)}`}>{status.llm.runtime === "ollama" ? "Ollama" : "tryb regułowy"}</span>
              <span className="hint">{label(status.llm.status)}</span></div>
            {status.llm.models && <div className="mono" style={{ marginTop: 10 }}>modele: {status.llm.models.join(", ") || "brak"}</div>}
            {status.llm.detail && <div className="hint" style={{ marginTop: 8 }}>{status.llm.detail}</div>}
            <p className="hint" style={{ marginTop: 10 }}>Aplikacja nie ładuje ani nie zwalnia modelu. To wymaga osobnego testu na GPU.</p>
          </>}
        </div>
      </div>

      <div className="card">
        <h3>Diagnostyka środowiska (doctor)</h3>
        {!doctor && <div className="hint">Ładowanie…</div>}
        {doctor && (
          <table>
            <thead><tr><th>Element</th><th>Status</th><th>Szczegóły</th></tr></thead>
            <tbody>
              {doctor.items.map((it) => (
                <tr key={it.name}>
                  <td>{it.name}</td>
                  <td><span className={`badge ${badge(it.status)}`}>{label(it.status)}</span></td>
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
