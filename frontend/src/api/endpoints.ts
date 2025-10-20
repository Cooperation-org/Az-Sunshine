import axiosClient from './axiosClient';
import type {
  Candidate,
  CandidateDetails,
  Entity,
  CrowdReport,
  CreateReportInput,
  DashboardStats,
  SpendingTrend,
  SpendingByCandidate,
  RecentActivity,
  SyncStatus,
  PaginatedResponse,
  FilterParams,
  PaginationParams,
  UploadResult,
  DuplicateRecord,
} from '../types';

import {
  mockCandidates,
  mockEntities,
  mockReports,
  mockDashboardStats,
  mockSpendingTrends,
  mockSpendingByCandidate,
  mockRecentActivity,
  mockSyncStatus,
  mockCandidateDetails,
} from './mockData';

// Use mock data if API is not available
const USE_MOCK = true;

// Helper function to simulate API delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Dashboard API
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    if (USE_MOCK) {
      await delay(500);
      return mockDashboardStats;
    }
    const response = await axiosClient.get('/api/dashboard/stats');
    return response.data;
  },

  getSpendingTrends: async (year?: string): Promise<SpendingTrend[]> => {
    if (USE_MOCK) {
      await delay(500);
      return mockSpendingTrends;
    }
    const response = await axiosClient.get('/api/dashboard/spending-trends', {
      params: { year },
    });
    return response.data;
  },

  getSpendingByCandidate: async (): Promise<SpendingByCandidate[]> => {
    if (USE_MOCK) {
      await delay(500);
      return mockSpendingByCandidate;
    }
    const response = await axiosClient.get('/api/dashboard/spending-by-candidate');
    return response.data;
  },

  getRecentActivity: async (): Promise<RecentActivity[]> => {
    if (USE_MOCK) {
      await delay(500);
      return mockRecentActivity;
    }
    const response = await axiosClient.get('/api/dashboard/recent-activity');
    return response.data;
  },
};

// Candidates API
export const candidatesApi = {
  getAll: async (
    params?: FilterParams & PaginationParams
  ): Promise<PaginatedResponse<Candidate>> => {
    if (USE_MOCK) {
      await delay(500);
      let filtered = [...mockCandidates];

      // Apply filters
      if (params?.search) {
        const search = params.search.toLowerCase();
        filtered = filtered.filter(
          (c) =>
            c.name.toLowerCase().includes(search) ||
            c.race.toLowerCase().includes(search) ||
            c.email.toLowerCase().includes(search)
        );
      }

      if (params?.status) {
        filtered = filtered.filter((c) => c.status === params.status);
      }

      // Apply pagination
      const page = params?.page || 1;
      const pageSize = params?.pageSize || 10;
      const start = (page - 1) * pageSize;
      const end = start + pageSize;

      return {
        data: filtered.slice(start, end),
        total: filtered.length,
        page,
        pageSize,
        totalPages: Math.ceil(filtered.length / pageSize),
      };
    }

    const response = await axiosClient.get('/api/candidates', { params });
    return response.data;
  },

  getById: async (id: string): Promise<CandidateDetails> => {
    if (USE_MOCK) {
      await delay(500);
      return mockCandidateDetails[id] || { ...mockCandidates[0], donors: [], spendingByType: { pac: 0, individual: 0, organization: 0 }, ieExpenditures: [] };
    }
    const response = await axiosClient.get(`/api/candidates/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<Candidate>): Promise<Candidate> => {
    if (USE_MOCK) {
      await delay(500);
      const candidate = mockCandidates.find((c) => c.id === id);
      return { ...candidate!, ...data };
    }
    const response = await axiosClient.patch(`/api/candidates/${id}`, data);
    return response.data;
  },

  updateStatus: async (
    id: string,
    status: Candidate['status']
  ): Promise<Candidate> => {
    return candidatesApi.update(id, { status });
  },

  togglePledge: async (id: string): Promise<Candidate> => {
    if (USE_MOCK) {
      await delay(500);
      const candidate = mockCandidates.find((c) => c.id === id);
      return { ...candidate!, hasPledged: !candidate!.hasPledged };
    }
    const response = await axiosClient.post(`/api/candidates/${id}/toggle-pledge`);
    return response.data;
  },
};

// Entities API
export const entitiesApi = {
  getAll: async (
    params?: FilterParams & PaginationParams
  ): Promise<PaginatedResponse<Entity>> => {
    if (USE_MOCK) {
      await delay(500);
      let filtered = [...mockEntities];

      // Apply filters
      if (params?.search) {
        const search = params.search.toLowerCase();
        filtered = filtered.filter((e) => e.name.toLowerCase().includes(search));
      }

      if (params?.type) {
        filtered = filtered.filter((e) => e.type === params.type);
      }

      // Apply pagination
      const page = params?.page || 1;
      const pageSize = params?.pageSize || 10;
      const start = (page - 1) * pageSize;
      const end = start + pageSize;

      return {
        data: filtered.slice(start, end),
        total: filtered.length,
        page,
        pageSize,
        totalPages: Math.ceil(filtered.length / pageSize),
      };
    }

    const response = await axiosClient.get('/api/entities', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Entity> => {
    if (USE_MOCK) {
      await delay(500);
      return mockEntities.find((e) => e.id === id) || mockEntities[0];
    }
    const response = await axiosClient.get(`/api/entities/${id}`);
    return response.data;
  },
};

// Reports API
export const reportsApi = {
  getAll: async (
    params?: FilterParams & PaginationParams
  ): Promise<PaginatedResponse<CrowdReport>> => {
    if (USE_MOCK) {
      await delay(500);
      let filtered = [...mockReports];

      // Apply filters
      if (params?.status) {
        filtered = filtered.filter((r) => r.status === params.status);
      }

      if (params?.search) {
        const search = params.search.toLowerCase();
        filtered = filtered.filter(
          (r) =>
            r.description.toLowerCase().includes(search) ||
            r.candidateName?.toLowerCase().includes(search)
        );
      }

      // Apply pagination
      const page = params?.page || 1;
      const pageSize = params?.pageSize || 10;
      const start = (page - 1) * pageSize;
      const end = start + pageSize;

      return {
        data: filtered.slice(start, end),
        total: filtered.length,
        page,
        pageSize,
        totalPages: Math.ceil(filtered.length / pageSize),
      };
    }

    const response = await axiosClient.get('/api/reports', { params });
    return response.data;
  },

  create: async (data: CreateReportInput): Promise<CrowdReport> => {
    if (USE_MOCK) {
      await delay(1000);
      const newReport: CrowdReport = {
        id: String(Date.now()),
        reporterName: data.reporterName,
        reporterEmail: data.reporterEmail,
        adType: data.adType as CrowdReport['adType'],
        description: data.description,
        link: data.link,
        candidateName: data.candidateName,
        status: 'pending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      mockReports.unshift(newReport);
      return newReport;
    }

    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value);
      }
    });

    const response = await axiosClient.post('/api/reports', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  updateStatus: async (
    id: string,
    status: CrowdReport['status']
  ): Promise<CrowdReport> => {
    if (USE_MOCK) {
      await delay(500);
      const report = mockReports.find((r) => r.id === id);
      return { ...report!, status, updatedAt: new Date().toISOString() };
    }
    const response = await axiosClient.patch(`/api/reports/${id}`, { status });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  uploadCSV: async (file: File, type: string): Promise<UploadResult> => {
    if (USE_MOCK) {
      await delay(2000);
      return {
        success: true,
        recordsProcessed: 150,
        duplicatesFound: 5,
        errors: [],
      };
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await axiosClient.post('/api/admin/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getSyncStatus: async (): Promise<SyncStatus> => {
    if (USE_MOCK) {
      await delay(500);
      return mockSyncStatus;
    }
    const response = await axiosClient.get('/api/admin/sync-status');
    return response.data;
  },

  getDuplicates: async (): Promise<DuplicateRecord[]> => {
    if (USE_MOCK) {
      await delay(500);
      return [];
    }
    const response = await axiosClient.get('/api/admin/duplicates');
    return response.data;
  },

  resolveDuplicate: async (
    id: string,
    action: 'keep_existing' | 'use_new' | 'merge'
  ): Promise<void> => {
    if (USE_MOCK) {
      await delay(500);
      return;
    }
    await axiosClient.post(`/api/admin/duplicates/${id}/resolve`, { action });
  },
};

