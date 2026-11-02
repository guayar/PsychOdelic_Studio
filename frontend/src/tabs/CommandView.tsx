import { useState } from "react";
import type { Command } from "../api";

function shellQuote(s: string) {
  return /^[A-Za-z0-9_@%+=:,./\-]+$/.test(s) ? s : `'${s.replace(/'/g, "'\\''")}'`;
}

export function CommandView({ command }: { command: Command }) {
  const [copied, setCopied] = useState(false);
  const envPrefix = Object.entries(command.env).map(([k, v]) => `${k}=${shellQuote(v)}`).join(" ");
  const line = `cd ${shellQuote(command.cwd)} && ${envPrefix ? envPrefix + " " : ""}${command.argv.map(shellQuote).join(" ")}`;

  return (
    <div className="stack">
      {command.warnings.map((w, i) => <div key={i} className="alert warn">{w}</div>)}
      {command.errors.map((w, i) => <div key={i} className="alert err">{w}</div>)}
      <div className="row end">
        <button onClick={() => { navigator.clipboard?.writeText(line); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
          {copied ? "Skopiowano" : "Kopiuj polecenie"}
        </button>
      </div>
      <pre className="cmd">{line}</pre>
      <div className="grid2">
        <div>
          <div className="hint" style={{ marginBottom: 6 }}>Zmienne środowiskowe</div>
          <table>
            <tbody>
              {Object.entries(command.env).length === 0 && <tr><td className="hint">brak</td></tr>}
              {Object.entries(command.env).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td className="mono">{v}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div>
          <div className="hint" style={{ marginBottom: 6 }}>Oczekiwany wynik</div>
          <div className="mono">{command.expected_output ?? "—"}</div>
          <div className="hint" style={{ marginTop: 10 }}>Skrypt: <code>{command.script}</code></div>
        </div>
      </div>
    </div>
  );
}
