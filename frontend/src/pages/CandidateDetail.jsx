// frontend/src/pages/CandidateDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getCandidate,
  getExpenditures,
  getCandidateIESpending,
  getCandidateIEByCommittee,
} from "../api/api";
import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import Preloader from "../components/Preloader";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [expenditures, setExpenditures] = useState([]);
  const [ieSpending, setIESpending] = useState(null);
  const [ieByCommittee, setIEByCommittee] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCandidate() {
      setLoading(true);
      try {
        const [candData, expData, ieData, ieCommData] = await Promise.all([
          getCandidate(id),
          getExpenditures({ page_size: 100 }),
          getCandidateIESpending(id),
          getCandidateIEByCommittee(id),
        ]);

        setCandidate(candData);
        
        // Filter expenditures for this candidate
        const candidateExpenditures = (expData.results || expData || []).filter(
          exp => exp.candidate_name === (candData.candidate?.full_name || candData.name?.full_name)
        );
        setExpenditures(candidateExpenditures);
        
        setIESpending(ieData);
        setIEByCommittee(ieCommData);
      } catch (err) {
        console.error("Error loading candidate detail:", err);
      } finally {
        setLoading(false);
      }
    }
    if (id) {
      loadCandidate();
    }
  }, [id]);

  // Show preloader while candidate data is loading
  if (loading) {
    return <Preloader message="Loading candidate details..." />;
  }

  if (!candidate) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 lg:ml-0 min-w-0 p-4 sm:p-6 lg:p-8">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Candidate Not Found</h2>
            <p className="text-gray-600 mb-4">The candidate you're looking for doesn't exist.</p>
            <Link to="/candidates" className="text-purple-600 hover:text-purple-700">
              ← Back to Candidates
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const candidateName = candidate.candidate?.full_name || candidate.name?.full_name || "Unknown Candidate";

  // --- prepare chart data ---
  const spendByCommittee = {};
  if (ieByCommittee?.ie_committees) {
    ieByCommittee.ie_committees.forEach(comm => {
      const committeeName = comm.committee__name__last_name || "Unknown Committee";
      spendByCommittee[committeeName] = (spendByCommittee[committeeName] || 0) + Number(comm.total || 0);
    });
  }

  const committeeLabels = Object.keys(spendByCommittee);
  const committeeTotals = Object.values(spendByCommittee);

  const barData = {
    labels: committeeLabels.length > 0 ? committeeLabels : ["No Data"],
    datasets: [
      {
        label: "Total IE Spending by Committee (USD)",
        data: committeeTotals.length > 0 ? committeeTotals : [0],
        backgroundColor: "rgba(124, 107, 166, 0.6)",
        borderColor: "rgba(124, 107, 166, 1)",
        borderWidth: 1,
      },
    ],
  };

  // Support vs Oppose data from IE spending summary
  const pieData = {
    labels: ["Support", "Oppose"],
    datasets: [{
      data: [
        ieSpending?.ie_spending?.for?.total || 0,
        ieSpending?.ie_spending?.against?.total || 0,
      ],
      backgroundColor: [
        "rgba(34, 197, 94, 0.6)", // green for support
        "rgba(239, 68, 68, 0.6)", // red for oppose
      ],
      borderColor: [
        "rgba(34, 197, 94, 1)",
        "rgba(239, 68, 68, 1)",
      ],
      borderWidth: 1,
    }],
  };

  // --- candidate details for header ---
  const infoPairs = [
    ["Name", candidateName],
    ["Office", candidate.candidate_office?.name || "N/A"],
    ["Party", candidate.candidate_party?.name || "N/A"],
    ["Election Cycle", candidate.election_cycle?.name || "N/A"],
    ["Status", candidate.is_incumbent ? "Incumbent" : "Challenger"],
    ["IE For", `$${Number(ieSpending?.ie_spending?.for?.total || 0).toLocaleString()}`],
    ["IE Against", `$${Number(ieSpending?.ie_spending?.against?.total || 0).toLocaleString()}`],
    ["Net IE", `$${Number(ieSpending?.ie_spending?.net || 0).toLocaleString()}`],
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      {/* Main Content - Responsive: No left margin on mobile */}
      <main className="flex-1 lg:ml-0 min-w-0">
        {/* Header - Responsive */}
        <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900">{candidateName}</h1>
              <p className="text-xs sm:text-sm text-gray-500 mt-1">Candidate details and Independent Expenditure overview</p>
            </div>
            <Link 
              to="/candidates" 
              className="text-sm sm:text-base text-purple-600 hover:text-purple-700 font-medium transition-colors duration-200 hover:underline"
            >
              ← Back to Candidates
            </Link>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Candidate Information - Responsive: 1 column on mobile, 2 on desktop */}
          <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
            <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4">Candidate Information</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {infoPairs.map(([label, val]) => (
                <div key={label} className="border-b border-gray-100 pb-2">
                  <span className="text-sm font-semibold text-gray-600">{label}:</span>
                  <span className="ml-2 text-gray-900">{val}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Charts */}
          {/* Charts Section - Responsive: 1 column on mobile, 2 on desktop */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">IE Spending by Committee</h3>
              {committeeLabels.length > 0 ? (
                <div style={{ height: 300 }}>
                  <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              ) : (
                <p className="text-gray-500">No IE spending data for this candidate.</p>
              )}
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Support vs Oppose</h3>
              {(ieSpending?.ie_spending?.for?.total > 0 || ieSpending?.ie_spending?.against?.total > 0) ? (
                <div style={{ height: 300 }}>
                  <Pie data={pieData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              ) : (
                <p className="text-gray-500">No support/oppose data.</p>
              )}
            </div>
          </div>

          {/* Expenditures Table */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-bold text-gray-900">
                Independent Expenditures for {candidateName}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Date</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Committee</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Amount</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Purpose</th>
                    <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Support/Oppose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {expenditures.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-12 text-center text-gray-500">
                        No expenditures recorded.
                      </td>
                    </tr>
                  ) : (
                    expenditures.map((e, idx) => (
                      <tr key={idx} className="hover:bg-purple-50/50 transition-colors duration-150">
                        <td className="py-4 px-6 text-gray-700">
                          {e.date ? new Date(e.date).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          }) : "N/A"}
                        </td>
                        <td className="py-4 px-6 text-gray-700">
                          {e.ie_committee?.name || "Unknown"}
                        </td>
                        <td className="py-4 px-6 text-gray-900 font-semibold">
                          ${Number(e.amount || 0).toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="py-4 px-6 text-gray-700">
                          {e.purpose || "N/A"}
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            e.support_oppose === "Support"
                              ? "bg-green-100 text-green-700"
                              : e.support_oppose === "Oppose"
                              ? "bg-red-100 text-red-700"
                              : "bg-gray-100 text-gray-700"
                          }`}>
                            {e.support_oppose || "Unknown"}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
