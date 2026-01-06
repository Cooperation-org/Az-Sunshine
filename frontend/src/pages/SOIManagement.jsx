import React, { useState, useEffect, useRef } from "react";
import {
  Play, CheckCircle, Clock, AlertCircle, Search, Mail, Phone, Loader, RefreshCw, Users,
  Target, Award, CheckSquare, Square, X, Download, Database
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { TableSkeleton, StatsGridSkeleton } from "../components/SkeletonLoader";
import { useDarkMode } from "../context/DarkModeContext";
import { useToast } from "../components/Toast";
import Pagination from "../components/Pagination";

// --- SCRAPER MODAL COMPONENT ---
const ScraperModal = ({ isOpen, onClose, status, newCandidates, onViewNewCandidates, darkMode }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={status === 'complete' ? onClose : undefined} />

      {/* Modal */}
      <div className={`relative w-full max-w-md mx-4 p-6 rounded-2xl shadow-2xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
        {status === 'running' && (
          <div className="text-center py-8">
            <div className="relative mx-auto w-20 h-20 mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-purple-200 dark:border-purple-900"></div>
              <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
              <Database className="absolute inset-0 m-auto w-8 h-8 text-purple-500" />
            </div>
            <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Scraping in Progress
            </h3>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Stand by as we collect Statement of Interest filings from the Arizona Secretary of State...
            </p>
            <div className="mt-6 flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}

        {status === 'complete' && (
          <div className="text-center py-6">
            <div className="mx-auto w-16 h-16 mb-4 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Scraping Complete!
            </h3>
            <p className={`text-sm mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {newCandidates.length > 0
                ? `Found ${newCandidates.length} new candidate${newCandidates.length > 1 ? 's' : ''}!`
                : 'No new candidates found. Database is up to date.'}
            </p>

            {newCandidates.length > 0 && (
              <div className={`max-h-48 overflow-y-auto mb-4 rounded-xl p-3 ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
                <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                  New Candidates
                </p>
                {newCandidates.map((c, idx) => (
                  <div key={idx} className={`flex items-center gap-2 py-2 border-b last:border-0 ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${darkMode ? 'bg-purple-500/20 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>
                      {(c.candidate_name || '?').charAt(0)}
                    </div>
                    <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {c.candidate_name || 'Unknown'}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              {newCandidates.length > 0 && (
                <button
                  onClick={onViewNewCandidates}
                  className="flex-1 px-4 py-2.5 bg-purple-500 hover:bg-purple-600 text-white rounded-xl font-medium transition-colors"
                >
                  View New Candidates
                </button>
              )}
              <button
                onClick={onClose}
                className={`flex-1 px-4 py-2.5 rounded-xl font-medium transition-colors ${
                  darkMode
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                {newCandidates.length > 0 ? 'Go to Full List' : 'Close'}
              </button>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center py-6">
            <div className="mx-auto w-16 h-16 mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Scraping Failed
            </h3>
            <p className={`text-sm mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Unable to connect to the scraper. Please ensure the laptop is connected and try again.
            </p>
            <button
              onClick={onClose}
              className={`px-6 py-2.5 rounded-xl font-medium transition-colors ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// --- API HELPERS (Keeping your existing logic) ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1/";

const getSOICandidates = async (params) => {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page);
  if (params.page_size) queryParams.append('page_size', params.page_size);
  if (params.status) queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  const response = await fetch(`${API_BASE_URL}soi/candidates/?${queryParams}`);
  if (!response.ok) throw new Error("Failed");
  return response.json();
};

const getSOIDashboardStats = async () => {
  const response = await fetch(`${API_BASE_URL}soi/dashboard-stats/`);
  return response.json();
};

const getScraperStatus = async () => {
  const response = await fetch(`${API_BASE_URL}scraper-status/`);
  return response.json();
};

// --- REFINED BANNER COMPONENT ---
const Banner = ({ controls, searchTerm, setSearchTerm, onSearch }) => {
  const { darkMode } = useDarkMode();

  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              SOI <span style={{ color: '#A78BFA' }}>Management</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Track Statement of Interest filings and manage manual candidate outreach.
            </p>
          </div>
          <div className="flex-shrink-0">{controls}</div>
        </div>

        <div className="flex justify-start">
          <form onSubmit={(e) => { e.preventDefault(); onSearch(); }} className="relative w-full max-w-md">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="text-gray-400" size={16} />
            </div>
            <input
              type="text"
              placeholder="Search candidates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border-none rounded-full py-2.5 pl-11 pr-4 text-sm text-white placeholder-gray-400 outline-none transition-all focus:ring-1 focus:ring-[#7667C1]"
              style={darkMode
                ? { background: 'rgba(31, 27, 49, 0.8)' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            />
          </form>
        </div>
      </div>
    </div>
  );
};

export default function SOIManagement() {
  const { darkMode } = useDarkMode();
  const { addToast } = useToast();
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [processingIds, setProcessingIds] = useState(new Set());
  const [scraperRunning, setScraperRunning] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalStatus, setModalStatus] = useState('running'); // 'running' | 'complete' | 'error'
  const [newCandidates, setNewCandidates] = useState([]);
  const [showNewOnly, setShowNewOnly] = useState(false);
  const previousCandidateIds = useRef(new Set());

  // Load logic
  useEffect(() => {
    fetchInitialData();
  }, [currentPage, statusFilter]);

  // Search Debounce
  useEffect(() => {
    const delay = setTimeout(() => { if(searchTerm) fetchInitialData(); }, 500);
    return () => clearTimeout(delay);
  }, [searchTerm]);

  async function fetchInitialData(trackNewCandidates = false) {
    setLoading(true);
    try {
      const [statsData, candidatesData] = await Promise.all([
        getSOIDashboardStats(),
        getSOICandidates({
          page: currentPage,
          page_size: 10,
          status: statusFilter !== 'all' ? statusFilter : null,
          search: searchTerm || null
        })
      ]);
      setStats(statsData);
      const results = candidatesData.results || [];
      setCandidates(results);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));

      // Track new candidates if scraping
      if (trackNewCandidates && previousCandidateIds.current.size > 0) {
        const newOnes = results.filter(c => !previousCandidateIds.current.has(c.id));
        setNewCandidates(newOnes);
      }

      // Save current IDs for future comparison
      previousCandidateIds.current = new Set(results.map(c => c.id));
    } catch (err) {
      addToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  }

  const handleRunScraper = async () => {
    if (scraperRunning) return;

    // Save current candidate IDs before scraping
    const allCandidatesResponse = await getSOICandidates({ page: 1, page_size: 1000 });
    previousCandidateIds.current = new Set((allCandidatesResponse.results || []).map(c => c.id));

    setScraperRunning(true);
    setModalOpen(true);
    setModalStatus('running');
    setNewCandidates([]);

    try {
      const response = await fetch(`${API_BASE_URL}trigger-scrape/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (data.success) {
        // Poll scraper status endpoint until complete
        let attempts = 0;
        const maxAttempts = 60; // 60 * 3 = 180 seconds max (3 minutes)

        const pollStatus = async () => {
          attempts++;

          try {
            const statusData = await getScraperStatus();

            if (statusData.status === 'complete') {
              // Scraper finished successfully - fetch fresh data
              const freshData = await getSOICandidates({ page: 1, page_size: 1000 });
              const freshResults = freshData.results || [];
              const newOnes = freshResults.filter(c => !previousCandidateIds.current.has(c.id));

              setNewCandidates(newOnes.length > 0 ? newOnes : []);
              setModalStatus('complete');
              setScraperRunning(false);
              fetchInitialData();
              return;
            }

            if (statusData.status === 'error') {
              // Scraper failed
              setModalStatus('error');
              setScraperRunning(false);
              return;
            }

            // Still running - check for timeout
            if (attempts >= maxAttempts) {
              // Timeout - assume complete with no new candidates
              setNewCandidates([]);
              setModalStatus('complete');
              setScraperRunning(false);
              fetchInitialData();
              return;
            }

            // Keep polling every 3 seconds
            setTimeout(pollStatus, 3000);
          } catch (pollErr) {
            console.error('Poll error:', pollErr);
            // On error, keep trying unless max attempts reached
            if (attempts >= maxAttempts) {
              setNewCandidates([]);
              setModalStatus('complete');
              setScraperRunning(false);
              fetchInitialData();
            } else {
              setTimeout(pollStatus, 3000);
            }
          }
        };

        // Start polling after short delay
        setTimeout(pollStatus, 2000);
      } else {
        setModalStatus('error');
        setScraperRunning(false);
      }
    } catch (err) {
      setModalStatus('error');
      setScraperRunning(false);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setShowNewOnly(false);
    fetchInitialData();
  };

  const handleViewNewCandidates = () => {
    setShowNewOnly(true);
    setModalOpen(false);
  };

  const ScraperButton = (
    <button
      onClick={handleRunScraper}
      disabled={scraperRunning}
      className={`flex items-center gap-2 ${scraperRunning ? 'bg-gray-500 cursor-not-allowed' : 'bg-[#7667C1] hover:bg-[#6556b0]'} text-white px-5 py-2 rounded-full text-sm font-medium transition-all active:scale-95 shadow-sm`}
    >
      {scraperRunning ? <Loader className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
      <span>{scraperRunning ? 'Running...' : 'Run Scraper'}</span>
    </button>
  );

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} p-5 rounded-2xl border shadow-sm flex items-center gap-4`}>
      <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color: color }} />
      </div>
      <div>
        <p className={`text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{title}</p>
        <p className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{value ?? '0'}</p>
      </div>
    </div>
  );

  // Determine which candidates to display
  const displayCandidates = showNewOnly ? newCandidates : candidates;

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />

      {/* Scraper Modal */}
      <ScraperModal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        status={modalStatus}
        newCandidates={newCandidates}
        onViewNewCandidates={handleViewNewCandidates}
        darkMode={darkMode}
      />

      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner
            controls={ScraperButton}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            onSearch={fetchInitialData}
          />

          {/* New Candidates Banner */}
          {showNewOnly && (
            <div className={`mb-6 p-4 rounded-xl flex items-center justify-between ${darkMode ? 'bg-green-900/30 border border-green-700' : 'bg-green-50 border border-green-200'}`}>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <p className={`font-semibold ${darkMode ? 'text-green-300' : 'text-green-800'}`}>
                    Showing {newCandidates.length} New Candidate{newCandidates.length !== 1 ? 's' : ''}
                  </p>
                  <p className={`text-sm ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                    These candidates were just added from the latest scrape
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowNewOnly(false)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  darkMode
                    ? 'bg-green-700 hover:bg-green-600 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                Go Back to Full List
              </button>
            </div>
          )}

          {/* Compact Stats Grid */}
          {!showNewOnly && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <StatCard title="Total" value={stats?.total_candidates} icon={Users} color="#7667C1" />
              <StatCard title="Needs Contact" value={stats?.uncontacted} icon={Target} color="#ef4444" />
              <StatCard title="Awaiting" value={stats?.contacted} icon={Clock} color="#fbbf24" />
              <StatCard title="Pledges" value={stats?.pledged} icon={Award} color="#22c55e" />
            </div>
          )}

          {/* Table Container */}
          <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
            <div className="p-4 border-b border-gray-700/50 flex justify-between items-center">
              {!showNewOnly && (
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className={`text-xs font-medium rounded-lg px-3 py-1.5 outline-none ${darkMode ? 'bg-[#1F1B31] text-gray-300' : 'bg-gray-50 text-gray-600'}`}
                >
                  <option value="all">All Statuses</option>
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="pledged">Pledges</option>
                </select>
              )}
              {showNewOnly && (
                <span className={`text-sm font-medium ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                  New Candidates from Scrape
                </span>
              )}
              {selectedIds.size > 0 && (
                <span className="text-xs text-purple-400 font-medium">{selectedIds.size} Selected</span>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className={darkMode ? 'bg-[#373052]' : 'bg-gray-50'}>
                  <tr>
                    <th className="px-6 py-4 text-left"><Square size={14} className="text-gray-500" /></th>
                    {["Candidate", "Contact Information", "Status", "Actions"].map((h) => (
                      <th key={h} className={`py-4 px-6 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-100'}`}>
                  {loading ? (
                    <TableSkeleton rows={8} columns={5} />
                  ) : displayCandidates.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-gray-500">
                        {showNewOnly ? 'No new candidates found.' : 'No candidates found.'}
                      </td>
                    </tr>
                  ) : (
                    displayCandidates.map((candidate) => (
                      <tr key={candidate.id} className={`transition-colors ${darkMode ? 'hover:bg-[#373052]' : 'hover:bg-purple-50/50'}`}>
                        <td className="px-6 py-4">
                           <button onClick={() => {
                             const next = new Set(selectedIds);
                             next.has(candidate.id) ? next.delete(candidate.id) : next.add(candidate.id);
                             setSelectedIds(next);
                           }}>
                             {selectedIds.has(candidate.id) ? <CheckSquare size={16} className="text-[#7667C1]" /> : <Square size={16} className="text-gray-500" />}
                           </button>
                        </td>
                        <td className="py-4 px-6 flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${darkMode ? 'bg-purple-500/20 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>
                            {(candidate.candidate_name || "?").charAt(0)}
                          </div>
                          <div>
                            <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>{candidate.candidate_name}</p>
                            <p className="text-xs text-gray-500">{candidate.office?.name || 'Not specified'}</p>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                           <div className="flex flex-col gap-1">
                             <div className="flex items-center gap-2 text-xs text-gray-400"><Mail size={12}/> {candidate.email || 'No Email'}</div>
                             <div className="flex items-center gap-2 text-xs text-gray-400"><Phone size={12}/> {candidate.phone || 'No Phone'}</div>
                           </div>
                        </td>
                        <td className="py-4 px-6">
                           <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                             candidate.pledge_received ? "bg-green-100 text-green-700" : candidate.contacted ? "bg-blue-100 text-blue-700" : "bg-red-100 text-red-700"
                           }`}>
                             {candidate.pledge_received ? 'Pledged' : candidate.contacted ? 'Contacted' : 'New'}
                           </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex gap-2">
                             {!candidate.contacted && <button className="text-[11px] font-bold text-purple-400 hover:underline">Mark Contacted</button>}
                             {!candidate.pledge_received && <button className="text-[11px] font-bold text-green-500 hover:underline">Receive Pledge</button>}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

          </div>

          {!showNewOnly && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalCount={totalCount}
              onPageChange={setCurrentPage}
              loading={loading}
            />
          )}
        </div>
      </main>
    </div>
  );
}