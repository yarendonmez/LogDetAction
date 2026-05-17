import { useTranslation } from "react-i18next";

function StatusDot({ running }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full mr-1.5 ${
        running ? "bg-accent-green animate-pulse" : "bg-text-dim"
      }`}
    />
  );
}

function MiniCard({ label, value, accent }) {
  const cls = {
    red: "text-accent-red",
    amber: "text-accent-amber",
    green: "text-accent-green",
    cyan: "text-accent-cyan",
    muted: "text-text-secondary",
  };
  return (
    <div className="bg-bg-elevated rounded p-3 flex flex-col gap-1">
      <span className="text-text-dim text-xs uppercase tracking-wider">{label}</span>
      <span className={`text-lg font-mono font-bold ${cls[accent] || "text-text-primary"}`}>
        {value ?? "—"}
      </span>
    </div>
  );
}

export default function LiveStatusCard({ status, events }) {
  const { t } = useTranslation();
  if (!status) return null;

  const running = status.running;
  const malCount = events.filter((e) => e.label === "malicious").length;
  const susCount  = events.filter((e) => e.label === "suspicious").length;
  const benCount  = events.filter((e) => e.label === "benign").length;
  const avgTime =
    events.length > 0
      ? (events.reduce((s, e) => s + (e.total_time_sec || 0), 0) / events.length).toFixed(2)
      : null;

  return (
    <div className="card space-y-4">
      {/* Status row */}
      <div className="flex items-center gap-2">
        <StatusDot running={running} />
        <span className={`text-sm font-medium ${running ? "text-accent-green" : "text-text-secondary"}`}>
          {running ? t("live.status_running") : t("live.status_stopped")}
        </span>
        <span className="text-text-dim text-xs ml-auto font-mono truncate max-w-xs" title={status.live_log_path}>
          {status.live_log_path}
        </span>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        <MiniCard label={t("live.processed_lines")} value={status.processed_lines} accent="muted" />
        <MiniCard label={t("live.malicious")}        value={malCount}               accent="red"   />
        <MiniCard label={t("live.suspicious")}       value={susCount}               accent="amber" />
        <MiniCard label={t("live.benign")}            value={benCount}               accent="green" />
        <MiniCard
          label={t("live.avg_latency")}
          value={avgTime != null ? `${avgTime}s` : "—"}
          accent="cyan"
        />
        <MiniCard
          label={t("live.last_event")}
          value={status.last_event_at ? new Date(status.last_event_at).toLocaleTimeString() : "—"}
          accent="muted"
        />
      </div>

      {status.last_error && (
        <p className="text-accent-red text-xs font-mono mt-1">
          {t("live.status_error")}: {status.last_error}
        </p>
      )}
    </div>
  );
}
