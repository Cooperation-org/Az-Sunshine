// frontend/src/api/api.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
});

// --- Candidates ---
export async function getCandidates() {
  const res = await api.get("candidates/");
  return res.data;
}

export async function getCandidate(id) {
  const res = await api.get(`candidates/${id}/`);
  return res.data;
}

// --- Races ---
export async function getRaces() {
  const res = await api.get("races/");
  return res.data;
}

// --- Committees ---
export async function getCommittees(params = {}) {
  const res = await api.get("committees/", { params });
  return res.data;
}

// --- Donors ---
export async function getDonors(params = {}) {
  const res = await api.get("donors/", { params });
  return res.data;
}

// --- Expenditures ---
export async function getExpenditures(params = {}) {
  const res = await api.get("expenditures/", { params });
  return res.data;
}

// --- Aggregates / Top-level summaries ---
export async function getTopDonors() {
  const res = await api.get("donors/?ordering=-total_contribution");
  return res.data;
}

export async function getTopCommittees() {
  const res = await api.get("committees/?ordering=-total");
  return res.data;
}

export async function getSupportOpposeByCandidate(params = {}) {
  const res = await api.get("expenditures/", { params });
  const rows = res.data.results || res.data;
  const grouped = {};
  rows.forEach((r) => {
    const type = r.support_oppose || "Unknown";
    grouped[type] = (grouped[type] || 0) + Number(r.amount || 0);
  });
  return Object.entries(grouped).map(([support_oppose, total]) => ({
    support_oppose,
    total,
  }));
}

// --- Metrics (backend-provided) ---
export async function getMetrics() {
  const res = await api.get("metrics/");
  return res.data;
}

export default api;
