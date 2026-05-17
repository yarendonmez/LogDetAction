import { useTranslation } from "react-i18next";

function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function shortId(id) {
  return id ? id.slice(0, 8) : "—";
}

export default function AnalysisHistoryPanel({ analyses }) {
  const { t } = useTranslation();

  if (!analyses || analyses.length === 0) {
    return (
      <div className="card space-y-3">
        <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
          {t("analytics.history_panel")}
        </h3>
        <p className="text-text-dim text-sm py-6 text-center">{t("analytics.empty")}</p>
      </div>
    );
  }

  const sourceLabel = (type) => {
    if (type === "file") return t("analytics.source_file");
    if (type === "text") return t("analytics.source_text");
    if (type === "live") return t("analytics.source_live");
    return type;
  };

  const modeLabel = (mode) =>
    mode === "combined" ? t("analytics.mode_combined") : t("analytics.mode_separate");

  return (
    <div className="card space-y-3">
      <h3 className="text-text-secondary text-xs uppercase tracking-wider font-medium">
        {t("analytics.history_panel")}
      </h3>
      <div className="overflow-x-auto">
        <table
          className="table-fixed font-mono text-xs border-collapse"
          style={{ minWidth: "780px", width: "100%" }}
        >
          <colgroup>
            <col style={{ width: "72px" }} />
            <col style={{ width: "160px" }} />
            <col style={{ width: "64px" }} />
            <col style={{ width: "80px" }} />
            <col style={{ width: "60px" }} />
            <col style={{ width: "64px" }} />
            <col style={{ width: "160px" }} />
            <col style={{ width: "60px" }} />
          </colgroup>
          <thead>
            <tr className="border-b border-bg-border">
              {[
                t("analytics.col_id"),
                t("analytics.col_source"),
                t("analytics.col_type"),
                t("analytics.col_mode"),
                t("analytics.col_total"),
                t("analytics.col_malicious"),
                t("analytics.col_date"),
                t("analytics.col_csv"),
              ].map((h) => (
                <th
                  key={h}
                  className="py-2 px-2 text-left text-text-dim font-medium text-xs uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {analyses.map((a) => (
              <tr
                key={a.analysis_id}
                className="border-b border-bg-border/50 hover:bg-bg-elevated/40 transition-colors"
              >
                <td className="py-2 px-2 text-text-dim">{shortId(a.analysis_id)}</td>
                <td className="py-2 px-2">
                  <div className="truncate text-text-secondary" title={a.source_name}>
                    {a.source_name}
                  </div>
                </td>
                <td className="py-2 px-2 text-text-secondary">{sourceLabel(a.source_type)}</td>
                <td className="py-2 px-2 text-text-secondary">{modeLabel(a.analysis_mode)}</td>
                <td className="py-2 px-2 text-right text-text-secondary">{a.total_logs}</td>
                <td className="py-2 px-2 text-right text-accent-red">{a.malicious_count}</td>
                <td className="py-2 px-2 text-text-dim whitespace-nowrap">{fmtDate(a.generated_at)}</td>
                <td className="py-2 px-2">
                  {a.csv_download_url ? (
                    <a
                      href={a.csv_download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-cyan hover:underline"
                    >
                      {t("analytics.download")}
                    </a>
                  ) : (
                    <span className="text-text-dim">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
