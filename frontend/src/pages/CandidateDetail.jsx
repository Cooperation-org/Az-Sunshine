// frontend/src/pages/CandidateDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Calendar,
  Mail,
  Phone,
  MapPin,
  ExternalLink,
  Download,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Building2,
  Percent,
  Award,
  BarChart3
} from "lucide-react";
import { Pie, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

import Sidebar from "../components/Sidebar";

import GrassrootsThresholdBadge from "../components/GrassrootsThresholdBadge";
import { getCandidateById, getCandidateIESpending, getCandidateAggregate, getCandidateAggregateIESpending, getTransactions } from "../api/api";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function CandidateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { darkMode } = useDarkMode();

  const [candidate, setCandidate] = useState(null);
  const [ieSpending, setIESpending] = useState(null);
  const [aggregateData, setAggregateData] = useState(null);
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expendituresLoading, setExpendituresLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [expenditureFilter, setExpenditureFilter] = useState("all"); // all, for, against

  useEffect(() => {
    loadCandidateData();
    loadExpenditures();
  }, [id]);

  async function loadCandidateData() {
    setLoading(true);
    setError(null);

    try {
      // Try to get aggregate data first (combines all committees for same candidate)
      let aggregateResult = null;
      let aggregateIEResult = null;

      try {
        [aggregateResult, aggregateIEResult] = await Promise.all([
          getCandidateAggregate(id),
          getCandidateAggregateIESpending(id),
        ]);
      } catch (aggErr) {
        console.log("Aggregate endpoint not available, falling back to single committee");
      }

      // Fallback to single committee data
      const [candidateData, ieData] = await Promise.all([
        getCandidateById(id),
        getCandidateIESpending(id),
      ]);

      setCandidate(candidateData);
      setAggregateData(aggregateResult);

      // Use aggregate IE data if available, otherwise use single committee data
      if (aggregateIEResult) {
        setIESpending(aggregateIEResult);
      } else {
        setIESpending(ieData);
      }
    } catch (err) {
      console.error("Error loading candidate:", err);
      setError(err.message || "Failed to load candidate data");
    } finally {
      setLoading(false);
    }
  }

  async function loadExpenditures() {
    setExpendituresLoading(true);
    
    try {
      const response = await getTransactions({
        subject_committee: id,
        transaction_type: "IE",
        limit: 100,
      });
      
      setExpenditures(response.results || response || []);
    } catch (err) {
      console.error("Error loading expenditures:", err);
    } finally {
      setExpendituresLoading(false);
    }
  }

  function handleExportExpenditures() {
    const columns = [
      { key: "date_of_transaction", label: "Date" },
      { key: "committee.name", label: "Committee" },
      { key: "amount", label: "Amount" },
      { key: "support_oppose", label: "Support/Oppose" },
      { key: "transaction_type", label: "Type" },
      { key: "description", label: "Description" },
    ];

    exportToCSV(
      filteredExpenditures,
      columns,
      `candidate_${candidate?.name?.full_name || id}_expenditures.csv`
    );
  }

  if (loading) {
    return (
      <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
        <Sidebar />
        <main className="flex-1 lg:ml-0">
          
          <div className="p-8">
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <RefreshCw className={`w-12 h-12 animate-spin ${darkMode ? 'text-purple-300' : 'text-purple-600'} mx-auto mb-4`} />
                <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'} font-medium`}>Loading candidate details...</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
        <Sidebar />
        <main className="flex-1 lg:ml-0">
          <Header title="Error" subtitle="Failed to load candidate" />
          <div className="p-8">
            <div className={`${darkMode ? 'bg-red-900/30 border-red-800' : 'bg-red-50 border-red-200'} border-2 rounded-2xl p-8 text-center`}>
              <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 className={`text-2xl font-bold ${darkMode ? 'text-red-300' : 'text-red-900'} mb-2`}>
                Failed to Load Candidate
              </h2>
              <p className={`${darkMode ? 'text-red-400' : 'text-red-700'} mb-6`}>{error || "Candidate not found"}</p>
              <button
                onClick={() => navigate("/candidates")}
                className="px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-colors inline-flex items-center gap-2"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Candidates
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Calculate totals - use absolute values since IE expenses are stored as negative
  const rawIEFor = parseFloat(ieSpending?.ie_spending?.for?.total || 0);
  const rawIEAgainst = parseFloat(ieSpending?.ie_spending?.against?.total || 0);
  const totalIEFor = Math.abs(rawIEFor);
  const totalIEAgainst = Math.abs(rawIEAgainst);
  const totalIE = totalIEFor + totalIEAgainst;
  const netIE = totalIEFor - totalIEAgainst;

  // Check if we're showing aggregated data from multiple committees
  const isAggregated = ieSpending?.is_aggregated || aggregateData?.is_aggregated;
  const relatedCommitteesCount = ieSpending?.related_committees_count || aggregateData?.related_committees_count || 1;

  // Pie chart data
  const pieChartData = {
    labels: ["Support", "Oppose"],
    datasets: [
      {
        data: [totalIEFor, totalIEAgainst],
        backgroundColor: [
          "rgba(34, 197, 94, 0.8)",
          "rgba(239, 68, 68, 0.8)",
        ],
        borderColor: [
          "rgba(34, 197, 94, 1)",
          "rgba(239, 68, 68, 1)",
        ],
        borderWidth: 2,
      },
    ],
  };

  // Bar chart data (IE by committee)
  const committeeData = ieSpending?.ie_by_committee || [];
  const barChartData = {
    labels: committeeData.slice(0, 10).map((c) => c.committee__name || "Unknown"),
    datasets: [
      {
        label: "IE Spending",
        data: committeeData.slice(0, 10).map((c) => parseFloat(c.total_ie || 0)),
        backgroundColor: "rgba(139, 92, 246, 0.7)",
        borderColor: "rgba(139, 92, 246, 1)",
        borderWidth: 2,
        borderRadius: 8,
      },
    ],
  };

  // Filter expenditures
  const filteredExpenditures = expenditures.filter((exp) => {
    if (expenditureFilter === "all") return true;
    if (expenditureFilter === "for") return exp.support_oppose?.toLowerCase() === "support";
    if (expenditureFilter === "against") return exp.support_oppose?.toLowerCase() === "oppose";
    return true;
  });

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 lg:ml-0">
        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => navigate("/candidates")}
            className={`mb-6 px-4 py-2 ${darkMode ? 'bg-[#3d3559] text-gray-300 border-[#4a3f66] hover:bg-[#4a3f66]' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'} rounded-xl font-medium transition-all inline-flex items-center gap-2 shadow-sm border hover:shadow-md`}
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Candidates
          </button>

          {/* Candidate Header Card */}
          <div className={`${darkMode ? 'bg-[#3d3559] border border-[#4a3f66]' : 'bg-gradient-to-r from-[#6B5B95] to-[#4C3D7D]'} rounded-2xl p-8 mb-6 text-white shadow-2xl`}>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-white/20'} backdrop-blur-sm p-3 rounded-xl`}>
                    <Users className="w-8 h-8" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold">
                      {candidate.name?.full_name || "Unknown Candidate"}
                    </h1>
                    <p className={`${darkMode ? 'text-gray-300' : 'text-purple-100'} text-lg`}>
                      {candidate.office?.name || "Office Unknown"}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                  <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-white/10'} backdrop-blur-sm rounded-xl p-3`}>
                    <p className={`${darkMode ? 'text-gray-400' : 'text-purple-100'} text-xs mb-1`}>Party</p>
                    <p className="font-bold text-lg">{candidate.party?.name || "Unknown"}</p>
                  </div>
                  <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-white/10'} backdrop-blur-sm rounded-xl p-3`}>
                    <p className={`${darkMode ? 'text-gray-400' : 'text-purple-100'} text-xs mb-1`}>Cycle</p>
                    <p className="font-bold text-lg">{candidate.cycle?.name || "N/A"}</p>
                  </div>
                  <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-white/10'} backdrop-blur-sm rounded-xl p-3`}>
                    <p className={`${darkMode ? 'text-gray-400' : 'text-purple-100'} text-xs mb-1`}>Committee ID</p>
                    <p className="font-bold text-lg">{candidate.committee_id || "N/A"}</p>
                  </div>
                  <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-white/10'} backdrop-blur-sm rounded-xl p-3`}>
                    <p className={`${darkMode ? 'text-gray-400' : 'text-purple-100'} text-xs mb-1`}>Type</p>
                    <p className="font-bold text-lg">{candidate.committee_type || "N/A"}</p>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className={`${darkMode ? 'bg-[#4a3f66] border-[#5f5482]' : 'bg-white/10 border-white/20'} backdrop-blur-sm rounded-2xl p-6 border-2`}>
                <p className={`${darkMode ? 'text-gray-400' : 'text-purple-100'} text-sm mb-2`}>Total IE Spending</p>
                <p className="text-4xl font-black mb-2">${totalIE.toLocaleString()}</p>
                <div className="flex items-center gap-2 text-sm">
                  {netIE >= 0 ? (
                    <>
                      <TrendingUp className="w-4 h-4 text-green-300" />
                      <span className="text-green-300 font-semibold">
                        Net +${netIE.toLocaleString()}
                      </span>
                    </>
                  ) : (
                    <>
                      <TrendingDown className="w-4 h-4 text-red-300" />
                      <span className="text-red-300 font-semibold">
                        Net ${netIE.toLocaleString()}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Aggregation Indicator */}
          {isAggregated && (
            <div className={`${darkMode ? 'bg-blue-900/30 border-blue-700' : 'bg-blue-50 border-blue-200'} border rounded-xl p-4 mb-6 flex items-center gap-3`}>
              <CheckCircle className={`w-5 h-5 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
              <div>
                <p className={`font-semibold ${darkMode ? 'text-blue-300' : 'text-blue-800'}`}>
                  Aggregated Data from {relatedCommitteesCount} Committees
                </p>
                <p className={`text-sm ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                  This candidate has multiple campaign committees. Totals shown combine all related committees.
                </p>
              </div>
            </div>
          )}

          {/* Tab Navigation */}
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl shadow-lg border mb-6 overflow-hidden`}>
            <div className={`flex ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'} border-b overflow-x-auto`}>
              {[
                { id: "overview", label: "Overview", icon: BarChart3 },
                { id: "spending", label: "IE Spending", icon: DollarSign },
                { id: "expenditures", label: "Expenditures", icon: TrendingDown },
                { id: "threshold", label: "Threshold Analysis", icon: AlertTriangle },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 min-w-[140px] px-6 py-4 font-semibold transition-all inline-flex items-center justify-center gap-2 ${
                    activeTab === tab.id
                      ? darkMode
                        ? "bg-[#4a3f66] text-purple-300 border-b-4 border-purple-400"
                        : "bg-purple-50 text-purple-700 border-b-4 border-purple-600"
                      : darkMode
                      ? "text-gray-300 hover:bg-[#4a3f66] hover:text-gray-100"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={TrendingUp}
                  label="IE Support"
                  value={`$${totalIEFor.toLocaleString()}`}
                  iconColor="text-green-600"
                  darkMode={darkMode}
                  percentage={totalIE > 0 ? ((totalIEFor / totalIE) * 100).toFixed(1) : 0}
                />
                <StatCard
                  icon={TrendingDown}
                  label="IE Oppose"
                  value={`$${totalIEAgainst.toLocaleString()}`}
                  iconColor="text-red-600"
                  darkMode={darkMode}
                  percentage={totalIE > 0 ? ((totalIEAgainst / totalIE) * 100).toFixed(1) : 0}
                />
                <StatCard
                  icon={DollarSign}
                  label="Total IE"
                  value={`$${totalIE.toLocaleString()}`}
                  iconColor="text-purple-600"
                  darkMode={darkMode}
                />
                <StatCard
                  icon={Building2}
                  label="IE Committees"
                  value={committeeData.length}
                  iconColor="text-blue-600"
                  darkMode={darkMode}
                />
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pie Chart */}
                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl p-6 shadow-lg border`}>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'} mb-4 flex items-center gap-2`}>
                    <Percent className={`w-5 h-5 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                    Support vs Oppose
                  </h3>
                  {totalIE > 0 ? (
                    <div className="h-64">
                      <Pie
                        data={pieChartData}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { position: "bottom" },
                            tooltip: {
                              callbacks: {
                                label: (context) =>
                                  `${context.label}: $${context.parsed.toLocaleString()}`,
                              },
                            },
                          },
                        }}
                      />
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-gray-400">
                      No IE spending data
                    </div>
                  )}
                </div>

                {/* Bar Chart */}
                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl p-6 shadow-lg border`}>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'} mb-4 flex items-center gap-2`}>
                    <BarChart3 className={`w-5 h-5 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                    Top IE Committees
                  </h3>
                  {committeeData.length > 0 ? (
                    <div className="h-64">
                      <Bar
                        data={barChartData}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          indexAxis: "y",
                          plugins: {
                            legend: { display: false },
                            tooltip: {
                              callbacks: {
                                label: (context) =>
                                  `$${context.parsed.x.toLocaleString()}`,
                              },
                            },
                          },
                          scales: {
                            x: {
                              beginAtZero: true,
                              ticks: {
                                callback: (value) => `$${value.toLocaleString()}`,
                              },
                            },
                          },
                        }}
                      />
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-gray-400">
                      No committee data
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === "spending" && (
            <div className="space-y-6">
              {/* IE Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 border-2 shadow-lg hover:shadow-xl transition-all`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="bg-green-600 p-3 rounded-xl">
                      <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>IE Support</p>
                      <p className={`text-3xl font-black text-green-600`}>
                        ${totalIEFor.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {totalIE > 0
                        ? `${((totalIEFor / totalIE) * 100).toFixed(1)}% of total IE`
                        : "0% of total IE"}
                    </p>
                  </div>
                </div>

                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 border-2 shadow-lg hover:shadow-xl transition-all`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="bg-red-600 p-3 rounded-xl">
                      <TrendingDown className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>IE Oppose</p>
                      <p className={`text-3xl font-black text-red-600`}>
                        ${totalIEAgainst.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {totalIE > 0
                        ? `${((totalIEAgainst / totalIE) * 100).toFixed(1)}% of total IE`
                        : "0% of total IE"}
                    </p>
                  </div>
                </div>

                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 border-2 shadow-lg hover:shadow-xl transition-all`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="bg-purple-600 p-3 rounded-xl">
                      <DollarSign className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Net IE</p>
                      <p className={`text-3xl font-black text-purple-600`}>
                        {netIE >= 0 ? "+" : ""}${netIE.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Support minus Oppose
                    </p>
                  </div>
                </div>
              </div>

              {/* Committee Breakdown Table */}
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl shadow-lg border overflow-hidden`}>
                <div className={`p-6 ${darkMode ? 'border-[#4a3f66] bg-[#4a3f66]' : 'border-gray-200 bg-gradient-to-r from-purple-50 to-indigo-50'} border-b`}>
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'} flex items-center gap-2`}>
                    <Building2 className={`w-5 h-5 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                    IE Spending by Committee
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className={`${darkMode ? 'bg-[#4a3f66] border-[#4a3f66]' : 'bg-gray-50 border-gray-200'} border-b`}>
                      <tr>
                        <th className={`px-6 py-4 text-left text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Committee
                        </th>
                        <th className={`px-6 py-4 text-right text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Total IE
                        </th>
                        <th className={`px-6 py-4 text-right text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Support
                        </th>
                        <th className={`px-6 py-4 text-right text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Oppose
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-200'}`}>
                      {committeeData.length > 0 ? (
                        committeeData.map((committee, idx) => (
                          <tr
                            key={idx}
                            className={`${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50'} transition-colors`}
                          >
                            <td className={`px-6 py-4 text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-900'}`}>
                              {committee.committee__name || "Unknown Committee"}
                            </td>
                            <td className={`px-6 py-4 text-sm text-right font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                              ${parseFloat(committee.total_ie || 0).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 text-sm text-right text-green-600 font-semibold">
                              ${parseFloat(committee.total_for || 0).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 text-sm text-right text-red-600 font-semibold">
                              ${parseFloat(committee.total_against || 0).toLocaleString()}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td
                            colSpan="4"
                            className="px-6 py-8 text-center text-gray-500"
                          >
                            No committee data available
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === "expenditures" && (
            <div className="space-y-6">
              {/* Filter Bar */}
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl p-4 shadow-lg border flex flex-wrap items-center justify-between gap-4`}>
                <div className="flex items-center gap-3">
                  <Filter className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`} />
                  <select
                    value={expenditureFilter}
                    onChange={(e) => setExpenditureFilter(e.target.value)}
                    className={`px-4 py-2 border ${darkMode ? 'bg-[#4a3f66] border-[#4a3f66] text-gray-200' : 'border-gray-300 bg-white text-gray-900'} rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500`}
                  >
                    <option value="all">All Expenditures</option>
                    <option value="for">Support Only</option>
                    <option value="against">Oppose Only</option>
                  </select>
                  <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    {filteredExpenditures.length} results
                  </span>
                </div>
                <button
                  onClick={handleExportExpenditures}
                  className={`px-4 py-2 ${darkMode ? 'bg-[#7d6fa3] hover:bg-[#8b7cb8]' : 'bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] hover:from-[#7C6BA6] hover:to-[#5B4D7D]'} text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2`}
                >
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
              </div>

              {/* Expenditures Table */}
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl shadow-lg border overflow-hidden`}>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className={`${darkMode ? 'bg-[#4a3f66] border-[#4a3f66]' : 'bg-gradient-to-r from-purple-50 to-indigo-50 border-gray-200'} border-b`}>
                      <tr>
                        <th className={`px-6 py-4 text-left text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Date
                        </th>
                        <th className={`px-6 py-4 text-left text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Committee
                        </th>
                        <th className={`px-6 py-4 text-right text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Amount
                        </th>
                        <th className={`px-6 py-4 text-center text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Type
                        </th>
                        <th className={`px-6 py-4 text-left text-xs font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'} uppercase tracking-wider`}>
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-200'}`}>
                      {expendituresLoading ? (
                        <tr>
                          <td colSpan="5" className="px-6 py-8 text-center">
                            <RefreshCw className={`w-6 h-6 animate-spin ${darkMode ? 'text-purple-400' : 'text-purple-600'} mx-auto mb-2`} />
                            <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Loading expenditures...</p>
                          </td>
                        </tr>
                      ) : filteredExpenditures.length > 0 ? (
                        filteredExpenditures.map((exp, idx) => (
                          <tr
                            key={idx}
                            className={`${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50'} transition-colors`}
                          >
                            <td className={`px-6 py-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-900'}`}>
                              {exp.date_of_transaction
                                ? new Date(exp.date_of_transaction).toLocaleDateString()
                                : "N/A"}
                            </td>
                            <td className={`px-6 py-4 text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                              {exp.committee?.name || "Unknown"}
                            </td>
                            <td className={`px-6 py-4 text-sm text-right font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                              ${parseFloat(exp.amount || 0).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 text-center">
                              <span
                                className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                                  exp.support_oppose?.toLowerCase() === "support"
                                    ? "bg-green-100 text-green-800"
                                    : "bg-red-100 text-red-800"
                                }`}
                              >
                                {exp.support_oppose || "Unknown"}
                              </span>
                            </td>
                            <td className={`px-6 py-4 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} max-w-xs truncate`}>
                              {exp.description || "No description"}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td
                            colSpan="5"
                            className={`px-6 py-8 text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}
                          >
                            No expenditures found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === "threshold" && (
            <div className="space-y-6">
              <GrassrootsThresholdBadge
                ieFor={totalIEFor}
                ieAgainst={totalIEAgainst}
                threshold={5000}
                detailed={true}
              />

              {/* Additional Threshold Info */}
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl p-6 shadow-lg border`}>
                <h3 className={`text-lg font-bold ${darkMode ? 'text-gray-200' : 'text-gray-900'} mb-4 flex items-center gap-2`}>
                  <Award className={`w-5 h-5 ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                  What is the Grassroots Threshold?
                </h3>
                <div className={`prose prose-sm max-w-none ${darkMode ? 'text-gray-300' : 'text-gray-700'} space-y-3`}>
                  <p>
                    The grassroots threshold is a limit set by Arizona law to ensure
                    transparency in campaign finance. When a candidate receives more than
                    <strong> $5,000</strong> in independent expenditures (IE), they are
                    required to file additional disclosure reports.
                  </p>
                  <p>
                    This candidate has received <strong>${totalIE.toLocaleString()}</strong>{" "}
                    in total IE spending, which is{" "}
                    {totalIE > 5000 ? (
                      <span className="text-red-600 font-bold">
                        ${(totalIE - 5000).toLocaleString()} over the threshold
                      </span>
                    ) : (
                      <span className="text-green-600 font-bold">
                        ${(5000 - totalIE).toLocaleString()} below the threshold
                      </span>
                    )}
                    .
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ==================== STAT CARD COMPONENT ====================

function StatCard({ icon: Icon, label, value, iconColor, darkMode, percentage }) {
  return (
    <div className={`${darkMode ? 'bg-[#3d3559]' : 'bg-white'} rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 border ${darkMode ? 'border-[#4a3f66]' : 'border-gray-100'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-100'} p-3 rounded-xl`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>
        {percentage !== undefined && (
          <span className={`text-2xl font-bold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{percentage}%</span>
        )}
      </div>
      <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-1`}>{label}</p>
      <p className={`text-3xl font-black ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>{value}</p>
    </div>
  );
}