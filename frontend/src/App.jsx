import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { checkHealth } from "./api/client";
import useAnalysisStore from "./store/analysisStore";
import { useAnalysis } from "./hooks/useAnalysis";

import Header from "./components/layout/Header";
import FileUploadZone from "./components/input/FileUploadZone";
import ManualInputPanel from "./components/input/ManualInputPanel";
import SummaryCards from "./components/dashboard/SummaryCards";
import FilterBar from "./components/dashboard/FilterBar";
import SearchInput from "./components/dashboard/SearchInput";
import ResultTable from "./components/dashboard/ResultTable";
import LogDetailModal from "./components/modals/LogDetailModal";
import LoadingOverlay from "./components/shared/LoadingOverlay";
import ProgressPanel from "./components/progress/ProgressPanel";
import HistoryPanel from "./components/history/HistoryPanel";
import HistoryDetailView from "./components/history/HistoryDetailView";
import AnalyticsDashboard from "./components/analytics/AnalyticsDashboard";
import LiveMonitorPanel from "./components/live/LiveMonitorPanel";

const INPUT_TABS = ["file", "text"];
const NAV_TABS = ["analyze", "history", "analytics", "live"];

// ── Limitations banner ────────────────────────────────────────────────────────
function LimitationsBanner() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  if (!open) return null;
  return (
    <div className="bg-bg-elevated border border-bg-border rounded-lg px-4 py-3 flex items-start gap-3">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent-amber mt-0.5 shrink-0">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div className="flex-1">
        <span className="text-xs font-semibold text-accent-amber uppercase tracking-wide">{t("limitations.title")}</span>
        <p className="text-text-secondary text-xs leading-relaxed mt-0.5">{t("limitations.text")}</p>
      </div>
      <button onClick={() => setOpen(false)} className="text-text-dim hover:text-text-secondary ml-2 shrink-0">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

// ── Error banner ──────────────────────────────────────────────────────────────
function ErrorBanner() {
  const { t } = useTranslation();
  const error = useAnalysisStore((s) => s.error);
  const clearError = useAnalysisStore((s) => s.clearError);
  if (!error) return null;
  return (
    <div className="bg-red-950/40 border border-red-800/50 rounded-lg px-4 py-3 flex items-start gap-3">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent-red mt-0.5 shrink-0">
        <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
      </svg>
      <p className="text-text-primary text-sm flex-1">{error}</p>
      <button onClick={clearError} className="text-text-dim hover:text-text-secondary ml-2 shrink-0">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

// ── Analyze tab ───────────────────────────────────────────────────────────────
function AnalyzeTab() {
  const { t } = useTranslation();
  const [inputTab, setInputTab] = useState("file");
  const { runFile, runText } = useAnalysis();
  const loading       = useAnalysisStore((s) => s.loading);
  const currentResult = useAnalysisStore((s) => s.currentResult);
  const jobId         = useAnalysisStore((s) => s.jobId);

  return (
    <div className="space-y-6">
      <LimitationsBanner />
      <ErrorBanner />

      {/* Progress panel — visible while a job is active */}
      {jobId && <ProgressPanel />}

      {/* Input panel — hidden while job is running */}
      <section className={jobId ? "hidden" : ""}>
        <div className="flex gap-1 mb-4 border-b border-bg-border">
          {INPUT_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setInputTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors -mb-px border-b-2 ${
                inputTab === tab
                  ? "border-accent-cyan text-accent-cyan"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {t(`input.${tab}_tab`)}
            </button>
          ))}
        </div>

        {inputTab === "file" ? (
          <FileUploadZone onSubmit={runFile} loading={loading} />
        ) : (
          <ManualInputPanel onSubmit={runText} loading={loading} />
        )}
      </section>

      {/* Results — shown after job is accepted */}
      {!jobId && currentResult && (
        <section className="space-y-4">
          <SummaryCards result={currentResult} />
          <div className="card space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <FilterBar result={currentResult} />
              <div className="flex items-center gap-2">
                <SearchInput />
                <a href={currentResult.csv_download_url} download className="btn-ghost whitespace-nowrap">
                  {t("dashboard.download_csv")}
                </a>
              </div>
            </div>
            <ResultTable />
          </div>
        </section>
      )}
    </div>
  );
}

// ── History tab ───────────────────────────────────────────────────────────────
function HistoryTab() {
  const historyView = useAnalysisStore((s) => s.historyView);
  return historyView === "detail" ? <HistoryDetailView /> : <HistoryPanel />;
}

// ── Tab label helper ──────────────────────────────────────────────────────────
function tabLabel(tab, t) {
  switch (tab) {
    case "analyze":   return t("nav.tab_analyze");
    case "history":   return t("nav.tab_history");
    case "analytics": return t("nav.tab_analytics");
    case "live":      return t("nav.tab_live");
    default:          return tab;
  }
}

// ── Root app ──────────────────────────────────────────────────────────────────
export default function App() {
  const { t } = useTranslation();
  const [navTab, setNavTab] = useState("analyze");
  const setHealth = useAnalysisStore((s) => s.setHealth);

  useEffect(() => {
    async function poll() {
      try { setHealth(await checkHealth()); }
      catch { setHealth({ status: "offline" }); }
    }
    poll();
    const id = setInterval(poll, 30000);
    return () => clearInterval(id);
  }, [setHealth]);

  return (
    <div className="min-h-screen bg-bg-base flex flex-col font-ui">
      <Header />
      <LoadingOverlay visible={false} />
      <LogDetailModal />

      <main className="flex-1 max-w-screen-xl mx-auto w-full px-4 sm:px-6 py-6">
        {/* Top-level navigation */}
        <div className="flex gap-1 mb-6 border-b border-bg-border overflow-x-auto">
          {NAV_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setNavTab(tab)}
              className={`px-5 py-2.5 text-sm font-medium transition-colors -mb-px border-b-2 whitespace-nowrap ${
                navTab === tab
                  ? "border-accent-cyan text-accent-cyan"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {tabLabel(tab, t)}
            </button>
          ))}
        </div>

        {navTab === "analyze"   && <AnalyzeTab />}
        {navTab === "history"   && <HistoryTab />}
        {navTab === "analytics" && <AnalyticsDashboard />}
        {navTab === "live"      && <LiveMonitorPanel />}
      </main>
    </div>
  );
}
