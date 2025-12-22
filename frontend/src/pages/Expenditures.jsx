import React, { useEffect, useState, useRef } from "react";
import { ChevronRight, Download, Loader, Search } from "lucide-react";
import { getExpenditures } from "../api/api";
import Sidebar from "../components/Sidebar";
import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";

// --- REFINED BANNER COMPONENT ---
const Banner = ({ controls, searchTerm, setSearchTerm, onSearch }) => {
  const { darkMode } = useDarkMode();

  const handleLocalSearch = (e) => {
    e.preventDefault();
    onSearch();
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
              Political <span style={{ color: '#A78BFA' }}>Expenditures</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Track campaign spending and financial activity to ensure transparency.
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
              placeholder="Search purpose or committee..."
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

// --- MAIN EXPENDITURES PAGE ---
export default function Expenditures() {
  const { darkMode } = useDarkMode();
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);
  const isFirstRender = useRef(true);

  useEffect(() => {
    loadExpenditures(currentPage);
  }, [currentPage]);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const delaySearch = setTimeout(() => {
      setCurrentPage(1);
      loadExpenditures(1);
    }, 500);
    return () => clearTimeout(delaySearch);
  }, [searchTerm]);

  const handleSearch = () => {
    setCurrentPage(1);
    loadExpenditures(1);
  };

  async function loadExpenditures(page) {
    setLoading(true);
    try {
      const params = { page, page_size: 10 };
      if (searchTerm) params.search = searchTerm;
      const data = await getExpenditures(params);
      setExpenditures(data.results || []);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / 10));
    } catch (err) {
      console.error("Error loading expenditures:", err);
      setExpenditures([]);
    } finally {
      setLoading(false);
    }
  }

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const params = { page_size: totalCount || 1000 };
      if (searchTerm) params.search = searchTerm;
      const allData = await getExpenditures(params);
      const allExpenditures = allData.results || [];
      const columns = [
        { key: 'committee.name.full_name', label: 'Committee' },
        { key: 'subject_committee.name.full_name', label: 'Candidate' },
        { key: 'transaction_date', label: 'Date' },
        { key: 'amount', label: 'Amount' },
        { key: 'is_for_benefit', label: 'Type' },
        { key: 'purpose', label: 'Purpose' },
      ];
      const csvData = allExpenditures.map(exp => ({
        ...exp,
        'is_for_benefit': exp.is_for_benefit === true ? 'Support' : exp.is_for_benefit === false ? 'Oppose' : 'N/A',
      }));
      await exportToCSV(csvData, columns, `expenditures_${new Date().toISOString().split('T')[0]}.csv`, setExporting);
    } catch (error) {
      console.error("Export error:", error);
      setExporting(false);
    }
  };

  const ExportButton = (
    <button
      onClick={handleExportCSV}
      disabled={exporting || expenditures.length === 0}
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
            setSearchTerm={setSearchTerm}
            onSearch={handleSearch}
          />
          
          <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className={darkMode ? 'bg-[#373052]' : 'bg-gray-50'}>
                  <tr>
                    {["Committee", "Candidate", "Date", "Amount", "Type", "Purpose"].map((h) => (
                      <th key={h} className={`py-4 px-6 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-100'}`}>
                  {loading && currentPage === 1 ? (
                    <TableSkeleton rows={10} columns={6} />
                  ) : expenditures.length === 0 ? (
                    <tr><td colSpan="6" className="py-12 text-center text-gray-500 text-sm">No expenditures found.</td></tr>
                  ) : (
                    expenditures.map((exp, idx) => (
                      <tr key={exp.transaction_id || idx} className={`transition-colors ${darkMode ? 'hover:bg-[#373052]' : 'hover:bg-purple-50/50'}`}>
                        <td className={`py-4 px-6 text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          {exp.committee?.name?.full_name || 'N/A'}
                        </td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                          {exp.subject_committee?.name?.full_name || 'N/A'}
                        </td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          {exp.transaction_date ? new Date(exp.transaction_date).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className={`py-4 px-6 text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          ${Math.abs(parseFloat(exp.amount || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            exp.is_for_benefit === true 
                              ? "bg-green-100 text-green-700" 
                              : exp.is_for_benefit === false ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-700"
                          }`}>
                            {exp.is_for_benefit === true ? 'Support' : exp.is_for_benefit === false ? 'Oppose' : 'N/A'}
                          </span>
                        </td>
                        <td className={`py-4 px-6 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} max-w-xs truncate`}>
                          {exp.purpose || 'N/A'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{totalCount} Results</p>
            <div className="flex gap-2">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${
                    currentPage === page
                      ? 'bg-[#7667C1] text-white shadow-md'
                      : darkMode ? 'bg-[#2D2844] text-gray-300 hover:bg-[#373052]' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}