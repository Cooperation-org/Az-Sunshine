// frontend/src/pages/Visualizations.jsx
import React, { useState, useEffect } from "react";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import MoneyFlowSankey from "../components/MoneyFlowSankey";
import { getOffices, getCycles, getTopCandidatesByIE } from "../api/api";
import { ChartSkeleton, CardSkeleton } from "../components/SkeletonLoader";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Visualizations() {
  const [offices, setOffices] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [selectedOffice, setSelectedOffice] = useState("");
  const [selectedCycle, setSelectedCycle] = useState("");
  const [topCandidates, setTopCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartsLoading, setChartsLoading] = useState(false);

  useEffect(() => {
    loadDropdowns();
  }, []);

  useEffect(() => {
    if (selectedOffice && selectedCycle) {
      loadChartData();
    }
  }, [selectedOffice, selectedCycle]);

  async function loadDropdowns() {
    try {
      const [officesData, cyclesData] = await Promise.all([
        getOffices(),
        getCycles(),
      ]);
      
      setOffices(officesData);
      setCycles(cyclesData);
      
      // Auto-select first office and cycle
      if (officesData.length > 0) setSelectedOffice(officesData[0].office_id);
      if (cyclesData.length > 0) setSelectedCycle(cyclesData[0].cycle_id);
    } catch (error) {
      console.error("Error loading dropdowns:", error);
    } finally {
      setLoading(false);
    }
  }

  async function loadChartData() {
    setChartsLoading(true);
    try {
      const candidatesData = await getTopCandidatesByIE({
        office: selectedOffice,
        cycle: selectedCycle,
        limit: 10,
      });
      
      setTopCandidates(candidatesData.results || candidatesData || []);
    } catch (error) {
      console.error("Error loading chart data:", error);
      setTopCandidates([]);
    } finally {
      setChartsLoading(false);
    }
  }

  // Prepare chart data
  const barChartData = {
    labels: topCandidates.map(c => 
      c.candidate?.full_name || c.name?.full_name || "Unknown"
    ),
    datasets: [
      {
        label: "IE For",
        data: topCandidates.map(c => parseFloat(c.ie_total_for || 0)),
        backgroundColor: "rgba(34, 197, 94, 0.6)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
      },
      {
        label: "IE Against",
        data: topCandidates.map(c => parseFloat(c.ie_total_against || 0)),
        backgroundColor: "rgba(239, 68, 68, 0.6)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      
      <main className="flex-1 lg:ml-0 min-w-0">
        <Header title="Arizona Sunshine" subtitle="IE Spending Visualizations" />

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Filter Section */}
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Select Race</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Office
                </label>
                <select
                  value={selectedOffice}
                  onChange={(e) => setSelectedOffice(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  disabled={loading}
                >
                  <option value="">Select Office</option>
                  {offices.map((office) => (
                    <option key={office.office_id} value={office.office_id}>
                      {office.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Election Cycle
                </label>
                <select
                  value={selectedCycle}
                  onChange={(e) => setSelectedCycle(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  disabled={loading}
                >
                  <option value="">Select Cycle</option>
                  {cycles.map((cycle) => (
                    <option key={cycle.cycle_id} value={cycle.cycle_id}>
                      {cycle.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartSkeleton height="400px" />
              <ChartSkeleton height="400px" />
            </div>
          ) : selectedOffice && selectedCycle ? (
            <>
              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Bar Chart */}
                <div className="bg-white rounded-2xl p-6 shadow-lg">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">
                    Top 10 Candidates by IE Spending
                  </h3>
                  {chartsLoading ? (
                    <ChartSkeleton height="300px" />
                  ) : topCandidates.length > 0 ? (
                    <div className="h-[300px]">
                      <Bar
                        data={barChartData}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { display: true, position: "top" },
                            tooltip: {
                              callbacks: {
                                label: (context) =>
                                  `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`,
                              },
                            },
                          },
                          scales: {
                            y: {
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
                    <div className="flex items-center justify-center h-64 text-gray-500">
                      No data available
                    </div>
                  )}
                </div>

                {/* Money Flow Sankey */}
                {chartsLoading ? (
                  <ChartSkeleton height="400px" />
                ) : (
                  <MoneyFlowSankey
                    officeId={selectedOffice}
                    cycleId={selectedCycle}
                    limit={20}
                  />
                )}
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
                  <p className="text-sm text-purple-700 font-medium mb-1">
                    Total IE Spending
                  </p>
                  <p className="text-3xl font-bold text-purple-900">
                    $
                    {topCandidates
                      .reduce(
                        (sum, c) =>
                          sum +
                          parseFloat(c.ie_total_for || 0) +
                          parseFloat(c.ie_total_against || 0),
                        0
                      )
                      .toLocaleString()}
                  </p>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
                  <p className="text-sm text-green-700 font-medium mb-1">
                    Support
                  </p>
                  <p className="text-3xl font-bold text-green-900">
                    $
                    {topCandidates
                      .reduce((sum, c) => sum + parseFloat(c.ie_total_for || 0), 0)
                      .toLocaleString()}
                  </p>
                </div>
                
                <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-6 border border-red-200">
                  <p className="text-sm text-red-700 font-medium mb-1">
                    Oppose
                  </p>
                  <p className="text-3xl font-bold text-red-900">
                    $
                    {topCandidates
                      .reduce(
                        (sum, c) => sum + parseFloat(c.ie_total_against || 0),
                        0
                      )
                      .toLocaleString()}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Select an office and cycle to view visualizations
            </div>
          )}
        </div>
      </main>
    </div>
  );
}