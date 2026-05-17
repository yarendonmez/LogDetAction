import { useTranslation } from "react-i18next";
import LabelBadge from "../shared/LabelBadge";
import useAnalysisStore from "../../store/analysisStore";

function fmtTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

export default function LiveEventsTable({ events, filter, onFilterChange }) {
  const { t } = useTranslation();
  const openModal = useAnalysisStore((s) => s.openModal);

  const FILTERS = ["all", "malicious", "suspicious", "benign"];

  if (events.length === 0) {
    return (
      <div className="card space-y-3">
        {/* Filter tabs */}
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-accent-cyan/20 text-accent-cyan"
                  : "text-text-dim hover:text-text-secondary"
              }`}
            >
              {t(`live.filter_${f}`)}
            </button>
          ))}
        </div>
        <p className="text-text-dim text-sm text-center py-8">{t("live.no_events")}</p>
      </div>
    );
  }

  return (
    <div className="card space-y-3">
      {/* Filter tabs */}
      <div className="flex gap-1">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => onFilterChange(f)}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              filter === f
                ? "bg-accent-cyan/20 text-accent-cyan"
                : "text-text-dim hover:text-text-secondary"
            }`}
          >
            {t(`live.filter_${f}`)}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table
          className="table-fixed font-mono text-xs border-collapse"
          style={{ minWidth: "960px", width: "100%" }}
        >
          <colgroup>
            <col style={{ width: "36px" }} />
            <col style={{ width: "90px" }} />
            <col style={{ width: "220px" }} />
            <col style={{ width: "80px" }} />
            <col style={{ width: "68px" }} />
            <col style={{ width: "240px" }} />
            <col style={{ width: "64px" }} />
          </colgroup>
          <thead>
            <tr className="border-b border-bg-border">
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">#</th>
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">{t("live.col_time")}</th>
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">{t("live.col_log")}</th>
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">{t("live.col_label")}</th>
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">{t("live.col_severity")}</th>
              <th className="py-2 px-2 text-left text-text-dim font-medium text-xs">{t("live.col_explanation")}</th>
              <th className="py-2 px-2 text-right text-text-dim font-medium text-xs">{t("live.col_total_time")}</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev, i) => {
              const rowBg =
                ev.label === "malicious"
                  ? "bg-accent-red/5 hover:bg-accent-red/10"
                  : ev.label === "suspicious"
                  ? "bg-accent-amber/5 hover:bg-accent-amber/10"
                  : "hover:bg-bg-elevated/40";

              return (
                <tr
                  key={i}
                  className={`border-b border-bg-border/40 cursor-pointer transition-colors ${rowBg}`}
                  onClick={() => openModal(ev)}
                >
                  <td className="py-2 px-2 text-text-dim">{ev.index ?? i + 1}</td>
                  <td className="py-2 px-2 text-text-dim whitespace-nowrap">{fmtTime(ev.created_at)}</td>
                  <td className="py-2 px-2">
                    <div className="truncate text-text-secondary" title={ev.log}>{ev.log}</div>
                  </td>
                  <td className="py-2 px-2">
                    <LabelBadge label={ev.label} />
                  </td>
                  <td className="py-2 px-2 text-text-secondary capitalize">{ev.severity}</td>
                  <td className="py-2 px-2">
                    <div className="truncate text-text-dim" title={ev.explanation || ""}>
                      {ev.explanation || "—"}
                    </div>
                  </td>
                  <td className="py-2 px-2 text-right text-text-dim whitespace-nowrap">
                    {ev.total_time_sec != null ? `${ev.total_time_sec}s` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
