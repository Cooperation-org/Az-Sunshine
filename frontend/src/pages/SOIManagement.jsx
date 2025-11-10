import React, { useState, useEffect } from "react";
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
  Download,
  RefreshCw,
  Users,
  Target,
  Award,
  TrendingUp
} from "lucide-react";
import SideBar from "../components/Sidebar";

import {
  triggerScraping,
  getScrapingStatus,
  getSOICandidates,
  getSOIDashboardStats,
  markCandidateContacted,
  markPledgeReceived,
} from "../api/api";

// Scraping Modal Component
function ScrapingModal({ isOpen, onClose }) {
  const [status, setStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (isOpen && !isPolling) {
      startScraping();
    }
  }, [isOpen]);

  const startScraping = async () => {
    try {
      setIsPolling(true);
      const result = await triggerScraping();
      setStatus(result);
      
      // Start polling for status
      const pollInterval = setInterval(async () => {
        try {
          const currentStatus = await getScrapingStatus();
          setStatus(currentStatus);
          
          if (currentStatus.status !== 'running') {
            clearInterval(pollInterval);
            setIsPolling(false);
          }
        } catch (error) {
          console.error('Polling error:', error);
          clearInterval(pollInterval);
          setIsPolling(false);
        }
      }, 2000);
      
    } catch (error) {
      setStatus({
        status: 'error',
        error: error.message,
        logs: [`Error: ${error.message}`]
      });
      setIsPolling(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'bg-gradient-to-r from-purple-500 to-purple-600';
      case 'completed': return 'bg-gradient-to-r from-green-500 to-green-600';
      case 'error': return 'bg-gradient-to-r from-red-500 to-red-600';
      default: return 'bg-gray-500';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {status?.status === 'running' ? (
                <Loader className="w-6 h-6 animate-spin" />
              ) : status?.status === 'completed' ? (
                <CheckCircle className="w-6 h-6" />
              ) : status?.status === 'error' ? (
                <AlertCircle className="w-6 h-6" />
              ) : (
                <RefreshCw className="w-6 h-6" />
              )}
              <h2 className="text-2xl font-bold">SOI Data Scraping</h2>
            </div>
            <button
              onClick={onClose}
              className="hover:bg-white/20 p-2 rounded-lg transition"
              disabled={status?.status === 'running'}
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Progress */}
        {status && (
          <div className="p-6">
            <div className="mb-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700">
                  {status.current_step || 'Initializing...'}
                </span>
                <span className="text-sm font-semibold text-gray-700">
                  {status.progress || 0}%
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
            {status.stats && (
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.total_candidates || status.stats.urls_discovered || 0}
                  </div>
                  <div className="text-xs text-gray-600">
                    {status.stats.total_candidates ? 'Total' : 'URLs'}
                  </div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.uncontacted || status.stats.pages_scraped || 0}
                  </div>
                  <div className="text-xs text-gray-600">
                    {status.stats.uncontacted ? 'Uncontacted' : 'Scraped'}
                  </div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center border border-purple-100">
                  <div className="text-2xl font-bold text-purple-600">
                    {status.stats.pending_pledge || status.stats.candidates_processed || 0}
                  </div>
                  <div className="text-xs text-gray-600">
                    {status.stats.pending_pledge ? 'Pending' : 'Processed'}
                  </div>
                </div>
              </div>
            )}

            {/* Console Logs */}
            <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
              <div className="font-mono text-xs text-green-400">
                {status.logs?.map((log, idx) => (
                  <div key={idx} className="mb-1">
                    {log}
                  </div>
                ))}
              </div>
            </div>

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

// Main SOI Component
export default function SOIManagement() {
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showScrapingModal, setShowScrapingModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [candidatesData, statsData] = await Promise.all([
        getSOICandidates(),
        getSOIDashboardStats(),
      ]);
      setCandidates(Array.isArray(candidatesData) ? candidatesData : []);
      setStats(statsData || {});
    } catch (error) {
      console.error("Error loading data:", error);
      setCandidates([]);
      setStats({});
    } finally {
      setLoading(false);
    }
  };

  const handleMarkContacted = async (id) => {
    try {
      await markCandidateContacted(id);
      loadData();
    } catch (error) {
      console.error("Error marking contacted:", error);
    }
  };

  const handleMarkPledged = async (id) => {
    try {
      await markPledgeReceived(id);
      loadData();
    } catch (error) {
      console.error("Error marking pledged:", error);
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
      <div className="flex h-screen">
        <SideBar />
        <div className="flex-1 ml-20 flex items-center justify-center">
          <Loader className="w-12 h-12 animate-spin text-purple-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <SideBar />
      
      <div className="flex-1 ml-20 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Statement of Interest Tracking
            </h1>
            <p className="text-gray-600">
              Monitor and manage candidate SOI filings and pledge commitments
            </p>
          </div>

          {/* Automation Control */}
          <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-purple-800 rounded-2xl p-8 mb-8 text-white shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                  <RefreshCw className="w-6 h-6" />
                  Automated SOI Scraping
                </h2>
                <p className="text-purple-100">
                  Automatically discover and process new SOI filings from Arizona.vote
                </p>
              </div>
              <button
                onClick={() => setShowScrapingModal(true)}
                className="bg-white text-purple-600 px-8 py-4 rounded-xl font-bold text-lg hover:bg-purple-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-3"
              >
                <Play className="w-5 h-5" />
                Scrape Data Now!
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search candidates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            <div className="flex gap-2">
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
                      ? "bg-gradient-to-r from-purple-600 to-purple-700 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>
          </div>

          {/* Candidates Table */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
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
                <tbody className="divide-y">
                  {filteredCandidates.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-900">{candidate.name}</div>
                        <div className="text-sm text-gray-500">{candidate.party}</div>
                      </td>
                      <td className="px-6 py-4 text-gray-700">{candidate.office}</td>
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
                  ))}
                </tbody>
              </table>
            </div>

            {filteredCandidates.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                <Users className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <div className="text-lg font-semibold mb-1">No candidates found</div>
                <div className="text-sm">
                  Try adjusting your filters or run a new scrape
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <ScrapingModal
        isOpen={showScrapingModal}
        onClose={() => {
          setShowScrapingModal(false);
          loadData(); // Reload data after scraping
        }}
      />
    </div>
  );
}