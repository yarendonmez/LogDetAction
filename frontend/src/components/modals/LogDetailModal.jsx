import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";
import LabelBadge from "../shared/LabelBadge";
import StatusBadge from "../shared/StatusBadge";
import AnalystActionPanel from "../shared/AnalystActionPanel";

function TimingRow({ label, value }) {
  return (
    <div className="flex justify-between text-xs py-1 border-b border-bg-border last:border-0">
      <span className="text-text-secondary">{label}</span>
      <span className="font-mono text-accent-cyan">{value}s</span>
    </div>
  );
}

export default function LogDetailModal() {
  const { t } = useTranslation();
  const modalLog = useAnalysisStore((s) => s.modalLog);
  const closeModal = useAnalysisStore((s) => s.closeModal);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") closeModal();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [closeModal]);

  if (!modalLog) return null;

  const row = modalLog;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-bg-base/80 backdrop-blur-sm p-4"
      onClick={closeModal}
    >
      <div
        className="bg-bg-surface border border-bg-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-bg-border">
          <h3 className="text-text-primary font-semibold">{t("modal.title")}</h3>
          <button
            onClick={closeModal}
            className="text-text-dim hover:text-text-primary transition-colors"
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-5">
          {/* Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <LabelBadge label={row.label} />
            <StatusBadge status={row.status} />
            <span className="text-xs text-text-dim font-mono capitalize border border-bg-border px-2 py-0.5 rounded">
              {row.severity}
            </span>
          </div>

          {/* Log text */}
          <div>
            <p className="text-xs text-text-dim mb-1.5">{t("modal.full_log")}</p>
            <pre className="font-mono text-xs text-text-secondary bg-bg-elevated border border-bg-border rounded p-3 whitespace-pre-wrap break-all leading-relaxed">
              {row.log}
            </pre>
          </div>

          {/* Explanation */}
          {row.explanation && (
            <div>
              <p className="text-xs text-text-dim mb-1.5">{t("modal.explanation")}</p>
              <p className="text-sm text-text-primary leading-relaxed bg-bg-elevated border border-bg-border rounded p-3">
                {row.explanation}
              </p>
            </div>
          )}

          {/* Recommendation */}
          {row.recommendation && (
            <div>
              <p className="text-xs text-text-dim mb-1.5">{t("modal.recommendation")}</p>
              <p className="text-sm text-text-primary leading-relaxed bg-bg-elevated border border-bg-border rounded p-3">
                {row.recommendation}
              </p>
            </div>
          )}

          {/* Timing */}
          <div>
            <p className="text-xs text-text-dim mb-1.5">{t("modal.timing")}</p>
            <div className="bg-bg-elevated border border-bg-border rounded p-3">
              <TimingRow label={t("modal.class_time")} value={row.classification_time_sec} />
              <TimingRow label={t("modal.analysis_time")} value={row.analysis_generation_time_sec} />
              <TimingRow label={t("modal.total_time")} value={row.total_time_sec} />
            </div>
          </div>

          {/* Analyst action panel */}
          <AnalystActionPanel label={row.label} />
        </div>
      </div>
    </div>
  );
}
