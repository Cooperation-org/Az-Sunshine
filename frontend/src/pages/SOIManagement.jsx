import React, { useState, useEffect, useRef } from "react";
import {
  Play, CheckCircle, Clock, AlertCircle, Search, Mail, Phone, Loader, RefreshCw, Users,
  Target, Award, ChevronRight, ChevronLeft, CheckSquare, Square, X, Download
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { TableSkeleton, StatsGridSkeleton } from "../components/SkeletonLoader";
import { useDarkMode } from "../context/DarkModeContext";
import { useToast } from "../components/Toast";

// --- API HELPERS (Keeping your existing logic) ---
const API_BASE_URL = "http://localhost:8000/api/v1/";

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

  // Load logic
  useEffect(() => {
    fetchInitialData();
  }, [currentPage, statusFilter]);

  // Search Debounce
  useEffect(() => {
    const delay = setTimeout(() => { if(searchTerm) fetchInitialData(); }, 500);
    return () => clearTimeout(delay);
  }, [searchTerm]);

  async function fetchInitialData() {
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
      setCandidates(candidatesData.results || []);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));
    } catch (err) {
      addToast('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  }

  const handleRunScraper = () => {
    addToast('Scraper started in background...', 'info');
    // Your scraper logic here
  };

  const ScraperButton = (
    <button
      onClick={handleRunScraper}
      className="flex items-center gap-2 bg-[#7667C1] hover:bg-[#6556b0] text-white px-5 py-2 rounded-full text-sm font-medium transition-all active:scale-95 shadow-sm"
    >
      <RefreshCw className="w-3.5 h-3.5" />
      <span>Run Scraper</span>
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

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner 
            controls={ScraperButton}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            onSearch={fetchInitialData}
          />

          {/* Compact Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total" value={stats?.total_candidates} icon={Users} color="#7667C1" />
            <StatCard title="Needs Contact" value={stats?.uncontacted} icon={Target} color="#ef4444" />
            <StatCard title="Awaiting" value={stats?.contacted} icon={Clock} color="#fbbf24" />
            <StatCard title="Pledges" value={stats?.pledged} icon={Award} color="#22c55e" />
          </div>

          {/* Table Container */}
          <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
            <div className="p-4 border-b border-gray-700/50 flex justify-between items-center">
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
                  ) : (
                    candidates.map((candidate) => (
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
        </div>
      </main>
    </div>
  );
}