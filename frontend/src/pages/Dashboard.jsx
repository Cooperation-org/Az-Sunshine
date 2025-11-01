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
  getMetrics,
} from "../api/api";
import { Link } from "react-router-dom";
import { Bell, Search } from "lucide-react";
import Sidebar from "../components/Sidebar";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export default function Dashboard() {
  const [metrics, setMetrics] = useState({});
  const [topCommittees, setTopCommittees] = useState([]);
  const [topDonors, setTopDonors] = useState([]);
  const [expenditures, setExpenditures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        console.log("🔄 Loading dashboard data from backend...");
        const [metricData, committees, donors, exp] = await Promise.all([
          getMetrics(),
          getTopCommittees(),
          getTopDonors(),
          getExpenditures(),
        ]);
        console.log("✅ Metrics:", metricData);
        console.log("✅ Top Committees:", committees);
        console.log("✅ Top Donors:", donors);
        console.log("✅ Expenditures:", exp);
        
        setMetrics(metricData || {});
        setTopCommittees(committees.results || committees || []);
        setTopDonors(donors.results || donors || []);
        setExpenditures(exp.results || exp || []);
      } catch (err) {
        console.error("❌ Dashboard load error:", err);
        console.error("Error details:", err.response?.data || err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 text-gray-500">
        Loading dashboard...
      </div>
    );

  // === Prepare chart data ===
  const committeesToShow = topCommittees.slice(0, 10);
  const donorsToShow = topDonors.slice(0, 10);

  const donorData = {
    labels: donorsToShow.map((d) => d.name || "Unknown"),
    datasets: [
      {
        label: "Total Contributions (USD)",
        data: donorsToShow.map((d) => d.total_contribution || 0),
        backgroundColor: "rgba(255, 255, 255, 0.3)",
        borderColor: "rgba(255, 255, 255, 0.5)",
        borderWidth: 1,
        borderRadius: 6,
        barThickness: 30,
      },
    ],
  };

  // Calculate support vs oppose
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
        backgroundColor: ["#5B4A7D", "#E5E7EB"],
        borderWidth: 0,
        borderRadius: 4,
      },
    ],
  };

  // Latest expenditures for table
  const latestExpenditures = expenditures.slice(0, 4);

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
            <p className="text-sm text-gray-500">Dashboard</p>
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

        {/* === Dashboard Content === */}
        <div className="p-8">
          <div className="grid grid-cols-3 gap-6 mb-6">
            {/* === Top 10 Donors Chart (2 cols) === */}
            <div className="col-span-2 bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] rounded-3xl p-8 shadow-lg">
              <h2 className="text-white text-xl font-bold mb-1">Top 10 Donors</h2>
              <p className="text-white/70 text-sm mb-6">Total Contribution</p>
              <div className="h-[240px] bg-white/5 rounded-xl p-4">
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
                      x: {
                        display: false,
                        grid: { display: false }
                      },
                      y: {
                        display: false,
                        grid: { display: false }
                      }
                    }
                  }} 
                />
              </div>
            </div>

            {/* === Support vs Oppose Chart === */}
            <div className="bg-white rounded-3xl p-8 shadow-lg">
              <h2 className="text-gray-900 text-xl font-bold mb-1">Support vs Oppose</h2>
              <p className="text-gray-500 text-sm mb-6">Spending</p>
              <div className="flex justify-center items-center h-[240px]">
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
              </div>
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
            </div>
          </div>

          {/* === Metric Cards === */}
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="bg-white  rounded-2xl p-6 shadow-lg text-black relative overflow-hidden ">
              <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-bl-full"></div>
              <p className="text-black/90 text-sm mb-1">Total IE Spending</p>
              <p className="text-3xl font-bold">$ {Number(metrics.total_expenditures || 0).toLocaleString()}</p>
              <button className="absolute top-6 right-6 text-white/80 hover:text-white">
                <span className="text-xl">•••</span>
              </button>
            </div>
            
            <div className="bg-white  rounded-2xl p-6 shadow-lg text-black relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-bl-full"></div>
              <p className="text-black/90 text-sm mb-1">Total Candidates</p>
              <p className="text-3xl font-bold">{Number(metrics.num_candidates || 0).toLocaleString()}</p>
              <button className="absolute top-6 right-6 text-white/80 hover:text-white">
                <span className="text-xl">•••</span>
              </button>
            </div>
            
            <div className="bg-white  rounded-2xl p-6 shadow-lg text-black relative overflow-hidden">
              <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-bl-full"></div>
                <p className="text-black/90 text-sm mb-1">Total Expenditures Count</p>
              <p className="text-3xl font-bold">{Number(metrics.num_expenditures || 0).toLocaleString()}</p>
              <button className="absolute top-6 right-6 text-white/80 hover:text-white">
                <span className="text-xl">•••</span>
              </button>
            </div>
          </div>

          {/* === Latest Expenditures Table & Top Committees === */}
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
                  {latestExpenditures.map((exp, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-4 px-2 text-sm text-gray-700">
                        {exp.date ? new Date(exp.date).toLocaleDateString() : "N/A"}
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
                  ))}
                </tbody>
              </table>
              <Link to="/" className="inline-block mt-4 text-purple-600 hover:text-purple-700 text-sm font-medium">
                View All Independent Expenditure →
              </Link>
            </div>

            {/* === Top 10 IE Committees === */}
            <div className="bg-white rounded-2xl p-6 shadow-lg">
              <h2 className="text-gray-900 text-lg font-semibold mb-4">Top 10 IE Committees by Spending</h2>
              <div className="space-y-3">
                {committeesToShow.map((committee, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white  flex items-center justify-center text-white font-semibold flex-shrink-0">
                      {committee.name?.charAt(0) || "?"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{committee.name || "Unknown"}</p>
                      <p className="text-xs text-gray-500">$ {Number(committee.total || 0).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
