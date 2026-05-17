import { useTranslation } from "react-i18next";
import LabelBadge from "../shared/LabelBadge";
import useAnalysisStore from "../../store/analysisStore";

function fmtTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function RecentCriticalEvents({ events }) {
  const { t } = useTranslation();
  const openModal = useAnalysisStore((s) => s.openModal);

  if (!events || events.length === 0) {
    return (
      <div className="card space-y-3">
        <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
          {t("analytics.recent_critical")}
        </h3>
        <p className="text-text-dim text-sm py-6 text-center">{t("analytics.no_critical")}</p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
        {t("analytics.recent_critical")}
      </h3>
      <div className="divide-y divide-bg-border">
        {events.map((ev, i) => (
          <button
            key={i}
            onClick={() => openModal({
              log: ev.log,
              label: ev.label,
              severity: ev.severity,
              status: ev.status,
              explanation: ev.explanation,
              recommendation: ev.recommendation,
            })}
            className="w-full text-left py-2.5 hover:bg-bg-elevated/60 transition-colors"
          >
            <div className="flex items-start gap-3 px-1">
              <LabelBadge label={ev.label} />
              <div className="flex-1 min-w-0">
                <p className="font-mono text-xs text-text-secondary truncate">{ev.log}</p>
                <p className="text-text-dim text-xs mt-0.5">{fmtTime(ev.created_at)}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
