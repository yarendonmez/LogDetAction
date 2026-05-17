import { useTranslation } from "react-i18next";
import { useLiveMonitor } from "../../hooks/useLiveMonitor";
import useAnalysisStore from "../../store/analysisStore";
import LiveStatusCard from "./LiveStatusCard";
import LiveEventsTable from "./LiveEventsTable";
import ModeSelector from "../input/ModeSelector";
import { useState } from "react";

export default function LiveMonitorPanel() {
  const { t } = useTranslation();
  const [mode, setMode] = useState("combined");
  const health = useAnalysisStore((s) => s.health);

  const {
    status,
    events,
    eventsFilter,
    changeFilter,
    isRunning,
    actionLoading,
    error,
    startMonitor,
    stopMonitor,
    refreshEvents,
    refreshStatus,
  } = useLiveMonitor();

  const modelReady = health?.model_loaded === true;

  const handleRefresh = () => {
    refreshStatus();
    refreshEvents(eventsFilter);
  };

  return (
    <div className="space-y-5">
      {/* Header + controls */}
      <div className="card space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-text-primary font-semibold text-sm">{t("live.title")}</h2>
            <p className="text-text-dim text-xs mt-1 font-mono">
              {status?.live_log_path || t("live.subtitle", { path: "backend/live/live_demo.log" })}
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={handleRefresh}
              disabled={actionLoading}
              className="btn-ghost text-xs px-3 py-1.5"
            >
              {t("live.refresh")}
            </button>
            {!isRunning ? (
              <button
                onClick={() => startMonitor(mode)}
                disabled={actionLoading || !modelReady}
                className="btn-primary text-xs px-4 py-1.5 disabled:opacity-50"
                title={!modelReady ? t("live.model_not_ready") : undefined}
              >
                {actionLoading ? t("live.starting") : t("live.start")}
              </button>
            ) : (
              <button
                onClick={stopMonitor}
                disabled={actionLoading}
                className="px-4 py-1.5 text-xs font-medium rounded border border-accent-red/50 text-accent-red hover:bg-accent-red/10 transition-colors disabled:opacity-50"
              >
                {actionLoading ? t("live.stopping") : t("live.stop")}
              </button>
            )}
          </div>
        </div>

        {!modelReady && (
          <p className="text-accent-amber text-xs">{t("live.model_not_ready")}</p>
        )}

        {error && (
          <p className="text-accent-red text-xs font-mono">{error}</p>
        )}

        {/* Mode selector — only relevant before starting */}
        {!isRunning && (
          <div className="pt-1">
            <ModeSelector value={mode} onChange={setMode} />
          </div>
        )}

        {/* Demo hint */}
        <div className="border-t border-bg-border pt-3 space-y-1">
          <p className="text-text-dim text-xs">{t("live.demo_hint")}</p>
          <code className="block bg-bg-elevated text-accent-cyan text-xs font-mono px-3 py-2 rounded">
            {t("live.demo_cmd")}
          </code>
        </div>
      </div>

      {/* Status card */}
      <LiveStatusCard status={status} events={events} />

      {/* Events table */}
      <LiveEventsTable
        events={events}
        filter={eventsFilter}
        onFilterChange={changeFilter}
      />
    </div>
  );
}
