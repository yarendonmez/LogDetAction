import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";

const FILTERS = [
  { key: "all", i18nKey: "dashboard.filter_all", count: (r) => r.total_logs },
  { key: "malicious", i18nKey: "dashboard.filter_malicious", count: (r) => r.malicious_count },
  { key: "suspicious", i18nKey: "dashboard.filter_suspicious", count: (r) => r.suspicious_count },
  { key: "benign", i18nKey: "dashboard.filter_benign", count: (r) => r.benign_count },
];

const ACTIVE_STYLES = {
  all: "border-accent-cyan text-accent-cyan bg-accent-cyan/10",
  malicious: "border-accent-red text-accent-red bg-red-900/20",
  suspicious: "border-accent-amber text-accent-amber bg-amber-900/20",
  benign: "border-accent-green text-accent-green bg-green-900/20",
};

export default function FilterBar({ result }) {
  const { t } = useTranslation();
  const activeFilter = useAnalysisStore((s) => s.activeFilter);
  const setActiveFilter = useAnalysisStore((s) => s.setActiveFilter);

  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map(({ key, i18nKey, count }) => {
        const active = activeFilter === key;
        const n = result ? count(result) : 0;
        return (
          <button
            key={key}
            onClick={() => setActiveFilter(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs font-mono transition-all ${
              active
                ? ACTIVE_STYLES[key]
                : "border-bg-border text-text-secondary hover:border-accent-muted"
            }`}
          >
            {t(i18nKey)}
            <span className={`text-xs px-1 rounded ${active ? "bg-white/10" : "bg-bg-elevated text-text-dim"}`}>
              {n}
            </span>
          </button>
        );
      })}
    </div>
  );
}
