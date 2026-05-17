import { useTranslation } from "react-i18next";

function LatencyBar({ label, value, max, color }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-text-secondary">{label}</span>
        <span className="font-mono text-text-primary">{value}s</span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-elevated overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function LatencyOverview({ data }) {
  const { t } = useTranslation();
  if (!data) return null;

  const cls  = data.avg_classification_time_sec    || 0;
  const gen  = data.avg_analysis_generation_time_sec || 0;
  const tot  = data.avg_total_time_sec              || 0;
  const max  = Math.max(cls, gen, tot, 0.001);

  return (
    <div className="card space-y-4">
      <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
        {t("analytics.latency_overview")}
      </h3>
      <div className="space-y-3">
        <LatencyBar label={t("analytics.latency_class")}    value={cls}  max={max} color="#38bdf8" />
        <LatencyBar label={t("analytics.latency_analysis")} value={gen}  max={max} color="#818cf8" />
        <LatencyBar label={t("analytics.latency_total")}    value={tot}  max={max} color="#64748b" />
      </div>
    </div>
  );
}
