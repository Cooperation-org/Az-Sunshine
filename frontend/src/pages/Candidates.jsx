import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight } from "lucide-react";
import { getCandidates, getExpenditures } from "../api/api";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadCandidates(currentPage);
  }, [currentPage]);

  async function loadCandidates(page) {
    setLoading(true);
    try {
      const [candidatesData, expendituresData] = await Promise.all([
        getCandidates({ page, page_size: 10 }),
        getExpenditures({ page_size: 1000 })
      ]);
      
      const candidatesList = candidatesData.results || [];
      const expenditures = expendituresData.results || [];
      
      // Calculate IE totals for each candidate
      const candidatesWithTotals = candidatesList.map(candidate => {
        const candidateExpenditures = expenditures.filter(
          exp => exp.candidate?.id === candidate.id || exp.candidate_name === candidate.name
        );
        
        const forTotal = candidateExpenditures
          .filter(exp => exp.support_oppose === "Support")
          .reduce((sum, exp) => sum + Number(exp.amount || 0), 0);
        
        const againstTotal = candidateExpenditures
          .filter(exp => exp.support_oppose === "Oppose")
          .reduce((sum, exp) => sum + Number(exp.amount || 0), 0);
        
        return {
          ...candidate,
          ie_total_for: forTotal,
          ie_total_against: againstTotal
        };
      });
      
      setCandidates(candidatesWithTotals);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));
    } catch (err) {
      console.error("Error loading candidates:", err);
    } finally {
      setLoading(false);
    }
  }

  const getContactedStatus = (candidate) => {
    if (candidate.contacted) {
      return { label: "Contacted", color: "bg-green-100 text-green-700" };
    } else if (candidate.contacted_at) {
      return { label: "Attempted", color: "bg-yellow-100 text-yellow-700" };
    }
    return { label: "Not Contacted", color: "bg-red-100 text-red-700" };
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
            <p className="text-sm text-gray-500">Candidates</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search"
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
              Loading candidates...
            </div>
          ) : (
            <>
              {/* === Candidates Table === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        Candidate Name
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        Race
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        Party
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        Contacted Status
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        IE Total For
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
                        IE Total Against
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {candidates.map((candidate, idx) => {
                      const status = getContactedStatus(candidate);
                      return (
                        <tr key={candidate.id || idx} className="hover:bg-gray-50 transition">
                          <td className="py-5 px-6">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-600  flex items-center justify-center text-white font-semibold text-lg flex-shrink-0">
                                {candidate.name?.charAt(0)?.toUpperCase() || "?"}
                              </div>
                              <Link 
                                to={`/candidate/${candidate.id}`}
                                className="text-gray-900 font-medium hover:text-purple-600 transition"
                              >
                                {candidate.name || "Unknown"}
                              </Link>
                            </div>
                          </td>
                          <td className="py-5 px-6 text-gray-700">
                            {candidate.race?.name || candidate.race || "N/A"}
                          </td>
                          <td className="py-5 px-6 text-gray-700">
                            {candidate.party?.name || "N/A"}
                          </td>
                          <td className="py-5 px-6">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${status.color}`}>
                              {status.label}
                            </span>
                          </td>
                          <td className="py-5 px-6 text-green-600 font-semibold">
                            ${Number(candidate.ie_total_for || 0).toLocaleString()}
                          </td>
                          <td className="py-5 px-6 text-red-600 font-semibold">
                            ${Number(candidate.ie_total_against || 0).toLocaleString()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* === Results Count and Pagination === */}
              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {totalCount} Results
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

