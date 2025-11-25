import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, ChevronLeft, Download, Loader } from "lucide-react";
import { getExpenditures } from "../api/api";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
import { exportToCSV } from "../utils/csvExport";

export default function Expenditures() {
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadExpenditures(currentPage);
  }, [currentPage]);

  async function loadExpenditures(page) {
    setLoading(true);
    try {
      const data = await getExpenditures({ page, page_size: 25 });
      setExpenditures(data.results || []);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / 25));
    } catch (err) {
      console.error("Error loading expenditures:", err);
      setExpenditures([]);
    } finally {
      setLoading(false);
    }
  }

  // Filter expenditures based on search term
  const filteredExpenditures = expenditures.filter((exp) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      (exp.ie_committee?.name || "").toLowerCase().includes(searchLower) ||
      (exp.candidate_name || "").toLowerCase().includes(searchLower) ||
      (exp.support_oppose || "").toLowerCase().includes(searchLower)
    );
  });

  // Show preloader while initial data is loading
  if (loading && currentPage === 1) {
    return <Preloader message="Loading expenditures..." />;
  }

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  // Export expenditures to CSV
  const handleExportCSV = async () => {
    try {
      setExporting(true);
      
      // Load all expenditures for export (not just current page)
      const allExpendituresData = await getExpenditures({ page_size: totalCount || 1000 });
      const allExpenditures = allExpendituresData.results || [];
      
      // Filter if search term exists
      const dataToExport = searchTerm
        ? allExpenditures.filter((exp) => {
            const searchLower = searchTerm.toLowerCase();
            return (
              (exp.ie_committee?.name || "").toLowerCase().includes(searchLower) ||
              (exp.candidate_name || "").toLowerCase().includes(searchLower) ||
              (exp.support_oppose || "").toLowerCase().includes(searchLower)
            );
          })
        : allExpenditures;
      
      // Define CSV columns
      const columns = [
        { key: 'date', label: 'Date' },
        { key: 'ie_committee.name', label: 'Committee Name' },
        { key: 'candidate_name', label: 'Candidate' },
        { key: 'amount', label: 'Amount' },
        { key: 'support_oppose', label: 'Support/Oppose' },
        { key: 'purpose', label: 'Purpose' },
      ];
      
      // Transform data for CSV (format dates)
      const csvData = dataToExport.map(exp => ({
        ...exp,
        date: exp.date ? formatDate(exp.date) : 'N/A',
        'ie_committee.name': exp.ie_committee?.name || 'Unknown Committee',
        amount: parseFloat(exp.amount || 0).toFixed(2),
      }));
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `expenditures_${timestamp}.csv`;
      
      // Export to CSV
      await exportToCSV(csvData, columns, filename, setExporting);
      
    } catch (error) {
      console.error("Error exporting CSV:", error);
      alert("Failed to export CSV. Please try again.");
      setExporting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content - Responsive: No left margin on mobile === */}
      <main className="flex-1 lg:ml-0 min-w-0">
        {/* === Header === */}
        <Header title="Arizona Sunshine" subtitle="Expenditures" />

        {/* === Content - Responsive padding === */}
        <div className="p-4 sm:p-6 lg:p-8">
          {loading ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Loading expenditures...
            </div>
          ) : (
            <>
              {/* === Export Button - Responsive === */}
              <div className="mb-4 sm:mb-6 flex justify-end">
                <button
                  onClick={handleExportCSV}
                  disabled={exporting || filteredExpenditures.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md active:scale-95 text-sm sm:text-base"
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
              </div>

              {/* === Summary Stats - Responsive: 1 column on mobile, 3 on desktop === */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
                {/* Stats Cards - Responsive padding and text sizes */}
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Total Expenditures</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {totalCount.toLocaleString()}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Total Amount</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    ${filteredExpenditures
                      .reduce((sum, exp) => sum + parseFloat(exp.amount || 0), 0)
                      .toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Showing</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {filteredExpenditures.length} {filteredExpenditures.length === 1 ? "result" : "results"}
                  </p>
                </div>
              </div>

              {/* === Expenditures Table - Responsive: Horizontal scroll on mobile === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                {/* Table Container - Horizontal scroll on mobile */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        {/* Table Headers - Responsive text sizes and padding */}
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Date
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Committee Name
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Candidate
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Amount
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Purpose
                        </th>
                      </tr>
                    </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredExpenditures.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-gray-500">
                          {searchTerm
                            ? "No expenditures found matching your search."
                            : "No expenditures found."}
                        </td>
                      </tr>
                    ) : (
                      filteredExpenditures.map((exp, idx) => (
                        <tr key={idx} className="hover:bg-purple-50/50 transition-colors duration-150">
                          {/* Table Cells - Responsive padding and text sizes */}
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                            {formatDate(exp.date)}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex items-center gap-2 sm:gap-3">
                              {/* Avatar - Responsive size */}
                              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0">
                                {(exp.ie_committee?.name || "?").charAt(0).toUpperCase()}
                              </div>
                              <span className="text-xs sm:text-sm lg:text-base text-gray-900 font-medium truncate max-w-[120px] sm:max-w-none">
                                {exp.ie_committee?.name || "Unknown Committee"}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 font-medium truncate max-w-[100px] sm:max-w-none">
                            {exp.candidate_name || "N/A"}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-900 font-semibold whitespace-nowrap">
                            ${parseFloat(exp.amount || 0).toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex flex-col gap-1">
                              <span
                                className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium w-fit whitespace-nowrap ${
                                  exp.support_oppose === "Support"
                                    ? "bg-green-100 text-green-700"
                                    : exp.support_oppose === "Oppose"
                                    ? "bg-red-100 text-red-700"
                                    : "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {exp.support_oppose || "Unknown"}
                              </span>
                              {exp.purpose && (
                                <span className="text-xs text-gray-500 mt-1 truncate max-w-[150px] sm:max-w-none">
                                  {exp.purpose}
                                </span>
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

              {/* === Pagination - Responsive: Stack on mobile === */}
              {totalPages > 1 && (
                <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                  <p className="text-xs sm:text-sm text-gray-600">
                    Showing page {currentPage} of {totalPages} ({totalCount} total results)
                  </p>
                  {/* Pagination - Responsive: Wrap on mobile */}
                  <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center transition-all duration-200 ${
                        currentPage === 1
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                      }`}
                    >
                      <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                    {Array.from(
                      { length: Math.min(totalPages, 5) },
                      (_, i) => {
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
                        return page;
                      }
                    ).map((page) => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${
                          currentPage === page
                            ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md"
                            : "bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center transition ${
                        currentPage === totalPages
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                      }`}
                    >
                      <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

