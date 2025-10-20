import type {
  Candidate,
  CandidateDetails,
  Entity,
  CrowdReport,
  DashboardStats,
  SpendingTrend,
  SpendingByCandidate,
  RecentActivity,
  SyncStatus,
  IEExpenditure,
  Donor,
} from '../types';

// Mock Candidates
export const mockCandidates: Candidate[] = [
  {
    id: '1',
    name: 'John Smith',
    race: 'State Senate District 10',
    email: 'john.smith@example.com',
    phone: '(602) 555-0100',
    status: 'contacted',
    totalSpending: 125000,
    hasPledged: false,
    createdAt: '2024-01-15T00:00:00Z',
    updatedAt: '2024-06-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    race: 'State House District 15',
    email: 'sarah.johnson@example.com',
    phone: '(602) 555-0101',
    status: 'pledged',
    totalSpending: 85000,
    hasPledged: true,
    createdAt: '2024-01-20T00:00:00Z',
    updatedAt: '2024-05-15T00:00:00Z',
  },
  {
    id: '3',
    name: 'Michael Davis',
    race: 'State Senate District 5',
    email: 'michael.davis@example.com',
    status: 'uncontacted',
    totalSpending: 210000,
    hasPledged: false,
    createdAt: '2024-02-01T00:00:00Z',
    updatedAt: '2024-02-01T00:00:00Z',
  },
  {
    id: '4',
    name: 'Emily Martinez',
    race: 'State House District 22',
    email: 'emily.martinez@example.com',
    phone: '(602) 555-0103',
    status: 'contacted',
    totalSpending: 95000,
    hasPledged: false,
    createdAt: '2024-01-10T00:00:00Z',
    updatedAt: '2024-05-20T00:00:00Z',
  },
  {
    id: '5',
    name: 'Robert Wilson',
    race: 'State Senate District 12',
    email: 'robert.wilson@example.com',
    status: 'declined',
    totalSpending: 175000,
    hasPledged: false,
    createdAt: '2024-02-15T00:00:00Z',
    updatedAt: '2024-06-10T00:00:00Z',
  },
];

// Mock Entities
export const mockEntities: Entity[] = [
  {
    id: '1',
    name: 'Arizona Future PAC',
    type: 'PAC',
    totalContributions: 450000,
    numberOfContributions: 12,
    topRecipient: 'Michael Davis',
    address: '123 Capitol Ave, Phoenix, AZ',
  },
  {
    id: '2',
    name: 'Citizens for Progress',
    type: 'PAC',
    totalContributions: 320000,
    numberOfContributions: 8,
    topRecipient: 'John Smith',
    address: '456 Democracy Blvd, Tucson, AZ',
  },
  {
    id: '3',
    name: 'David Thompson',
    type: 'Individual',
    totalContributions: 85000,
    numberOfContributions: 5,
    topRecipient: 'Sarah Johnson',
  },
  {
    id: '4',
    name: 'Arizona Business Coalition',
    type: 'Organization',
    totalContributions: 280000,
    numberOfContributions: 15,
    topRecipient: 'Robert Wilson',
    address: '789 Commerce Way, Scottsdale, AZ',
  },
  {
    id: '5',
    name: 'Jennifer Lee',
    type: 'Individual',
    totalContributions: 125000,
    numberOfContributions: 10,
    topRecipient: 'Michael Davis',
  },
];

// Mock Reports
export const mockReports: CrowdReport[] = [
  {
    id: '1',
    reporterName: 'Jane Doe',
    reporterEmail: 'jane.doe@example.com',
    adType: 'TV',
    description: 'Attack ad against John Smith during evening news',
    link: 'https://youtube.com/example1',
    candidateName: 'John Smith',
    status: 'approved',
    createdAt: '2024-06-01T10:30:00Z',
    updatedAt: '2024-06-02T09:00:00Z',
  },
  {
    id: '2',
    reporterName: 'Bob Anderson',
    reporterEmail: 'bob.anderson@example.com',
    adType: 'Digital',
    description: 'Facebook ads supporting Sarah Johnson',
    link: 'https://facebook.com/ad-example',
    candidateName: 'Sarah Johnson',
    status: 'pending',
    createdAt: '2024-06-10T14:20:00Z',
    updatedAt: '2024-06-10T14:20:00Z',
  },
  {
    id: '3',
    reporterEmail: 'anonymous@example.com',
    adType: 'Billboard',
    description: 'Large billboard on I-10 opposing Michael Davis',
    candidateName: 'Michael Davis',
    status: 'approved',
    createdAt: '2024-06-05T08:15:00Z',
    updatedAt: '2024-06-06T11:30:00Z',
  },
  {
    id: '4',
    reporterName: 'Lisa Chen',
    reporterEmail: 'lisa.chen@example.com',
    adType: 'Mail',
    description: 'Negative mailer received about Emily Martinez',
    candidateName: 'Emily Martinez',
    status: 'rejected',
    createdAt: '2024-06-08T16:45:00Z',
    updatedAt: '2024-06-09T10:00:00Z',
  },
];

// Mock Dashboard Data
export const mockDashboardStats: DashboardStats = {
  totalIESpending: 1260000,
  totalCandidates: 5,
  topDonor: {
    name: 'Arizona Future PAC',
    amount: 450000,
  },
  totalReports: 4,
};

export const mockSpendingTrends: SpendingTrend[] = [
  { date: '2024-01', month: 'Jan', amount: 125000 },
  { date: '2024-02', month: 'Feb', amount: 180000 },
  { date: '2024-03', month: 'Mar', amount: 220000 },
  { date: '2024-04', month: 'Apr', amount: 310000 },
  { date: '2024-05', month: 'May', amount: 280000 },
  { date: '2024-06', month: 'Jun', amount: 145000 },
];

export const mockSpendingByCandidate: SpendingByCandidate[] = [
  { candidateName: 'Michael Davis', amount: 210000, race: 'SD-5' },
  { candidateName: 'Robert Wilson', amount: 175000, race: 'SD-12' },
  { candidateName: 'John Smith', amount: 125000, race: 'SD-10' },
  { candidateName: 'Emily Martinez', amount: 95000, race: 'HD-22' },
  { candidateName: 'Sarah Johnson', amount: 85000, race: 'HD-15' },
];

export const mockRecentActivity: RecentActivity[] = [
  {
    id: '1',
    type: 'expenditure',
    description: 'Arizona Future PAC spent $45,000 supporting Michael Davis',
    amount: 45000,
    date: '2024-06-10T00:00:00Z',
  },
  {
    id: '2',
    type: 'report',
    description: 'New crowd report submitted for John Smith',
    date: '2024-06-10T14:20:00Z',
  },
  {
    id: '3',
    type: 'candidate',
    description: 'Sarah Johnson pledged to support transparency',
    date: '2024-06-09T00:00:00Z',
  },
  {
    id: '4',
    type: 'expenditure',
    description: 'Citizens for Progress spent $32,000 opposing Robert Wilson',
    amount: 32000,
    date: '2024-06-08T00:00:00Z',
  },
];

// Mock Sync Status
export const mockSyncStatus: SyncStatus = {
  lastUpdate: '2024-06-11T08:00:00Z',
  totalRecords: 1547,
  candidateCount: 5,
  entityCount: 5,
  expenditureCount: 1533,
  reportCount: 4,
};

// Mock Candidate Details
export const mockCandidateDetails: Record<string, CandidateDetails> = {
  '1': {
    ...mockCandidates[0],
    donors: [
      {
        id: 'd1',
        name: 'Arizona Future PAC',
        type: 'PAC',
        amount: 50000,
        date: '2024-03-15T00:00:00Z',
        candidateId: '1',
        candidateName: 'John Smith',
      },
      {
        id: 'd2',
        name: 'Citizens for Progress',
        type: 'PAC',
        amount: 40000,
        date: '2024-04-20T00:00:00Z',
        candidateId: '1',
        candidateName: 'John Smith',
      },
      {
        id: 'd3',
        name: 'David Thompson',
        type: 'Individual',
        amount: 35000,
        date: '2024-05-10T00:00:00Z',
        candidateId: '1',
        candidateName: 'John Smith',
      },
    ],
    spendingByType: {
      pac: 90000,
      individual: 35000,
      organization: 0,
    },
    ieExpenditures: [
      {
        id: 'ie1',
        amount: 50000,
        spender: 'Arizona Future PAC',
        spenderType: 'PAC',
        candidateId: '1',
        candidateName: 'John Smith',
        supportOppose: 'Support',
        date: '2024-03-15T00:00:00Z',
        purpose: 'Television advertising',
      },
    ],
  },
};

