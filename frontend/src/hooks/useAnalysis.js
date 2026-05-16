import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useAnalysisStore from "../store/analysisStore";
import { startFileJob, startTextJob } from "../api/client";

export function useAnalysis() {
  const { t } = useTranslation();
  const setLoading = useAnalysisStore((s) => s.setLoading);
  const setError = useAnalysisStore((s) => s.setError);
  const setJob = useAnalysisStore((s) => s.setJob);

  function mapError(err) {
    if (!err.response) return t("errors.NETWORK_ERROR");
    const data = err.response.data;
    if (data?.code && t(`errors.${data.code}`) !== `errors.${data.code}`) {
      return t(`errors.${data.code}`);
    }
    return data?.message || t("errors.UNKNOWN_ERROR");
  }

  const runFile = useCallback(async (file, mode) => {
    setLoading(true);
    setError(null);
    try {
      const data = await startFileJob(file, mode);
      // data = { job_id, total }
      setJob({
        job_id: data.job_id,
        status: "running",
        total: data.total,
        processed: 0,
        results: [],
        analysis_mode: mode,
        source_name: file.name,
      });
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const runText = useCallback(async (text, mode) => {
    setLoading(true);
    setError(null);
    try {
      const data = await startTextJob(text, mode);
      setJob({
        job_id: data.job_id,
        status: "running",
        total: data.total,
        processed: 0,
        results: [],
        analysis_mode: mode,
        source_name: "manual_input",
      });
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  return { runFile, runText };
}
