import { useCallback, useEffect, useRef, useState } from "react";
import { feedbackAPI } from "../utils/api.js";

const REFRESH_MS = 30_000;

/**
 * Owner dashboard data with 30s auto-refresh.
 */
export default function useOwnerData() {
  const [summary, setSummary] = useState(null);
  const [flagged, setFlagged] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forbidden, setForbidden] = useState(false);
  const mountedRef = useRef(true);

  const load = useCallback(async () => {
    try {
      const [summaryData, flaggedData] = await Promise.all([
        feedbackAPI.getSummary(),
        feedbackAPI.getFlagged(),
      ]);
      if (!mountedRef.current) return;
      setSummary(summaryData);
      setFlagged(flaggedData.items || []);
      setError(null);
      setForbidden(false);
    } catch (err) {
      if (!mountedRef.current) return;
      if (err.response?.status === 403 || err.response?.status === 401) {
        setForbidden(true);
        setError("You do not have permission to view the owner dashboard.");
      } else {
        setError(
          err.response?.data?.detail || err.message || "Failed to load dashboard data"
        );
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [load]);

  const toggleFlag = useCallback(
    async (feedbackId) => {
      await feedbackAPI.toggleFlag(feedbackId);
      await load();
    },
    [load]
  );

  return {
    summary,
    flagged,
    isLoading,
    error,
    forbidden,
    refresh: load,
    toggleFlag,
  };
}
