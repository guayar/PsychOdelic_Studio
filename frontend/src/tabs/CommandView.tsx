import { useState } from "react";
import type { Command } from "../api";
import { useI18n } from "../i18n";

function shellQuote(s: string) {
  return /^[A-Za-z0-9_@%+=:,./\-]+$/.test(s) ? s : `'${s.replace(/'/g, "'\\''")}'`;
}

export function CommandView({ command }: { command: Command }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const envPrefix = Object.entries(command.env).map(([k, v]) => `${k}=${shellQuote(v)}`).join(" ");
  const line = `cd ${shellQuote(command.cwd)} && ${envPrefix ? envPrefix + " " : ""}${command.argv.map(shellQuote).join(" ")}`;

  return (
    <div className="stack">
      {command.warnings.map((w, i) => <div key={i} className="alert warn">{w}</div>)}
      {command.errors.map((w, i) => <div key={i} className="alert err">{w}</div>)}
      <div className="row end">
        <button onClick={() => { navigator.clipboard?.writeText(line); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
          {copied ? t("cmd.copied") : t("cmd.copy")}
        </button>
      </div>
      <pre className="cmd">{line}</pre>
      <div className="grid2">
        <div>
          <div className="hint" style={{ marginBottom: 6 }}>{t("cmd.env")}</div>
          <table>
            <tbody>
              {Object.entries(command.env).length === 0 && <tr><td className="hint">{t("cmd.none")}</td></tr>}
              {Object.entries(command.env).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td className="mono">{v}</td></tr>)}
            </tbody>
          </table>
        </div>
        <div>
          <div className="hint" style={{ marginBottom: 6 }}>{t("cmd.expected")}</div>
          <div className="mono">{command.expected_output ?? "—"}</div>
          <div className="hint" style={{ marginTop: 10 }}>{t("cmd.script")}: <code>{command.script}</code></div>
        </div>
      </div>
    </div>
  );
}
