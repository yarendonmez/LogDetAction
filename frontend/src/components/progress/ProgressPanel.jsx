import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";
import { useJobPolling } from "../../hooks/useJobPolling";
import LabelBadge from "../shared/LabelBadge";

const LABEL_COLOR = {
  malicious: "text-accent-red",
  suspicious: "text-accent-amber",
  benign: "text-accent-green",
  unknown: "text-text-dim",
};

function truncate(str, n = 70) {
  if (!str) return "";
  return str.length > n ? str.slice(0, n) + "…" : str;
}

function StatusIcon({ status }) {
  if (status === "running") {
    return (
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse" />
        <span className="text-accent-cyan text-xs font-mono">LIVE</span>
      </span>
    );
  }
  if (status === "completed") {
    return (
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-accent-green" />
        <span className="text-accent-green text-xs font-mono">DONE</span>
      </span>
    );
  }
  if (status === "cancelled") {
    return (
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-accent-amber" />
        <span className="text-accent-amber text-xs font-mono">STOPPED</span>
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-accent-red" />
        <span className="text-accent-red text-xs font-mono">FAILED</span>
      </span>
    );
  }
  return null;
}

export default function ProgressPanel() {
  const { t } = useTranslation();
  const { stopJob, acceptResults } = useJobPolling();
  const [stopping, setStopping] = useState(false);
  const tableBodyRef = useRef(null);

  const jobId = useAnalysisStore((s) => s.jobId);
  const jobStatus = useAnalysisStore((s) => s.jobStatus);
  const jobTotal = useAnalysisStore((s) => s.jobTotal);
  const jobProcessed = useAnalysisStore((s) => s.jobProcessed);
  const jobResults = useAnalysisStore((s) => s.jobResults);
  const jobSourceName = useAnalysisStore((s) => s.jobSourceName);
  const jobAnalysisMode = useAnalysisStore((s) => s.jobAnalysisMode);

  const pct = jobTotal > 0 ? Math.round((jobProcessed / jobTotal) * 100) : 0;
  const isRunning = jobStatus === "running";
  const isDone = jobStatus === "completed" || jobStatus === "cancelled" || jobStatus === "failed";
  const lastLog = jobResults.length > 0 ? jobResults[jobResults.length - 1] : null;

  // Auto-scroll live table to bottom
  useEffect(() => {
    if (tableBodyRef.current && isRunning) {
      tableBodyRef.current.scrollTop = tableBodyRef.current.scrollHeight;
    }
  }, [jobResults.length, isRunning]);

  async function handleStop() {
    setStopping(true);
    await stopJob();
    setStopping(false);
  }

  if (!jobId) return null;

  const titleKey = isRunning
    ? "progress.title"
    : jobStatus === "completed"
    ? "progress.done_title"
    : jobStatus === "cancelled"
    ? "progress.stopped_title"
    : "progress.failed_title";

  return (
    <div className="card space-y-5 border-accent-cyan/20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <StatusIcon status={jobStatus} />
          <div>
            <h2 className="text-text-primary font-semibold text-sm">{t(titleKey)}</h2>
            <p className="text-text-dim text-xs font-mono mt-0.5">
              {jobSourceName} · {jobAnalysisMode === "combined" ? t("input.mode_combined") : t("input.mode_separate")}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isRunning && (
            <button
              onClick={handleStop}
              disabled={stopping}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-red-800/60 text-accent-red text-xs font-mono hover:bg-red-900/20 disabled:opacity-50 transition-all"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <rect width="10" height="10" rx="1" />
              </svg>
              {stopping ? t("progress.stopping") : t("progress.stop")}
            </button>
          )}

          {isDone && jobResults.length > 0 && (
            <button onClick={acceptResults} className="btn-primary text-xs px-4 py-1.5">
              {t("progress.view_results")}
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-mono text-text-secondary">
          <span>{t("progress.logs_processed", { processed: jobProcessed, total: jobTotal })}</span>
          <span className="text-accent-cyan">{pct}%</span>
        </div>
        <div className="h-1.5 bg-bg-elevated rounded-full overflow-hidden">
          <div
            className="h-full bg-accent-cyan rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Current log being processed */}
      {isRunning && lastLog && (
        <div className="flex items-start gap-2 text-xs">
          <span className="text-text-dim font-mono shrink-0 mt-0.5">{t("progress.current_log")}</span>
          <span className="font-mono text-text-secondary break-all leading-relaxed">
            {truncate(lastLog.log, 120)}
          </span>
        </div>
      )}

      {/* Cancelled / stopped note */}
      {jobStatus === "cancelled" && (
        <p className="text-xs text-accent-amber bg-amber-900/20 border border-amber-800/30 rounded px-3 py-2">
          {t("progress.cancelled_note", { processed: jobProcessed, total: jobTotal })}
        </p>
      )}

      {/* Live results table */}
      {jobResults.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-text-dim uppercase tracking-wide font-mono">
            {t("progress.live_preview")}
          </p>
          <div
            ref={tableBodyRef}
            className="overflow-y-auto max-h-64 rounded border border-bg-border"
          >
            <table className="w-full text-xs font-mono border-collapse">
              <thead className="sticky top-0 bg-bg-elevated z-10">
                <tr className="border-b border-bg-border text-text-dim text-left">
                  <th className="py-1.5 px-2 w-8">{t("progress.col_index")}</th>
                  <th className="py-1.5 px-2">{t("progress.col_log")}</th>
                  <th className="py-1.5 px-2 w-24">{t("progress.col_label")}</th>
                  <th className="py-1.5 px-2 w-16 text-right">{t("progress.col_time")}</th>
                </tr>
              </thead>
              <tbody>
                {jobResults.map((row, i) => (
                  <tr
                    key={i}
                    className={`border-b border-bg-border/50 ${
                      row.label === "malicious"
                        ? "bg-red-950/20"
                        : row.label === "suspicious"
                        ? "bg-amber-950/10"
                        : ""
                    }`}
                  >
                    <td className="py-1 px-2 text-text-dim">{(row.index ?? i) + 1}</td>
                    <td className="py-1 px-2 text-text-secondary max-w-sm">
                      {truncate(row.log, 80)}
                    </td>
                    <td className="py-1 px-2">
                      <LabelBadge label={row.label} />
                    </td>
                    <td className={`py-1 px-2 text-right ${LABEL_COLOR[row.label] ?? LABEL_COLOR.unknown}`}>
                      {row.total_time_sec}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Quick stats */}
          <div className="flex gap-4 text-xs font-mono text-text-dim pt-1">
            <span className="text-accent-red">
              {jobResults.filter((r) => r.label === "malicious").length} malicious
            </span>
            <span className="text-accent-amber">
              {jobResults.filter((r) => r.label === "suspicious").length} suspicious
            </span>
            <span className="text-accent-green">
              {jobResults.filter((r) => r.label === "benign").length} benign
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
