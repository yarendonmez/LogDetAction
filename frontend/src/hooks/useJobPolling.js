import { useEffect, useRef } from "react";
import useAnalysisStore from "../store/analysisStore";
import { pollJob, cancelJob as cancelJobApi } from "../api/client";

const POLL_INTERVAL_MS = 1500;
const TERMINAL_STATUSES = new Set(["completed", "cancelled", "failed"]);

export function useJobPolling() {
  const jobId = useAnalysisStore((s) => s.jobId);
  const updateJobProgress = useAnalysisStore((s) => s.updateJobProgress);
  const clearJob = useAnalysisStore((s) => s.clearJob);
  const setCurrentResult = useAnalysisStore((s) => s.setCurrentResult);
  const setActiveFilter = useAnalysisStore((s) => s.setActiveFilter);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    async function tick() {
      try {
        const data = await pollJob(jobId);
        updateJobProgress(data);

        if (TERMINAL_STATUSES.has(data.status)) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      } catch {
        // Network hiccup — keep polling
      }
    }

    tick();
    timerRef.current = setInterval(tick, POLL_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [jobId]);

  async function stopJob() {
    if (!jobId) return;
    try {
      await cancelJobApi(jobId);
    } catch {
      // Ignore
    }
  }

  function acceptResults() {
    const s = useAnalysisStore.getState();
    if (!s.jobResults.length) return;

    // Build a result object compatible with the results dashboard
    setCurrentResult({
      analysis_id: s.jobAnalysisId ?? s.jobId,
      source_type: "job",
      source_name: s.jobSourceName,
      analysis_mode: s.jobAnalysisMode,
      generated_at: new Date().toISOString(),
      total_logs: s.jobResults.length,
      malicious_count: s.jobResults.filter((r) => r.label === "malicious").length,
      suspicious_count: s.jobResults.filter((r) => r.label === "suspicious").length,
      benign_count: s.jobResults.filter((r) => r.label === "benign").length,
      avg_classification_time_sec: s.jobAvgTimes?.classification ?? 0,
      avg_analysis_generation_time_sec: s.jobAvgTimes?.analysis ?? 0,
      avg_total_time_sec: s.jobAvgTimes?.total ?? 0,
      csv_download_url: s.jobCsvUrl ?? "",
      results: s.jobResults,
    });
    setActiveFilter("all");
    clearJob();
  }

  return { stopJob, acceptResults };
}
