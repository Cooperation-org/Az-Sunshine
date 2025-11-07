// frontend/src/api/api.js
import axios from "axios";

// Use environment variable if available, otherwise use localhost for development
// Change to "http://167.172.30.134:8000/api/" when backend is running on remote server

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1/";


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
  // Use committees endpoint with candidates_only filter
  const res = await api.get("committees/", { 
    params: { ...params, candidates_only: 'true' } 
  });
  return res.data;
}

export async function getCandidate(id) {
  const res = await api.get(`committees/${id}/`);
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
  const res = await api.get("entities/", { params });
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

export async function getCandidateIESpending(id) {
  try {
    const res = await api.get(`committees/${id}/ie_spending_summary/`);
    return res.data;
  } catch (error) {
    console.error("Error fetching IE spending summary:", error);
    return null;
  }
}

export async function getCandidateIEByCommittee(id) {
  try {
    const res = await api.get(`committees/${id}/ie_spending_by_committee/`);
    return res.data;
  } catch (error) {
    console.error("Error fetching IE by committee:", error);
    return null;
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
    // Use dashboard/summary endpoint as metrics endpoint has issues
    const res = await api.get("dashboard/summary/");
    const data = res.data;
    return {
      total_expenditures: parseFloat(data.total_ie_spending || 0),
      num_candidates: data.candidate_committees || 0,
      num_expenditures: 0, // Will be populated from expenditures endpoint
      candidates: []
    };
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
