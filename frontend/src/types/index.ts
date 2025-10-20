// Candidate Types
export interface Candidate {
  id: string;
  name: string;
  race: string;
  email: string;
  phone?: string;
  status: 'uncontacted' | 'contacted' | 'pledged' | 'declined';
  totalSpending: number;
  hasPledged: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CandidateDetails extends Candidate {
  donors: Donor[];
  spendingByType: {
    pac: number;
    individual: number;
    organization: number;
  };
  ieExpenditures: IEExpenditure[];
}

// Entity Types
export interface Entity {
  id: string;
  name: string;
  type: 'PAC' | 'Individual' | 'Organization';
  totalContributions: number;
  numberOfContributions: number;
  topRecipient?: string;
  address?: string;
}

// Donor Types
export interface Donor {
  id: string;
  name: string;
  type: 'PAC' | 'Individual' | 'Organization';
  amount: number;
  date: string;
  candidateId: string;
  candidateName: string;
}

// IE Expenditure Types
export interface IEExpenditure {
  id: string;
  amount: number;
  spender: string;
  spenderType: 'PAC' | 'Individual' | 'Organization';
  candidateId: string;
  candidateName: string;
  supportOppose: 'Support' | 'Oppose';
  date: string;
  purpose?: string;
}

// Report Types
export interface CrowdReport {
  id: string;
  reporterName?: string;
  reporterEmail?: string;
  adType: 'TV' | 'Radio' | 'Digital' | 'Print' | 'Billboard' | 'Mail' | 'Other';
  description: string;
  link?: string;
  imageUrl?: string;
  candidateName?: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  updatedAt: string;
}

export interface CreateReportInput {
  reporterName?: string;
  reporterEmail?: string;
  adType: string;
  description: string;
  link?: string;
  image?: File;
  candidateName?: string;
}

// Dashboard Types
export interface DashboardStats {
  totalIESpending: number;
  totalCandidates: number;
  topDonor: {
    name: string;
    amount: number;
  };
  totalReports: number;
}

export interface SpendingTrend {
  date: string;
  amount: number;
  month?: string;
}

export interface SpendingByCandidate {
  candidateName: string;
  amount: number;
  race: string;
}

export interface RecentActivity {
  id: string;
  type: 'expenditure' | 'report' | 'candidate';
  description: string;
  amount?: number;
  date: string;
}

// Admin Types
export interface UploadResult {
  success: boolean;
  recordsProcessed: number;
  duplicatesFound: number;
  errors?: string[];
}

export interface DuplicateRecord {
  id: string;
  type: 'candidate' | 'entity' | 'expenditure';
  existingRecord: any;
  newRecord: any;
  matchFields: string[];
}

export interface SyncStatus {
  lastUpdate: string;
  totalRecords: number;
  candidateCount: number;
  entityCount: number;
  expenditureCount: number;
  reportCount: number;
}

// Filter/Pagination Types
export interface PaginationParams {
  page: number;
  pageSize: number;
}

export interface FilterParams {
  search?: string;
  year?: string;
  type?: string;
  status?: string;
  race?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Auth Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'viewer';
}

export interface AuthResponse {
  user: User;
  token: string;
}

// Theme Types
export type ThemeMode = 'light' | 'dark';

