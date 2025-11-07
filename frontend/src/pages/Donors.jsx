import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight } from "lucide-react";
import { getDonors } from "../api/api";
import Sidebar from "../components/Sidebar";

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

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content === */}
      <main className="ml-20 flex-1">
        {/* === Header === */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Arizona Sunshine</h1>
            <p className="text-sm text-gray-500">Donor Entities</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <form onSubmit={handleSearch}>
                <input
                  type="text"
                  placeholder="Search donors..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-80 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </form>
            </div>
            <button className="p-2 rounded-lg bg-purple-600 hover:bg-purple-700 transition">
              <Bell className="w-5 h-5 text-white" />
            </button>
          </div>
        </header>

        {/* === Content === */}
        <div className="p-8">
          {loading ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Loading donors...
            </div>
          ) : (
            <>
              {/* === Donors Table === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Donor/Entity Name
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Entity Type
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Location
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {donors.length === 0 ? (
                      <tr>
                        <td colSpan="3" className="py-12 text-center text-gray-500">
                          {searchTerm
                            ? "No donors found matching your search."
                            : "No donors found."}
                        </td>
                      </tr>
                    ) : (
                      donors.map((donor, idx) => (
                      <tr key={donor.name_id || idx} className="hover:bg-gray-50 transition">
                        <td className="py-5 px-6">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white font-semibold text-lg flex-shrink-0">
                              {(donor.full_name || donor.name || "?").charAt(0).toUpperCase()}
                            </div>
                            <span className="text-gray-900 font-medium">{donor.full_name || donor.name || "Unknown"}</span>
                          </div>
                        </td>
                        <td className="py-5 px-6 text-gray-700 font-medium">
                          {donor.entity_type?.name || "N/A"}
                        </td>
                        <td className="py-5 px-6 text-gray-900 font-semibold">
                          {donor.city && donor.state ? `${donor.city}, ${donor.state}` : "N/A"}
                        </td>
                      </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* === Pagination === */}
              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {totalCount} results
                </p>
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
            </>
          )}
        </div>
      </main>
    </div>
  );
}

