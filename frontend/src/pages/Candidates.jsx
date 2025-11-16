import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight } from "lucide-react";
import { getCandidates } from "../api/api";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
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

  // Show preloader while initial data is loading
  if (loading && currentPage === 1) {
    return <Preloader message="Loading candidates..." />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content === */}
      <main className="ml-20 flex-1">
        {/* === Header === */}
      <Header title="Arizona Sunshine" subtitle="Candidates" />

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
                        Election Cycle
                      </th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">
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
                          <tr key={candidate.committee_id || idx} className="hover:bg-gray-50 transition">
                            <td className="py-5 px-6">
                              <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-600  flex items-center justify-center text-white font-semibold text-lg flex-shrink-0">
                                  {candidateName.charAt(0).toUpperCase()}
                                </div>
                                <Link 
                                  to={`/candidate/${candidate.committee_id}`}
                                  className="text-gray-900 font-medium hover:text-purple-600 transition"
                                >
                                  {candidateName}
                                </Link>
                              </div>
                            </td>
                            <td className="py-5 px-6 text-gray-700">
                              {candidate.candidate_office?.name || "N/A"}
                            </td>
                            <td className="py-5 px-6 text-gray-700">
                              {candidate.candidate_party?.name || "N/A"}
                            </td>
                            <td className="py-5 px-6">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${status.color}`}>
                                {status.label}
                              </span>
                            </td>
                            <td className="py-5 px-6 text-gray-700">
                              {candidate.election_cycle?.name || "N/A"}
                            </td>
                            <td className="py-5 px-6 text-gray-700">
                              {candidate.is_incumbent ? (
                                <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                  Incumbent
                                </span>
                              ) : (
                                <span className="text-gray-500">Challenger</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
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

