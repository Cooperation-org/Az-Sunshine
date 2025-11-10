import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1/";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 80000,
  headers: {
    'Content-Type': 'application/json',
  }
});

console.log('🔗 API Base URL:', API_BASE_URL);

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

//
// ==================== PHASE 1: SOI TRACKING ====================
//

// Scraping endpoints
export async function triggerScraping() {
  const res = await api.post("soi/scrape/trigger/");
  return res.data;
}

export async function getScrapingStatus() {
  const res = await api.get("soi/scrape/status/");
  return res.data;
}

export async function getScrapingHistory() {
  const res = await api.get("soi/scrape/history/");
  return res.data;
}

export async function getSOIDashboardStats() {
  const res = await api.get("soi/dashboard-stats/");
  return res.data;
}

// Candidate SOI endpoints
export async function getSOICandidates(params = {}) {
  const res = await api.get("candidate-soi/", { params });
  return res.data;
}

export async function getUncontactedCandidates() {
  const res = await api.get("candidate-soi/uncontacted/");
  return res.data;
}

export async function getPendingPledges() {
  const res = await api.get("candidate-soi/pending_pledges/");
  return res.data;
}

export async function getSOISummaryStats() {
  const res = await api.get("candidate-soi/summary_stats/");
  return res.data;
}

export async function markCandidateContacted(id, contactedBy) {
  const res = await api.post(`candidate-soi/${id}/mark_contacted/`, { contacted_by: contactedBy });
  return res.data;
}

export async function markPledgeReceived(id, notes = "") {
  const res = await api.post(`candidate-soi/${id}/mark_pledge_received/`, { notes });
  return res.data;
}

//
// ==================== CANDIDATES (COMMITTEES) ====================
//

export async function getCandidates(params = {}) {
  const res = await api.get("committees/", { 
    params: { ...params, candidates_only: 'true' } 
  });
  return res.data;
}

export async function getCandidate(id) {
  const res = await api.get(`committees/${id}/`);
  return res.data;
}

export async function getCandidateIESpending(id) {
  const res = await api.get(`committees/${id}/ie_spending_summary/`);
  return res.data;
}

export async function getCandidateIEByCommittee(id) {
  const res = await api.get(`committees/${id}/ie_spending_by_committee/`);
  return res.data;
}

export async function getCandidateIEDonors(id) {
  const res = await api.get(`committees/${id}/ie_donors/`);
  return res.data;
}

export async function getCandidateGrassrootsComparison(id, threshold = 5000) {
  const res = await api.get(`committees/${id}/grassroots_threshold/`, { params: { threshold } });
  return res.data;
}

//
// ==================== RACES ====================
//

export async function getRaceIESpending(officeId, cycleId, partyId = null) {
  const params = { office: officeId, cycle: cycleId };
  if (partyId) params.party = partyId;
  const res = await api.get("races/ie-spending/", { params });
  return res.data;
}

export async function getRaceTopDonors(officeId, cycleId, limit = 20) {
  const res = await api.get("races/top-donors/", { 
    params: { office: officeId, cycle: cycleId, limit } 
  });
  return res.data;
}

//
// ==================== OFFICES & CYCLES ====================
//

export async function getOffices() {
  const res = await api.get("offices/");
  return res.data;
}

export async function getCycles() {
  const res = await api.get("cycles/");
  return res.data;
}

//
// ==================== DASHBOARD ====================
//

export async function getDashboardSummary() {
  const res = await api.get("dashboard/summary/");
  return res.data;
}

//
// ==================== VALIDATION ====================
//

export async function validatePhase1Data() {
  const res = await api.get("validation/phase1/");
  return res.data;
}

//
// ==================== DONORS ====================
//

export async function getDonors(params = {}) {
  const res = await api.get("entities/", { params });
  return res.data;
}

export async function getTopDonors(limit = 50) {
  const res = await api.get("donors/top/", { params: { limit } });
  return res.data;
}

//
// ==================== EXPENDITURES ====================
//

export async function getExpenditures(params = {}) {
  const res = await api.get("expenditures/", { params });
  return res.data;
}

export async function getTopCommittees(limit = 10) {
  const res = await api.get("committees/top/", { params: { limit } });
  return res.data;
}

//
// ==================== DEFAULT EXPORT ====================
//

export default api;