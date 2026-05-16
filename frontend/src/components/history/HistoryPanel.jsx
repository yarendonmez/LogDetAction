import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";
import { fetchResults, fetchResultById } from "../../api/client";

const TIME_FILTERS = [
  { key: "all",  i18n: "history.time_all" },
  { key: "today", i18n: "history.time_today" },
  { key: "7d",   i18n: "history.time_7d" },
  { key: "30d",  i18n: "history.time_30d" },
];

function formatDate(iso) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function CountChip({ count, color }) {
  return (
    <span className={`font-mono text-xs px-1.5 py-0.5 rounded ${color}`}>
      {count}
    </span>
  );
}

function SourceIcon({ type }) {
  if (type === "file") {
    return (
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    );
  }
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0">
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" y1="19" x2="20" y2="19" />
    </svg>
  );
}

export default function HistoryPanel() {
  const { t } = useTranslation();

  const historyItems     = useAnalysisStore((s) => s.historyItems);
  const historyLoading   = useAnalysisStore((s) => s.historyLoading);
  const historyTimeFilter = useAnalysisStore((s) => s.historyTimeFilter);
  const setHistoryItems   = useAnalysisStore((s) => s.setHistoryItems);
  const setHistoryLoading = useAnalysisStore((s) => s.setHistoryLoading);
  const setHistoryTimeFilter = useAnalysisStore((s) => s.setHistoryTimeFilter);
  const openHistoryDetail = useAnalysisStore((s) => s.openHistoryDetail);
  const getFilteredHistory = useAnalysisStore((s) => s.getFilteredHistory);

  async function load() {
    setHistoryLoading(true);
    try {
      const data = await fetchResults();
      setHistoryItems(data);
    } catch {
      // silently fail
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleViewDetail(item) {
    try {
      const full = await fetchResultById(item.analysis_id);
      openHistoryDetail(full);
    } catch {
      // show empty detail gracefully
      openHistoryDetail({ ...item, results: [] });
    }
  }

  const filtered = getFilteredHistory();

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h2 className="text-text-primary font-semibold">{t("history.title")}</h2>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Time filter pills */}
          <div className="flex gap-1">
            {TIME_FILTERS.map(({ key, i18n }) => (
              <button
                key={key}
                onClick={() => setHistoryTimeFilter(key)}
                className={`px-3 py-1 rounded text-xs font-mono transition-all ${
                  historyTimeFilter === key
                    ? "bg-accent-cyan/20 border border-accent-cyan text-accent-cyan"
                    : "border border-bg-border text-text-secondary hover:border-accent-muted"
                }`}
              >
                {t(i18n)}
              </button>
            ))}
          </div>

          {/* Refresh */}
          <button
            onClick={load}
            disabled={historyLoading}
            className="btn-ghost py-1 px-2 text-xs"
            title={t("history.refresh")}
          >
            <svg
              width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2"
              className={historyLoading ? "animate-spin" : ""}
            >
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      {historyLoading && !filtered.length ? (
        <p className="text-text-dim text-sm text-center py-12 font-mono">{t("history.loading")}</p>
      ) : filtered.length === 0 ? (
        <p className="text-text-dim text-sm text-center py-12 font-mono">{t("history.empty")}</p>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-bg-border text-text-dim text-left bg-bg-elevated">
                <th className="py-2.5 px-4">{t("history.col_source")}</th>
                <th className="py-2.5 px-3">{t("history.col_date")}</th>
                <th className="py-2.5 px-3">{t("history.col_mode")}</th>
                <th className="py-2.5 px-3 text-center">{t("history.col_total")}</th>
                <th className="py-2.5 px-3 text-center">{t("history.col_malicious")}</th>
                <th className="py-2.5 px-3 text-center">{t("history.col_suspicious")}</th>
                <th className="py-2.5 px-3 text-center">{t("history.col_benign")}</th>
                <th className="py-2.5 px-3 text-right">{t("history.col_avg_time")}</th>
                <th className="py-2.5 px-3 text-right">{t("history.col_actions")}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr
                  key={item.analysis_id}
                  className="border-b border-bg-border hover:bg-bg-elevated transition-colors group"
                >
                  {/* Source */}
                  <td className="py-2.5 px-4">
                    <div className="flex items-center gap-2 text-text-secondary">
                      <SourceIcon type={item.source_type} />
                      <span className="truncate max-w-[160px]" title={item.source_name}>
                        {item.source_name}
                      </span>
                    </div>
                  </td>

                  {/* Date */}
                  <td className="py-2.5 px-3 text-text-dim whitespace-nowrap">
                    {formatDate(item.generated_at)}
                  </td>

                  {/* Mode */}
                  <td className="py-2.5 px-3">
                    <span className={`px-1.5 py-0.5 rounded border text-xs ${
                      item.analysis_mode === "combined"
                        ? "border-accent-cyan/40 text-accent-cyan bg-accent-cyan/10"
                        : "border-accent-violet/40 text-accent-violet bg-accent-violet/10"
                    }`}>
                      {item.analysis_mode === "combined"
                        ? t("history.mode_combined")
                        : t("history.mode_separate")}
                    </span>
                  </td>

                  {/* Counts */}
                  <td className="py-2.5 px-3 text-center text-text-secondary">{item.total_logs}</td>
                  <td className="py-2.5 px-3 text-center">
                    <CountChip count={item.malicious_count} color="text-accent-red bg-red-900/30" />
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <CountChip count={item.suspicious_count} color="text-accent-amber bg-amber-900/20" />
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <CountChip count={item.benign_count} color="text-accent-green bg-green-900/20" />
                  </td>

                  {/* Avg time */}
                  <td className="py-2.5 px-3 text-right text-text-dim">
                    {item.avg_total_time_sec}s
                  </td>

                  {/* Actions */}
                  <td className="py-2.5 px-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleViewDetail(item)}
                        className="text-accent-cyan text-xs hover:underline"
                      >
                        {t("history.view_detail")}
                      </button>
                      {item.csv_download_url && (
                        <a
                          href={item.csv_download_url}
                          download
                          className="text-text-dim hover:text-text-secondary text-xs"
                          title={t("history.download_csv")}
                        >
                          {t("history.download_csv")}
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
