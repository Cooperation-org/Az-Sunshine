import React, { useState, useEffect, useCallback } from "react";
import { Line, Doughnut, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import { getAnalyticsDashboard, getAnalyticsRealtime } from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import {
  Users,
  Eye,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  Clock,
  TrendingUp,
  MapPin,
  RefreshCw,
  Activity,
  Loader,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, color, subtitle, darkMode }) => (
  <div
    className={`p-5 rounded-2xl border shadow-sm ${
      darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
    }`}
  >
    <div className="flex items-center justify-between">
      <div>
        <p
          className={`text-xs font-medium uppercase tracking-wider ${
            darkMode ? "text-gray-400" : "text-gray-500"
          }`}
        >
          {title}
        </p>
        <p
          className={`text-2xl font-bold mt-1 ${
            darkMode ? "text-white" : "text-gray-900"
          }`}
        >
          {value.toLocaleString()}
        </p>
        {subtitle && (
          <p className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
            {subtitle}
          </p>
        )}
      </div>
      <div
        className="p-3 rounded-xl"
        style={{ backgroundColor: `${color}15` }}
      >
        <Icon size={24} style={{ color }} />
      </div>
    </div>
  </div>
);

// Real-time Indicator
const RealtimeIndicator = ({ count, darkMode }) => (
  <div
    className={`flex items-center gap-3 px-4 py-2 rounded-xl ${
      darkMode ? "bg-green-900/20" : "bg-green-50"
    }`}
  >
    <div className="relative">
      <Activity size={18} className="text-green-500" />
      <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
    </div>
    <div>
      <p className={`text-sm font-semibold ${darkMode ? "text-green-400" : "text-green-700"}`}>
        {count} active now
      </p>
      <p className={`text-xs ${darkMode ? "text-green-500/70" : "text-green-600/70"}`}>
        Real-time visitors
      </p>
    </div>
  </div>
);

export default function Analytics() {
  const { darkMode } = useDarkMode();
  const [data, setData] = useState(null);
  const [realtime, setRealtime] = useState({ count: 0, visitors: [] });
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(30);
  const [refreshing, setRefreshing] = useState(false);
  const [visitsPage, setVisitsPage] = useState(1);
  const visitsPerPage = 15;

  const loadData = useCallback(async () => {
    try {
      const [dashboardData, realtimeData] = await Promise.all([
        getAnalyticsDashboard(dateRange),
        getAnalyticsRealtime(),
      ]);
      setData(dashboardData);
      setRealtime(realtimeData || { count: 0, visitors: [] });
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateRange]);

  useEffect(() => {
    loadData();
    // Refresh realtime data every 30 seconds
    const interval = setInterval(async () => {
      try {
        const realtimeData = await getAnalyticsRealtime();
        setRealtime(realtimeData || { count: 0, visitors: [] });
      } catch (e) {
        console.error("Realtime refresh failed:", e);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <div className={`flex min-h-screen ${darkMode ? "bg-[#1A1625]" : "bg-gray-50"}`}>
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader className="w-8 h-8 animate-spin text-[#7667C1]" />
        </main>
      </div>
    );
  }

  // Chart configurations
  const visitsChartData = {
    labels: data?.visits_by_day?.map((d) => d.date) || [],
    datasets: [
      {
        label: "Visits",
        data: data?.visits_by_day?.map((d) => d.count) || [],
        borderColor: "#7667C1",
        backgroundColor: "rgba(118, 103, 193, 0.1)",
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
      },
    ],
  };

  const deviceChartData = {
    labels: ["Desktop", "Mobile", "Tablet"],
    datasets: [
      {
        data: [
          data?.devices?.desktop || 0,
          data?.devices?.mobile || 0,
          data?.devices?.tablet || 0,
        ],
        backgroundColor: ["#7667C1", "#22c55e", "#f59e0b"],
        borderWidth: 0,
      },
    ],
  };

  const browserChartData = {
    labels: data?.browsers?.map((b) => b.browser) || [],
    datasets: [
      {
        label: "Visitors",
        data: data?.browsers?.map((b) => b.count) || [],
        backgroundColor: "rgba(118, 103, 193, 0.8)",
        borderRadius: 4,
      },
    ],
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? "bg-[#1A1625]" : "bg-gray-50"}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Header */}
          <div
            className="w-full rounded-2xl p-6 md:p-10 mb-8 text-white"
            style={
              darkMode
                ? { background: "#2D2844" }
                : { background: "linear-gradient(to bottom, #685994, #4c3e7c)" }
            }
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
                  Site <span style={{ color: "#A78BFA" }}>Analytics</span>
                </h1>
                <p className="text-white/70 text-sm mt-1">
                  Track visitor behavior, traffic sources, and geographic distribution
                </p>
              </div>
              <div className="flex items-center gap-4">
                <RealtimeIndicator count={realtime.count} darkMode={darkMode} />
                <select
                  value={dateRange}
                  onChange={(e) => {
                    setDateRange(parseInt(e.target.value));
                    setLoading(true);
                  }}
                  className={`px-4 py-2 rounded-full text-sm ${
                    darkMode
                      ? "bg-[#1F1B31] text-white"
                      : "bg-white/15 text-white"
                  } border-none outline-none`}
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <RefreshCw
                    size={18}
                    className={refreshing ? "animate-spin" : ""}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              title="Total Visits"
              value={data?.summary?.total_visits || 0}
              icon={Eye}
              color="#7667C1"
              subtitle={`${dateRange} day period`}
              darkMode={darkMode}
            />
            <StatCard
              title="Unique Visitors"
              value={data?.summary?.unique_visitors || 0}
              icon={Users}
              color="#22c55e"
              darkMode={darkMode}
            />
            <StatCard
              title="Sessions"
              value={data?.summary?.unique_sessions || 0}
              icon={Clock}
              color="#f59e0b"
              darkMode={darkMode}
            />
            <StatCard
              title="Countries"
              value={data?.countries?.length || 0}
              icon={Globe}
              color="#ef4444"
              darkMode={darkMode}
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
            {/* Visits Over Time */}
            <div
              className={`col-span-2 p-6 rounded-2xl border ${
                darkMode
                  ? "bg-[#2D2844] border-gray-700"
                  : "bg-white border-gray-100"
              }`}
            >
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Traffic Over Time
                </h3>
              </div>
              <div className="h-[300px]">
                <Line
                  data={visitsChartData}
                  options={{
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                    },
                    scales: {
                      x: {
                        grid: { display: false },
                        ticks: {
                          color: darkMode ? "#9CA3AF" : "#6B7280",
                          maxTicksLimit: 10,
                        },
                      },
                      y: {
                        grid: {
                          color: darkMode
                            ? "rgba(255,255,255,0.05)"
                            : "rgba(0,0,0,0.05)",
                        },
                        ticks: {
                          color: darkMode ? "#9CA3AF" : "#6B7280",
                        },
                      },
                    },
                  }}
                />
              </div>
            </div>

            {/* Device Distribution */}
            <div
              className={`p-6 rounded-2xl border ${
                darkMode
                  ? "bg-[#2D2844] border-gray-700"
                  : "bg-white border-gray-100"
              }`}
            >
              <div className="flex items-center gap-3 mb-6">
                <Monitor size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Devices
                </h3>
              </div>
              <div className="h-[200px] flex items-center justify-center">
                <Doughnut
                  data={deviceChartData}
                  options={{
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: "bottom",
                        labels: {
                          color: darkMode ? "#9CA3AF" : "#6B7280",
                          padding: 20,
                        },
                      },
                    },
                    cutout: "70%",
                  }}
                />
              </div>
              <div className="grid grid-cols-3 gap-2 mt-4">
                <div className="text-center">
                  <Monitor size={16} className="mx-auto text-[#7667C1]" />
                  <p className={`text-xs mt-1 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                    {data?.devices?.desktop || 0}
                  </p>
                </div>
                <div className="text-center">
                  <Smartphone size={16} className="mx-auto text-green-500" />
                  <p className={`text-xs mt-1 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                    {data?.devices?.mobile || 0}
                  </p>
                </div>
                <div className="text-center">
                  <Tablet size={16} className="mx-auto text-amber-500" />
                  <p className={`text-xs mt-1 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                    {data?.devices?.tablet || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top Pages */}
            <div
              className={`p-6 rounded-2xl border ${
                darkMode
                  ? "bg-[#2D2844] border-gray-700"
                  : "bg-white border-gray-100"
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <Eye size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Top Pages
                </h3>
              </div>
              <div className="space-y-3">
                {data?.top_pages?.slice(0, 8).map((page, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between"
                  >
                    <span
                      className={`text-sm truncate max-w-[200px] ${
                        darkMode ? "text-gray-300" : "text-gray-700"
                      }`}
                    >
                      {page.path}
                    </span>
                    <span
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-400" : "text-gray-500"
                      }`}
                    >
                      {page.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Countries */}
            <div
              className={`p-6 rounded-2xl border ${
                darkMode
                  ? "bg-[#2D2844] border-gray-700"
                  : "bg-white border-gray-100"
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <MapPin size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Top Countries
                </h3>
              </div>
              <div className="space-y-3">
                {data?.countries?.slice(0, 8).map((country, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {getCountryFlag(country.country_code)}
                      </span>
                      <span
                        className={`text-sm ${
                          darkMode ? "text-gray-300" : "text-gray-700"
                        }`}
                      >
                        {country.country}
                      </span>
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        darkMode ? "text-gray-400" : "text-gray-500"
                      }`}
                    >
                      {country.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Browsers */}
            <div
              className={`p-6 rounded-2xl border ${
                darkMode
                  ? "bg-[#2D2844] border-gray-700"
                  : "bg-white border-gray-100"
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <Globe size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Browsers
                </h3>
              </div>
              <div className="h-[200px]">
                <Bar
                  data={browserChartData}
                  options={{
                    maintainAspectRatio: false,
                    indexAxis: "y",
                    plugins: {
                      legend: { display: false },
                    },
                    scales: {
                      x: {
                        grid: {
                          color: darkMode
                            ? "rgba(255,255,255,0.05)"
                            : "rgba(0,0,0,0.05)",
                        },
                        ticks: {
                          color: darkMode ? "#9CA3AF" : "#6B7280",
                        },
                      },
                      y: {
                        grid: { display: false },
                        ticks: {
                          color: darkMode ? "#9CA3AF" : "#6B7280",
                        },
                      },
                    },
                  }}
                />
              </div>
            </div>
          </div>

          {/* Recent Visits Table with Pagination */}
          <div
            className={`mt-8 p-6 rounded-2xl border ${
              darkMode
                ? "bg-[#2D2844] border-gray-700"
                : "bg-white border-gray-100"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Activity size={18} className="text-[#7667C1]" />
                <h3
                  className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}
                >
                  Recent Visits
                </h3>
                <span className={`text-xs ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                  ({data?.recent_visits?.length || 0} total)
                </span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr
                    className={`text-xs uppercase ${
                      darkMode ? "text-gray-400" : "text-gray-500"
                    }`}
                  >
                    <th className="text-left py-2 px-3">Page</th>
                    <th className="text-left py-2 px-3">Location</th>
                    <th className="text-left py-2 px-3">Device</th>
                    <th className="text-left py-2 px-3">Browser</th>
                    <th className="text-left py-2 px-3">Time</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${darkMode ? "divide-gray-700" : "divide-gray-100"}`}>
                  {data?.recent_visits
                    ?.slice((visitsPage - 1) * visitsPerPage, visitsPage * visitsPerPage)
                    .map((visit, idx) => (
                    <tr key={idx}>
                      <td
                        className={`py-3 px-3 text-sm ${
                          darkMode ? "text-gray-300" : "text-gray-700"
                        }`}
                      >
                        {visit.path}
                      </td>
                      <td
                        className={`py-3 px-3 text-sm ${
                          darkMode ? "text-gray-400" : "text-gray-500"
                        }`}
                      >
                        {visit.city && visit.country
                          ? `${visit.city}, ${visit.country}`
                          : visit.country || "Unknown"}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs ${
                            darkMode
                              ? "bg-purple-900/30 text-purple-300"
                              : "bg-purple-100 text-purple-700"
                          }`}
                        >
                          {visit.device_type}
                        </span>
                      </td>
                      <td
                        className={`py-3 px-3 text-sm ${
                          darkMode ? "text-gray-400" : "text-gray-500"
                        }`}
                      >
                        {visit.browser}
                      </td>
                      <td
                        className={`py-3 px-3 text-sm ${
                          darkMode ? "text-gray-400" : "text-gray-500"
                        }`}
                      >
                        {formatTime(visit.timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {data?.recent_visits?.length > visitsPerPage && (
              <div className={`flex items-center justify-between mt-4 pt-4 border-t ${
                darkMode ? "border-gray-700" : "border-gray-200"
              }`}>
                <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                  Showing {((visitsPage - 1) * visitsPerPage) + 1} - {Math.min(visitsPage * visitsPerPage, data?.recent_visits?.length)} of {data?.recent_visits?.length}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setVisitsPage(Math.max(1, visitsPage - 1))}
                    disabled={visitsPage === 1}
                    className={`w-9 h-9 rounded-lg border flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed ${
                      darkMode
                        ? "bg-[#1F1B31] text-gray-300 hover:bg-[#16131F] border-gray-700"
                        : "bg-white text-gray-700 hover:bg-gray-100 border-gray-300"
                    }`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className={`text-sm px-3 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                    Page {visitsPage} of {Math.ceil((data?.recent_visits?.length || 0) / visitsPerPage)}
                  </span>
                  <button
                    onClick={() => setVisitsPage(Math.min(Math.ceil((data?.recent_visits?.length || 0) / visitsPerPage), visitsPage + 1))}
                    disabled={visitsPage >= Math.ceil((data?.recent_visits?.length || 0) / visitsPerPage)}
                    className={`w-9 h-9 rounded-lg border flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed ${
                      darkMode
                        ? "bg-[#1F1B31] text-gray-300 hover:bg-[#16131F] border-gray-700"
                        : "bg-white text-gray-700 hover:bg-gray-100 border-gray-300"
                    }`}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// Helper function to get country flag emoji
function getCountryFlag(countryCode) {
  if (!countryCode) return "";
  const codePoints = countryCode
    .toUpperCase()
    .split("")
    .map((char) => 127397 + char.charCodeAt());
  return String.fromCodePoint(...codePoints);
}

// Helper function to format timestamp
function formatTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Just now";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
}
