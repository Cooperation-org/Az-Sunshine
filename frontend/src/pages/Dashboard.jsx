// frontend/src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
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
import {
  getCandidates,
  getExpenditures,
  getTopCommittees,
  getTopDonors,
  getMetrics,
} from "../api/api";
import { Link } from "react-router-dom";

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
        const [metricData, committees, donors, exp] = await Promise.all([
          getMetrics(),
          getTopCommittees(),
          getTopDonors(),
          getExpenditures(),
        ]);
        setMetrics(metricData);
        setTopCommittees(committees.results || committees || []);
        setTopDonors(donors.results || donors || []);
        setExpenditures(exp.results || exp || []);
      } catch (err) {
        console.error("Dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center h-screen text-gray-500">
        Loading dashboard...
      </div>
    );

  // === Prepare chart data ===
  const committeesToShow = topCommittees.slice(0, 10);
  const donorsToShow = topDonors.slice(0, 10);

  const committeeData = {
    labels: committeesToShow.map((c) => c.name || "Unknown"),
    datasets: [
      {
        label: "Total IE Spending (USD)",
        data: committeesToShow.map((c) => c.total || 0),
        backgroundColor: "#2563EB",
        borderRadius: 8,
      },
    ],
  };

  const donorData = {
    labels: donorsToShow.map((d) => d.name || "Unknown"),
    datasets: [
      {
        label: "Total Contributions (USD)",
        data: donorsToShow.map((d) => d.total_contribution || 0),
        backgroundColor: "#F97316",
        borderRadius: 8,
      },
    ],
  };

  const totalsByType = expenditures.reduce((acc, e) => {
    const key = e.support_oppose || "Unknown";
    acc[key] = (acc[key] || 0) + Number(e.amount || 0);
    return acc;
  }, {});

  const pieData = {
    labels: Object.keys(totalsByType),
    datasets: [
      {
        data: Object.values(totalsByType),
        backgroundColor: ["#10B981", "#EF4444", "#F59E0B", "#3B82F6"],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* === Navbar === */}
      <nav className="bg-white shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-blue-700">
            Arizona Sunshine Transparency Project
          </h1>
          <Link
            to="/"
            className="text-sm text-blue-600 hover:text-blue-800 transition"
          >
            Home
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        {/* === Metrics Section === */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl shadow p-6 text-center">
            <p className="text-gray-500 text-sm">Total IE Spending</p>
            <p className="text-3xl font-bold text-blue-700 mt-2">
              ${metrics.total_expenditures?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-2xl shadow p-6 text-center">
            <p className="text-gray-500 text-sm">Total Candidates</p>
            <p className="text-3xl font-bold text-blue-700 mt-2">
              {metrics.num_candidates || 0}
            </p>
          </div>
          <div className="bg-white rounded-2xl shadow p-6 text-center">
            <p className="text-gray-500 text-sm">Total Expenditures</p>
            <p className="text-3xl font-bold text-blue-700 mt-2">
              {metrics.num_expenditures || 0}
            </p>
          </div>
        </div>

        {/* === Charts === */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl shadow p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              Top 10 IE Committees by Spending
            </h2>
            <div className="h-[400px]">
              <Bar
                data={committeeData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: {
                      ticks: { color: "#374151" },
                      grid: { display: false },
                    },
                    y: {
                      beginAtZero: true,
                      ticks: { color: "#374151" },
                      grid: { color: "#E5E7EB" },
                    },
                  },
                  plugins: {
                    legend: { display: false },
                    tooltip: { mode: "index", intersect: false },
                  },
                }}
              />
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              Top 10 Donors by Total Contribution
            </h2>
            <div className="h-[400px]">
              <Bar
                data={donorData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: {
                      ticks: { color: "#374151" },
                      grid: { display: false },
                    },
                    y: {
                      beginAtZero: true,
                      ticks: { color: "#374151" },
                      grid: { color: "#E5E7EB" },
                    },
                  },
                  plugins: {
                    legend: { display: false },
                    tooltip: { mode: "index", intersect: false },
                  },
                }}
              />
            </div>
          </div>
        </section>

        {/* === Pie chart for Support/Oppose === */}
        <section className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Support vs Oppose Spending
          </h2>
          <div className="flex justify-center h-[350px]">
            <Pie data={pieData} />
          </div>
        </section>

        {/* === Candidate Links === */}
        <section className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Explore Candidates
          </h2>
          <ul className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {(metrics.candidates || []).slice(0, 12).map((c) => (
              <li
                key={c.id}
                className="p-3 bg-blue-50 rounded-md hover:bg-blue-100 transition"
              >
                <Link to={`/candidate/${c.id}`} className="text-blue-700 font-medium">
                  {c.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="py-6 text-center text-gray-500 text-sm">
        Data provided by the Arizona Sunshine Transparency Project © 2025
      </footer>
    </div>
  );
}
