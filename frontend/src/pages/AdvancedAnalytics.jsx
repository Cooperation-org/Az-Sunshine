import React, { useState, useEffect, useCallback } from "react";
import { Line, Doughnut, Bar, Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import {
  getAdvancedAnalyticsDashboard,
  getUserJourneys,
  getFunnelAnalysis,
  getCandidateHeatmap,
  getCandidateViralAlerts,
  getSearchAnalytics,
  getReferrerIntelligence,
  getEngagementMetrics,
  getGeographicIntelligence,
  getTimePatterns,
  getAPIUsageAnalytics,
  getContentPerformance,
  getAnomalyAlerts,
  acknowledgeAlert,
  runAnomalyDetection,
} from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import {
  Users,
  TrendingUp,
  Search,
  Link,
  Target,
  MapPin,
  Clock,
  Server,
  FileText,
  AlertTriangle,
  RefreshCw,
  Loader,
  ChevronRight,
  Check,
  X,
  Flame,
  Zap,
  Eye,
  Filter,
  ArrowUp,
  ArrowDown,
  Globe,
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Tab definitions
const TABS = [
  { id: "overview", label: "Overview", icon: TrendingUp },
  { id: "journeys", label: "User Journeys", icon: Users },
  { id: "heatmap", label: "Candidate Heatmap", icon: Flame },
  { id: "search", label: "Search Analytics", icon: Search },
  { id: "referrers", label: "Referrer Intel", icon: Link },
  { id: "engagement", label: "Engagement", icon: Target },
  { id: "geographic", label: "Geographic", icon: MapPin },
  { id: "time", label: "Time Patterns", icon: Clock },
  { id: "api", label: "API Usage", icon: Server },
  { id: "content", label: "Content", icon: FileText },
  { id: "alerts", label: "Alerts", icon: AlertTriangle },
];

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, color, subtitle, trend, darkMode }) => (
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
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        {subtitle && (
          <p className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
            {subtitle}
          </p>
        )}
        {trend !== undefined && (
          <div className={`flex items-center gap-1 mt-1 text-xs ${
            trend >= 0 ? "text-green-500" : "text-red-500"
          }`}>
            {trend >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
            {Math.abs(trend)}% vs last period
          </div>
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

// Alert Card Component
const AlertCard = ({ alert, darkMode, onAcknowledge }) => {
  const severityColors = {
    low: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
    medium: { bg: "bg-yellow-500/10", text: "text-yellow-500", border: "border-yellow-500/30" },
    high: { bg: "bg-orange-500/10", text: "text-orange-500", border: "border-orange-500/30" },
    critical: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/30" },
  };

  const colors = severityColors[alert.severity] || severityColors.medium;

  return (
    <div className={`p-4 rounded-xl border ${colors.bg} ${colors.border} ${
      alert.is_acknowledged ? "opacity-60" : ""
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <AlertTriangle className={colors.text} size={20} />
          <div>
            <h4 className={`font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
              {alert.title}
            </h4>
            <p className={`text-sm mt-1 ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              {alert.description}
            </p>
            <div className="flex items-center gap-3 mt-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}>
                {alert.severity.toUpperCase()}
              </span>
              <span className={`text-xs ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
        {!alert.is_acknowledged && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className={`p-2 rounded-lg transition ${
              darkMode ? "hover:bg-white/10" : "hover:bg-black/5"
            }`}
          >
            <Check size={16} className={darkMode ? "text-gray-400" : "text-gray-500"} />
          </button>
        )}
      </div>
    </div>
  );
};

// Funnel Step Component
const FunnelStep = ({ step, index, total, darkMode }) => {
  const width = 100 - (index * (60 / total));
  return (
    <div className="relative">
      <div
        className={`h-12 rounded-lg flex items-center justify-between px-4 mx-auto transition-all ${
          darkMode ? "bg-purple-900/30" : "bg-purple-100"
        }`}
        style={{ width: `${width}%` }}
      >
        <span className={`text-sm font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
          {step.step}
        </span>
        <span className={`text-sm font-bold ${darkMode ? "text-purple-300" : "text-purple-700"}`}>
          {step.users?.toLocaleString() || 0}
        </span>
      </div>
      {step.conversion_rate !== undefined && index > 0 && (
        <div className={`text-center text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
          {step.conversion_rate.toFixed(1)}% conversion
        </div>
      )}
    </div>
  );
};

export default function AdvancedAnalytics() {
  const { darkMode } = useDarkMode();
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dateRange, setDateRange] = useState(30);

  // Data states for each section
  const [overview, setOverview] = useState(null);
  const [journeys, setJourneys] = useState(null);
  const [funnels, setFunnels] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [viralAlerts, setViralAlerts] = useState([]);
  const [searchData, setSearchData] = useState(null);
  const [referrers, setReferrers] = useState(null);
  const [engagement, setEngagement] = useState(null);
  const [geographic, setGeographic] = useState(null);
  const [timePatterns, setTimePatterns] = useState(null);
  const [apiUsage, setApiUsage] = useState(null);
  const [content, setContent] = useState(null);
  const [alerts, setAlerts] = useState([]);

  const loadData = useCallback(async () => {
    try {
      // Load all data in parallel
      const [
        overviewData,
        journeysData,
        funnelsData,
        heatmapData,
        viralData,
        searchAnalytics,
        referrerData,
        engagementData,
        geoData,
        timePatternsData,
        apiData,
        contentData,
        alertsData,
      ] = await Promise.all([
        getAdvancedAnalyticsDashboard(dateRange).catch(() => null),
        getUserJourneys({ days: dateRange }).catch(() => null),
        getFunnelAnalysis({ days: dateRange }).catch(() => null),
        getCandidateHeatmap({ days: dateRange }).catch(() => null),
        getCandidateViralAlerts({ days: dateRange }).catch(() => []),
        getSearchAnalytics({ days: dateRange }).catch(() => null),
        getReferrerIntelligence({ days: dateRange }).catch(() => null),
        getEngagementMetrics({ days: dateRange }).catch(() => null),
        getGeographicIntelligence({ days: dateRange }).catch(() => null),
        getTimePatterns({ days: dateRange }).catch(() => null),
        getAPIUsageAnalytics({ days: dateRange }).catch(() => null),
        getContentPerformance({ days: dateRange }).catch(() => null),
        getAnomalyAlerts({ days: dateRange }).catch(() => []),
      ]);

      setOverview(overviewData);
      setJourneys(journeysData);
      setFunnels(funnelsData);
      setHeatmap(heatmapData);
      setViralAlerts(viralData?.alerts || []);
      setSearchData(searchAnalytics);
      setReferrers(referrerData);
      setEngagement(engagementData);
      setGeographic(geoData);
      setTimePatterns(timePatternsData);
      setApiUsage(apiData);
      setContent(contentData);
      setAlerts(alertsData?.alerts || []);
    } catch (error) {
      console.error("Failed to load advanced analytics:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateRange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, is_acknowledged: true } : a
      ));
    } catch (error) {
      console.error("Failed to acknowledge alert:", error);
    }
  };

  const handleRunDetection = async () => {
    try {
      setRefreshing(true);
      await runAnomalyDetection();
      const alertsData = await getAnomalyAlerts({ days: dateRange });
      setAlerts(alertsData?.alerts || []);
    } catch (error) {
      console.error("Failed to run detection:", error);
    } finally {
      setRefreshing(false);
    }
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

  // Helper to parse engagement distribution array into segments object
  const getEngagementSegments = () => {
    const segments = { casual: 0, interested: 0, engaged: 0, power_user: 0 };
    if (overview?.engagement_distribution) {
      overview.engagement_distribution.forEach(item => {
        if (segments.hasOwnProperty(item.engagement_score)) {
          segments[item.engagement_score] = item.count;
        }
      });
    }
    return segments;
  };

  const engagementSegments = getEngagementSegments();

  // Chart configurations
  const hourlyChartData = {
    labels: timePatterns?.hourly?.map(h => `${h.hour}:00`) || [],
    datasets: [{
      label: "Visitors",
      data: timePatterns?.hourly?.map(h => h.visits || h.count || 0) || [],
      borderColor: "#7667C1",
      backgroundColor: "rgba(118, 103, 193, 0.2)",
      fill: true,
      tension: 0.4,
    }],
  };

  const engagementRadarData = {
    labels: ["Casual", "Interested", "Engaged", "Power Users"],
    datasets: [{
      label: "User Distribution",
      data: [
        engagementSegments.casual,
        engagementSegments.interested,
        engagementSegments.engaged,
        engagementSegments.power_user,
      ],
      backgroundColor: "rgba(118, 103, 193, 0.3)",
      borderColor: "#7667C1",
      pointBackgroundColor: "#7667C1",
    }],
  };

  const referrerChartData = {
    labels: referrers?.top_referrers?.slice(0, 8).map(r => r.domain || r.source) || [],
    datasets: [{
      label: "Visitors",
      data: referrers?.top_referrers?.slice(0, 8).map(r => r.count || r.visitors) || [],
      backgroundColor: [
        "#7667C1", "#22c55e", "#f59e0b", "#ef4444",
        "#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4"
      ],
      borderRadius: 4,
    }],
  };

  const apiUsageChartData = {
    labels: apiUsage?.top_endpoints?.slice(0, 8).map(e => e.endpoint?.split('/').pop() || e.endpoint) || [],
    datasets: [{
      label: "Calls",
      data: apiUsage?.top_endpoints?.slice(0, 8).map(e => e.count) || [],
      backgroundColor: "rgba(118, 103, 193, 0.8)",
      borderRadius: 4,
    }],
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return (
          <div className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Total Sessions"
                value={overview?.sessions?.total || journeys?.summary?.total_sessions || 0}
                icon={Users}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Session Duration"
                value={`${Math.round((overview?.sessions?.avg_duration || journeys?.summary?.avg_duration || 0) / 60)}m`}
                icon={Clock}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Engagement Rate"
                value={`${(engagement?.engagement_rate || 0).toFixed(1)}%`}
                icon={Target}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Active Alerts"
                value={alerts.filter(a => !a.is_acknowledged).length}
                icon={AlertTriangle}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            {/* Quick Insights */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Trending Candidates */}
              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <Flame size={18} className="text-orange-500" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    Trending Candidates
                  </h3>
                </div>
                <div className="space-y-3">
                  {(heatmap?.candidates || heatmap?.top_candidates)?.slice(0, 5).map((candidate, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          idx === 0 ? "bg-yellow-500 text-white" :
                          idx === 1 ? "bg-gray-400 text-white" :
                          idx === 2 ? "bg-amber-600 text-white" :
                          darkMode ? "bg-gray-700 text-gray-300" : "bg-gray-200 text-gray-600"
                        }`}>
                          {idx + 1}
                        </span>
                        <span className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                          {candidate.candidate_name || candidate.name}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                        {candidate.views || candidate.view_count || 0} views
                      </span>
                    </div>
                  ))}
                  {(!heatmap?.candidates && !heatmap?.top_candidates) && (
                    <p className={`text-sm ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                      No candidate data available yet
                    </p>
                  )}
                </div>
              </div>

              {/* Recent Alerts */}
              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <AlertTriangle size={18} className="text-red-500" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    Recent Alerts
                  </h3>
                </div>
                <div className="space-y-3">
                  {alerts.slice(0, 3).map((alert, idx) => (
                    <AlertCard
                      key={idx}
                      alert={alert}
                      darkMode={darkMode}
                      onAcknowledge={handleAcknowledgeAlert}
                    />
                  ))}
                  {alerts.length === 0 && (
                    <p className={`text-sm ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                      No alerts - system running smoothly
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Traffic Pattern */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Clock size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Hourly Traffic Pattern
                </h3>
              </div>
              <div className="h-[250px]">
                <Line
                  data={hourlyChartData}
                  options={{
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: {
                        grid: { display: false },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                      y: {
                        grid: { color: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                    },
                  }}
                />
              </div>
            </div>
          </div>
        );

      case "journeys":
        return (
          <div className="space-y-6">
            {/* Journey Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Sessions"
                value={journeys?.summary?.total_sessions || 0}
                icon={Users}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Pages/Session"
                value={(journeys?.summary?.avg_pages_per_session || 0).toFixed(1)}
                icon={FileText}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Duration"
                value={`${Math.round((journeys?.summary?.avg_duration || 0) / 60)}m`}
                icon={Clock}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Bounce Rate"
                value={`${(journeys?.summary?.bounce_rate || 0).toFixed(1)}%`}
                icon={X}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            {/* Funnel Analysis */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-6">
                <Filter size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Conversion Funnel
                </h3>
              </div>
              <div className="space-y-4">
                {(funnels?.steps || funnels?.funnel_steps)?.map((step, idx) => (
                  <FunnelStep
                    key={idx}
                    step={{...step, users: step.count || step.users}}
                    index={idx}
                    total={(funnels?.steps || funnels?.funnel_steps)?.length || 1}
                    darkMode={darkMode}
                  />
                ))}
                {(!funnels?.steps && !funnels?.funnel_steps) && (
                  <p className={`text-center py-8 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No funnel data available yet. User journey tracking will populate this.
                  </p>
                )}
              </div>
            </div>

            {/* Common Paths */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <ChevronRight size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Common User Paths
                </h3>
              </div>
              <div className="space-y-3">
                {journeys?.common_paths?.slice(0, 8).map((path, idx) => (
                  <div key={idx} className={`p-3 rounded-lg ${
                    darkMode ? "bg-[#1F1B31]" : "bg-gray-50"
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 overflow-x-auto">
                        {path.path?.map((page, pIdx) => (
                          <React.Fragment key={pIdx}>
                            <span className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                              darkMode ? "bg-purple-900/30 text-purple-300" : "bg-purple-100 text-purple-700"
                            }`}>
                              {page}
                            </span>
                            {pIdx < path.path.length - 1 && (
                              <ChevronRight size={14} className={darkMode ? "text-gray-600" : "text-gray-400"} />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                      <span className={`text-sm font-medium ml-4 ${
                        darkMode ? "text-gray-400" : "text-gray-500"
                      }`}>
                        {path.count} users
                      </span>
                    </div>
                  </div>
                ))}
                {(!journeys?.common_paths || journeys.common_paths.length === 0) && (
                  <p className={`text-center py-4 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No path data available yet
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      case "heatmap":
        return (
          <div className="space-y-6">
            {/* Heatmap Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Candidate Views"
                value={heatmap?.summary?.total_views || 0}
                icon={Eye}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Unique Candidates Viewed"
                value={heatmap?.summary?.unique_candidates || 0}
                icon={Users}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Time on Profile"
                value={`${Math.round((heatmap?.summary?.avg_time_on_page || 0) / 60)}m`}
                icon={Clock}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Viral Candidates"
                value={viralAlerts.length}
                icon={Flame}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            {/* Viral Alerts */}
            {viralAlerts.length > 0 && (
              <div className={`p-6 rounded-2xl border border-orange-500/30 ${
                darkMode ? "bg-orange-900/10" : "bg-orange-50"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <Zap size={18} className="text-orange-500" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest text-orange-500`}>
                    Viral Alert - Candidates Getting Attention
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {viralAlerts.map((alert, idx) => (
                    <div key={idx} className={`p-4 rounded-lg ${
                      darkMode ? "bg-[#2D2844]" : "bg-white"
                    }`}>
                      <h4 className={`font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                        {alert.candidate_name}
                      </h4>
                      <p className={`text-sm mt-1 ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                        {alert.view_count} views ({alert.increase_percent}% increase)
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Candidates Table */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Flame size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Candidate Interest Rankings
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className={`text-xs uppercase ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                      <th className="text-left py-2 px-3">Rank</th>
                      <th className="text-left py-2 px-3">Candidate</th>
                      <th className="text-left py-2 px-3">District</th>
                      <th className="text-right py-2 px-3">Views</th>
                      <th className="text-right py-2 px-3">Avg Time</th>
                      <th className="text-right py-2 px-3">IE Interest</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${darkMode ? "divide-gray-700" : "divide-gray-100"}`}>
                    {(heatmap?.candidates || heatmap?.top_candidates)?.map((candidate, idx) => (
                      <tr key={idx}>
                        <td className={`py-3 px-3 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            idx === 0 ? "bg-yellow-500 text-white" :
                            idx === 1 ? "bg-gray-400 text-white" :
                            idx === 2 ? "bg-amber-600 text-white" :
                            darkMode ? "bg-gray-700 text-gray-300" : "bg-gray-200 text-gray-600"
                          }`}>
                            {idx + 1}
                          </span>
                        </td>
                        <td className={`py-3 px-3 font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                          {candidate.candidate_name || candidate.name}
                        </td>
                        <td className={`py-3 px-3 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {candidate.district || "-"}
                        </td>
                        <td className={`py-3 px-3 text-right font-medium ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                          {candidate.views || candidate.view_count || 0}
                        </td>
                        <td className={`py-3 px-3 text-right ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {candidate.avg_time ? `${Math.round(candidate.avg_time / 60)}m` : "-"}
                        </td>
                        <td className={`py-3 px-3 text-right ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {candidate.ie_interest_rate ? `${candidate.ie_interest_rate.toFixed(0)}%` : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(!heatmap?.candidates && !heatmap?.top_candidates) && (
                  <p className={`text-center py-8 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No candidate view data available yet
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      case "search":
        return (
          <div className="space-y-6">
            {/* Search Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Searches"
                value={searchData?.summary?.total_searches || 0}
                icon={Search}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Unique Queries"
                value={searchData?.summary?.unique_queries || 0}
                icon={FileText}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Success Rate"
                value={`${(100 - (searchData?.summary?.no_results_rate || 0)).toFixed(1)}%`}
                icon={Check}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Zero Results"
                value={searchData?.summary?.no_results_count || searchData?.summary?.zero_results || 0}
                icon={X}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Searches */}
              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp size={18} className="text-[#7667C1]" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    Top Search Terms
                  </h3>
                </div>
                <div className="space-y-3">
                  {searchData?.top_searches?.map((search, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                        "{search.normalized_query || search.query}"
                      </span>
                      <span className={`text-sm font-medium ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                        {search.count}
                      </span>
                    </div>
                  ))}
                  {(!searchData?.top_searches || searchData.top_searches.length === 0) && (
                    <p className={`text-center py-4 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                      No search data available yet
                    </p>
                  )}
                </div>
              </div>

              {/* Failed Searches */}
              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <X size={18} className="text-red-500" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    Failed Searches (No Results)
                  </h3>
                </div>
                <div className="space-y-3">
                  {(searchData?.content_gaps || searchData?.failed_searches)?.map((search, idx) => (
                    <div key={idx} className={`flex items-center justify-between p-2 rounded ${
                      darkMode ? "bg-red-900/10" : "bg-red-50"
                    }`}>
                      <span className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                        "{search.normalized_query || search.query}"
                      </span>
                      <span className="text-sm font-medium text-red-500">
                        {search.count}x
                      </span>
                    </div>
                  ))}
                  {(!searchData?.content_gaps && !searchData?.failed_searches) && (
                    <p className={`text-center py-4 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                      No failed searches - great news!
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case "referrers":
        return (
          <div className="space-y-6">
            {/* Referrer Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Referrals"
                value={referrers?.summary?.total_referrals || 0}
                icon={Link}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Unique Sources"
                value={referrers?.summary?.unique_sources || 0}
                icon={Globe}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Social Traffic"
                value={`${(referrers?.summary?.social_percent || 0).toFixed(1)}%`}
                icon={Users}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Direct Traffic"
                value={`${(referrers?.summary?.direct_percent || 0).toFixed(1)}%`}
                icon={Target}
                color="#3b82f6"
                darkMode={darkMode}
              />
            </div>

            {/* Referrer Chart */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Link size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Traffic Sources
                </h3>
              </div>
              <div className="h-[300px]">
                <Bar
                  data={referrerChartData}
                  options={{
                    maintainAspectRatio: false,
                    indexAxis: "y",
                    plugins: { legend: { display: false } },
                    scales: {
                      x: {
                        grid: { color: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                      y: {
                        grid: { display: false },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                    },
                  }}
                />
              </div>
            </div>

            {/* UTM Campaigns */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Target size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Campaign Performance (UTM)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className={`text-xs uppercase ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                      <th className="text-left py-2 px-3">Campaign</th>
                      <th className="text-left py-2 px-3">Source</th>
                      <th className="text-left py-2 px-3">Medium</th>
                      <th className="text-right py-2 px-3">Visitors</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${darkMode ? "divide-gray-700" : "divide-gray-100"}`}>
                    {referrers?.campaigns?.map((campaign, idx) => (
                      <tr key={idx}>
                        <td className={`py-3 px-3 font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                          {campaign.campaign || "(not set)"}
                        </td>
                        <td className={`py-3 px-3 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {campaign.source || "-"}
                        </td>
                        <td className={`py-3 px-3 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {campaign.medium || "-"}
                        </td>
                        <td className={`py-3 px-3 text-right font-medium ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                          {campaign.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(!referrers?.campaigns || referrers.campaigns.length === 0) && (
                  <p className={`text-center py-8 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No UTM campaign data available. Add UTM parameters to your marketing links.
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      case "engagement":
        return (
          <div className="space-y-6">
            {/* Engagement Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Avg Engagement Score"
                value={(engagement?.overview?.avg_engagement_score || engagement?.avg_score || 0).toFixed(1)}
                icon={Target}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Power Users"
                value={engagementSegments.power_user}
                icon={Zap}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Engaged Users"
                value={engagementSegments.engaged}
                icon={Users}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Bounce Rate"
                value={`${(engagement?.overview?.bounce_rate || journeys?.summary?.bounce_rate || 0).toFixed(1)}%`}
                icon={X}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            {/* Engagement Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <Target size={18} className="text-[#7667C1]" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    User Segments
                  </h3>
                </div>
                <div className="h-[300px] flex items-center justify-center">
                  <Radar
                    data={engagementRadarData}
                    options={{
                      maintainAspectRatio: false,
                      scales: {
                        r: {
                          beginAtZero: true,
                          grid: { color: darkMode ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)" },
                          pointLabels: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                          ticks: { display: false },
                        },
                      },
                      plugins: { legend: { display: false } },
                    }}
                  />
                </div>
              </div>

              <div className={`p-6 rounded-2xl border ${
                darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
              }`}>
                <div className="flex items-center gap-3 mb-4">
                  <Users size={18} className="text-[#7667C1]" />
                  <h3 className={`text-sm font-bold uppercase tracking-widest ${
                    darkMode ? "text-gray-400" : "text-gray-500"
                  }`}>
                    Segment Breakdown
                  </h3>
                </div>
                <div className="space-y-4">
                  {[
                    { label: "Power Users", count: engagementSegments.power_user, color: "#22c55e", desc: "5+ pages, 3+ min" },
                    { label: "Engaged", count: engagementSegments.engaged, color: "#3b82f6", desc: "3-5 pages, 1-3 min" },
                    { label: "Interested", count: engagementSegments.interested, color: "#f59e0b", desc: "2-3 pages" },
                    { label: "Casual", count: engagementSegments.casual, color: "#9CA3AF", desc: "1 page" },
                  ].map((segment, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: segment.color }} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={`font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                            {segment.label}
                          </span>
                          <span className={`font-bold ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                            {segment.count}
                          </span>
                        </div>
                        <p className={`text-xs ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                          {segment.desc}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case "geographic":
        return (
          <div className="space-y-6">
            {/* Geographic Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Arizona Visitors"
                value={geographic?.az_stats?.total || 0}
                icon={MapPin}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Maricopa County"
                value={geographic?.az_stats?.maricopa || 0}
                icon={MapPin}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Pima County"
                value={geographic?.az_stats?.pima || 0}
                icon={MapPin}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Other AZ"
                value={geographic?.az_stats?.other || 0}
                icon={MapPin}
                color="#3b82f6"
                darkMode={darkMode}
              />
            </div>

            {/* Arizona Regions */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <MapPin size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Arizona Regional Distribution
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {geographic?.regions?.map((region, idx) => (
                  <div key={idx} className={`p-4 rounded-lg ${
                    darkMode ? "bg-[#1F1B31]" : "bg-gray-50"
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className={`font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                        {region.region}
                      </span>
                      <span className={`font-bold ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                        {region.count}
                      </span>
                    </div>
                    <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500 rounded-full"
                        style={{ width: `${(region.count / (geographic?.az_stats?.total || 1)) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
                {(!geographic?.regions || geographic.regions.length === 0) && (
                  <p className={`col-span-full text-center py-4 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No geographic data available yet
                  </p>
                )}
              </div>
            </div>

            {/* Top Cities */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <MapPin size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Top Cities
                </h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {geographic?.top_cities?.map((city, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                      {city.city}
                    </span>
                    <span className={`text-sm font-medium ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                      {city.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case "time":
        const peakHourValue = typeof timePatterns?.peak_hour === 'object'
          ? timePatterns.peak_hour?.hour
          : timePatterns?.peak_hour;
        return (
          <div className="space-y-6">
            {/* Time Pattern Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Peak Hour"
                value={`${peakHourValue ?? 12}:00`}
                icon={Clock}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Best Day"
                value={timePatterns?.best_day || timePatterns?.peak_day || "Monday"}
                icon={Clock}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Weekend Traffic"
                value={`${(timePatterns?.weekend_percent || 0).toFixed(1)}%`}
                icon={Clock}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="After Hours"
                value={`${(timePatterns?.after_hours_percent || 0).toFixed(1)}%`}
                icon={Clock}
                color="#3b82f6"
                darkMode={darkMode}
              />
            </div>

            {/* Hourly Distribution */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Clock size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Hourly Traffic Distribution
                </h3>
              </div>
              <div className="h-[300px]">
                <Line
                  data={hourlyChartData}
                  options={{
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: {
                        grid: { display: false },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                      y: {
                        grid: { color: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                    },
                  }}
                />
              </div>
            </div>

            {/* Weekly Heatmap */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Clock size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Daily Distribution
                </h3>
              </div>
              <div className="grid grid-cols-7 gap-2">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day, idx) => {
                  const dailyData = timePatterns?.daily || timePatterns?.daily_distribution || [];
                  const dayData = dailyData.find(d => d.day === idx || d.day_of_week === idx) || { count: 0, visits: 0 };
                  const counts = dailyData.map(d => d.count || d.visits || 0);
                  const maxCount = Math.max(...counts, 1);
                  const count = dayData.count || dayData.visits || 0;
                  const intensity = count / maxCount;
                  return (
                    <div key={day} className="text-center">
                      <p className={`text-xs mb-1 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                        {day}
                      </p>
                      <div
                        className="h-16 rounded-lg flex items-center justify-center"
                        style={{
                          backgroundColor: `rgba(118, 103, 193, ${0.1 + intensity * 0.7})`,
                        }}
                      >
                        <span className={`text-sm font-medium ${
                          intensity > 0.5 ? "text-white" : darkMode ? "text-gray-300" : "text-gray-700"
                        }`}>
                          {count}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );

      case "api":
        return (
          <div className="space-y-6">
            {/* API Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total API Calls"
                value={apiUsage?.summary?.total_calls || 0}
                icon={Server}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Response Time"
                value={`${(apiUsage?.summary?.avg_response_time || 0).toFixed(0)}ms`}
                icon={Clock}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Error Rate"
                value={`${(apiUsage?.summary?.error_rate || 0).toFixed(2)}%`}
                icon={X}
                color="#ef4444"
                darkMode={darkMode}
              />
              <StatCard
                title="Unique Endpoints"
                value={apiUsage?.summary?.unique_endpoints || 0}
                icon={Target}
                color="#f59e0b"
                darkMode={darkMode}
              />
            </div>

            {/* Top Endpoints Chart */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Server size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Top API Endpoints
                </h3>
              </div>
              <div className="h-[300px]">
                <Bar
                  data={apiUsageChartData}
                  options={{
                    maintainAspectRatio: false,
                    indexAxis: "y",
                    plugins: { legend: { display: false } },
                    scales: {
                      x: {
                        grid: { color: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)" },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                      y: {
                        grid: { display: false },
                        ticks: { color: darkMode ? "#9CA3AF" : "#6B7280" },
                      },
                    },
                  }}
                />
              </div>
            </div>

            {/* Slowest Endpoints */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <Clock size={18} className="text-orange-500" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Slowest Endpoints
                </h3>
              </div>
              <div className="space-y-3">
                {apiUsage?.slowest_endpoints?.map((endpoint, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                      {endpoint.endpoint}
                    </span>
                    <span className={`text-sm font-medium ${
                      endpoint.avg_time > 1000 ? "text-red-500" :
                      endpoint.avg_time > 500 ? "text-orange-500" : "text-green-500"
                    }`}>
                      {endpoint.avg_time.toFixed(0)}ms
                    </span>
                  </div>
                ))}
                {(!apiUsage?.slowest_endpoints || apiUsage.slowest_endpoints.length === 0) && (
                  <p className={`text-center py-4 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No API usage data available yet
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      case "content":
        return (
          <div className="space-y-6">
            {/* Content Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Page Views"
                value={content?.summary?.total_views || 0}
                icon={Eye}
                color="#7667C1"
                darkMode={darkMode}
              />
              <StatCard
                title="Unique Pages"
                value={content?.summary?.unique_pages || 0}
                icon={FileText}
                color="#22c55e"
                darkMode={darkMode}
              />
              <StatCard
                title="Avg Time on Page"
                value={`${Math.round((content?.summary?.avg_time || 0) / 60)}m`}
                icon={Clock}
                color="#f59e0b"
                darkMode={darkMode}
              />
              <StatCard
                title="Exit Rate"
                value={`${(content?.summary?.exit_rate || 0).toFixed(1)}%`}
                icon={X}
                color="#ef4444"
                darkMode={darkMode}
              />
            </div>

            {/* Top Content */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <FileText size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  Top Performing Pages
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className={`text-xs uppercase ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                      <th className="text-left py-2 px-3">Page</th>
                      <th className="text-right py-2 px-3">Views</th>
                      <th className="text-right py-2 px-3">Unique</th>
                      <th className="text-right py-2 px-3">Avg Time</th>
                      <th className="text-right py-2 px-3">Bounce</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${darkMode ? "divide-gray-700" : "divide-gray-100"}`}>
                    {content?.top_pages?.map((page, idx) => (
                      <tr key={idx}>
                        <td className={`py-3 px-3 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                          <a
                            href={page.path}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`hover:underline ${
                              darkMode ? "text-purple-400" : "text-purple-600"
                            }`}
                          >
                            {page.path}
                          </a>
                        </td>
                        <td className={`py-3 px-3 text-right font-medium ${darkMode ? "text-white" : "text-gray-900"}`}>
                          {page.views}
                        </td>
                        <td className={`py-3 px-3 text-right ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {page.unique_views}
                        </td>
                        <td className={`py-3 px-3 text-right ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {page.avg_time ? `${Math.round(page.avg_time / 60)}m` : "-"}
                        </td>
                        <td className={`py-3 px-3 text-right ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                          {page.bounce_rate ? `${page.bounce_rate.toFixed(1)}%` : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(!content?.top_pages || content.top_pages.length === 0) && (
                  <p className={`text-center py-8 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    No content performance data available yet
                  </p>
                )}
              </div>
            </div>
          </div>
        );

      case "alerts":
        return (
          <div className="space-y-6">
            {/* Alert Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <StatCard
                  title="Active Alerts"
                  value={alerts.filter(a => !a.is_acknowledged).length}
                  icon={AlertTriangle}
                  color="#ef4444"
                  darkMode={darkMode}
                />
                <StatCard
                  title="Total Alerts"
                  value={alerts.length}
                  icon={AlertTriangle}
                  color="#7667C1"
                  darkMode={darkMode}
                />
              </div>
              <button
                onClick={handleRunDetection}
                disabled={refreshing}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
                  darkMode
                    ? "bg-purple-600 hover:bg-purple-700 text-white"
                    : "bg-purple-600 hover:bg-purple-700 text-white"
                }`}
              >
                <Zap size={18} className={refreshing ? "animate-pulse" : ""} />
                Run Detection
              </button>
            </div>

            {/* Alerts List */}
            <div className={`p-6 rounded-2xl border ${
              darkMode ? "bg-[#2D2844] border-gray-700" : "bg-white border-gray-100"
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <AlertTriangle size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}>
                  All Alerts
                </h3>
              </div>
              <div className="space-y-4">
                {alerts.map((alert, idx) => (
                  <AlertCard
                    key={idx}
                    alert={alert}
                    darkMode={darkMode}
                    onAcknowledge={handleAcknowledgeAlert}
                  />
                ))}
                {alerts.length === 0 && (
                  <div className={`text-center py-12 ${darkMode ? "text-gray-500" : "text-gray-400"}`}>
                    <AlertTriangle size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No alerts detected</p>
                    <p className="text-sm mt-1">System is running smoothly</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
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
                  Advanced <span style={{ color: "#A78BFA" }}>Analytics</span>
                </h1>
                <p className="text-white/70 text-sm mt-1">
                  Deep insights beyond basic metrics - user journeys, engagement, and anomaly detection
                </p>
              </div>
              <div className="flex items-center gap-4">
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

          {/* Tabs */}
          <div className="mb-6 overflow-x-auto">
            <div className="flex gap-2 min-w-max">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                    activeTab === tab.id
                      ? darkMode
                        ? "bg-purple-600 text-white"
                        : "bg-purple-600 text-white"
                      : darkMode
                        ? "bg-[#2D2844] text-gray-300 hover:bg-[#3D3854]"
                        : "bg-white text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  <tab.icon size={16} />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
}
