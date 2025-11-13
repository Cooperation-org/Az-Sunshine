import React, { useEffect, useState } from "react";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import {
  getExpenditures,
  getTopCommittees,
  getTopDonors,
  getDashboardSummary,
} from "../api/api";
import { Link } from "react-router-dom";
import { Bell, Search } from "lucide-react";
import Sidebar from "../components/Sidebar";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

// Date formatting utility
const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "N/A";
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "N/A";
  }
};

// Skeleton components
const ChartSkeleton = () => (
  <div className="h-full w-full bg-gray-200 animate-pulse rounded-xl"></div>
);

const MetricCardSkeleton = () => (
  <div className="bg-white rounded-2xl p-6 shadow-lg">
    <div className="h-4 bg-gray-200 rounded w-2/3 mb-3 animate-pulse"></div>
    <div className="h-8 bg-gray-200 rounded w-1/2 animate-pulse"></div>
  </div>
);

const TableRowSkeleton = () => (
  <tr className="border-b border-gray-100">
    {[1, 2, 3, 4, 5].map((i) => (
      <td key={i} className="py-4 px-2">
        <div className="h-4 bg-gray-200 rounded w-full animate-pulse"></div>
      </td>
    ))}
  </tr>
);

const CommitteeItemSkeleton = () => (
  <div className="flex items-center gap-3">
    <div className="w-10 h-10 rounded-lg bg-gray-200 animate-pulse flex-shrink-0"></div>
    <div className="flex-1">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2 animate-pulse"></div>
      <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse"></div>
    </div>
  </div>
);

export default function Dashboard() {
  const [metrics, setMetrics] = useState({});
  const [topCommittees, setTopCommittees] = useState([]);
  const [topDonors, setTopDonors] = useState([]);
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState({
    summary: true,
    committees: true,
    donors: true,
    expenditures: true,
  });
  const [errors, setErrors] = useState({
    summary: null,
    committees: null,
    donors: null,
    expenditures: null,
  });

  useEffect(() => {
    // Create AbortController for cleanup
    const abortController = new AbortController();
    const signal = abortController.signal;

    async function loadData() {
      try {
        console.log("🔄 Loading dashboard data from backend...");
        
        // Load summary first (critical data)
        getDashboardSummary()
          .then((summaryData) => {
            if (signal.aborted) return;
            console.log("✅ Summary:", summaryData);
            setMetrics({
              total_expenditures: parseFloat(summaryData.total_ie_spending || 0),
              num_candidates: summaryData.candidate_committees || 0,
              num_expenditures: 0, // Will update when expenditures load
              soi_stats: summaryData.soi_tracking || {}
            });
            setLoading(prev => ({ ...prev, summary: false }));
            setErrors(prev => ({ ...prev, summary: null }));
          })
          .catch(err => {
            if (signal.aborted) return;
            console.error("❌ Summary load error:", err);
            setLoading(prev => ({ ...prev, summary: false }));
            setErrors(prev => ({ 
              ...prev, 
              summary: err.response?.data?.detail || err.message || "Failed to load summary data" 
            }));
          });

        // Load donors data from /api/donors endpoint
        getTopDonors(10)
          .then((donorsData) => {
            if (signal.aborted) return;
            console.log("✅ Top Donors:", donorsData);
            // Handle both array and paginated responses
            const donors = Array.isArray(donorsData) 
              ? donorsData 
              : (donorsData.results || donorsData.data || []);
            setTopDonors(donors);
            setLoading(prev => ({ ...prev, donors: false }));
            setErrors(prev => ({ ...prev, donors: null }));
          })
          .catch(err => {
            if (signal.aborted) return;
            console.error("❌ Donors load error:", err);
            console.warn("⚠️ Failed to load donor data:", err.response?.data || err.message);
            setTopDonors([]);
            setLoading(prev => ({ ...prev, donors: false }));
            setErrors(prev => ({ 
              ...prev, 
              donors: err.response?.data?.detail || err.message || "Failed to load donor data" 
            }));
          });

        // Load expenditures data from /api/expenditures endpoint
        getExpenditures({ page_size: 100 })
          .then((expData) => {
            if (signal.aborted) return;
            console.log("✅ Expenditures:", expData);
            // Handle both array and paginated responses
            const expendituresList = Array.isArray(expData) 
              ? expData 
              : (expData.results || expData.data || []);
            setExpenditures(expendituresList);
            setMetrics(prev => ({ 
              ...prev, 
              num_expenditures: expData.count || expendituresList.length || 0 
            }));
            setLoading(prev => ({ ...prev, expenditures: false }));
            setErrors(prev => ({ ...prev, expenditures: null }));
          })
          .catch(err => {
            if (signal.aborted) return;
            console.error("❌ Expenditures load error:", err);
            console.warn("⚠️ Failed to load expenditure data:", err.response?.data || err.message);
            setExpenditures([]);
            setLoading(prev => ({ ...prev, expenditures: false }));
            setErrors(prev => ({ 
              ...prev, 
              expenditures: err.response?.data?.detail || err.message || "Failed to load expenditure data" 
            }));
          });

        // Load top committees
        getTopCommittees(10)
          .then((committeesData) => {
            if (signal.aborted) return;
            console.log("✅ Top Committees:", committeesData);
            // Handle both array and paginated responses
            const committees = Array.isArray(committeesData) 
              ? committeesData 
              : (committeesData.results || committeesData.data || []);
            setTopCommittees(committees);
            setLoading(prev => ({ ...prev, committees: false }));
            setErrors(prev => ({ ...prev, committees: null }));
          })
          .catch(err => {
            if (signal.aborted) return;
            console.error("❌ Committees load error:", err);
            console.warn("⚠️ Failed to load committee data:", err.response?.data || err.message);
            setTopCommittees([]);
            setLoading(prev => ({ ...prev, committees: false }));
            setErrors(prev => ({ 
              ...prev, 
              committees: err.response?.data?.detail || err.message || "Failed to load committee data" 
            }));
          });
        
      } catch (err) {
        if (signal.aborted) return;
        console.error("❌ Dashboard load error:", err);
        console.error("Error details:", err.response?.data || err.message);
        setLoading({ summary: false, committees: false, donors: false, expenditures: false });
      }
    }
    
    loadData();

    // Cleanup function to abort requests if component unmounts
    return () => {
      abortController.abort();
    };
  }, []);

  const committeesToShow = topCommittees.slice(0, 10);
  const donorsToShow = topDonors.slice(0, 10);

  const donorData = {
    labels: donorsToShow.map((d) => d.name || d.full_name || "Unknown"),
    datasets: [
      {
        label: "Total Contributions (USD)",
        data: donorsToShow.map((d) => parseFloat(d.total_contribution || d.total_contributed || 0)),
        backgroundColor: "#FFFFFF",
        borderColor: "#FFFFFF",
        borderWidth: 0.5,
        borderRadius: 6,
        barThickness: 30,
      },
    ],
  };

  const totalsByType = expenditures.reduce((acc, e) => {
    const key = e.support_oppose || "Unknown";
    acc[key] = (acc[key] || 0) + Number(e.amount || 0);
    return acc;
  }, {});

  const supportAmount = totalsByType["Support"] || 0;
  const opposeAmount = totalsByType["Oppose"] || 0;
  const totalAmount = supportAmount + opposeAmount;
  const supportPercent = totalAmount > 0 ? ((supportAmount / totalAmount) * 100).toFixed(0) : 50;
  const opposePercent = totalAmount > 0 ? ((opposeAmount / totalAmount) * 100).toFixed(0) : 50;

  const pieData = {
    labels: ["Support", "Oppose"],
    datasets: [
      {
        data: [supportAmount, opposeAmount],
        backgroundColor: ["#5B4A7D", "#FFFFFF"],
        borderWidth: 0,
        borderRadius: 4,
      },
    ],
  };

  const latestExpenditures = expenditures.slice(0, 4);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <main className="ml-20 flex-1">
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Arizona Sunshine</h1>
            <p className="text-sm text-gray-500">Dashboard - Phase 1 Overview</p>
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

        <div className="p-8">
          {/* Charts Section */}
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="col-span-2 bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] rounded-3xl p-8 shadow-lg">
              <h2 className="text-white text-xl font-bold mb-1">Top 10 Donors</h2>
              <p className="text-white/70 text-sm mb-6">Total Contribution</p>
              <div className="h-[240px] bg-white/5 rounded-xl p-4">
                {loading.donors ? (
                  <ChartSkeleton />
                ) : errors.donors ? (
                  <div className="flex flex-col items-center justify-center h-full text-white/70">
                    <p className="text-sm font-medium mb-1">⚠️ Error loading donor data</p>
                    <p className="text-xs text-white/50">{errors.donors}</p>
                  </div>
                ) : donorsToShow.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-white/50">
                    No donor data available
                  </div>
                ) : (
                  <Bar 
                    data={donorData} 
                    options={{ 
                      responsive: true, 
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          titleColor: '#1F2937',
                          bodyColor: '#1F2937',
                          borderColor: '#E5E7EB',
                          borderWidth: 1,
                          padding: 12,
                          displayColors: false,
                          callbacks: {
                            label: (context) => `$${context.parsed.y.toLocaleString()}`
                          }
                        }
                      },
                      scales: {
                        x: { display: false, grid: { display: false } },
                        y: { display: false, grid: { display: false } }
                      }
                    }} 
                  />
                )}
              </div>
            </div>

            <div className="bg-white rounded-3xl p-8 shadow-lg">
              <h2 className="text-gray-900 text-xl font-bold mb-1">Support vs Oppose</h2>
              <p className="text-gray-500 text-sm mb-6">Spending</p>
              <div className="flex justify-center items-center h-[240px]">
                {loading.expenditures ? (
                  <div className="w-52 h-52">
                    <ChartSkeleton />
                  </div>
                ) : errors.expenditures ? (
                  <div className="flex flex-col items-center justify-center text-gray-500">
                    <p className="text-sm font-medium mb-1">⚠️ Error loading data</p>
                    <p className="text-xs text-gray-400">{errors.expenditures}</p>
                  </div>
                ) : expenditures.length === 0 ? (
                  <div className="text-gray-400">No expenditure data</div>
                ) : (
                  <div className="relative w-52 h-52">
                    <Doughnut 
                      data={pieData} 
                      options={{ 
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '75%',
                        plugins: {
                          legend: { display: false },
                          tooltip: { 
                            enabled: true,
                            backgroundColor: 'rgba(255, 255, 255, 0.95)',
                            titleColor: '#1F2937',
                            bodyColor: '#1F2937',
                            borderColor: '#E5E7EB',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                              label: (context) => `${context.label}: $${context.parsed.toLocaleString()}`
                            }
                          }
                        }
                      }} 
                    />
                  </div>
                )}
              </div>
              {!loading.expenditures && expenditures.length > 0 && (
                <div className="flex justify-center gap-6 mt-6 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#5B4A7D]"></div>
                    <span className="text-gray-700 font-medium">{supportPercent}% Support</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#FFFFFF] border border-gray-300"></div>
                    <span className="text-gray-700 font-medium">{opposePercent}% Oppose</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Metrics Cards */}
          <div className="grid grid-cols-4 gap-6 mb-6">
            {loading.summary ? (
              <>
                <MetricCardSkeleton />
                <MetricCardSkeleton />
                <MetricCardSkeleton />
                <MetricCardSkeleton />
              </>
            ) : (
              <>
                <div className="bg-white rounded-2xl p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-sm mb-1">Total IE Spending</p>
                  <p className="text-3xl font-bold">${Number(metrics.total_expenditures || 0).toLocaleString()}</p>
                </div>
                
                <div className="bg-white rounded-2xl p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-sm mb-1">Total Candidates</p>
                  <p className="text-3xl font-bold">{Number(metrics.num_candidates || 0).toLocaleString()}</p>
                </div>
                
                <div className="bg-white rounded-2xl p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-sm mb-1">IE Transactions</p>
                  <p className="text-3xl font-bold">
                    {loading.expenditures ? (
                      <span className="text-gray-400">...</span>
                    ) : (
                      Number(metrics.num_expenditures || 0).toLocaleString()
                    )}
                  </p>
                </div>

                <Link to="/soi" className="bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] rounded-2xl p-6 shadow-lg text-white relative overflow-hidden hover:shadow-xl transition">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-bl-full"></div>
                  <p className="text-white/90 text-sm mb-1">SOI Uncontacted</p>
                  <p className="text-3xl font-bold">{metrics.soi_stats?.uncontacted || 0}</p>
                  <p className="text-xs text-white/70 mt-2">Click to manage →</p>
                </Link>
              </>
            )}
          </div>

          {/* Bottom Section */}
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 bg-white rounded-2xl p-6 shadow-lg">
              <h2 className="text-gray-900 text-lg font-semibold mb-4">Latest Independent Expenditure</h2>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">Date</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">Committee</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">Candidate</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">Amount</th>
                    <th className="text-left py-3 px-2 text-sm font-semibold text-gray-700">Support/Oppose</th>
                  </tr>
                </thead>
                <tbody>
                  {loading.expenditures ? (
                    <>
                      <TableRowSkeleton />
                      <TableRowSkeleton />
                      <TableRowSkeleton />
                      <TableRowSkeleton />
                    </>
                  ) : errors.expenditures ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-gray-400">
                        <p className="text-sm font-medium mb-1">⚠️ Error loading expenditure data</p>
                        <p className="text-xs">{errors.expenditures}</p>
                      </td>
                    </tr>
                  ) : latestExpenditures.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-gray-400">
                        No expenditure data available
                      </td>
                    </tr>
                  ) : (
                    latestExpenditures.map((exp, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-2 text-sm text-gray-700">
                          {formatDate(exp.date)}
                        </td>
                        <td className="py-4 px-2 text-sm text-gray-700">{exp.ie_committee?.name || "Unknown"}</td>
                        <td className="py-4 px-2 text-sm text-gray-700">{exp.candidate_name || "N/A"}</td>
                        <td className="py-4 px-2 text-sm text-gray-700">${Number(exp.amount || 0).toLocaleString()}</td>
                        <td className="py-4 px-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            exp.support_oppose === "Support" 
                              ? "bg-green-100 text-green-700" 
                              : "bg-red-100 text-red-700"
                          }`}>
                            {exp.support_oppose || "Unknown"}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              <Link to="/expenditures" className="inline-block mt-4 text-purple-600 hover:text-purple-700 text-sm font-medium">
                View All Expenditures →
              </Link>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <h2 className="text-gray-900 text-lg font-semibold mb-4">Top 10 IE Committees</h2>
              <div className="space-y-3">
                {loading.committees ? (
                  <>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                      <CommitteeItemSkeleton key={i} />
                    ))}
                  </>
                ) : errors.committees ? (
                  <div className="text-center text-gray-400 py-8">
                    <p className="text-sm font-medium mb-1">⚠️ Error loading data</p>
                    <p className="text-xs">{errors.committees}</p>
                  </div>
                ) : committeesToShow.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    No committee data available
                  </div>
                ) : (
                  committeesToShow.map((committee, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white font-semibold flex-shrink-0">
                        {(committee.name?.full_name || committee.name || "?").charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {committee.name?.full_name || committee.name || "Unknown"}
                        </p>
                        <p className="text-xs text-gray-500">${Number(committee.total || 0).toLocaleString()}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}