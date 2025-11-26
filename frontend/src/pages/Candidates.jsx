import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, Download, Loader } from "lucide-react";
import { getCandidates } from "../api/api";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";

export default function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadCandidates(currentPage);
  }, [currentPage]);

  async function loadCandidates(page) {
    setLoading(true);
    try {
      const candidatesData = await getCandidates({ page, page_size: 10 });
      
      const candidatesList = candidatesData.results || [];
      
      setCandidates(candidatesList);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));
    } catch (err) {
      console.error("Error loading candidates:", err);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  const getContactedStatus = (candidate) => {
    // Since we're using committees, we don't have SOI contact status
    // Return a default status
    return { label: "Active", color: "bg-green-100 text-green-700" };
  };

  // Export candidates to CSV
  const handleExportCSV = async () => {
    try {
      setExporting(true);
      
      // Load all candidates for export (not just current page)
      const allCandidatesData = await getCandidates({ page_size: totalCount || 1000 });
      const allCandidates = allCandidatesData.results || [];
      
      // Define CSV columns
      const columns = [
        { key: 'candidate.full_name', label: 'Candidate Name' },
        { key: 'name.full_name', label: 'Candidate Name (Alt)' },
        { key: 'candidate_office.name', label: 'Race' },
        { key: 'candidate_party.name', label: 'Party' },
        { key: 'election_cycle.name', label: 'Election Cycle' },
        { key: 'is_incumbent', label: 'Status' },
      ];
      
      // Transform data for CSV
      const csvData = allCandidates.map(candidate => ({
        ...candidate,
        'is_incumbent': candidate.is_incumbent ? 'Incumbent' : 'Challenger',
      }));
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `candidates_${timestamp}.csv`;
      
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
        <Header title="Arizona Sunshine" subtitle="Candidates" />

        {/* === Content - Responsive padding === */}
        <div className="p-4 sm:p-6 lg:p-8">
          {loading && currentPage === 1 ? (
            <>
              <div className="mb-4 sm:mb-6 flex justify-end">
                <div className="h-10 w-32 rounded-lg animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]"></div>
              </div>
              <TableSkeleton rows={8} columns={6} />
            </>
          ) : (
            <>
              {/* === Export Button - Responsive === */}
              <div className="mb-4 sm:mb-6 flex justify-end">
                <button
                  onClick={handleExportCSV}
                  disabled={exporting || candidates.length === 0}
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

              {/* === Candidates Table - Responsive: Horizontal scroll on mobile === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                {/* Table Container - Horizontal scroll on mobile */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        {/* Table Headers - Responsive text sizes and padding */}
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Candidate Name
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Race
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Party
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Contacted Status
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Election Cycle
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">
                          Status
                        </th>
                      </tr>
                    </thead>
                  <tbody className="divide-y divide-gray-100">
                    {candidates.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="py-12 text-center text-gray-500">
                          No candidates found.
                        </td>
                      </tr>
                    ) : (
                      candidates.map((candidate, idx) => {
                        const status = getContactedStatus(candidate);
                        const candidateName = candidate.candidate?.full_name || candidate.name?.full_name || "Unknown";
                        return (
                          <tr key={candidate.committee_id || idx} className="hover:bg-purple-50/50 transition-colors duration-150">
                            {/* Table Cells - Responsive padding and text sizes */}
                            <td className="py-3 sm:py-5 px-3 sm:px-6">
                              <div className="flex items-center gap-2 sm:gap-4">
                                {/* Avatar - Responsive size */}
                                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D]  flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0 shadow-sm">
                                  {candidateName.charAt(0).toUpperCase()}
                                </div>
                                <Link 
                                  to={`/candidate/${candidate.committee_id}`}
                                  className="text-gray-900 text-xs sm:text-sm lg:text-base font-medium hover:text-purple-600 transition truncate"
                                >
                                  {candidateName}
                                </Link>
                              </div>
                            </td>
                            <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                              {candidate.candidate_office?.name || "N/A"}
                            </td>
                            <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                              {candidate.candidate_party?.name || "N/A"}
                            </td>
                            <td className="py-3 sm:py-5 px-3 sm:px-6">
                              <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${status.color}`}>
                                {status.label}
                              </span>
                            </td>
                            <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                              {candidate.election_cycle?.name || "N/A"}
                            </td>
                            <td className="py-3 sm:py-5 px-3 sm:px-6">
                              {candidate.is_incumbent ? (
                                <span className="px-2 sm:px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 whitespace-nowrap">
                                  Incumbent
                                </span>
                              ) : (
                                <span className="text-xs sm:text-sm text-gray-500">Challenger</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                  </table>
                </div>
              </div>

              {/* === Results Count and Pagination - Responsive: Stack on mobile === */}
              <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                <p className="text-xs sm:text-sm text-gray-600">
                  {totalCount} Results
                </p>
                {/* Pagination - Responsive: Wrap on mobile */}
                <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
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
                  {totalPages > 5 && (
                    <button
                      onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}
                      className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition"
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

