import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDashboard } from "../../hooks/useDashboard";
import ExecutiveSummary from "./ExecutiveSummary";
import LabelDistributionChart from "./LabelDistributionChart";
import SeverityDistributionChart from "./SeverityDistributionChart";
import LatencyOverview from "./LatencyOverview";
import RecentCriticalEvents from "./RecentCriticalEvents";
import AnalysisHistoryPanel from "./AnalysisHistoryPanel";

export default function AnalyticsDashboard() {
  const { t } = useTranslation();
  const { data, loading, error, refresh } = useDashboard();

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h2 className="text-text-primary font-semibold text-sm">{t("analytics.title")}</h2>
        <button
          onClick={refresh}
          disabled={loading}
          className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-50"
        >
          {loading ? t("analytics.loading") : t("analytics.refresh")}
        </button>
      </div>

      {error && (
        <div className="card border border-accent-red/30 text-accent-red text-sm p-4">
          {error}
        </div>
      )}

      {!data && !loading && !error && (
        <div className="card text-text-dim text-sm text-center py-12">
          {t("analytics.empty")}
        </div>
      )}

      {data && (
        <>
          {/* Executive summary KPIs */}
          <ExecutiveSummary data={data} />

          {/* Charts row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <LabelDistributionChart data={data} />
            <SeverityDistributionChart data={data} />
            <LatencyOverview data={data} />
          </div>

          {/* Recent critical events */}
          <RecentCriticalEvents events={data.recent_critical_events} />

          {/* Analysis history table */}
          <AnalysisHistoryPanel analyses={data.recent_analyses} />
        </>
      )}
    </div>
  );
}
