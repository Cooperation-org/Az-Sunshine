import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import {
  Play,
  CheckCircle,
  Clock,
  AlertCircle,
  Search,
  Mail,
  Phone,
  Loader,
  RefreshCw,
  Users,
  Target,
  Award,
  ChevronRight,
  ChevronLeft,
  Filter,
  CheckSquare,
  Square,
  X,
  User,
  Building,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { TableSkeleton, CardSkeleton, StatsGridSkeleton } from "../components/SkeletonLoader";
import ConfirmationModal from "../components/ConfirmationModal";
import { ToastContainer, useToast } from "../components/Toast";
import { 
  highlightText, 
  getRecentSearches, 
  saveRecentSearch, 
  clearRecentSearches,
  generateSearchSuggestions 
} from "../utils/searchUtils.jsx";

// ==================== PHASE 1: API CALLS ====================

const API_BASE_URL = "http://167.172.30.134/api/v1/";

const getSOICandidates = async (params) => {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.append('page', params.page);
  if (params.page_size) queryParams.append('page_size', params.page_size);
  if (params.status) queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  
  const response = await fetch(`${API_BASE_URL}soi/candidates/?${queryParams}`);
  const data = await response.json();
  return data;
};

const getSOIDashboardStats = async () => {
  const response = await fetch(`${API_BASE_URL}soi/dashboard-stats/`);
  const data = await response.json();
  return data;
};

const markCandidateContacted = async (id) => {
  const response = await fetch(`${API_BASE_URL}candidate-soi/${id}/mark_contacted/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  return response.json();
};

const markPledgeReceived = async (id) => {
  const response = await fetch(`${API_BASE_URL}candidate-soi/${id}/mark_pledge_received/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  return response.json();
};

const bulkMarkContacted = async (ids) => {
  const promises = ids.map(id => markCandidateContacted(id));
  return Promise.allSettled(promises);
};

const bulkMarkAcknowledged = async (ids) => {
  const promises = ids.map(id => markPledgeReceived(id));
  return Promise.allSettled(promises);
};

// ==================== SCRAPING MODAL COMPONENT ====================

function ScrapingModal({ isOpen, onClose, onComplete }) {
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen && status === 'idle') {
      startScraping();
    }
  }, [isOpen, status]);

  const startScraping = async () => {
    setStatus('running');
    setMessage('Connecting to Arizona Secretary of State...');

    try {
      const response = await fetch(`${API_BASE_URL}trigger-scrape/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (result.success) {
        setStatus('success');
        setMessage('Successfully synced candidate filings!');
        setTimeout(() => {
          onComplete();
          onClose();
        }, 2000);
      } else {
        setStatus('error');
        setMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(`Connection failed: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-8 transform transition-all">
        <div className="text-center">
          {status === 'running' && (
            <>
              <div className="relative w-20 h-20 mx-auto mb-6">
                <Loader className="w-20 h-20 animate-spin text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold mb-3 text-gray-900">Syncing Data</h3>
              <p className="text-gray-600">{message}</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="w-20 h-20 mx-auto mb-6 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-12 h-12 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold mb-3 text-gray-900">Success!</h3>
              <p className="text-gray-600">{message}</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="w-20 h-20 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-12 h-12 text-red-600" />
              </div>
              <h3 className="text-2xl font-bold mb-3 text-gray-900">Error</h3>
              <p className="text-gray-600 mb-6">{message}</p>
              <button
                onClick={onClose}
                className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium transition"
              >
                Close
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ==================== MAIN COMPONENT ====================

export default function SOIManagement() {
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  
  // Filtering
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchFilter, setSearchFilter] = useState("all");
  
  // Scraping
  const [showScrapingModal, setShowScrapingModal] = useState(false);
  const [scraping, setScraping] = useState(false);
  
  // Bulk actions
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingBulkAction, setPendingBulkAction] = useState(null);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  
  const { toasts, addToast, removeToast } = useToast();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Load data
  useEffect(() => {
    loadData();
  }, [currentPage, pageSize, statusFilter, debouncedSearch]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [candidatesData, statsData] = await Promise.all([
        getSOICandidates({
          page: currentPage,
          page_size: pageSize,
          status: statusFilter !== 'all' ? statusFilter : null,
          search: debouncedSearch || null,
        }),
        getSOIDashboardStats(),
      ]);

      setCandidates(candidatesData.results || []);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / pageSize));
      setStats(statsData);
    } catch (err) {
      setError('Failed to load data');
      addToast('Failed to load candidates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkContacted = async (id) => {
    try {
      await markCandidateContacted(id);
      addToast('Candidate marked as contacted', 'success');
      loadData();
    } catch (error) {
      addToast('Failed to update candidate', 'error');
    }
  };

  const handleMarkPledged = async (id) => {
    try {
      await markPledgeReceived(id);
      addToast('Pledge received marked', 'success');
      loadData();
    } catch (error) {
      addToast('Failed to update pledge status', 'error');
    }
  };

  const handleSelectCandidate = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedIds.size === candidates.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(candidates.map(c => c.id)));
    }
  };

  const handleBulkAction = (action) => {
    if (selectedIds.size === 0) {
      addToast('Please select candidates first', 'warning');
      return;
    }
    setPendingBulkAction(action);
    setShowConfirmModal(true);
  };

  const executeBulkAction = async () => {
    setBulkActionLoading(true);
    try {
      const ids = Array.from(selectedIds);
      if (pendingBulkAction === 'contacted') {
        await bulkMarkContacted(ids);
        addToast(`${ids.length} candidates marked as contacted`, 'success');
      } else if (pendingBulkAction === 'acknowledged') {
        await bulkMarkAcknowledged(ids);
        addToast(`${ids.length} pledges marked as received`, 'success');
      }
      setSelectedIds(new Set());
      loadData();
    } catch (error) {
      addToast('Bulk action failed', 'error');
    } finally {
      setBulkActionLoading(false);
      setShowConfirmModal(false);
      setPendingBulkAction(null);
    }
  };

  const getStatusBadge = (candidate) => {
    if (candidate.pledge_received) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
          <CheckCircle className="w-3.5 h-3.5" />
          Pledge Received
        </span>
      );
    } else if (candidate.contacted || candidate.contact_status === 'contacted' || candidate.contact_status === 'acknowledged') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
          <Clock className="w-3.5 h-3.5" />
          Contacted
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">
          <AlertCircle className="w-3.5 h-3.5" />
          New
        </span>
      );
    }
  };

  if (loading && !candidates.length) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Header />
          <div className="p-8 space-y-8">
            <StatsGridSkeleton count={4} />
            <TableSkeleton />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Header />
        <div className="p-8 space-y-8">
          {/* Page Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Statement of Interest Management
              </h1>
              <p className="text-gray-600 mt-1">
                Phase 1: Track SOI filings and manual outreach
              </p>
            </div>
            <button
              onClick={() => setShowScrapingModal(true)}
              disabled={scraping}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5" />
              {scraping ? "Scraping..." : "Run Scraper"}
            </button>
          </div>

          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-purple-50 rounded-xl">
                    <Users className="w-6 h-6 text-purple-600" />
                  </div>
                  <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded-full">
                    TOTAL
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stats.total_candidates || 0}
                </div>
                <div className="text-sm text-gray-600">Candidates Filed</div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-rose-50 rounded-xl">
                    <Target className="w-6 h-6 text-rose-600" />
                  </div>
                  <span className="text-xs font-medium text-rose-600 bg-rose-50 px-2 py-1 rounded-full">
                    ACTION
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stats.uncontacted || 0}
                </div>
                <div className="text-sm text-gray-600">Need Contact</div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-amber-50 rounded-xl">
                    <Clock className="w-6 h-6 text-amber-600" />
                  </div>
                  <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
                    WAITING
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stats.contacted || 0}
                </div>
                <div className="text-sm text-gray-600">Awaiting Pledge</div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-emerald-50 rounded-xl">
                    <Award className="w-6 h-6 text-emerald-600" />
                  </div>
                  <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                    SUCCESS
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">
                  {stats.pledged || 0}
                </div>
                <div className="text-sm text-gray-600">Pledges Received</div>
              </div>
            </div>
          )}

          {/* Filters & Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
              <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
                <div className="relative flex-1 sm:flex-initial sm:w-80">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search candidates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="uncontacted">Uncontacted</option>
                  <option value="contacted">Contacted</option>
                  <option value="acknowledged">Acknowledged</option>
                </select>
              </div>

              {selectedIds.size > 0 && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleBulkAction('contacted')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                  >
                    Mark {selectedIds.size} as Contacted
                  </button>
                  <button
                    onClick={() => handleBulkAction('acknowledged')}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium"
                  >
                    Mark {selectedIds.size} Pledge Received
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Candidates Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left">
                      <button
                        onClick={handleSelectAll}
                        className="flex items-center justify-center"
                      >
                        {selectedIds.size === candidates.length && candidates.length > 0 ? (
                          <CheckSquare className="w-5 h-5 text-purple-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Candidate
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Office
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Contact Info
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {candidates.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <AlertCircle className="w-12 h-12 text-gray-400" />
                          <p className="text-gray-600 font-medium">No candidates found</p>
                          <p className="text-sm text-gray-500">Try adjusting your filters or run the scraper</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    candidates.map((candidate) => (
                      <tr 
                        key={candidate.id} 
                        className={`hover:bg-purple-50/50 transition-colors duration-150 ${
                          selectedIds.has(candidate.id) ? "bg-purple-50" : ""
                        }`}
                      >
                        <td className="px-6 py-5">
                          <button
                            onClick={() => handleSelectCandidate(candidate.id)}
                            className="flex items-center justify-center"
                          >
                            {selectedIds.has(candidate.id) ? (
                              <CheckSquare className="w-5 h-5 text-purple-600" />
                            ) : (
                              <Square className="w-5 h-5 text-gray-400 hover:text-purple-400" />
                            )}
                          </button>
                        </td>
                        <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] flex items-center justify-center text-white font-semibold text-sm">
                              {(candidate.name || candidate.candidate_name || '?').charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-gray-900">
                                {candidate.name || candidate.candidate_name || 'Unknown'}
                              </div>
                              {candidate.party && (
                                <div className="text-sm text-gray-500">{candidate.party}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <div className="text-sm font-medium text-gray-900">
                            {candidate.office || 'Not specified'}
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          <div className="space-y-1">
                            {candidate.email && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Mail className="w-4 h-4 text-gray-400" />
                                <span className="truncate max-w-xs">{candidate.email}</span>
                              </div>
                            )}
                            {candidate.phone && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Phone className="w-4 h-4 text-gray-400" />
                                <span>{candidate.phone}</span>
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-5">
                          {getStatusBadge(candidate)}
                        </td>
                        <td className="px-6 py-5">
                          <div className="flex gap-2">
                            {!candidate.contacted && (
                              <button
                                onClick={() => handleMarkContacted(candidate.id)}
                                className="px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg text-sm hover:shadow-md transition whitespace-nowrap"
                              >
                                Mark Contacted
                              </button>
                            )}
                            {candidate.contacted && !candidate.pledge_received && (
                              <button
                                onClick={() => handleMarkPledged(candidate.id)}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition whitespace-nowrap"
                              >
                                Pledge Received
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Showing <span className="font-medium">{((currentPage - 1) * pageSize) + 1}</span> to{' '}
                <span className="font-medium">{Math.min(currentPage * pageSize, totalCount)}</span> of{' '}
                <span className="font-medium">{totalCount}</span> results
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let page;
                  if (totalPages <= 5) {
                    page = i + 1;
                  } else if (currentPage <= 3) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    page = totalPages - 4 + i;
                  } else {
                    page = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-10 h-10 rounded-lg font-medium transition ${
                        currentPage === page
                          ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Scraping Modal */}
      <ScrapingModal
        isOpen={showScrapingModal}
        onClose={() => {
          setShowScrapingModal(false);
          setScraping(false);
        }}
        onComplete={() => {
          setScraping(false);
          loadData();
        }}
      />

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={showConfirmModal}
        onClose={() => {
          setShowConfirmModal(false);
          setPendingBulkAction(null);
        }}
        onConfirm={executeBulkAction}
        title={
          pendingBulkAction === "contacted"
            ? "Mark as Contacted"
            : "Mark as Acknowledged"
        }
        message={
          pendingBulkAction === "contacted"
            ? `Mark ${selectedIds.size} candidate${selectedIds.size !== 1 ? "s" : ""} as contacted?`
            : `Mark ${selectedIds.size} pledge${selectedIds.size !== 1 ? "s" : ""} as received?`
        }
        confirmText={bulkActionLoading ? "Processing..." : "Confirm"}
        type="warning"
      />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}