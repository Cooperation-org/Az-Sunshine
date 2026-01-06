import React, { useEffect, useState } from "react";
import { Search, Download, Loader } from "lucide-react";
import { getCandidates } from "../api/api";
import { Link, useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";
import Pagination from "../components/Pagination";

// --- REFINED BANNER COMPONENT ---
const Banner = ({ controls, searchTerm, onSearch }) => {
  const { darkMode } = useDarkMode();
  const [localSearch, setLocalSearch] = useState(searchTerm);

  // Sync local state when URL param changes (e.g., browser back button)
  useEffect(() => {
    setLocalSearch(searchTerm);
  }, [searchTerm]);

  // Debounce search - triggers 300ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== searchTerm) {
        onSearch(localSearch);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch]);

  const handleLocalSearch = (e) => {
    e.preventDefault();
    onSearch(localSearch);
  };

  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto">

        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Explore the <span style={{ color: darkMode ? '#A78BFA' : '#A78BFA' }}>Candidates</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Aggregating candidate data to correlate spending and legislative impact.
            </p>
          </div>

          <div className="flex-shrink-0">
            {controls}
          </div>
        </div>

        {/* Compact Search Bar */}
        <div className="flex justify-start">
          <form onSubmit={handleLocalSearch} className="relative w-full max-w-md">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="text-gray-400" size={16} />
            </div>
            <input
              type="text"
              placeholder="Search Candidates..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
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

// --- MAIN CANDIDATES PAGE ---
export default function Candidates() {
  const { darkMode } = useDarkMode();
  const [searchParams, setSearchParams] = useSearchParams();
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [exporting, setExporting] = useState(false);

  // Get search term and page from URL
  const searchTerm = searchParams.get('search') || '';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);

  const setCurrentPage = (page) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', page.toString());
    setSearchParams(params, { replace: true });
  };

  // Load candidates when URL params change
  useEffect(() => {
    const abortController = new AbortController();
    loadCandidates(currentPage, abortController.signal);
    return () => abortController.abort();
  }, [searchParams]);

  const handleSearch = (term) => {
    const params = new URLSearchParams(searchParams);
    if (term) {
      params.set('search', term);
    } else {
      params.delete('search');
    }
    params.set('page', '1');
    setSearchParams(params, { replace: true });
  };

  async function loadCandidates(page, signal = null) {
    setLoading(true);
    try {
      const params = { page, page_size: 10 };
      if (searchTerm) params.search = searchTerm;
      const candidatesData = await getCandidates(params, signal);
      setCandidates(candidatesData.results || []);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error("Error loading candidates:", err);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const params = { page_size: totalCount || 1000 };
      if (searchTerm) params.search = searchTerm;
      const allCandidatesData = await getCandidates(params);
      const allCandidates = allCandidatesData.results || [];
      const columns = [
        { key: 'candidate.full_name', label: 'Candidate Name' },
        { key: 'candidate_office.name', label: 'Race' },
        { key: 'candidate_party.name', label: 'Party' },
        { key: 'election_cycle.name', label: 'Election Cycle' },
        { key: 'is_incumbent', label: 'Status' },
      ];
      const csvData = allCandidates.map(c => ({
        ...c,
        'is_incumbent': c.is_incumbent ? 'Incumbent' : 'Challenger',
      }));
      await exportToCSV(csvData, columns, `candidates_${new Date().toISOString().split('T')[0]}.csv`, setExporting);
    } catch (error) {
      console.error("Export error:", error);
      setExporting(false);
    }
  };

  const ExportButton = (
    <button
      onClick={handleExportCSV}
      disabled={exporting || candidates.length === 0}
      className="flex items-center gap-2 bg-[#7667C1] hover:bg-[#6556b0] text-white px-5 py-2 rounded-full text-sm font-medium transition-all active:scale-95 disabled:opacity-50 shadow-sm"
    >
      {exporting ? <Loader className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
      <span>{exporting ? "Exporting..." : "Download Data"}</span>
    </button>
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner
            controls={ExportButton}
            searchTerm={searchTerm}
            onSearch={handleSearch}
          />

          <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className={darkMode ? 'bg-[#373052]' : 'bg-gray-50'}>
                  <tr>
                    {["Candidate Name", "Race", "Party", "Status", "Election Cycle", "Role"].map((h) => (
                      <th key={h} className={`py-4 px-6 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-100'}`}>
                  {loading ? (
                    <TableSkeleton rows={8} columns={6} />
                  ) : candidates.length === 0 ? (
                    <tr><td colSpan="6" className="py-12 text-center text-gray-500">No candidates found.</td></tr>
                  ) : (
                    candidates.map((candidate, idx) => (
                      <tr key={candidate.committee_id || idx} className={`transition-colors ${darkMode ? 'hover:bg-[#373052]' : 'hover:bg-purple-50/50'}`}>
                        <td className="py-4 px-6 flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#7667C1] flex items-center justify-center text-white text-xs font-bold">
                            {(candidate.candidate?.full_name || "U").charAt(0)}
                          </div>
                          <Link to={`/candidate/${candidate.committee_id}`} className={`text-sm font-medium ${darkMode ? 'text-white hover:text-purple-300' : 'text-gray-900 hover:text-purple-600'}`}>
                            {candidate.candidate?.full_name || "Unknown"}
                          </Link>
                        </td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{candidate.candidate_office?.name || "N/A"}</td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{candidate.candidate_party?.name || "N/A"}</td>
                        <td className="py-4 px-6">
                           <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${darkMode ? "bg-green-900/30 text-green-300" : "bg-green-100 text-green-700"}`}>Active</span>
                        </td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{candidate.election_cycle?.name || "N/A"}</td>
                        <td className="py-4 px-6 text-sm">
                          {candidate.is_incumbent ? 
                            <span className="text-blue-400 font-medium">Incumbent</span> : 
                            <span className="text-gray-400">Challenger</span>
                          }
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalCount={totalCount}
            onPageChange={setCurrentPage}
            loading={loading}
          />
        </div>
      </main>
    </div>
  );
}