import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";
import LabelBadge from "../shared/LabelBadge";
import StatusBadge from "../shared/StatusBadge";
import LogDetailModal from "../modals/LogDetailModal";

const LABEL_FILTERS = [
  { key: "all",        i18n: "history.filter_all" },
  { key: "malicious",  i18n: "history.filter_malicious" },
  { key: "suspicious", i18n: "history.filter_suspicious" },
  { key: "benign",     i18n: "history.filter_benign" },
];

const ROW_BG = {
  malicious: "bg-red-950/30 hover:bg-red-950/50",
  suspicious: "bg-amber-950/20 hover:bg-amber-950/40",
  benign: "hover:bg-bg-elevated",
  unknown: "hover:bg-bg-elevated",
};

function formatDate(iso) {
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
  } catch { return iso; }
}

function SummaryCard({ label, value, color }) {
  return (
    <div className={`bg-bg-surface border rounded-lg p-3 ${color}`}>
      <p className="text-xs font-mono text-text-dim mb-0.5">{label}</p>
      <p className="text-xl font-bold font-mono text-text-primary">{value}</p>
    </div>
  );
}

export default function HistoryDetailView() {
  const { t } = useTranslation();
  const [searchLocal, setSearchLocal] = useState("");

  const detail              = useAnalysisStore((s) => s.historyDetail);
  const detailFilter        = useAnalysisStore((s) => s.historyDetailFilter);
  const setDetailFilter     = useAnalysisStore((s) => s.setHistoryDetailFilter);
  const setDetailSearch     = useAnalysisStore((s) => s.setHistoryDetailSearch);
  const closeHistoryDetail  = useAnalysisStore((s) => s.closeHistoryDetail);
  const getRows             = useAnalysisStore((s) => s.getHistoryDetailRows);
  const openModal           = useAnalysisStore((s) => s.openModal);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDetailSearch(searchLocal), 300);
    return () => clearTimeout(t);
  }, [searchLocal, setDetailSearch]);

  if (!detail) return null;

  const rows = getRows();

  const countFor = (label) =>
    label === "all"
      ? detail.total_logs
      : detail.results?.filter((r) => r.label === label).length ?? 0;

  return (
    <>
      <LogDetailModal />

      <div className="space-y-5">
        {/* Back + title */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <button
              onClick={closeHistoryDetail}
              className="text-text-dim text-xs hover:text-accent-cyan font-mono mb-2 transition-colors"
            >
              {t("history.back")}
            </button>
            <h2 className="text-text-primary font-semibold">{t("history.detail_title")}</h2>
            <p className="text-text-dim text-xs font-mono mt-0.5">
              {detail.source_name} · {formatDate(detail.generated_at)} ·{" "}
              <span className={detail.analysis_mode === "combined" ? "text-accent-cyan" : "text-accent-violet"}>
                {detail.analysis_mode}
              </span>
            </p>
          </div>

          {detail.csv_download_url && (
            <a href={detail.csv_download_url} download className="btn-ghost text-xs py-1.5 whitespace-nowrap">
              {t("history.download_csv")}
            </a>
          )}
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <SummaryCard label={t("dashboard.total")} value={detail.total_logs} color="border-bg-border" />
          <SummaryCard label={t("dashboard.malicious")} value={detail.malicious_count} color="border-red-800/40 bg-red-900/10" />
          <SummaryCard label={t("dashboard.suspicious")} value={detail.suspicious_count} color="border-amber-800/30 bg-amber-900/10" />
          <SummaryCard label={t("dashboard.benign")} value={detail.benign_count} color="border-green-800/30 bg-green-900/10" />
          <SummaryCard label={t("dashboard.avg_latency")} value={`${detail.avg_total_time_sec}s`} color="border-bg-border" />
        </div>

        {/* Filter + search toolbar */}
        <div className="card space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            {/* Label filter tabs */}
            <div className="flex gap-1.5 flex-wrap">
              {LABEL_FILTERS.map(({ key, i18n }) => {
                const active = detailFilter === key;
                const n = countFor(key);
                const activeStyle = {
                  all: "border-accent-cyan text-accent-cyan bg-accent-cyan/10",
                  malicious: "border-accent-red text-accent-red bg-red-900/20",
                  suspicious: "border-accent-amber text-accent-amber bg-amber-900/20",
                  benign: "border-accent-green text-accent-green bg-green-900/20",
                }[key];

                return (
                  <button
                    key={key}
                    onClick={() => setDetailFilter(key)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs font-mono transition-all ${
                      active ? activeStyle : "border-bg-border text-text-secondary hover:border-accent-muted"
                    }`}
                  >
                    {t(i18n)}
                    <span className={`text-xs px-1 rounded ${active ? "bg-white/10" : "bg-bg-elevated text-text-dim"}`}>
                      {n}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Search */}
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-text-dim w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                value={searchLocal}
                onChange={(e) => setSearchLocal(e.target.value)}
                placeholder={t("history.search_placeholder")}
                className="input-base pl-8 w-full sm:w-64"
              />
            </div>
          </div>

          {/* Results table */}
          {rows.length === 0 ? (
            <p className="text-text-dim text-sm text-center py-8 font-mono">{t("history.no_results")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="table-fixed font-mono text-xs border-collapse" style={{ minWidth: "1000px", width: "100%" }}>
                <colgroup>
                  <col style={{ width: "36px" }} />
                  <col style={{ width: "200px" }} />
                  <col style={{ width: "90px" }} />
                  <col style={{ width: "150px" }} />
                  <col style={{ width: "220px" }} />
                  <col style={{ width: "220px" }} />
                  <col style={{ width: "70px" }} />
                  <col style={{ width: "78px" }} />
                  <col style={{ width: "68px" }} />
                </colgroup>
                <thead>
                  <tr className="border-b border-bg-border text-text-dim text-left">
                    <th className="py-2 px-2">{t("dashboard.col_index")}</th>
                    <th className="py-2 px-2">{t("dashboard.col_log")}</th>
                    <th className="py-2 px-2">{t("dashboard.col_label")}</th>
                    <th className="py-2 px-2">{t("dashboard.col_status")}</th>
                    <th className="py-2 px-2">{t("dashboard.col_explanation")}</th>
                    <th className="py-2 px-2">{t("dashboard.col_recommendation")}</th>
                    <th className="py-2 px-2 text-right">{t("dashboard.col_class_time")}</th>
                    <th className="py-2 px-2 text-right">{t("dashboard.col_analysis_time")}</th>
                    <th className="py-2 px-2 text-right">{t("dashboard.col_total_time")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr
                      key={row.index}
                      onClick={() => openModal(row)}
                      className={`border-b border-bg-border cursor-pointer transition-colors ${ROW_BG[row.label] ?? ROW_BG.unknown}`}
                    >
                      <td className="py-2 px-2 text-text-dim">{row.index + 1}</td>
                      <td className="py-2 px-2">
                        <div className="truncate text-text-secondary" title={row.log}>{row.log}</div>
                      </td>
                      <td className="py-2 px-2"><LabelBadge label={row.label} /></td>
                      <td className="py-2 px-2"><StatusBadge status={row.status} /></td>
                      <td className="py-2 px-2">
                        <div className="truncate text-text-secondary" title={row.explanation}>{row.explanation}</div>
                      </td>
                      <td className="py-2 px-2">
                        <div className="truncate text-text-secondary" title={row.recommendation}>{row.recommendation}</div>
                      </td>
                      <td className="py-2 px-2 text-right text-text-dim whitespace-nowrap">{row.classification_time_sec}s</td>
                      <td className="py-2 px-2 text-right text-text-dim whitespace-nowrap">{row.analysis_generation_time_sec}s</td>
                      <td className="py-2 px-2 text-right text-accent-cyan whitespace-nowrap">{row.total_time_sec}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
