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
import LoadingSpinner, { InlineLoader, TableSkeleton } from "../components/LoadingSpinner";

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
  const [isScraping, setIsScraping] = useState(false);

  useEffect(() => {
    if (isOpen && !isPolling) {
      startScraping();
    }
  }, [isOpen]);

  const startScraping = async () => {
    try {
      setIsPolling(true);
      setIsScraping(true);
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
            setIsScraping(false);
          }
        } catch (error) {
          console.error('Polling error:', error);
          clearInterval(pollInterval);
          setIsPolling(false);
          setIsScraping(false);
        }
      }, 2000);
      
    } catch (error) {
      setStatus({
        status: 'error',
        error: error.message,
        logs: [`Error: ${error.message}`]
      });
      setIsPolling(false);
      setIsScraping(false);
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
              {status?.status === 'running' || isScraping ? (
                <Loader className="w-6 h-6 animate-spin" />
              ) : status?.status === 'completed' ? (
                <CheckCircle className="w-6 h-6" />
              ) : status?.status === 'error' ? (
                <AlertCircle className="w-6 h-6" />
              ) : (
                <RefreshCw className="w-6 h-6" />
              )}
              <h2 className="text-xl sm:text-2xl font-bold leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>SOI Data Scraping</h2>
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
        {(status || isScraping) && (
          <div className="p-6">
            {/* Show loading message when scraping starts but status not yet available */}
            {isScraping && !status && (
              <div className="mb-6 text-center">
                <LoadingSpinner 
                  size="lg" 
                  message="Fetching SOI data... please wait." 
                  fullScreen={false}
                />
              </div>
            )}
            
            {status && (
              <>
              <div className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className="text-xs sm:text-sm font-semibold text-gray-700 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
                    {status.current_step || 'Initializing...'}
                  </span>
                  <span className="text-xs sm:text-sm font-semibold text-gray-700 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
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
            {status.logs && status.logs.length > 0 && (
              <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
                <div className="font-mono text-xs text-green-400">
                  {status.logs.map((log, idx) => (
                    <div key={idx} className="mb-1">
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
              </>
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
  const [fetchingData, setFetchingData] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [showScrapingModal, setShowScrapingModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setFetchingData(true);
      // Show loading indicator while fetching
      const [candidatesData, statsData] = await Promise.all([
        getSOICandidates(),
        getSOIDashboardStats(),
      ]);
      
      // Debug: Log the raw API response
      console.log("🔍 SOI Data Fetching Debug:");
      console.log("Raw candidatesData:", candidatesData);
      console.log("Type:", Array.isArray(candidatesData) ? "Array" : typeof candidatesData);
      
      // Ensure we handle array response correctly
      const candidatesArray = Array.isArray(candidatesData) 
        ? candidatesData 
        : (candidatesData?.results || candidatesData || []);
      
      // Debug: Log processed array and check for missing fields
      console.log("Processed candidatesArray length:", candidatesArray.length);
      if (candidatesArray.length > 0) {
        console.log("Sample candidate object:", candidatesArray[0]);
        console.log("Sample candidate fields:", Object.keys(candidatesArray[0]));
        
        // Check for missing or null fields
        const sampleCandidate = candidatesArray[0];
        const expectedFields = ['id', 'name', 'office', 'party', 'email', 'phone', 'contacted', 'pledge_received', 'filing_date'];
        const missingFields = expectedFields.filter(field => 
          !(field in sampleCandidate) || sampleCandidate[field] === null || sampleCandidate[field] === undefined
        );
        const emptyFields = expectedFields.filter(field => 
          sampleCandidate[field] === '' || sampleCandidate[field] === null || sampleCandidate[field] === undefined
        );
        
        if (missingFields.length > 0) {
          console.warn("⚠️ Missing fields in candidate data:", missingFields);
        }
        if (emptyFields.length > 0) {
          console.warn("⚠️ Empty/null fields in candidate data:", emptyFields);
        }
        
        // Log field values for debugging
        expectedFields.forEach(field => {
          const value = sampleCandidate[field];
          console.log(`  ${field}:`, value, `(type: ${typeof value})`);
        });
      }
      
      setCandidates(candidatesArray);
      setStats(statsData || {});
      
      console.log("✅ Data loaded successfully");
    } catch (error) {
      console.error("❌ Error loading data:", error);
      console.error("Error details:", error.response?.data || error.message);
      setCandidates([]);
      setStats({});
    } finally {
      setLoading(false);
      setFetchingData(false);
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
        <span className="flex items-center gap-1 px-2 sm:px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
          <CheckCircle className="w-3 h-3" />
          <span className="hidden sm:inline">Pledged</span>
          <span className="sm:hidden">✓</span>
        </span>
      );
    }
    if (candidate.contacted) {
      return (
        <span className="flex items-center gap-1 px-2 sm:px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
          <Clock className="w-3 h-3" />
          <span className="hidden sm:inline">Pending</span>
          <span className="sm:hidden">⏱</span>
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 px-2 sm:px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
        <AlertCircle className="w-3 h-3" />
        <span className="hidden sm:inline">New</span>
        <span className="sm:hidden">!</span>
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <SideBar />
        <div className="flex-1 ml-20 flex items-center justify-center bg-gray-50">
          <LoadingSpinner 
            size="xl" 
            message="Loading candidate data..." 
            fullScreen={false}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="soi-management flex h-screen bg-gray-50 relative" style={{ fontFamily: "'Inter', sans-serif" }}>
      <SideBar />
      
      {/* Loading Overlay - Shows when fetching/scraping data */}
      {fetchingData && (
        <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-40 flex items-center justify-center">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
            <LoadingSpinner 
              size="xl" 
              message="Fetching SOI data... please wait." 
              fullScreen={false}
            />
          </div>
        </div>
      )}
      
      <div className="flex-1 ml-20 overflow-y-auto">
        <div className="p-4 sm:p-6 md:p-8">
          {/* Header */}
          <div className="mb-6 md:mb-8">
            <h3 className="text-2xl font-bold text-gray-900">
              Statement of Interest Tracking
            </h3>
            <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
              Monitor and manage candidate SOI filings and pledge commitments
            </p>
          </div>

          {/* Automation Control */}
          <div className="bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] rounded-2xl p-6 sm:p-8 mb-6 md:mb-8 text-white shadow-xl">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-xl sm:text-2xl font-bold mb-2 flex items-center gap-2 leading-tight">
                  <RefreshCw className="w-5 h-5 sm:w-6 sm:h-6" />
                  Automated SOI Scraping
                </h2>
                <p className="text-sm sm:text-base text-purple-100 leading-relaxed">
                  Automatically discover and process new SOI filings from Arizona.vote
                </p>
              </div>
              <button
                onClick={() => setShowScrapingModal(true)}
                className="bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-semibold text-base sm:text-lg hover:bg-purple-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-2 sm:gap-3 whitespace-nowrap"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                <Play className="w-4 h-4 sm:w-5 sm:h-5" />
                <span className="hidden sm:inline">Scrape Data Now!</span>
                <span className="sm:hidden">Scrape</span>
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 md:mb-8">
              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-md border-l-4 border-purple-600">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs sm:text-sm text-gray-600 mb-1 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>Total Candidates</div>
                    <div className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>
                      {stats.total_candidates || 0}
                    </div>
                  </div>
                  <Users className="w-10 h-10 sm:w-12 sm:h-12 text-purple-600 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-md border-l-4 border-purple-500">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs sm:text-sm text-gray-600 mb-1 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>Uncontacted</div>
                    <div className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>
                      {stats.uncontacted || 0}
                    </div>
                  </div>
                  <Target className="w-10 h-10 sm:w-12 sm:h-12 text-purple-500 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-md border-l-4 border-purple-700">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs sm:text-sm text-gray-600 mb-1 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>Pending Pledge</div>
                    <div className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>
                      {stats.pending_pledge || 0}
                    </div>
                  </div>
                  <Clock className="w-10 h-10 sm:w-12 sm:h-12 text-purple-700 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-md border-l-4 border-purple-800">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs sm:text-sm text-gray-600 mb-1 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>Pledged</div>
                    <div className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>
                      {stats.pledged || 0}
                    </div>
                  </div>
                  <Award className="w-10 h-10 sm:w-12 sm:h-12 text-purple-800 opacity-20" />
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-xl p-4 sm:p-6 shadow-md mb-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 sm:w-5 sm:h-5" />
                <input
                  type="text"
                  placeholder="Search candidates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 sm:pl-10 pr-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                { id: "all", label: "All Candidates", count: candidates?.length || 0 },
                { id: "uncontacted", label: "Uncontacted", count: stats?.uncontacted || 0 },
                { id: "pending", label: "Pending Pledge", count: stats?.pending_pledge || 0 },
                { id: "pledged", label: "Pledged", count: stats?.pledged || 0 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 sm:px-4 py-2 rounded-lg font-medium text-sm sm:text-base transition ${
                    activeTab === tab.id
                      ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                  style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}
                >
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.label.split(' ')[0]}</span> ({tab.count})
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
                    <th className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-gray-700" style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}>
                      Candidate
                    </th>
                    <th className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-gray-700 hidden sm:table-cell" style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}>
                      Office
                    </th>
                    <th className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-gray-700 hidden md:table-cell" style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}>
                      Contact
                    </th>
                    <th className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-gray-700" style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}>
                      Status
                    </th>
                    <th className="px-4 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-semibold text-gray-700" style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filteredCandidates.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-gray-50 transition">
                      <td className="px-4 sm:px-6 py-3 sm:py-4">
                        <div className="font-semibold text-sm sm:text-base text-gray-900 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>
                          {candidate.name || candidate.candidate_name || 'Unknown Name'}
                        </div>
                        {candidate.party && (
                          <div className="text-xs sm:text-sm text-gray-500 leading-normal mt-1" style={{ fontFamily: "'Inter', sans-serif" }}>
                            {candidate.party}
                          </div>
                        )}
                      </td>
                      <td className="px-4 sm:px-6 py-3 sm:py-4 text-sm sm:text-base text-gray-700 hidden sm:table-cell leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
                        {candidate.office || 'Unknown Office'}
                      </td>
                      <td className="px-4 sm:px-6 py-3 sm:py-4 hidden md:table-cell">
                        <div className="space-y-1">
                          {candidate.email && (
                            <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
                              <Mail className="w-3 h-3 sm:w-4 sm:h-4" />
                              <span className="truncate max-w-[200px]">{candidate.email}</span>
                            </div>
                          )}
                          {candidate.phone && (
                            <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600 leading-normal" style={{ fontFamily: "'Inter', sans-serif" }}>
                              <Phone className="w-3 h-3 sm:w-4 sm:h-4" />
                              {candidate.phone}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 sm:px-6 py-3 sm:py-4">{getStatusBadge(candidate)}</td>
                      <td className="px-4 sm:px-6 py-3 sm:py-4">
                        <div className="flex flex-col sm:flex-row gap-2">
                          {!candidate.contacted && (
                            <button
                              onClick={() => handleMarkContacted(candidate.id)}
                              className="px-2 sm:px-3 py-1 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg text-xs sm:text-sm hover:from-purple-700 hover:to-purple-800 transition whitespace-nowrap"
                              style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}
                            >
                              <span className="hidden sm:inline">Mark Contacted</span>
                              <span className="sm:hidden">Contact</span>
                            </button>
                          )}
                          {candidate.contacted && !candidate.pledge_received && (
                            <button
                              onClick={() => handleMarkPledged(candidate.id)}
                              className="px-2 sm:px-3 py-1 bg-green-600 text-white rounded-lg text-xs sm:text-sm hover:bg-green-700 transition whitespace-nowrap"
                              style={{ fontFamily: "'Inter', sans-serif", lineHeight: '1.5' }}
                            >
                              <span className="hidden sm:inline">Pledge Received</span>
                              <span className="sm:hidden">Pledge</span>
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
              <div className="p-8 sm:p-12 text-center text-gray-500">
                <Users className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-4 opacity-20" />
                <div className="text-base sm:text-lg font-semibold mb-1 leading-tight" style={{ fontFamily: "'Inter', sans-serif" }}>No candidates found</div>
                <div className="text-xs sm:text-sm leading-relaxed" style={{ fontFamily: "'Inter', sans-serif" }}>
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
          setFetchingData(true); // Show loading when reloading data
          loadData(); // Reload data after scraping
        }}
      />
    </div>
  );
}