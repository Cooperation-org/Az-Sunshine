import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, Download, Loader } from "lucide-react";
import { getDonors } from "../api/api";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";

export default function Donors() {
  const { darkMode } = useDarkMode();
  const [donors, setDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadDonors(currentPage);
  }, [currentPage]);

  async function loadDonors(page) {
    setLoading(true);
    try {
      const params = { page, page_size: 8 };
      if (searchTerm) {
        params.search = searchTerm;
      }
      const data = await getDonors(params);
      setDonors(data.results || []);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / 8));
    } catch (err) {
      console.error("Error loading donors:", err);
      setDonors([]);
    } finally {
      setLoading(false);
    }
  }

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    loadDonors(1);
  };

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      
      const params = { page_size: totalCount || 1000 };
      if (searchTerm) {
        params.search = searchTerm;
      }
      const allDonorsData = await getDonors(params);
      const allDonors = allDonorsData.results || [];
      
      const columns = [
        { key: 'full_name', label: 'Donor/Entity Name' },
        { key: 'name', label: 'Name (Alt)' },
        { key: 'entity_type.name', label: 'Entity Type' },
        { key: 'city', label: 'City' },
        { key: 'state', label: 'State' },
        { key: 'location', label: 'Location' },
      ];
      
      const csvData = allDonors.map(donor => ({
        ...donor,
        location: donor.city && donor.state ? `${donor.city}, ${donor.state}` : (donor.city || donor.state || 'N/A'),
      }));
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `donors_${timestamp}.csv`;
      
      await exportToCSV(csvData, columns, filename, setExporting);
      
    } catch (error) {
      console.error("Error exporting CSV:", error);
      alert("Failed to export CSV. Please try again.");
      setExporting(false);
    }
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 lg:ml-0 min-w-0">
        <Header />

        <div className="p-4 sm:p-6 lg:p-8">
          {loading && currentPage === 1 ? (
            <>
              <div className="mb-4 sm:mb-6 flex justify-end">
                <div className="h-10 w-32 rounded-lg animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]"></div>
              </div>
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'} border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                      <tr>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Donor/Entity Name
                        </th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Entity Type
                        </th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Location
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-200'}`}>
                      <TableSkeleton rows={8} cols={3} />
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="mb-4 sm:mb-6 flex justify-end">
                <button
                  onClick={handleExportCSV}
                  disabled={exporting || donors.length === 0}
                  className={`flex items-center gap-2 px-4 py-2 ${darkMode ? 'bg-[#7d6fa3] hover:bg-[#8b7cb8]' : 'bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] hover:from-[#7C6BA6] hover:to-[#5B4D7D]'} text-white rounded-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md active:scale-95 text-sm sm:text-base`}
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

              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'} border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                      <tr>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Donor/Entity Name
                        </th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Entity Type
                        </th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider whitespace-nowrap`}>
                          Location
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-200'}`}>
                      {donors.length === 0 ? (
                        <tr>
                          <td colSpan="3" className={`py-8 sm:py-12 text-center text-xs sm:text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            {searchTerm
                              ? "No donors found matching your search."
                              : "No donors found."}
                          </td>
                        </tr>
                      ) : (
                        donors.map((donor, idx) => (
                        <tr key={donor.name_id || idx} className={`transition-colors duration-150 ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50/50'}`}>
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex items-center gap-2 sm:gap-4">
                              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0 shadow-sm">
                                {(donor.full_name || donor.name || "?").charAt(0).toUpperCase()}
                              </div>
                              <span className={`text-xs sm:text-sm lg:text-base ${darkMode ? 'text-white' : 'text-gray-900'} font-medium truncate`}>{donor.full_name || donor.name || "Unknown"}</span>
                            </div>
                          </td>
                          <td className={`py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} font-medium whitespace-nowrap`}>
                            {donor.entity_type?.name || "N/A"}
                          </td>
                          <td className={`py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-white' : 'text-gray-900'} font-semibold whitespace-nowrap`}>
                            {donor.city && donor.state ? `${donor.city}, ${donor.state}` : "N/A"}
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
                  {totalCount} results
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