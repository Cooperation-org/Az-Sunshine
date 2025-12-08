/**
 * Admin API Services for Phase 1 Features
 * Handles CSV imports, county scrapers, AZ SOS automation, and SeeTheMoney (FREE!)
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1/';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for long-running operations
});

/**
 * Data Import API
 */
export const importAPI = {
  /**
   * Upload and import CSV file
   * @param {File} file - CSV file to upload
   * @param {string} source - Source identifier
   * @param {boolean} dryRun - Dry run mode
   * @returns {Promise} Import result with statistics
   */
  uploadCSV: async (file, source = 'web_upload', dryRun = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', source);
    formData.append('dry_run', dryRun);

    const response = await api.post('/admin/imports/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * Get import history
   * @returns {Promise} Array of import records
   */
  getHistory: async () => {
    const response = await api.get('/admin/imports/history/');
    return response.data;
  },
};

/**
 * County Scraper API
 */
export const scraperAPI = {
  /**
   * Run county scraper
   * @param {string} county - County name (maricopa|pima|tucson|all)
   * @param {number} year - Year to scrape
   * @param {boolean} headless - Run browser in headless mode
   * @returns {Promise} Scraper results
   */
  runScraper: async (county = 'all', year = null, headless = true) => {
    const response = await api.post('/admin/scrapers/run/', {
      county,
      year,
      headless,
    });

    return response.data;
  },

  /**
   * Get latest scraper results
   * @returns {Promise} Array of recent scraper results
   */
  getResults: async () => {
    const response = await api.get('/admin/scrapers/results/');
    return response.data;
  },
};

/**
 * AZ Secretary of State API
 */
export const sosAPI = {
  /**
   * Download database from AZ SOS
   * @param {number} year - Year to download
   * @param {number} quarter - Quarter (1-4)
   * @param {boolean} purchase - Complete purchase
   * @param {boolean} headless - Run browser in headless mode
   * @returns {Promise} Download result
   */
  download: async (year = null, quarter = null, purchase = false, headless = true) => {
    const response = await api.post('/admin/sos/download/', {
      year,
      quarter,
      purchase,
      headless,
    });

    return response.data;
  },

  /**
   * Download and import data from AZ SOS
   * @param {number} year - Year to sync
   * @param {number} quarter - Quarter (1-4)
   * @param {boolean} headless - Run browser in headless mode
   * @returns {Promise} Sync result
   */
  sync: async (year = null, quarter = null, headless = true) => {
    const response = await api.post('/admin/sos/sync/', {
      year,
      quarter,
      headless,
    });

    return response.data;
  },
};

/**
 * SeeTheMoney.az.gov API (FREE alternative!)
 */
export const seeTheMoneyAPI = {
  /**
   * Download FREE data from SeeTheMoney
   * @param {number} year - Year to download
   * @param {string} entityType - Entity type (Candidate|PAC|Party|All)
   * @param {boolean} headless - Run browser in headless mode
   * @returns {Promise} Download result
   */
  download: async (year = null, entityType = 'Candidate', headless = true) => {
    const response = await api.post('/admin/seethemoney/download/', {
      year,
      entity_type: entityType,
      headless,
    });

    return response.data;
  },

  /**
   * Download and auto-import FREE data from SeeTheMoney
   * @param {number} year - Year to sync
   * @param {string} entityType - Entity type (Candidate|PAC|Party|All)
   * @param {boolean} headless - Run browser in headless mode
   * @returns {Promise} Sync result
   */
  sync: async (year = null, entityType = 'Candidate', headless = true) => {
    const response = await api.post('/admin/seethemoney/sync/', {
      year,
      entity_type: entityType,
      headless,
    });

    return response.data;
  },
};

/**
 * Error handler for admin API calls
 * @param {Error} error - Axios error object
 * @returns {object} Formatted error object
 */
export const handleAdminError = (error) => {
  if (error.response) {
    // Server responded with error
    return {
      status: 'error',
      message: error.response.data.error || 'Server error occurred',
      details: error.response.data,
    };
  } else if (error.request) {
    // Request made but no response
    return {
      status: 'error',
      message: 'Network error - server did not respond',
      details: null,
    };
  } else {
    // Something else happened
    return {
      status: 'error',
      message: error.message || 'Unknown error occurred',
      details: null,
    };
  }
};

export default {
  import: importAPI,
  scraper: scraperAPI,
  sos: sosAPI,
  seeTheMoney: seeTheMoneyAPI,
  handleError: handleAdminError,
};
