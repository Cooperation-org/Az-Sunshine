import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight } from "lucide-react";
import { getDonors } from "../api/api";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
export default function Donors() {
  const [donors, setDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");

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

  // Show preloader while initial data is loading
  if (loading && currentPage === 1) {
    return <Preloader message="Loading donors..." />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content - Responsive: No left margin on mobile === */}
      <main className="flex-1 lg:ml-0 min-w-0">
        {/* === Header === */}
        <Header title="Arizona Sunshine" subtitle="Donors" />

        {/* === Content - Responsive padding === */}
        <div className="p-4 sm:p-6 lg:p-8">
          {loading ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Loading donors...
            </div>
          ) : (
            <>
              {/* === Donors Table - Responsive: Horizontal scroll on mobile === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                {/* Table Container - Horizontal scroll on mobile */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        {/* Table Headers - Responsive text sizes and padding */}
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Donor/Entity Name
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Entity Type
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Location
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {donors.length === 0 ? (
                        <tr>
                          <td colSpan="3" className="py-8 sm:py-12 text-center text-xs sm:text-sm text-gray-500">
                            {searchTerm
                              ? "No donors found matching your search."
                              : "No donors found."}
                          </td>
                        </tr>
                      ) : (
                        donors.map((donor, idx) => (
                        <tr key={donor.name_id || idx} className="hover:bg-gray-50 transition">
                          {/* Table Cells - Responsive padding and text sizes */}
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex items-center gap-2 sm:gap-4">
                              {/* Avatar - Responsive size */}
                              <div className="w-8 h-8 sm:w-10 sm:h-12 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white text-xs sm:text-sm lg:text-lg font-semibold flex-shrink-0">
                                {(donor.full_name || donor.name || "?").charAt(0).toUpperCase()}
                              </div>
                              <span className="text-xs sm:text-sm lg:text-base text-gray-900 font-medium truncate">{donor.full_name || donor.name || "Unknown"}</span>
                            </div>
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 font-medium whitespace-nowrap">
                            {donor.entity_type?.name || "N/A"}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-900 font-semibold whitespace-nowrap">
                            {donor.city && donor.state ? `${donor.city}, ${donor.state}` : "N/A"}
                          </td>
                        </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* === Pagination - Responsive: Stack on mobile === */}
              <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                <p className="text-xs sm:text-sm text-gray-600">
                  {totalCount} results
                </p>
                {/* Pagination - Responsive: Wrap on mobile */}
                <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg text-xs sm:text-sm font-medium transition ${
                        currentPage === page
                          ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
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

