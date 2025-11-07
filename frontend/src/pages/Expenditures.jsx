import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, ChevronLeft } from "lucide-react";
import { getExpenditures } from "../api/api";
import Sidebar from "../components/Sidebar";

export default function Expenditures() {
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");

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
            <p className="text-sm text-gray-500">Independent Expenditures</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by committee, candidate, or type..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-80 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
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
              Loading expenditures...
            </div>
          ) : (
            <>
              {/* === Summary Stats === */}
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div className="bg-white rounded-2xl p-6 shadow-lg">
                  <p className="text-gray-500 text-sm mb-1">Total Expenditures</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {totalCount.toLocaleString()}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-6 shadow-lg">
                  <p className="text-gray-500 text-sm mb-1">Total Amount</p>
                  <p className="text-3xl font-bold text-gray-900">
                    ${expenditures
                      .reduce((sum, exp) => sum + parseFloat(exp.amount || 0), 0)
                      .toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-6 shadow-lg">
                  <p className="text-gray-500 text-sm mb-1">Showing</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {filteredExpenditures.length} {filteredExpenditures.length === 1 ? "result" : "results"}
                  </p>
                </div>
              </div>

              {/* === Expenditures Table === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Committee Name
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Candidate
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 uppercase tracking-wider">
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
                        <tr key={idx} className="hover:bg-gray-50 transition">
                          <td className="py-5 px-6 text-gray-700">
                            {formatDate(exp.date)}
                          </td>
                          <td className="py-5 px-6">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white font-semibold flex-shrink-0">
                                {(exp.ie_committee?.name || "?").charAt(0).toUpperCase()}
                              </div>
                              <span className="text-gray-900 font-medium">
                                {exp.ie_committee?.name || "Unknown Committee"}
                              </span>
                            </div>
                          </td>
                          <td className="py-5 px-6 text-gray-700 font-medium">
                            {exp.candidate_name || "N/A"}
                          </td>
                          <td className="py-5 px-6 text-gray-900 font-semibold">
                            ${parseFloat(exp.amount || 0).toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                          <td className="py-5 px-6">
                            <div className="flex flex-col gap-1">
                              <span
                                className={`px-3 py-1 rounded-full text-xs font-medium w-fit ${
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
                                <span className="text-xs text-gray-500 mt-1">
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

              {/* === Pagination === */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Showing page {currentPage} of {totalPages} ({totalCount} total results)
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className={`w-10 h-10 rounded-lg flex items-center justify-center transition ${
                        currentPage === 1
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                      }`}
                    >
                      <ChevronLeft className="w-5 h-5" />
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
                        className={`w-10 h-10 rounded-lg font-medium transition ${
                          currentPage === page
                            ? "bg-purple-600 text-white"
                            : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className={`w-10 h-10 rounded-lg flex items-center justify-center transition ${
                        currentPage === totalPages
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                      }`}
                    >
                      <ChevronRight className="w-5 h-5" />
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

