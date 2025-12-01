// frontend/src/api/api.js
/**
 * API Client for Arizona Sunshine Transparency Project
 * Centralized API calls with error handling and token management
 */

import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
      
      // Handle 401 Unauthorized
      if (error.response.status === 401) {
        localStorage.removeItem('auth_token');
        // Optional: redirect to login
        // window.location.href = '/login';
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ==================== HELPER FUNCTIONS ====================

/**
 * Handle API errors with user-friendly messages
 */
function handleError(error, defaultMessage = 'An error occurred') {
  if (error.response?.data?.detail) {
    throw new Error(error.response.data.detail);
  } else if (error.response?.data?.message) {
    throw new Error(error.response.data.message);
  } else if (error.message) {
    throw new Error(error.message);
  } else {
    throw new Error(defaultMessage);
  }
}

/**
 * Build query string from params object
 */
function buildQueryString(params) {
  const query = new URLSearchParams();
  Object.keys(params).forEach(key => {
    if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
      query.append(key, params[key]);
    }
  });
  return query.toString();
}


// ==================== DASHBOARD ENDPOINTS ====================

/**
 * Get dashboard summary statistics
 */
export async function getDashboardSummary() {
  try {
    const res = await api.get('/dashboard/summary-optimized/');
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load dashboard summary');
  }
}

/**
 * Get dashboard charts data
 */
export async function getDashboardCharts() {
  try {
    const res = await api.get('/dashboard/charts-data/');
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load dashboard charts');
  }
}

/**
 * Get recent expenditures
 */
export async function getRecentExpenditures(limit = 10) {
  try {
    const res = await api.get(`/dashboard/recent-expenditures/?limit=${limit}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load recent expenditures');
  }
}


// ==================== CANDIDATE ENDPOINTS ====================

/**
 * Get all candidates with filters
 */
export async function getCandidates(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/candidates/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load candidates');
  }
}

/**
 * Get single candidate by ID
 */
export async function getCandidateById(candidateId) {
  try {
    const res = await api.get(`/committees/${candidateId}/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load candidate details');
  }
}

/**
 * Get candidate IE spending breakdown
 */
export async function getCandidateIESpending(candidateId) {
  try {
    const res = await api.get(`/committees/${candidateId}/ie_spending/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load candidate IE spending');
  }
}

/**
 * Get top candidates by IE spending
 */
export async function getTopCandidatesByIE(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/committees/top_by_ie/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load top candidates');
  }
}


// ==================== COMMITTEE ENDPOINTS ====================

/**
 * Get all committees
 */
export async function getCommittees(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/committees/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load committees');
  }
}

/**
 * Get committee by ID
 */
export async function getCommitteeById(committeeId) {
  try {
    const res = await api.get(`/committees/${committeeId}/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load committee details');
  }
}

/**
 * Get top IE committees
 */
export async function getTopCommittees(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/committees/top/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load top committees');
  }
}


// ==================== DONOR ENDPOINTS ====================

/**
 * Get all donors
 */
export async function getDonors(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/donors/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load donors');
  }
}

/**
 * Get top donors
 */
export async function getTopDonors(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/donors/top/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load top donors');
  }
}


// ==================== EXPENDITURE ENDPOINTS ====================

/**
 * Get expenditures with filters
 */
export async function getExpenditures(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/expenditures/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load expenditures');
  }
}


// ==================== TRANSACTION ENDPOINTS ====================

/**
 * Get transactions
 */
export async function getTransactions(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/transactions/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load transactions');
  }
}


// ==================== RACE ANALYSIS ENDPOINTS ====================

/**
 * Get IE spending by race
 */
export async function getRaceIESpending(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/races/ie-spending/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load race IE spending');
  }
}

/**
 * Get top donors in race
 */
export async function getRaceTopDonors(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/races/top-donors/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load race top donors');
  }
}

/**
 * Get money flow for Sankey diagram
 */
export async function getMoneyFlow(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/races/money-flow/?${queryString}`);
    
    // If endpoint doesn't exist yet, use getRaceIESpending as fallback
    if (res.status === 404) {
      const ieData = await getRaceIESpending(params);
      const donorsData = await getRaceTopDonors(params);
      
      return {
        candidates: ieData.results || ieData,
        top_donors: donorsData.results || donorsData,
      };
    }
    
    return res.data;
  } catch (error) {
    // Fallback to combining multiple endpoints
    try {
      const ieData = await getRaceIESpending(params);
      const donorsData = await getRaceTopDonors(params);
      
      return {
        candidates: ieData.results || ieData,
        top_donors: donorsData.results || donorsData,
      };
    } catch (fallbackError) {
      handleError(error, 'Failed to load money flow data');
    }
  }
}


// ==================== OFFICE & CYCLE ENDPOINTS ====================

/**
 * Get all offices
 */
export async function getOffices() {
  try {
    const res = await api.get('/offices/');
    return res.data.results || res.data;
  } catch (error) {
    handleError(error, 'Failed to load offices');
  }
}

/**
 * Get all election cycles
 */
export async function getCycles() {
  try {
    const res = await api.get('/cycles/');
    return res.data.results || res.data;
  } catch (error) {
    handleError(error, 'Failed to load cycles');
  }
}

/**
 * Get all parties
 */
export async function getParties() {
  try {
    const res = await api.get('/parties/');
    return res.data.results || res.data;
  } catch (error) {
    handleError(error, 'Failed to load parties');
  }
}


// ==================== SOI (STATEMENT OF INTEREST) ENDPOINTS ====================

/**
 * Get all SOI candidates
 */
export async function getSOICandidates(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/candidate-soi/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to load SOI candidates');
  }
}

/**
 * Mark candidate as contacted
 */
export async function markCandidateContacted(candidateId) {
  try {
    const res = await api.post(`/candidate-soi/${candidateId}/mark_contacted/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to mark candidate as contacted');
  }
}

/**
 * Mark pledge received
 */
export async function markPledgeReceived(candidateId) {
  try {
    const res = await api.post(`/candidate-soi/${candidateId}/mark_pledge_received/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to mark pledge received');
  }
}

/**
 * Bulk mark candidates as contacted
 */
export async function bulkMarkContacted(candidateIds) {
  try {
    const res = await api.post('/candidate-soi/bulk_mark_contacted/', {
      candidate_ids: candidateIds,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to bulk mark candidates as contacted');
  }
}

/**
 * Bulk mark pledges received
 */
export async function bulkMarkPledgeReceived(candidateIds) {
  try {
    const res = await api.post('/candidate-soi/bulk_mark_pledge_received/', {
      candidate_ids: candidateIds,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to bulk mark pledges received');
  }
}

/**
 * Trigger SOI scraper
 */
export async function triggerSOIScraper() {
  try {
    const res = await api.post('/candidate-soi/trigger_scraper/');
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to trigger SOI scraper');
  }
}


// ==================== EMAIL CAMPAIGN ENDPOINTS ====================

/**
 * Get email statistics
 */
export async function getEmailStatistics(dateFrom = null, dateTo = null) {
  try {
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    
    const queryString = buildQueryString(params);
    const res = await api.get(`/email/statistics/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to get email statistics');
  }
}

/**
 * Send single email
 */
export async function sendSingleEmail(candidateId, templateId, customSubject = null, customBody = null) {
  try {
    const res = await api.post('/email/send-single/', {
      candidate_id: candidateId,
      template_id: templateId,
      subject: customSubject,
      body: customBody,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to send email');
  }
}

/**
 * Send bulk emails
 */
export async function sendBulkEmails(candidateIds, templateId, customSubject = null, customBody = null) {
  try {
    const res = await api.post('/email/send-bulk/', {
      candidate_ids: candidateIds,
      template_id: templateId,
      subject: customSubject,
      body: customBody,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to send bulk emails');
  }
}

/**
 * Get email templates
 */
export async function getEmailTemplates(category = null) {
  try {
    const params = {};
    if (category) params.category = category;
    
    const queryString = buildQueryString(params);
    const res = await api.get(`/email-templates/?${queryString}`);
    return res.data.results || res.data;
  } catch (error) {
    handleError(error, 'Failed to get email templates');
  }
}

/**
 * Create email template
 */
export async function createEmailTemplate(templateData) {
  try {
    const res = await api.post('/email-templates/', templateData);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to create email template');
  }
}

/**
 * Update email template
 */
export async function updateEmailTemplate(templateId, templateData) {
  try {
    const res = await api.put(`/email-templates/${templateId}/`, templateData);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to update email template');
  }
}

/**
 * Delete email template
 */
export async function deleteEmailTemplate(templateId) {
  try {
    const res = await api.delete(`/email-templates/${templateId}/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to delete email template');
  }
}

/**
 * Get email campaigns
 */
export async function getEmailCampaigns(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/email-campaigns/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to get email campaigns');
  }
}

/**
 * Create email campaign
 */
export async function createEmailCampaign(campaignData) {
  try {
    const res = await api.post('/email-campaigns/', campaignData);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to create email campaign');
  }
}

/**
 * Send email campaign
 */
export async function sendEmailCampaign(campaignId) {
  try {
    const res = await api.post(`/email-campaigns/${campaignId}/send/`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to send email campaign');
  }
}

/**
 * Get email logs
 */
export async function getEmailLogs(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/email-logs/?${queryString}`);
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to get email logs');
  }
}


// ==================== DATA VALIDATION ENDPOINTS ====================

/**
 * Validate Phase 1 data
 */
export async function validatePhase1Data() {
  try {
    const res = await api.get('/validation/phase1/');
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to validate Phase 1 data');
  }
}

/**
 * Find duplicate entities
 */
export async function findDuplicateEntities() {
  try {
    const res = await api.get('/validation/find-duplicates/');
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to find duplicate entities');
  }
}

/**
 * Merge duplicate entities
 */
export async function mergeDuplicateEntities(primaryId, duplicateIds) {
  try {
    const res = await api.post('/validation/merge-entities/', {
      primary_id: primaryId,
      duplicate_ids: duplicateIds,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to merge entities');
  }
}


// ==================== SCRAPER ENDPOINTS ====================

/**
 * Trigger scraper
 */
export async function triggerScraper(scraperType = 'all') {
  try {
    const res = await api.post('/trigger-scrape/', {
      scraper_type: scraperType,
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to trigger scraper');
  }
}

/**
 * Upload scraped data
 */
export async function uploadScrapedData(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await api.post('/upload-scraped/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  } catch (error) {
    handleError(error, 'Failed to upload scraped data');
  }
}


// ==================== EXPORT FUNCTIONS ====================

/**
 * Export candidates to CSV
 */
export async function exportCandidatesCSV(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/candidates/export/?${queryString}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `candidates_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    handleError(error, 'Failed to export candidates');
  }
}

/**
 * Export donors to CSV
 */
export async function exportDonorsCSV(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/donors/export/?${queryString}`, {
      responseType: 'blob',
    });
    
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `donors_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    handleError(error, 'Failed to export donors');
  }
}

/**
 * Export expenditures to CSV
 */
export async function exportExpendituresCSV(params = {}) {
  try {
    const queryString = buildQueryString(params);
    const res = await api.get(`/expenditures/export/?${queryString}`, {
      responseType: 'blob',
    });
    
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `expenditures_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  } catch (error) {
    handleError(error, 'Failed to export expenditures');
  }
}


// Export the api instance for custom requests
export { api };

// Default export
export default api;