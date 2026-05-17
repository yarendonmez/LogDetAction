import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 600000,
});

// ── Legacy full-wait endpoints (kept as fallback) ─────────────────────────────
export async function analyzeFile(file, analysisMode) {
  const form = new FormData();
  form.append("file", file);
  form.append("analysis_mode", analysisMode);
  const res = await client.post("/analyze/file", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function analyzeText(text, analysisMode) {
  const res = await client.post("/analyze/text", { text, analysis_mode: analysisMode });
  return res.data;
}

// ── Job-based endpoints ───────────────────────────────────────────────────────
export async function startFileJob(file, analysisMode) {
  const form = new FormData();
  form.append("file", file);
  form.append("analysis_mode", analysisMode);
  const res = await client.post("/jobs/file", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data; // { job_id, total }
}

export async function startTextJob(text, analysisMode) {
  const res = await client.post("/jobs/text", {
    text,
    analysis_mode: analysisMode,
  });
  return res.data; // { job_id, total }
}

export async function pollJob(jobId) {
  const res = await client.get(`/jobs/${jobId}`);
  return res.data;
}

export async function cancelJob(jobId) {
  const res = await client.post(`/jobs/${jobId}/cancel`);
  return res.data;
}

// ── Results ───────────────────────────────────────────────────────────────────
export async function fetchResults() {
  const res = await client.get("/results");
  return res.data;
}

export async function fetchResultById(analysisId) {
  const res = await client.get(`/results/${analysisId}`);
  return res.data;
}

export async function checkHealth() {
  const res = await client.get("/health");
  return res.data;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export async function fetchDashboardSummary() {
  const res = await client.get("/dashboard/summary");
  return res.data;
}

// ── Live monitor ──────────────────────────────────────────────────────────────
export async function startLiveMonitor(analysisMode = "combined") {
  const res = await client.post("/live/start", { analysis_mode: analysisMode });
  return res.data;
}

export async function stopLiveMonitor() {
  const res = await client.post("/live/stop");
  return res.data;
}

export async function fetchLiveStatus() {
  const res = await client.get("/live/status");
  return res.data;
}

export async function fetchLiveEvents(limit = 50, label = "all") {
  const res = await client.get("/live/events", { params: { limit, label } });
  return res.data;
}

export default client;
