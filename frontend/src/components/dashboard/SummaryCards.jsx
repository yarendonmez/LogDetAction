import { useTranslation } from "react-i18next";

function Card({ label, value, sub, colorClass }) {
  return (
    <div className={`bg-bg-surface border rounded-lg p-4 ${colorClass}`}>
      <p className="text-xs font-mono text-text-secondary mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono text-text-primary">{value}</p>
      {sub && <p className="text-xs text-text-dim mt-0.5">{sub}</p>}
    </div>
  );
}

export default function SummaryCards({ result }) {
  const { t } = useTranslation();
  if (!result) return null;

  const {
    total_logs,
    malicious_count,
    suspicious_count,
    benign_count,
    avg_total_time_sec,
  } = result;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <Card
        label={t("dashboard.total")}
        value={total_logs}
        colorClass="border-bg-border"
      />
      <Card
        label={t("dashboard.malicious")}
        value={malicious_count}
        colorClass="border-red-800/40 bg-red-900/10"
      />
      <Card
        label={t("dashboard.suspicious")}
        value={suspicious_count}
        colorClass="border-amber-800/30 bg-amber-900/10"
      />
      <Card
        label={t("dashboard.benign")}
        value={benign_count}
        colorClass="border-green-800/30 bg-green-900/10"
      />
      <Card
        label={t("dashboard.avg_latency")}
        value={`${avg_total_time_sec}s`}
        colorClass="border-bg-border"
      />
    </div>
  );
}
