import React, { useState, useEffect } from "react";
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
  Bell,
  ChevronRight,
  ChevronLeft,
  Filter
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import Preloader from "../components/Preloader";

// REAL API CALLS
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

// Scraping Modal
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

export default function SOIManagement() {
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [showScrapingModal, setShowScrapingModal] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setCurrentPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    loadData();
  }, [currentPage, activeTab, debouncedSearch]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const params = {
        page: currentPage,
        page_size: pageSize
      };

      if (activeTab === 'uncontacted') {
        params.status = 'uncontacted';
      } else if (activeTab === 'pending') {
        params.status = 'contacted';
      } else if (activeTab === 'pledged') {
        params.status = 'pledged';
      }

      if (debouncedSearch) {
        params.search = debouncedSearch;
      }

      const [candidatesData, statsData] = await Promise.all([
        getSOICandidates(params),
        getSOIDashboardStats()
      ]);
      
      const results = candidatesData?.results || (Array.isArray(candidatesData) ? candidatesData : []);
      const count = candidatesData?.count || results.length || 0;
      
      setCandidates(results);
      setStats(statsData);
      setTotalCount(count);
      setTotalPages(Math.ceil(count / pageSize));
      
    } catch (error) {
      console.error("Error loading data:", error);
      setCandidates([]);
      setStats({});
      setTotalCount(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setCurrentPage(1);
  };

  const handleMarkContacted = async (id) => {
    try {
      await markCandidateContacted(id);
      loadData();
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const handleMarkPledged = async (id) => {
    try {
      await markPledgeReceived(id);
      loadData();
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const getStatusBadge = (candidate) => {
    if (candidate.pledge_received) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
          <CheckCircle className="w-3 h-3" />
          Pledged
        </span>
      );
    }
    if (candidate.contacted) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold">
          <Clock className="w-3 h-3" />
          Pending
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
        <AlertCircle className="w-3 h-3" />
        New
      </span>
    );
  };

  // Show preloader on initial page load (same as original SOI implementation)
  if (loading && currentPage === 1) {
    return <Preloader message="Loading candidate data..." />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      {/* Main Content - Responsive: No left margin on mobile */}
      <main className="flex-1 lg:ml-0 min-w-0">
        {/* Header - Responsive */}
        <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-3 sm:py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 sticky top-0 z-10">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Arizona Sunshine</h1>
            <p className="text-xs sm:text-sm text-gray-500">Statement of Interest Tracking</p>
          </div>
          <div className="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
            <div className="relative flex-1 sm:flex-initial">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search candidates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full sm:w-64 lg:w-80 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm sm:text-base hover:border-gray-400"
              />
            </div>
            <button 
              className="p-2 rounded-lg bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 flex-shrink-0 hover:shadow-md active:scale-95 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5 text-white" />
            </button>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
          {/* Update Banner - Responsive: Stack on mobile */}
          <div className="bg-gradient-to-r bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] rounded-2xl shadow-xl overflow-hidden">
            <div className="p-4 sm:p-6 lg:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0">
              <div className="flex-1">
                <div className="flex items-center gap-2 sm:gap-3 mb-2">
                  <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                    <RefreshCw className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                  </div>
                  <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-white">Update Candidate Filings</h2>
                </div>
                <p className="text-purple-100 text-xs sm:text-sm ml-0 sm:ml-14">
                  Sync latest statements of interest from Arizona Secretary of State
                </p>
              </div>
              <button
                onClick={() => {
                  setScraping(true);
                  setShowScrapingModal(true);
                }}
                disabled={scraping}
                className="w-full sm:w-auto bg-white text-purple-700 px-6 sm:px-8 py-3 sm:py-4 rounded-xl text-sm sm:text-base font-semibold hover:bg-purple-50 transition-all shadow-lg flex items-center justify-center gap-2 sm:gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4 sm:w-5 sm:h-5" />
                {scraping ? "Updating..." : "Check for Updates"}
              </button>
            </div>
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
                  {stats.pending_pledge || 0}
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

          {/* Filter Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                <Filter className="w-5 h-5" />
                Filter Candidates
              </h3>
              <div className="flex gap-3 flex-wrap">
                {[
                  { id: "all", label: "All Candidates", count: stats?.total_candidates || 0, color: "purple" },
                  { id: "uncontacted", label: "Uncontacted", count: stats?.uncontacted || 0, color: "rose" },
                  { id: "pending", label: "Pending Pledge", count: stats?.pending_pledge || 0, color: "amber" },
                  { id: "pledged", label: "Pledged", count: stats?.pledged || 0, color: "emerald" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                      activeTab === tab.id
                        ? tab.color === "purple" ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md" :
                          tab.color === "rose" ? "bg-rose-600 text-white shadow-md" :
                          tab.color === "amber" ? "bg-amber-600 text-white shadow-md" :
                          "bg-emerald-600 text-white shadow-md"
                        : "bg-gray-50 text-gray-700 hover:bg-gray-100 hover:shadow-sm active:scale-95"
                    }`}
                  >
                    <span>{tab.label}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                      activeTab === tab.id ? "bg-white/20" : "bg-gray-200"
                    }`}>
                      {tab.count}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Candidates Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Candidate
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Office
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Contact Info
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {loading ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center">
                        <Loader className="w-8 h-8 animate-spin text-purple-600 mx-auto mb-2" />
                        <p className="text-gray-500 text-sm">Loading candidates...</p>
                      </td>
                    </tr>
                  ) : candidates.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-16 text-center">
                        <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                        <div className="text-lg font-semibold text-gray-900 mb-1">No candidates found</div>
                        <div className="text-sm text-gray-500">
                          {searchTerm ? "Try a different search term" : "Run an update to sync latest filings"}
                        </div>
                      </td>
                    </tr>
                  ) : (
                    candidates.map((candidate) => (
                      <tr key={candidate.id} className="hover:bg-purple-50/50 transition-colors duration-150">
                        <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                              {(candidate.name || candidate.candidate_name || '?').charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-gray-900">
                                {candidate.name || candidate.candidate_name || 'Unknown'}
                              </div>
                              {candidate.party && (
                                <div className="text-sm text-gray-500 flex items-center gap-1">
                                  {candidate.party}
                                </div>
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
                                className="px-3 py-1 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg text-sm hover:bg-purple-700 transition whitespace-nowrap"
                              >
                                Mark Contacted
                              </button>
                            )}
                            {candidate.contacted && !candidate.pledge_received && (
                              <button
                                onClick={() => handleMarkPledged(candidate.id)}
                                className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition whitespace-nowrap"
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
                  className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
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
                  className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

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
    </div>
  );
}