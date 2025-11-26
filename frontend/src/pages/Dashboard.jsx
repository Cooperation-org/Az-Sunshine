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
import Header from "../components/Header";
import {
  CardSkeleton,
  ChartSkeleton,
  ListItemSkeleton,
  StatsGridSkeleton,
} from "../components/SkeletonLoader";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

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
  // Using bright, visible colors that contrast well with the purple gradient background
  const donorData = chartsData?.top_donors?.length > 0 ? {
    labels: chartsData.top_donors.map(d => d.name_full || "Unknown"),
    datasets: [{
      label: "Total Contributions (USD)",
      data: chartsData.top_donors.map(d => parseFloat(d.total_contributed || 0)),
      // Bright cyan/teal color for better visibility against purple background
      backgroundColor: "rgba(255, 255, 255, 0.8)",  // Cyan-500 with 80% opacity for better visibility
      borderColor: "rgba(255, 255, 255, 1)",      // White border for sharp contrast
      borderWidth: 2,                              // Thicker border for better visibility
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

  // No longer using full-page preloader - show skeleton loaders inline
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      {/* Main Content - Responsive: No left margin on mobile, padding on desktop */}
      <main className="flex-1 lg:ml-0 min-w-0">
        <Header title="Arizona Sunshine" subtitle="Dashboard - Phase 1 Overview" />

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Charts Section - Responsive: 1 column on mobile, 2 on tablet, 3 on desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
            {/* Top Donors Chart - Responsive: Full width on mobile/tablet, 2 columns on desktop */}
            <div className="md:col-span-2 lg:col-span-2 bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 shadow-lg">
              <h2 className="text-white text-lg sm:text-xl font-bold mb-1">Top 10 Donors</h2>
              <p className="text-white/70 text-xs sm:text-sm mb-4 sm:mb-6">Total Contribution</p>
              {/* Chart Container - Responsive height */}
              <div className="h-[200px] sm:h-[240px] lg:h-[280px] bg-white/5 rounded-xl p-2 sm:p-4">
                {loading.charts ? (
                  <div className="h-full w-full">
                    <ChartSkeleton height="100%" className="bg-transparent" />
                  </div>
                ) : !donorData || (donorData.labels && donorData.labels.length === 0) ? (
                  <div className="flex flex-col items-center justify-center h-full text-white/50">
                    <div className="text-sm mb-2">No donor data available</div>
                    <div className="text-xs opacity-75">Chart will appear when data is loaded</div>
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
                          displayColors: true,  // Show color in tooltip for better visibility
                          callbacks: {
                            label: (context) => `$${context.parsed.y.toLocaleString()}`
                          }
                        }
                      },
                      scales: {
                        x: { 
                          display: false, 
                          grid: { display: false } 
                        },
                        y: { 
                          display: false, 
                          grid: { display: false } 
                        }
                      },
                      // Enhanced visual settings for better visibility
                      animation: {
                        duration: 1000,
                        easing: 'easeOutQuart'
                      }
                    }} 
                  />
                )}
              </div>
            </div>

            {/* Support vs Oppose Chart - Responsive: Full width on mobile, 1 column on desktop */}
            <div className="bg-white rounded-2xl sm:rounded-3xl p-4 sm:p-6 lg:p-8 shadow-lg">
              <h2 className="text-gray-900 text-lg sm:text-xl font-bold mb-1">Support vs Oppose</h2>
              <p className="text-gray-500 text-xs sm:text-sm mb-4 sm:mb-6">Spending</p>
              {/* Chart Container - Responsive height and size */}
              <div className="flex justify-center items-center h-[200px] sm:h-[240px] lg:h-[280px]">
                {loading.charts ? (
                  <div className="w-40 h-40 sm:w-48 sm:h-48 lg:w-52 lg:h-52 rounded-full">
                    <ChartSkeleton height="100%" />
                  </div>
                ) : (supportAmount === 0 && opposeAmount === 0) ? (
                  <div className="flex flex-col items-center justify-center text-gray-400">
                    <div className="text-sm mb-2">No expenditure data</div>
                    <div className="text-xs opacity-75">Chart will appear when data is loaded</div>
                  </div>
                ) : (
                  // Doughnut Chart - Responsive size
                  <div className="relative w-40 h-40 sm:w-48 sm:h-48 lg:w-52 lg:h-52">
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

          {/* Metrics Cards - Responsive: 1 column on mobile, 2 on tablet, 4 on desktop */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-4 sm:mb-6">
            {loading.summary ? (
              <StatsGridSkeleton count={4} />
            ) : (
              <>
                {/* Metric Cards - Responsive padding and text sizes */}
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 sm:w-20 sm:h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-xs sm:text-sm mb-1">Total IE Spending</p>
                  <p className="text-2xl sm:text-3xl font-bold">${Number(metrics.total_expenditures || 0).toLocaleString()}</p>
                </div>
                
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 sm:w-20 sm:h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-xs sm:text-sm mb-1">Total Candidates</p>
                  <p className="text-2xl sm:text-3xl font-bold">{Number(metrics.num_candidates || 0).toLocaleString()}</p>
                </div>
                
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg text-black relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-16 h-16 sm:w-20 sm:h-20 bg-purple-100 rounded-bl-full"></div>
                  <p className="text-black/90 text-xs sm:text-sm mb-1">IE Transactions</p>
                  <p className="text-2xl sm:text-3xl font-bold">{Number(metrics.num_expenditures || 0).toLocaleString()}</p>
                </div>

                {/* SOI Card - Responsive padding and text sizes */}
                <Link to="/soi" className="bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] rounded-2xl p-4 sm:p-6 shadow-lg text-white relative overflow-hidden hover:shadow-xl hover:scale-[1.02] transition-all duration-200 active:scale-100">
                  <div className="absolute top-0 right-0 w-16 h-16 sm:w-20 sm:h-20 bg-white/10 rounded-bl-full"></div>
                  <p className="text-white/90 text-xs sm:text-sm mb-1">SOI Uncontacted</p>
                  <p className="text-2xl sm:text-3xl font-bold">{metrics.soi_stats?.uncontacted || 0}</p>
                  <p className="text-xs text-white/70 mt-2">Click to manage →</p>
                </Link>
              </>
            )}
          </div>

          {/* Bottom Section - Responsive: 1 column on mobile, 3 columns on desktop */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
            {/* Expenditures Table - Responsive: Full width on mobile, 2 columns on desktop */}
            <div className="lg:col-span-2 bg-white rounded-2xl p-4 sm:p-6 shadow-lg overflow-hidden flex flex-col">
              <h2 className="text-gray-900 text-base sm:text-lg font-semibold mb-4">Latest Independent Expenditure</h2>
              {/* Scrollable Table Container - Vertical scroll with fixed max-height */}
              <div className="overflow-y-auto overflow-x-auto -mx-4 sm:mx-0 max-h-[300px] sm:max-h-[400px] lg:max-h-[500px] flex-1">
                <div className="inline-block min-w-full align-middle">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr className="border-b border-gray-200">
                        {/* Table Headers - Responsive text sizes */}
                        <th className="text-left py-3 px-2 sm:px-4 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Date</th>
                        <th className="text-left py-3 px-2 sm:px-4 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Committee</th>
                        <th className="text-left py-3 px-2 sm:px-4 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Candidate</th>
                        <th className="text-left py-3 px-2 sm:px-4 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Amount</th>
                        <th className="text-left py-3 px-2 sm:px-4 text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Support/Oppose</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loading.expenditures ? (
                        <>
                          {[1, 2, 3, 4, 5].map((i) => (
                            <tr key={i} className="border-b border-gray-100">
                              {[1, 2, 3, 4, 5].map((j) => (
                                <td key={j} className="py-4 px-2 sm:px-4">
                                  <div className="h-4 w-full rounded animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]"></div>
                                </td>
                              ))}
                            </tr>
                          ))}
                        </>
                      ) : recentExpenditures.length === 0 ? (
                        <tr>
                          <td colSpan="5" className="py-8 text-center text-gray-400 text-sm">
                            No expenditure data available
                          </td>
                        </tr>
                      ) : (
                        recentExpenditures.map((exp, idx) => (
                          <tr key={idx} className="border-b border-gray-100 hover:bg-purple-50/50 transition-colors duration-150">
                            {/* Table Cells - Responsive padding and text sizes */}
                            <td className="py-3 sm:py-4 px-2 sm:px-4 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                              {exp.transaction_date ? new Date(exp.transaction_date).toLocaleDateString() : "N/A"}
                            </td>
                            <td className="py-3 sm:py-4 px-2 sm:px-4 text-xs sm:text-sm text-gray-700 max-w-[120px] sm:max-w-none truncate sm:whitespace-normal">{exp.committee_name || "Unknown"}</td>
                            <td className="py-3 sm:py-4 px-2 sm:px-4 text-xs sm:text-sm text-gray-700 max-w-[100px] sm:max-w-none truncate sm:whitespace-normal">{exp.candidate_name || "N/A"}</td>
                            <td className="py-3 sm:py-4 px-2 sm:px-4 text-xs sm:text-sm text-gray-700 whitespace-nowrap">${Number(exp.amount || 0).toLocaleString()}</td>
                            <td className="py-3 sm:py-4 px-2 sm:px-4">
                              <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
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
                </div>
              </div>
              {/* View All Link - Fixed at bottom, outside scrollable area */}
              <Link to="/expenditures" className="inline-block mt-4 text-purple-600 hover:text-purple-700 text-sm font-medium">
                View All Expenditures →
              </Link>
            </div>

            {/* Top Committees List - Responsive: Full width on mobile, 1 column on desktop */}
            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg flex flex-col">
              <h2 className="text-gray-900 text-base sm:text-lg font-semibold mb-4">Top 10 IE Committees</h2>
              {/* Scrollable Content Container - Vertical scroll with fixed max-height */}
              <div className="overflow-y-auto space-y-2 sm:space-y-3 max-h-[300px] sm:max-h-[400px] lg:max-h-[500px] flex-1 pr-2">
                {loading.charts ? (
                  <>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                      <ListItemSkeleton key={i} />
                    ))}
                  </>
                ) : !chartsData?.top_committees || chartsData.top_committees.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    No committee data available
                  </div>
                ) : (
                  chartsData.top_committees.map((committee, idx) => (
                    <div key={idx} className="flex items-center gap-2 sm:gap-3">
                      {/* Committee Avatar - Responsive size */}
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0">
                        {(committee.name_full || "?").charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs sm:text-sm font-medium text-gray-900 truncate">
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