import { useState, useCallback, useEffect, useRef } from "react";
import {
  startLiveMonitor,
  stopLiveMonitor,
  fetchLiveStatus,
  fetchLiveEvents,
} from "../api/client";

const POLL_MS = 3000;

export function useLiveMonitor() {
  const [status, setStatus] = useState(null);       // raw state from backend
  const [events, setEvents] = useState([]);
  const [eventsFilter, setEventsFilter] = useState("all");
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const isRunning = status?.running === true;

  const refreshStatus = useCallback(async () => {
    try {
      const s = await fetchLiveStatus();
      setStatus(s);
    } catch {
      // ignore status poll errors silently
    }
  }, []);

  const refreshEvents = useCallback(async (filter = eventsFilter) => {
    try {
      const ev = await fetchLiveEvents(100, filter);
      setEvents(ev);
    } catch {
      // ignore
    }
  }, [eventsFilter]);

  // Poll while running
  useEffect(() => {
    if (isRunning) {
      pollRef.current = setInterval(async () => {
        await refreshStatus();
        await refreshEvents(eventsFilter);
      }, POLL_MS);
    } else {
      clearInterval(pollRef.current);
    }
    return () => clearInterval(pollRef.current);
  }, [isRunning, refreshStatus, refreshEvents, eventsFilter]);

  // Initial load
  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const startMonitor = useCallback(async (mode) => {
    setActionLoading(true);
    setError(null);
    try {
      const s = await startLiveMonitor(mode);
      if (s?.error) {
        setError(s.message || s.code);
      } else {
        setStatus(s);
      }
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Failed to start monitor.");
    } finally {
      setActionLoading(false);
    }
  }, []);

  const stopMonitor = useCallback(async () => {
    setActionLoading(true);
    setError(null);
    try {
      const s = await stopLiveMonitor();
      if (s?.error) {
        setError(s.message || s.code);
      } else {
        setStatus(s);
        // Final refresh of events after stopping
        await refreshEvents(eventsFilter);
      }
    } catch (err) {
      setError(err?.response?.data?.message || err.message || "Failed to stop monitor.");
    } finally {
      setActionLoading(false);
    }
  }, [refreshEvents, eventsFilter]);

  const changeFilter = useCallback((f) => {
    setEventsFilter(f);
    refreshEvents(f);
  }, [refreshEvents]);

  return {
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
  };
}
