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
  ChevronRight
} from "lucide-react";

import {
  getSOICandidates,
  getSOIDashboardStats,
  markCandidateContacted,
  markPledgeReceived,
} from "../api/api";

import Sidebar from "../components/Sidebar";

// Simple scraping modal - no complex polling needed
function ScrapingModal({ isOpen, onClose, onComplete }) {
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen && status === 'idle') {
      startScraping();
    }
  }, [isOpen]);

  const startScraping = async () => {
    setStatus('running');
    setMessage('Triggering scraper on home laptop...');

    try {
      const response = await fetch('http://167.172.30.134/api/v1/trigger-scrape/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.success) {
        setStatus('success');
        setMessage('✅ Scraper triggered successfully! Data will be processed shortly.');
        setTimeout(() => {
          onComplete();
          onClose();
        }, 2000);
      } else {
        setStatus('error');
        setMessage(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(`❌ Failed to trigger scraper: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
        <div className="text-center">
          {status === 'running' && (
            <>
              <Loader className="w-16 h-16 animate-spin text-purple-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Triggering Scraper...</h3>
              <p className="text-gray-600">{message}</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Success!</h3>
              <p className="text-gray-600">{message}</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <AlertCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Error</h3>
              <p className="text-gray-600">{message}</p>
              <button
                onClick={onClose}
                className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
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
  const [showScrapingModal, setShowScrapingModal] = useState(false);
  const [scraping, setScraping] = useState(false);
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
      
      console.log("📡 Loading SOI data from Django backend...");
      
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
    }
  };

  const handleMarkContacted = async (id) => {
    try {
      await markCandidateContacted(id);
      loadData();
    } catch (error) {
      console.error("Error marking contacted:", error);
      alert("Failed to mark candidate as contacted.");
    }
  };

  const handleMarkPledged = async (id) => {
    try {
      await markPledgeReceived(id);
      loadData();
    } catch (error) {
      console.error("Error marking pledged:", error);
      alert("Failed to mark pledge as received.");
    }
  };

  const handleTriggerScraping = async () => {
    setScraping(true);
    setShowScrapingModal(true);
  };

  const handleScrapingComplete = () => {
    setScraping(false);
    loadData(); // Refresh data after scraping
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
          <p className="text-gray-600">Loading SOI data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <main className="ml-20 flex-1">
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

        <div className="p-8">
          {/* Scraping Control */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-800 rounded-2xl p-8 mb-8 text-white shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                  <RefreshCw className="w-6 h-6" />
                  Residential IP Scraping
                </h2>
                <p className="text-purple-100">
                  FastAPI agent on home laptop • Bypasses datacenter blocking • Secure ngrok tunnel
                </p>
              </div>
              <button
                onClick={handleTriggerScraping}
                disabled={scraping}
                className="bg-white text-purple-700 px-8 py-4 rounded-xl font-semibold hover:bg-purple-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5" />
                {scraping ? "Scraping..." : "Scrape Now"}
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

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Uncontacted</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.uncontacted || 0}
                    </div>
                  </div>
                  <Target className="w-12 h-12 text-red-500 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-yellow-500">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Pending Pledge</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.pending_pledge || 0}
                    </div>
                  </div>
                  <Clock className="w-12 h-12 text-yellow-500 opacity-20" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Pledged</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {stats.pledged || 0}
                    </div>
                  </div>
                  <Award className="w-12 h-12 text-green-500 opacity-20" />
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
                      ? "bg-purple-600 text-white"
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
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Candidate</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Office</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Contact</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Actions</th>
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
                                className="px-3 py-1 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition"
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

          {/* Pagination */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-600">{totalCount} Results</p>
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
        onClose={() => setShowScrapingModal(false)}
        onComplete={handleScrapingComplete}
      />
    </div>
  );
}