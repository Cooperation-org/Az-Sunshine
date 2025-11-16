import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  CheckCircle,
  Clock,
  AlertCircle,
  Search,
  Mail,
  Phone,
  X,
  Loader,
  RefreshCw,
  Users,
  Target,
  Award,
  Bell,
  ChevronRight
} from "lucide-react";

// ✅ REAL API IMPORTS - Connected to your Django backend
import {
  triggerWebhookScraping,
  getWebhookScrapingStatus,
  getSOICandidates,
  getSOIDashboardStats,
  markCandidateContacted,
  markPledgeReceived,
} from "../api/api";

import Sidebar from "../components/Sidebar";

// Scraping Modal with Real-Time Webhook Updates
function ScrapingModal({ isOpen, onClose }) {
  const [status, setStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    if (isOpen && !isPolling) {
      startScraping();
    }
    
    // Cleanup on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [isOpen]);

  const startScraping = async () => {
    try {
      setIsPolling(true);
      
      // ✅ Trigger scraping on home machine via Django VPS
      console.log("🚀 Triggering webhook scraping...");
      const result = await triggerWebhookScraping();
      
      setStatus({
        status: 'triggered',
        progress: 0,
        current_step: 'Triggering home scraper...',
        logs: ['✅ Scraping triggered successfully', 'Waiting for home machine response...']
      });
      
      // ✅ Start polling for real-time updates every 2 seconds
      pollIntervalRef.current = setInterval(async () => {
        try {
          console.log("📊 Polling for status update...");
          const currentStatus = await getWebhookScrapingStatus();
          
          console.log("Status update:", currentStatus);
          setStatus(currentStatus);
          
          // Stop polling if completed or error
          if (currentStatus.status === 'completed' || currentStatus.status === 'error') {
            console.log("✅ Scraping finished, stopping poll");
            clearInterval(pollIntervalRef.current);
            setIsPolling(false);
          }
        } catch (error) {
          console.error('Polling error:', error);
          // Don't stop polling on network errors, just log them
        }
      }, 2000);
      
    } catch (error) {
      console.error("❌ Failed to trigger scraping:", error);
      setStatus({
        status: 'error',
        error: error.response?.data?.error || error.message || 'Failed to trigger scraping',
        logs: [`❌ Error: ${error.response?.data?.error || error.message}`]
      });
      setIsPolling(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
      case 'triggered':
        return 'bg-gradient-to-r from-purple-500 to-purple-600';
      case 'completed':
        return 'bg-gradient-to-r from-green-500 to-green-600';
      case 'error':
        return 'bg-gradient-to-r from-red-500 to-red-600';
      default:
        return 'bg-gray-500';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        
        <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {status?.status === 'running' || status?.status === 'triggered' || isPolling ? (
                <Loader className="w-6 h-6 animate-spin" />
              ) : status?.status === 'completed' ? (
                <CheckCircle className="w-6 h-6" />
              ) : status?.status === 'error' ? (
                <AlertCircle className="w-6 h-6" />
              ) : (
                <RefreshCw className="w-6 h-6" />
              )}
              <h2 className="text-xl sm:text-2xl font-bold">SOI Data Scraping</h2>
            </div>

            {/* <button
              onClick={onClose}
              className="hover:bg-white/20 p-2 rounded-lg transition"
              disabled={status?.status === 'running' || status?.status === 'triggered'}
            >
              <X className="w-5 h-5" />
            </button> */}

            <button
              onClick={async () => {
                setScraping(true);
                try {
                  setShowScrapingModal(true);
                  await triggerWebhookScraping();
                } catch (err) {
                  console.error(err);
                  alert("Failed to trigger scraping");
                } finally {
                  setScraping(false);
                }
              }}
              disabled={scraping}
              className="bg-white text-purple-700 px-8 py-4 rounded-xl font-semibold hover:bg-purple-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-3 disabled:opacity-50"
            >
              <Play className="w-5 h-5" />
              {scraping ? "Scraping..." : "Scrape Data Now!"}
            </button>

            </div>
          </div>

          
        {status && (
          <div className="p-6">
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700">
                  {status.current_step || 'Initializing...'}
                </span>
                <span className="text-sm font-semibold text-gray-700">
                  {Math.round(status.progress || 0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${getStatusColor(status.status)}`}
                  style={{ width: `${status.progress || 0}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            {status.stats && Object.keys(status.stats).length > 0 && (
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.total_candidates || status.stats.total || 0}
                  </div>
                  <div className="text-xs text-gray-600">Total</div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.created || 0}
                  </div>
                  <div className="text-xs text-gray-600">Created</div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.updated || 0}
                  </div>
                  <div className="text-xs text-gray-600">Updated</div>
                </div>
              </div>
            )}

            {/* Console Logs */}
            {status.logs && status.logs.length > 0 && (
              <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
                <div className="font-mono text-xs text-green-400 space-y-1">
                  {status.logs.map((log, idx) => (
                    <div key={idx} className="leading-relaxed">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {status.status === 'completed' && (
              <div className="mt-4 flex gap-3">
                <button
                  onClick={onClose}
                  className="flex-1 bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:via-purple-800 hover:to-purple-900 transition"
                >
                  View Candidates
                </button>
              </div>
            )}

            {status.status === 'error' && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-red-900">Scraping Failed</div>
                    <div className="text-sm text-red-700">{status.error}</div>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="mt-3 w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 transition"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Main Component - Connected to Real Django Backend
export default function SOIManagement() {
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fetchingData, setFetchingData] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showScrapingModal, setShowScrapingModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    loadData();
  }, [currentPage]);

  const loadData = async () => {
    try {
      setLoading(true);
      setFetchingData(true);
      
      console.log("📡 Loading SOI data from Django backend...");
      
      // ✅ Fetch real data from Django API
      const [candidatesData, statsData] = await Promise.all([
        getSOICandidates({ page: currentPage, page_size: pageSize }),
        getSOIDashboardStats(),
      ]);
      
      console.log("✅ Received candidates:", candidatesData);
      console.log("✅ Received stats:", statsData);
      
      const candidatesArray = Array.isArray(candidatesData) 
        ? candidatesData 
        : (candidatesData?.results || candidatesData || []);
      
      setCandidates(candidatesArray);
      setStats(statsData || {});
      setTotalCount(candidatesData?.count || candidatesArray.length || 0);
      setTotalPages(Math.ceil((candidatesData?.count || candidatesArray.length || 0) / pageSize));
      
    } catch (error) {
      console.error("❌ Error loading data:", error);
      setCandidates([]);
      setStats({});
      setTotalCount(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
      setFetchingData(false);
    }
  };

  const handleMarkContacted = async (id) => {
    try {
      console.log(`📞 Marking candidate ${id} as contacted...`);
      await markCandidateContacted(id);
      console.log("✅ Successfully marked as contacted");
      loadData(); // Reload to get fresh data
    } catch (error) {
      console.error("❌ Error marking contacted:", error);
      alert("Failed to mark candidate as contacted. Please try again.");
    }
  };

  const handleMarkPledged = async (id) => {
    try {
      console.log(`✅ Marking candidate ${id} pledge as received...`);
      await markPledgeReceived(id);
      console.log("✅ Successfully marked pledge as received");
      loadData(); // Reload to get fresh data
    } catch (error) {
      console.error("❌ Error marking pledged:", error);
      alert("Failed to mark pledge as received. Please try again.");
    }
  };

  const filteredCandidates = (Array.isArray(candidates) ? candidates : []).filter((c) => {
    const matchesSearch = c.name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (activeTab === "uncontacted") return matchesSearch && !c.contacted;
    if (activeTab === "pending") return matchesSearch && c.contacted && !c.pledge_received;
    if (activeTab === "pledged") return matchesSearch && c.pledge_received;
    return matchesSearch;
  });

  const getStatusBadge = (candidate) => {
    if (candidate.pledge_received) {
      return (
        <span className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
          <CheckCircle className="w-3 h-3" />
          Pledged
        </span>
      );
    }
    if (candidate.contacted) {
      return (
        <span className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold">
          <Clock className="w-3 h-3" />
          Pending
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
        <AlertCircle className="w-3 h-3" />
        New
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader className="w-12 h-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading SOI data from server...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content === */}
      <main className="ml-20 flex-1">
        {/* Loading Overlay */}
        {fetchingData && (
          <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-40 flex items-center justify-center">
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <Loader className="w-16 h-16 animate-spin text-purple-600 mx-auto" />
              <p className="mt-4 text-gray-600">Fetching SOI data...</p>
            </div>
          </div>
        )}
        
        {/* === Header === */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Arizona Sunshine</h1>
            <p className="text-sm text-gray-500">Statement of Interest Tracking</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search candidates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-80 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <button className="p-2 rounded-lg bg-purple-600 hover:bg-purple-700 transition">
              <Bell className="w-5 h-5 text-white" />
            </button>
          </div>
        </header>

        {/* === Content === */}
        <div className="p-8">
          {/* Automation Control */}
          <div className="bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] rounded-2xl p-8 mb-8 text-white shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                  <RefreshCw className="w-6 h-6" />
                  Automated SOI Scraping
                </h2>
                <p className="text-purple-100">
                  Trigger scraping on home machine • Real-time webhook updates • Cloudflare bypass
                </p>
              </div>
              <button
                onClick={() => setShowScrapingModal(true)}
                className="bg-white text-purple-700 px-8 py-4 rounded-xl font-semibold hover:bg-purple-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-3"
              >
                <Play className="w-5 h-5" />
                Scrape Data Now!
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-purple-600">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Total Candidates</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.total_candidates || 0}
                    </div>
                  </div>
                  <Users className="w-12 h-12 text-purple-600 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-purple-500">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Uncontacted</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.uncontacted || 0}
                    </div>
                  </div>
                  <Target className="w-12 h-12 text-purple-500 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-purple-700">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Pending Pledge</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.pending_pledge || 0}
                    </div>
                  </div>
                  <Clock className="w-12 h-12 text-purple-700 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-purple-800">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Pledged</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.pledged || 0}
                    </div>
                  </div>
                  <Award className="w-12 h-12 text-purple-800 opacity-20" />
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-xl p-6 shadow-md mb-6">
            <div className="flex gap-2 flex-wrap">
              {[
                { id: "all", label: "All Candidates", count: candidates?.length || 0 },
                { id: "uncontacted", label: "Uncontacted", count: stats?.uncontacted || 0 },
                { id: "pending", label: "Pending Pledge", count: stats?.pending_pledge || 0 },
                { id: "pledged", label: "Pledged", count: stats?.pledged || 0 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    activeTab === tab.id
                      ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>
          </div>

          {/* Candidates Table */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Candidate
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Office
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Contact
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredCandidates.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-gray-500">
                        <Users className="w-16 h-16 mx-auto mb-4 opacity-20" />
                        <div className="text-lg font-semibold mb-1">No candidates found</div>
                        <div className="text-sm">Try adjusting your filters or run a new scrape</div>
                      </td>
                    </tr>
                  ) : (
                    filteredCandidates.map((candidate) => (
                      <tr key={candidate.id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-gray-900">
                            {candidate.name || candidate.candidate_name || 'Unknown'}
                          </div>
                          {candidate.party && (
                            <div className="text-sm text-gray-500">{candidate.party}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-gray-700">
                          {candidate.office || 'Unknown'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="space-y-1">
                            {candidate.email && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Mail className="w-4 h-4" />
                                {candidate.email}
                              </div>
                            )}
                            {candidate.phone && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <Phone className="w-4 h-4" />
                                {candidate.phone}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">{getStatusBadge(candidate)}</td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            {!candidate.contacted && (
                              <button
                                onClick={() => handleMarkContacted(candidate.id)}
                                className="px-3 py-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg text-sm hover:from-purple-700 hover:to-purple-800 transition"
                              >
                                Mark Contacted
                              </button>
                            )}
                            {candidate.contacted && !candidate.pledge_received && (
                              <button
                                onClick={() => handleMarkPledged(candidate.id)}
                                className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition"
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

          {/* === Pagination === */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {totalCount} Results
            </p>
            <div className="flex items-center gap-2">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`w-10 h-10 rounded-lg font-medium transition ${
                    currentPage === page
                      ? "bg-purple-600 text-white"
                      : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                  }`}
                >
                  {page}
                </button>
              ))}
              {totalPages > 5 && (
                <button
                  onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}
                  className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </main>

      <ScrapingModal
        isOpen={showScrapingModal}
        onClose={() => {
          setShowScrapingModal(false);
          setFetchingData(true);
          loadData(); // Reload data after scraping completes
        }}
      />
    </div>
  );
}