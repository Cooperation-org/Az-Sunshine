import React, { useEffect, useState } from "react";
import { ChevronRight, Download, Loader, Search } from "lucide-react";
import { getExpenditures } from "../api/api";
import Sidebar from "../components/Sidebar";
import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";

// New Banner Component (Reused from other pages, updated for Expenditures)
const Banner = ({ controls, children, searchTerm, setSearchTerm, onSearch }) => {
  const { darkMode } = useDarkMode();

  // Local handler to submit search on form submit
  const handleLocalSearch = (e) => {
    e.preventDefault();
    onSearch();
  }

  return (
    <div className={`relative rounded-2xl overflow-hidden shadow-2xl mb-8 ${darkMode ? 'bg-gradient-to-br from-[#4C3D7D] to-[#3d3559]' : 'bg-gradient-to-br from-[#6B5B95] to-[#4C3D7D]'}`}>
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="pattern-circles" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse" patternContentUnits="userSpaceOnUse">
              <circle id="pattern-circle" cx="20" cy="20" r="2" fill="white"></circle>
            </pattern>
            <pattern id="pattern-squares" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="4" height="4" fill="white" opacity="0.5"></rect>
              <rect x="10" y="10" width="4" height="4" fill="white" opacity="0.5"></rect>
            </pattern>
          </defs>
          <rect x="0" y="0" width="100%" height="100%" fill="url(#pattern-circles)"></rect>
          <rect x="0" y="0" width="100%" height="100%" fill="url(#pattern-squares)" mask="url(#pattern-circles)"></rect>
        </svg>
      </div>
      <div className="relative p-8 sm:p-12 lg:p-16 text-center">
        {/* Controls positioned top-right */}
        {controls && (
          <div className="absolute top-4 right-4 sm:top-8 sm:right-8 z-10">
            {controls}
          </div>
        )}

        {/* Updated heading and subtext to the smaller sizes (text-3xl / text-4xl & text-base / text-lg) */}
        <h1 className="text-3xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
          Review Political Expenditures
        </h1>
        <p className="mt-4 text-base sm:text-lg text-gray-200 max-w-2xl mx-auto">
          Track campaign spending and financial activity.
        </p>
        <div className="mt-8 max-w-md mx-auto">
          <form onSubmit={handleLocalSearch} className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search purpose or committee..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-3 rounded-full text-lg ${darkMode ? 'bg-[#3d3559] text-white placeholder-gray-400 border border-transparent focus:ring-2 focus:ring-[#7d6fa3]' : 'bg-white text-gray-900 placeholder-gray-500 border border-gray-300 focus:ring-2 focus:ring-[#6B5B95]'}`}
            />
          </form>
        </div>
        {children}
      </div>
    </div>
  );
};


export default function Expenditures() {
  const { darkMode } = useDarkMode();
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState(""); // New state for search term
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadExpenditures(currentPage);
  }, [currentPage]);
  
  // New effect to re-load data when search term changes or enter is pressed
  const handleSearch = () => {
    if (currentPage !== 1) {
        setCurrentPage(1);
    } else {
        loadExpenditures(1);
    }
  };

  async function loadExpenditures(page) {
    setLoading(true);
    try {
      const params = { page, page_size: 10 };
      if (searchTerm) {
        params.search = searchTerm; // Apply search filter to API call
      }
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
      if (searchTerm) {
        params.search = searchTerm; // Apply search filter to export API call
      }

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
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `expenditures_${timestamp}.csv`;
      
      await exportToCSV(csvData, columns, filename, setExporting);
      
    } catch (error) {
      console.error("Error exporting CSV:", error);
      alert("Failed to export CSV. Please try again.");
      setExporting(false);
    }
  };

  // JSX for the Export Button, passed to the Banner
  const ExportButton = (
    <button
      onClick={handleExportCSV}
      disabled={exporting || expenditures.length === 0}
      className={`flex items-center gap-2 px-3 py-2 ${darkMode ? 'bg-white/10 hover:bg-white/20 backdrop-blur-sm' : 'bg-white/30 backdrop-blur-sm hover:bg-white/50'} text-white rounded-xl transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg active:scale-95 text-sm sm:text-base border border-white/20`}
    >
      {exporting ? (
        <>
          <Loader className="w-4 h-4 animate-spin" />
          <span>Exporting...</span>
        </>
      ) : (
        <>
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </>
      )}
    </button>
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 lg:ml-0 min-w-0">

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Integrated Banner */}
          <Banner 
            controls={ExportButton}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            onSearch={handleSearch}
          />
          
          {loading && currentPage === 1 ? (
            <>
              {/* Removed original loading button placeholder */}
              
              <div className={`overflow-x-auto shadow-lg rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>
                <table className="min-w-full divide-y divide-gray-200">
                  <tbody>
                    <TableSkeleton rows={10} columns={6} />
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <>
              {/* Removed original button div */}

              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'} border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                      <tr>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Committee</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Candidate</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Date</th>
                        <th className={`text-right py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Amount</th>
                        <th className={`text-center py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Type</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Purpose</th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-100'}`}>
                      {expenditures.length === 0 ? (
                        <tr>
                          <td colSpan="6" className={`py-12 text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            No expenditures found.
                          </td>
                        </tr>
                      ) : (
                        expenditures.map((exp, idx) => (
                          <tr key={exp.transaction_id || idx} className={`transition-colors duration-150 ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50/50'}`}>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-900'} font-medium`}>
                              {exp.committee?.name?.full_name || 'N/A'}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                              {exp.subject_committee?.name?.full_name || 'N/A'}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                              {exp.transaction_date ? new Date(exp.transaction_date).toLocaleDateString() : 'N/A'}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-white' : 'text-gray-900'} font-bold text-right`}>
                              ${Math.abs(parseFloat(exp.amount || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3 sm:py-4 px-3 sm:px-6 text-center">
                              <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                                exp.is_for_benefit === true 
                                  ? darkMode ? 'bg-green-900/30 text-green-300' : 'bg-green-100 text-green-800'
                                  : exp.is_for_benefit === false
                                  ? darkMode ? 'bg-red-900/30 text-red-300' : 'bg-red-100 text-red-800'
                                  : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'
                              }`}>
                                {exp.is_for_benefit === true ? 'Support' : exp.is_for_benefit === false ? 'Oppose' : 'N/A'}
                              </span>
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} max-w-xs truncate`}>
                              {exp.purpose || 'N/A'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                <p className={`text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  {totalCount} Results
                </p>
                <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${
                        currentPage === page
                          ? darkMode ? 'bg-[#7d6fa3] text-white shadow-md' : 'bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md'
                          : darkMode ? 'bg-[#4a3f66] text-gray-300 hover:bg-[#5f5482]' : 'bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  {totalPages > 5 && (
                    <button
                      onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg ${darkMode ? 'bg-[#4a3f66] text-gray-300 hover:bg-[#5f5482]' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'} flex items-center justify-center transition`}
                    >
                      <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}