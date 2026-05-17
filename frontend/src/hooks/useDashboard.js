import { useState, useCallback } from "react";
import { fetchDashboardSummary } from "../api/client";

export function useDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboardSummary();
      setData(result);
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, refresh };
}
