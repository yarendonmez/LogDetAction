import { useTranslation } from "react-i18next";
import useAnalysisStore from "../../store/analysisStore";
import LabelBadge from "../shared/LabelBadge";
import StatusBadge from "../shared/StatusBadge";

const ROW_BG = {
  malicious: "bg-red-950/30 hover:bg-red-950/50",
  suspicious: "bg-amber-950/20 hover:bg-amber-950/40",
  benign: "hover:bg-bg-elevated",
  unknown: "hover:bg-bg-elevated",
};

function Cell({ children, className = "" }) {
  return (
    <td className={`py-2 px-2 ${className}`}>
      <div className="truncate" title={typeof children === "string" ? children : undefined}>
        {children}
      </div>
    </td>
  );
}

export default function ResultTable() {
  const { t } = useTranslation();
  const openModal = useAnalysisStore((s) => s.openModal);
  const items = useAnalysisStore((s) => s.getVisibleResults());

  if (!items.length) {
    return (
      <p className="text-text-dim text-sm text-center py-8 font-mono">
        {t("dashboard.no_results")}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      {/* min-w forces horizontal scroll rather than text collapsing */}
      <table className="table-fixed font-mono text-xs border-collapse" style={{ minWidth: "1080px", width: "100%" }}>
        <colgroup>
          <col style={{ width: "36px" }} />   {/* # */}
          <col style={{ width: "200px" }} />  {/* Log */}
          <col style={{ width: "90px" }} />   {/* Label */}
          <col style={{ width: "68px" }} />   {/* Severity */}
          <col style={{ width: "150px" }} />  {/* Status */}
          <col style={{ width: "220px" }} />  {/* Explanation */}
          <col style={{ width: "220px" }} />  {/* Recommendation */}
          <col style={{ width: "70px" }} />   {/* Class. Time */}
          <col style={{ width: "78px" }} />   {/* Analysis Time */}
          <col style={{ width: "68px" }} />   {/* Total Time */}
        </colgroup>
        <thead>
          <tr className="border-b border-bg-border text-text-dim text-left">
            <th className="py-2 px-2">{t("dashboard.col_index")}</th>
            <th className="py-2 px-2">{t("dashboard.col_log")}</th>
            <th className="py-2 px-2">{t("dashboard.col_label")}</th>
            <th className="py-2 px-2">{t("dashboard.col_severity")}</th>
            <th className="py-2 px-2">{t("dashboard.col_status")}</th>
            <th className="py-2 px-2">{t("dashboard.col_explanation")}</th>
            <th className="py-2 px-2">{t("dashboard.col_recommendation")}</th>
            <th className="py-2 px-2 text-right">{t("dashboard.col_class_time")}</th>
            <th className="py-2 px-2 text-right">{t("dashboard.col_analysis_time")}</th>
            <th className="py-2 px-2 text-right">{t("dashboard.col_total_time")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr
              key={row.index}
              onClick={() => openModal(row)}
              className={`border-b border-bg-border cursor-pointer transition-colors ${
                ROW_BG[row.label] ?? ROW_BG.unknown
              }`}
            >
              <td className="py-2 px-2 text-text-dim">{row.index + 1}</td>
              <Cell className="text-text-secondary">{row.log}</Cell>
              <td className="py-2 px-2">
                <LabelBadge label={row.label} />
              </td>
              <Cell className="text-text-secondary capitalize">{row.severity}</Cell>
              <td className="py-2 px-2">
                <StatusBadge status={row.status} />
              </td>
              <Cell className="text-text-secondary">{row.explanation}</Cell>
              <Cell className="text-text-secondary">{row.recommendation}</Cell>
              <td className="py-2 px-2 text-right text-text-dim whitespace-nowrap">
                {row.classification_time_sec}s
              </td>
              <td className="py-2 px-2 text-right text-text-dim whitespace-nowrap">
                {row.analysis_generation_time_sec}s
              </td>
              <td className="py-2 px-2 text-right text-accent-cyan whitespace-nowrap">
                {row.total_time_sec}s
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
