// frontend/src/api/api.js
import axios from "axios";

// Use environment variable if available, otherwise use localhost for development
// Change to "http://167.172.30.134:8000/api/" when backend is running on remote server

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://167.172.30.134/api/";


const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

console.log('🔗 API Base URL:', API_BASE_URL);

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// --- Candidates ---
export async function getCandidates(params = {}) {
  const res = await api.get("candidates/", { params });
  return res.data;
}

export async function getCandidate(id) {
  const res = await api.get(`candidates/${id}/`);
  return res.data;
}

// --- Races ---
export async function getRaces(params = {}) {
  const res = await api.get("races/", { params });
  return res.data;
}

// --- Committees ---
export async function getCommittees(params = {}) {
  const res = await api.get("committees/", { params });
  return res.data;
}

export async function getTopCommittees() {
  try {
    const res = await api.get("committees/top/");
    return res.data;
  } catch (error) {
    console.error("Error fetching top committees:", error);
    return [];
  }
}

// --- Donors ---
export async function getDonors(params = {}) {
  const res = await api.get("donors/", { params });
  return res.data;
}

export async function getTopDonors() {
  try {
    const res = await api.get("donors/top/");
    return res.data;
  } catch (error) {
    console.error("Error fetching top donors:", error);
    return [];
  }
}

// --- Expenditures ---
export async function getExpenditures(params = {}) {
  const res = await api.get("expenditures/", { params });
  return res.data;
}

export async function getSupportOpposeByCandidate() {
  try {
    const res = await api.get("expenditures/support_oppose_by_candidate/");
    return res.data;
  } catch (error) {
    console.error("Error fetching support/oppose data:", error);
    return [];
  }
}

export async function getExpendituresByCandidate() {
  try {
    const res = await api.get("expenditures/summary_by_candidate/");
    return res.data;
  } catch (error) {
    console.error("Error fetching expenditures by candidate:", error);
    return [];
  }
}

// --- Contributions ---
export async function getContributions(params = {}) {
  const res = await api.get("contributions/", { params });
  return res.data;
}

// --- Metrics (backend-provided) ---
export async function getMetrics() {
  try {
    const res = await api.get("metrics/");
    return res.data;
  } catch (error) {
    console.error("Error fetching metrics:", error);
    return {
      total_expenditures: 0,
      num_candidates: 0,
      num_expenditures: 0,
      candidates: []
    };
  }
}

export default api;
