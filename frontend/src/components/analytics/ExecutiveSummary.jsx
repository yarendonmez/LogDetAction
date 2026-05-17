import { useTranslation } from "react-i18next";

function StatCard({ label, value, accent }) {
  const accentClasses = {
    cyan: "text-accent-cyan",
    red: "text-accent-red",
    amber: "text-accent-amber",
    green: "text-accent-green",
    muted: "text-text-secondary",
  };
  return (
    <div className="card flex flex-col gap-1 min-w-0">
      <span className="text-text-dim text-xs uppercase tracking-wider font-medium">{label}</span>
      <span className={`text-2xl font-bold font-mono ${accentClasses[accent] || "text-text-primary"}`}>
        {value ?? "—"}
      </span>
    </div>
  );
}

export default function ExecutiveSummary({ data }) {
  const { t } = useTranslation();
  if (!data) return null;
  const { total_analyses, total_logs, label_counts, avg_total_time_sec } = data;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <StatCard label={t("analytics.total_analyses")} value={total_analyses} accent="cyan" />
      <StatCard label={t("analytics.total_logs")} value={total_logs} accent="muted" />
      <StatCard label={t("analytics.malicious")} value={label_counts?.malicious} accent="red" />
      <StatCard label={t("analytics.suspicious")} value={label_counts?.suspicious} accent="amber" />
      <StatCard label={t("analytics.benign")} value={label_counts?.benign} accent="green" />
      <StatCard
        label={t("analytics.avg_latency")}
        value={avg_total_time_sec != null ? `${avg_total_time_sec}s` : "—"}
        accent="muted"
      />
    </div>
  );
}
