import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://167.172.30.134/api/v1/";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 80000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Set to true if you need cookies/sessions
});

console.log('🔗 API Base URL:', API_BASE_URL);

// Request interceptor for debugging
api.interceptors.request.use(
  config => {
    console.log(`📤 ${config.method.toUpperCase()} ${config.url}`, config.params || config.data);
    return config;
  },
  error => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  response => {
    console.log(`✅ Response from ${response.config.url}:`, response.data);
    return response;
  },
  error => {
    console.error('❌ API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

//
// ==================== NEW: WEBHOOK-BASED SOI SCRAPING ====================
//

/**
 * Trigger scraping on home machine via webhook
 * POST /api/v1/soi/trigger-local/
 * 
 * This is the NEW preferred method that:
 * 1. Sends trigger to home machine
 * 2. Home machine runs scraper
 * 3. Progress updates sent via webhook
 * 4. Frontend polls for status
 */
export async function triggerWebhookScraping() {
  try {
    const res = await api.post("soi/trigger-local/");
    return res.data;
  } catch (error) {
    console.error("Failed to trigger webhook scraping:", error);
    throw error;
  }
}

/**
 * Get webhook scraping status (for real-time updates)
 * GET /api/v1/soi/webhook/status/
 * 
 * Frontend should poll this endpoint every 2-3 seconds
 * during active scraping to get real-time progress
 */
export async function getWebhookScrapingStatus() {
  try {
    const res = await api.get("soi/webhook/status/");
    return res.data;
  } catch (error) {
    console.error("Failed to get webhook status:", error);
    throw error;
  }
}

/**
 * Get webhook scraping history
 * GET /api/v1/soi/webhook/history/
 */
export async function getWebhookScrapingHistory() {
  try {
    const res = await api.get("soi/webhook/history/");
    return res.data;
  } catch (error) {
    console.error("Failed to get webhook history:", error);
    throw error;
  }
}

//
// ==================== LEGACY: DIRECT SOI SCRAPING (VPS) ====================
// These endpoints run scraping directly on VPS (not recommended due to Cloudflare)
//

/**
 * LEGACY: Trigger SOI scraping directly on VPS
 * POST /api/v1/soi/scrape/trigger/
 * 
 * NOTE: This may fail due to Cloudflare blocking datacenter IPs
 * Use triggerWebhookScraping() instead for production
 */
export async function triggerScraping() {
  try {
    const res = await api.post("soi/scrape/trigger/");
    return res.data;
  } catch (error) {
    console.error("Failed to trigger scraping:", error);
    throw error;
  }
}

/**
 * LEGACY: Get current scraping status (direct VPS scraping)
 * GET /api/v1/soi/scrape/status/
 */
export async function getScrapingStatus() {
  try {
    const res = await api.get("soi/scrape/status/");
    return res.data;
  } catch (error) {
    console.error("Failed to get scraping status:", error);
    throw error;
  }
}

/**
 * LEGACY: Get scraping history (direct VPS scraping)
 * GET /api/v1/soi/scrape/history/
 */
export async function getScrapingHistory() {
  try {
    const res = await api.get("soi/scrape/history/");
    return res.data;
  } catch (error) {
    console.error("Failed to get scraping history:", error);
    throw error;
  }
}

//
// ==================== SOI DASHBOARD & CANDIDATES ====================
//

/**
 * Get SOI dashboard statistics
 * GET /api/v1/soi/dashboard-stats/
 */
export async function getSOIDashboardStats() {
  try {
    const res = await api.get("soi/dashboard-stats/");
    return res.data;
  } catch (error) {
    console.error("Failed to get SOI dashboard stats:", error);
    throw error;
  }
}

/**
 * Get SOI candidates list
 * GET /api/v1/soi/candidates/
 */
export async function getSOICandidates(params = {}) {
  try {
    console.log("📡 Fetching SOI candidates with params:", params);
    const res = await api.get("soi/candidates/", { params });
    
    console.log("📥 Raw response:", res);
    console.log("📥 Response data type:", Array.isArray(res.data) ? "Array" : typeof res.data);
    
    // Handle both array response and paginated response
    if (Array.isArray(res.data)) {
      console.log("✅ Received array response with", res.data.length, "candidates");
      return res.data;
    }
    
    // Fallback to paginated response format
    const data = res.data.results || res.data;
    console.log("✅ Received paginated/object response with", Array.isArray(data) ? data.length : 0, "candidates");
    return Array.isArray(data) ? data : [];
    
  } catch (error) {
    console.error("❌ Failed to fetch SOI candidates:", error);
    console.error("Error details:", {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    throw error;
  }
}

/**
 * Get uncontacted candidates
 * GET /api/v1/candidate-soi/uncontacted/
 */
export async function getUncontactedCandidates() {
  try {
    const res = await api.get("candidate-soi/uncontacted/");
    return res.data.results || res.data;
  } catch (error) {
    console.error("Failed to get uncontacted candidates:", error);
    throw error;
  }
}

/**
 * Get pending pledges
 * GET /api/v1/candidate-soi/pending_pledges/
 */
export async function getPendingPledges() {
  try {
    const res = await api.get("candidate-soi/pending_pledges/");
    return res.data.results || res.data;
  } catch (error) {
    console.error("Failed to get pending pledges:", error);
    throw error;
  }
}

/**
 * Get SOI summary statistics
 * GET /api/v1/candidate-soi/summary_stats/
 */
export async function getSOISummaryStats() {
  try {
    const res = await api.get("candidate-soi/summary_stats/");
    return res.data;
  } catch (error) {
    console.error("Failed to get SOI summary stats:", error);
    throw error;
  }
}

/**
 * Mark candidate as contacted
 * POST /api/v1/candidate-soi/{id}/mark_contacted/
 */
export async function markCandidateContacted(id, contactedBy = "") {
  try {
    const res = await api.post(`candidate-soi/${id}/mark_contacted/`, { 
      contacted_by: contactedBy 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to mark candidate as contacted:", error);
    throw error;
  }
}

/**
 * Mark pledge as received
 * POST /api/v1/candidate-soi/{id}/mark_pledge_received/
 */
export async function markPledgeReceived(id, notes = "") {
  try {
    const res = await api.post(`candidate-soi/${id}/mark_pledge_received/`, { 
      notes 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to mark pledge received:", error);
    throw error;
  }
}

//
// ==================== CANDIDATES (COMMITTEES) ====================
//

/**
 * Get candidates list (committee data with candidates_only filter)
 * GET /api/v1/committees/?candidates_only=true
 */
export async function getCandidates(params = {}) {
  try {
    const res = await api.get("committees/", { 
      params: { ...params, candidates_only: 'true' } 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to get candidates:", error);
    throw error;
  }
}

/**
 * Get single candidate details
 * GET /api/v1/committees/{id}/
 */
export async function getCandidate(id) {
  try {
    const res = await api.get(`committees/${id}/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get candidate details:", error);
    throw error;
  }
}

/**
 * Get candidate IE spending summary
 * GET /api/v1/committees/{id}/ie_spending_summary/
 */
export async function getCandidateIESpending(id) {
  try {
    const res = await api.get(`committees/${id}/ie_spending_summary/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get candidate IE spending:", error);
    throw error;
  }
}

/**
 * Get candidate IE spending by committee
 * GET /api/v1/committees/{id}/ie_spending_by_committee/
 */
export async function getCandidateIEByCommittee(id) {
  try {
    const res = await api.get(`committees/${id}/ie_spending_by_committee/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get candidate IE by committee:", error);
    throw error;
  }
}

/**
 * Get candidate IE donors
 * GET /api/v1/committees/{id}/ie_donors/
 */
export async function getCandidateIEDonors(id) {
  try {
    const res = await api.get(`committees/${id}/ie_donors/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get candidate IE donors:", error);
    throw error;
  }
}

/**
 * Get candidate grassroots threshold comparison
 * GET /api/v1/committees/{id}/grassroots_threshold/?threshold={threshold}
 */
export async function getCandidateGrassrootsComparison(id, threshold = 5000) {
  try {
    const res = await api.get(`committees/${id}/grassroots_threshold/`, { 
      params: { threshold } 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to get grassroots comparison:", error);
    throw error;
  }
}

/**
 * Get candidate financial summary
 * GET /api/v1/committees/{id}/financial_summary/
 */
export async function getCandidateFinancialSummary(id) {
  try {
    const res = await api.get(`committees/${id}/financial_summary/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get financial summary:", error);
    throw error;
  }
}

//
// ==================== RACES ====================
//

/**
 * Get race IE spending
 * GET /api/v1/races/ie-spending/?office={officeId}&cycle={cycleId}&party={partyId}
 */
export async function getRaceIESpending(officeId, cycleId, partyId = null) {
  try {
    const params = { office: officeId, cycle: cycleId };
    if (partyId) params.party = partyId;
    const res = await api.get("races/ie-spending/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get race IE spending:", error);
    throw error;
  }
}

/**
 * Get race top donors
 * GET /api/v1/races/top-donors/?office={officeId}&cycle={cycleId}&limit={limit}
 */
export async function getRaceTopDonors(officeId, cycleId, limit = 20) {
  try {
    const res = await api.get("races/top-donors/", { 
      params: { office: officeId, cycle: cycleId, limit } 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to get race top donors:", error);
    throw error;
  }
}

//
// ==================== OFFICES & CYCLES ====================
//

/**
 * Get all offices
 * GET /api/v1/offices/
 */
export async function getOffices() {
  try {
    const res = await api.get("offices/");
    return res.data;
  } catch (error) {
    console.error("Failed to get offices:", error);
    throw error;
  }
}

/**
 * Get all cycles
 * GET /api/v1/cycles/
 */
export async function getCycles() {
  try {
    const res = await api.get("cycles/");
    return res.data;
  } catch (error) {
    console.error("Failed to get cycles:", error);
    throw error;
  }
}

/**
 * Get all parties
 * GET /api/v1/parties/
 */
export async function getParties() {
  try {
    const res = await api.get("parties/");
    return res.data;
  } catch (error) {
    console.error("Failed to get parties:", error);
    throw error;
  }
}

//
// ==================== DASHBOARD ====================
//

/**
 * Get dashboard summary
 * GET /api/v1/dashboard/summary/
 */
export async function getDashboardSummary() {
  try {
    const res = await api.get("dashboard/summary/");
    return res.data;
  } catch (error) {
    console.error("Failed to get dashboard summary:", error);
    throw error;
  }
}

/**
 * Get metrics (frontend adapter)
 * GET /api/v1/metrics/
 */
export async function getMetrics() {
  try {
    const res = await api.get("metrics/");
    return res.data;
  } catch (error) {
    console.error("Failed to get metrics:", error);
    throw error;
  }
}

//
// ==================== VALIDATION ====================
//

/**
 * Validate Phase 1 data
 * GET /api/v1/validation/phase1/
 */
export async function validatePhase1Data() {
  try {
    const res = await api.get("validation/phase1/");
    return res.data;
  } catch (error) {
    console.error("Failed to validate phase1 data:", error);
    throw error;
  }
}

//
// ==================== DONORS ====================
//

/**
 * Get donors (entities)
 * GET /api/v1/entities/
 */
export async function getDonors(params = {}) {
  try {
    const res = await api.get("entities/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get donors:", error);
    throw error;
  }
}

/**
 * Get top donors
 * GET /api/v1/donors/top/?limit={limit}
 */
export async function getTopDonors(limit = 50) {
  try {
    const res = await api.get("donors/top/", { params: { limit } });
    return res.data;
  } catch (error) {
    console.error("Failed to get top donors:", error);
    throw error;
  }
}

/**
 * Get donors list (frontend adapter)
 * GET /api/v1/donors/
 */
export async function getDonorsList(params = {}) {
  try {
    const res = await api.get("donors/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get donors list:", error);
    throw error;
  }
}

/**
 * Get entity details
 * GET /api/v1/entities/{id}/
 */
export async function getEntity(id) {
  try {
    const res = await api.get(`entities/${id}/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get entity details:", error);
    throw error;
  }
}

/**
 * Get entity IE impact by candidate
 * GET /api/v1/entities/{id}/ie_impact_by_candidate/
 */
export async function getEntityIEImpact(id) {
  try {
    const res = await api.get(`entities/${id}/ie_impact_by_candidate/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get entity IE impact:", error);
    throw error;
  }
}

/**
 * Get entity contribution summary
 * GET /api/v1/entities/{id}/contribution_summary/
 */
export async function getEntityContributions(id) {
  try {
    const res = await api.get(`entities/${id}/contribution_summary/`);
    return res.data;
  } catch (error) {
    console.error("Failed to get entity contributions:", error);
    throw error;
  }
}

//
// ==================== EXPENDITURES & TRANSACTIONS ====================
//

/**
 * Get expenditures (IE transactions)
 * GET /api/v1/expenditures/
 */
export async function getExpenditures(params = {}) {
  try {
    const res = await api.get("expenditures/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get expenditures:", error);
    throw error;
  }
}

/**
 * Get transactions
 * GET /api/v1/transactions/
 */
export async function getTransactions(params = {}) {
  try {
    const res = await api.get("transactions/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get transactions:", error);
    throw error;
  }
}

/**
 * Get IE transactions
 * GET /api/v1/transactions/ie_transactions/
 */
export async function getIETransactions(params = {}) {
  try {
    const res = await api.get("transactions/ie_transactions/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get IE transactions:", error);
    throw error;
  }
}

/**
 * Get large contributions
 * GET /api/v1/transactions/large_contributions/?threshold={threshold}
 */
export async function getLargeContributions(threshold = 1000, params = {}) {
  try {
    const res = await api.get("transactions/large_contributions/", { 
      params: { ...params, threshold } 
    });
    return res.data;
  } catch (error) {
    console.error("Failed to get large contributions:", error);
    throw error;
  }
}

//
// ==================== COMMITTEES ====================
//

/**
 * Get top committees by IE spending
 * GET /api/v1/committees/top/?limit={limit}
 */
export async function getTopCommittees(limit = 10) {
  try {
    const res = await api.get("committees/top/", { params: { limit } });
    return res.data;
  } catch (error) {
    console.error("Failed to get top committees:", error);
    throw error;
  }
}

/**
 * Get committees list
 * GET /api/v1/committees/
 */
export async function getCommittees(params = {}) {
  try {
    const res = await api.get("committees/", { params });
    return res.data;
  } catch (error) {
    console.error("Failed to get committees:", error);
    throw error;
  }
}

//
// ==================== UTILITY FUNCTIONS ====================
//

/**
 * Check API health
 */
export async function checkAPIHealth() {
  try {
    const res = await api.get("");
    return { healthy: true, data: res.data };
  } catch (error) {
    return { healthy: false, error: error.message };
  }
}

/**
 * Format currency for display
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return "$0.00";
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Format date for display
 */
export function formatDate(dateString) {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

//
// ==================== DEFAULT EXPORT ====================
//

export default api;