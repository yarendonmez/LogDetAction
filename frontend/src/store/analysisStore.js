import { create } from "zustand";

const useAnalysisStore = create((set, get) => ({
  // ── Current full analysis result (Analyze tab) ────────────────────────────
  currentResult: null,
  setCurrentResult: (result) => set({ currentResult: result }),
  clearCurrentResult: () => set({ currentResult: null }),

  // ── Job (progress) state ──────────────────────────────────────────────────
  jobId: null,
  jobStatus: null,
  jobTotal: 0,
  jobProcessed: 0,
  jobResults: [],
  jobAnalysisId: null,
  jobCsvUrl: null,
  jobAvgTimes: null,
  jobSourceName: "",
  jobAnalysisMode: "combined",

  setJob: (data) =>
    set({
      jobId: data.job_id ?? null,
      jobStatus: data.status ?? "running",
      jobTotal: data.total ?? 0,
      jobProcessed: data.processed ?? 0,
      jobResults: data.results ?? [],
      jobAnalysisId: data.analysis_id ?? null,
      jobCsvUrl: data.csv_download_url ?? null,
      jobSourceName: data.source_name ?? "",
      jobAnalysisMode: data.analysis_mode ?? "combined",
      jobAvgTimes: data.avg_total_time_sec != null
        ? {
            classification: data.avg_classification_time_sec,
            analysis: data.avg_analysis_generation_time_sec,
            total: data.avg_total_time_sec,
          }
        : null,
    }),

  updateJobProgress: (data) =>
    set({
      jobStatus: data.status,
      jobProcessed: data.processed,
      jobResults: data.results ?? [],
      jobAnalysisId: data.analysis_id ?? null,
      jobCsvUrl: data.csv_download_url ?? null,
      jobAvgTimes: data.avg_total_time_sec != null
        ? {
            classification: data.avg_classification_time_sec,
            analysis: data.avg_analysis_generation_time_sec,
            total: data.avg_total_time_sec,
          }
        : null,
    }),

  clearJob: () =>
    set({
      jobId: null,
      jobStatus: null,
      jobTotal: 0,
      jobProcessed: 0,
      jobResults: [],
      jobAnalysisId: null,
      jobCsvUrl: null,
      jobAvgTimes: null,
      jobSourceName: "",
      jobAnalysisMode: "combined",
    }),

  // ── History ───────────────────────────────────────────────────────────────
  historyItems: [],          // list[AnalysisSummary]
  historyLoading: false,
  historyTimeFilter: "all",  // "all" | "today" | "7d" | "30d"
  historyView: "list",       // "list" | "detail"
  historyDetail: null,       // full AnalysisResponse when viewing a single record

  // Filter applied inside the detail view (label filter)
  historyDetailFilter: "all",
  historyDetailSearch: "",

  setHistoryItems: (items) => set({ historyItems: items }),
  setHistoryLoading: (v) => set({ historyLoading: v }),
  setHistoryTimeFilter: (f) => set({ historyTimeFilter: f }),
  openHistoryDetail: (detail) =>
    set({ historyView: "detail", historyDetail: detail, historyDetailFilter: "all", historyDetailSearch: "" }),
  closeHistoryDetail: () =>
    set({ historyView: "list", historyDetail: null }),
  setHistoryDetailFilter: (f) => set({ historyDetailFilter: f }),
  setHistoryDetailSearch: (q) => set({ historyDetailSearch: q }),

  // Derived: time-filtered history list
  getFilteredHistory: () => {
    const { historyItems, historyTimeFilter } = get();
    if (historyTimeFilter === "all") return historyItems;

    const now = new Date();
    const cutoffMs = {
      today: 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
      "30d": 30 * 24 * 60 * 60 * 1000,
    }[historyTimeFilter];

    if (!cutoffMs) return historyItems;
    const cutoff = new Date(now.getTime() - cutoffMs);
    return historyItems.filter((item) => new Date(item.generated_at) >= cutoff);
  },

  // Derived: filtered + searched results inside history detail
  getHistoryDetailRows: () => {
    const { historyDetail, historyDetailFilter, historyDetailSearch } = get();
    if (!historyDetail) return [];
    let items = historyDetail.results;

    if (historyDetailFilter !== "all") {
      items = items.filter((r) => r.label === historyDetailFilter);
    }
    if (historyDetailSearch.trim()) {
      const q = historyDetailSearch.toLowerCase();
      items = items.filter(
        (r) =>
          r.log?.toLowerCase().includes(q) ||
          r.explanation?.toLowerCase().includes(q) ||
          r.recommendation?.toLowerCase().includes(q) ||
          r.label?.toLowerCase().includes(q) ||
          r.status?.toLowerCase().includes(q)
      );
    }
    return items;
  },

  // ── Filters / search (Analyze tab) ───────────────────────────────────────
  activeFilter: "all",
  setActiveFilter: (f) => set({ activeFilter: f }),
  searchQuery: "",
  setSearchQuery: (q) => set({ searchQuery: q }),

  // ── Loading / error ───────────────────────────────────────────────────────
  loading: false,
  setLoading: (v) => set({ loading: v }),
  error: null,
  setError: (e) => set({ error: e }),
  clearError: () => set({ error: null }),

  // ── Modal ─────────────────────────────────────────────────────────────────
  modalLog: null,
  openModal: (log) => set({ modalLog: log }),
  closeModal: () => set({ modalLog: null }),

  // ── Health ────────────────────────────────────────────────────────────────
  health: null,
  setHealth: (h) => set({ health: h }),

  // ── Derived: visible results in Analyze tab ───────────────────────────────
  getVisibleResults: () => {
    const { currentResult, activeFilter, searchQuery } = get();
    if (!currentResult) return [];
    let items = currentResult.results;

    if (activeFilter !== "all") {
      items = items.filter((r) => r.label === activeFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (r) =>
          r.log?.toLowerCase().includes(q) ||
          r.explanation?.toLowerCase().includes(q) ||
          r.recommendation?.toLowerCase().includes(q) ||
          r.label?.toLowerCase().includes(q) ||
          r.status?.toLowerCase().includes(q)
      );
    }
    return items;
  },
}));

export default useAnalysisStore;
