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
import { Link } from "react-router-dom";
import { Bell, Search } from "lucide-react";
import Sidebar from "../components/Sidebar";
import api from "../api/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

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
  // Separate loading states for progressive loading
  const [metrics, setMetrics] = useState({});
  const [chartsData, setChartsData] = useState(null);
  const [recentExpenditures, setRecentExpenditures] = useState([]);
  
  const [loading, setLoading] = useState({
    summary: true,
    charts: true,
    expenditures: true,
  });

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    console.log("🚀 Loading dashboard with progressive enhancement...");
    
    // STEP 1: Load critical metrics first (fastest)
    loadSummary();
    
    // STEP 2: Load charts data after 100ms (allows UI to render)
    setTimeout(() => loadChartsData(), 100);
    
    // STEP 3: Load recent expenditures last (nice-to-have)
    setTimeout(() => loadRecentExpenditures(), 200);
  }

  async function loadSummary() {
    try {
      console.log("📊 Loading summary metrics...");
      const data = await api.get('dashboard/summary-optimized/');
      
      setMetrics({
        total_expenditures: parseFloat(data.data.total_ie_spending || 0),
        num_candidates: data.data.candidate_committees || 0,
        num_expenditures: data.data.num_expenditures || 0,
        soi_stats: data.data.soi_tracking || {}
      });
      
      setLoading(prev => ({ ...prev, summary: false }));
      console.log("✅ Summary loaded", data.data.cached ? "(from cache)" : "(fresh)");
      
    } catch (err) {
      console.error("❌ Summary load error:", err);
      setLoading(prev => ({ ...prev, summary: false }));
    }
  }

  async function loadChartsData() {
    try {
      console.log("📈 Loading charts data...");
      const data = await api.get('dashboard/charts-data/');
      
      setChartsData(data.data);
      setLoading(prev => ({ ...prev, charts: false }));
      console.log("✅ Charts loaded");
      
    } catch (err) {
      console.error("❌ Charts load error:", err);
      setChartsData({ top_committees: [], top_donors: [], support_oppose: { support: 0, oppose: 0 } });
      setLoading(prev => ({ ...prev, charts: false }));
    }
  }

  async function loadRecentExpenditures() {
    try {
      console.log("📋 Loading recent expenditures...");
      const data = await api.get('dashboard/recent-expenditures/');
      
      setRecentExpenditures(data.data);
      setLoading(prev => ({ ...prev, expenditures: false }));
      console.log("✅ Expenditures loaded");
      
    } catch (err) {
      console.error("❌ Expenditures load error:", err);
      setRecentExpenditures([]);
      setLoading(prev => ({ ...prev, expenditures: false }));
    }
  }

  // Prepare chart data
  const donorData = chartsData?.top_donors?.length > 0 ? {
    labels: chartsData.top_donors.map(d => d.name_full || "Unknown"),
    datasets: [{
      label: "Total Contributions (USD)",
      data: chartsData.top_donors.map(d => parseFloat(d.total_contributed || 0)),
      backgroundColor: "rgba(124, 107, 166, 0.6)",
      borderColor: "rgba(124, 107, 166, 1)",
      borderWidth: 1,
      borderRadius: 6,
      barThickness: 30,
    }],
  } : null;

  const supportAmount = chartsData?.support_oppose?.support || 0;
  const opposeAmount = chartsData?.support_oppose?.oppose || 0;
  const totalAmount = supportAmount + opposeAmount;
  const supportPercent = totalAmount > 0 ? ((supportAmount / totalAmount) * 100).toFixed(0) : 50;
  const opposePercent = totalAmount > 0 ? ((opposeAmount / totalAmount) * 100).toFixed(0) : 50;

  const pieData = {
    labels: ["Support", "Oppose"],
    datasets: [{
      data: [supportAmount, opposeAmount],
      backgroundColor: ["#5B4A7D", "#E5E7EB"],
      borderWidth: 0,
      borderRadius: 4,
    }],
  };

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
                {loading.charts ? (
                  <ChartSkeleton />
                ) : !donorData ? (
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
                {loading.charts ? (
                  <div className="w-52 h-52">
                    <ChartSkeleton />
                  </div>
                ) : (supportAmount === 0 && opposeAmount === 0) ? (
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
              {!loading.charts && (supportAmount > 0 || opposeAmount > 0) && (
                <div className="flex justify-center gap-6 mt-6 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#5B4A7D]"></div>
                    <span className="text-gray-700 font-medium">{supportPercent}% Support</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#E5E7EB]"></div>
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
                  <p className="text-3xl font-bold">{Number(metrics.num_expenditures || 0).toLocaleString()}</p>
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
                  ) : recentExpenditures.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-gray-400">
                        No expenditure data available
                      </td>
                    </tr>
                  ) : (
                    recentExpenditures.map((exp, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-4 px-2 text-sm text-gray-700">
                          {exp.transaction_date ? new Date(exp.transaction_date).toLocaleDateString() : "N/A"}
                        </td>
                        <td className="py-4 px-2 text-sm text-gray-700">{exp.committee_name || "Unknown"}</td>
                        <td className="py-4 px-2 text-sm text-gray-700">{exp.candidate_name || "N/A"}</td>
                        <td className="py-4 px-2 text-sm text-gray-700">${Number(exp.amount || 0).toLocaleString()}</td>
                        <td className="py-4 px-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            exp.is_for_benefit 
                              ? "bg-green-100 text-green-700" 
                              : "bg-red-100 text-red-700"
                          }`}>
                            {exp.is_for_benefit ? "Support" : "Oppose"}
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
                {loading.charts ? (
                  <>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                      <CommitteeItemSkeleton key={i} />
                    ))}
                  </>
                ) : !chartsData?.top_committees || chartsData.top_committees.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    No committee data available
                  </div>
                ) : (
                  chartsData.top_committees.map((committee, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white font-semibold flex-shrink-0">
                        {(committee.name_full || "?").charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {committee.name_full || "Unknown"}
                        </p>
                        <p className="text-xs text-gray-500">${Number(committee.total_ie || 0).toLocaleString()}</p>
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