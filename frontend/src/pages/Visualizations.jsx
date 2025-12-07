// frontend/src/pages/Visualizations.jsx
import React, { useState, useEffect } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import MoneyFlowSankey from "../components/MoneyFlowSankey";
import { getOffices, getCycles, getTopCandidatesByIE } from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import {
  SlidersHorizontal,
  BarChart3,
  GitMerge,
  DollarSign,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  Activity,
  Box,
  LayoutGrid
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ChartSkeleton = ({ className }) => {
  const { darkMode } = useDarkMode();
  return (
    <div className={`rounded-2xl ${darkMode ? 'bg-[#4a3f66]/50' : 'bg-gray-200'} animate-pulse ${className}`}></div>
  );
};


export default function Visualizations() {
  const { darkMode } = useDarkMode();
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

      // Ensure we have arrays (handle both direct arrays and {results: []} format)
      const offices = Array.isArray(officesData) ? officesData : (officesData?.results || []);
      const cycles = Array.isArray(cyclesData) ? cyclesData : (cyclesData?.results || []);

      setOffices(offices);
      setCycles(cycles);

      // Default to Governor (2000) and 2014 cycle (27) which has IE data
      const defaultOffice = offices.find(o => o.office_id === 2000) || offices[0];
      const defaultCycle = cycles.find(c => c.cycle_id === 27) || cycles[0];

      if (defaultOffice) setSelectedOffice(defaultOffice.office_id);
      if (defaultCycle) setSelectedCycle(defaultCycle.cycle_id);
    } catch (error) {
      console.error("Error loading dropdowns:", error);
      setOffices([]);
      setCycles([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadChartData() {
    setChartsLoading(true);
    try {
      const candidatesData = await getTopCandidatesByIE({
        office_id: selectedOffice,
        cycle_id: selectedCycle,
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

  // Calculate totals from API data (total_ie is negative, is_for_benefit indicates support/oppose)
  const totalIE = topCandidates.reduce((sum, c) => sum + Math.abs(parseFloat(c.total_ie || 0)), 0);
  const totalSupport = topCandidates.reduce((sum, c) => c.is_for_benefit === true ? sum + Math.abs(parseFloat(c.total_ie || 0)) : sum, 0);
  const totalOppose = topCandidates.reduce((sum, c) => c.is_for_benefit === false ? sum + Math.abs(parseFloat(c.total_ie || 0)) : sum, 0);

  // Group by candidate name and aggregate support/oppose
  const candidateMap = new Map();
  topCandidates.forEach(c => {
    const name = `${c.subject_committee__name__first_name || ''} ${c.subject_committee__name__last_name || ''}`.trim() || 'Unknown';
    if (!candidateMap.has(name)) {
      candidateMap.set(name, { support: 0, oppose: 0 });
    }
    const amounts = candidateMap.get(name);
    if (c.is_for_benefit === true) {
      amounts.support += Math.abs(parseFloat(c.total_ie || 0));
    } else if (c.is_for_benefit === false) {
      amounts.oppose += Math.abs(parseFloat(c.total_ie || 0));
    }
  });

  const uniqueCandidates = Array.from(candidateMap.keys());
  const barChartData = {
    labels: uniqueCandidates,
    datasets: [
      {
        label: "Support",
        data: uniqueCandidates.map(name => candidateMap.get(name).support),
        backgroundColor: darkMode ? 'rgba(74, 222, 128, 0.4)' : 'rgba(34, 197, 94, 0.6)',
        borderColor: darkMode ? 'rgba(74, 222, 128, 1)' : 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: "Oppose",
        data: uniqueCandidates.map(name => candidateMap.get(name).oppose),
        backgroundColor: darkMode ? 'rgba(248, 113, 113, 0.4)' : 'rgba(239, 68, 68, 0.6)',
        borderColor: darkMode ? 'rgba(248, 113, 113, 1)' : 'rgba(239, 68, 68, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        display: true, 
        position: 'bottom',
        labels: {
          color: darkMode ? '#d1d5db' : '#374151',
          padding: 20,
          font: {
            size: 13,
            family: 'Inter, sans-serif'
          }
        }
      },
      tooltip: {
        backgroundColor: darkMode ? 'rgba(51, 45, 84, 0.98)' : 'rgba(255, 255, 255, 0.98)',
        titleColor: darkMode ? '#ffffff' : '#1F2937',
        bodyColor: darkMode ? '#d1d5db' : '#374151',
        borderColor: darkMode ? '#4c3e7c' : '#E5E7EB',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: (context) => `${context.dataset.label}: $${context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: darkMode ? '#4a3f66' : '#e5e7eb',
          drawBorder: false,
        },
        ticks: {
          color: darkMode ? '#b8b3cc' : '#6b7280',
          callback: (value) => `$${(value/1000)}k`,
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: darkMode ? '#b8b3cc' : '#6b7280',
        },
      },
    },
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#2a2347]' : 'bg-gray-100'}`}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Header />
        <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          
          <div>
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Visualizations</h1>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Explore campaign finance data through interactive charts</p>
          </div>

          {/* Filter Card */}
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'} rounded-2xl p-6 border shadow-sm`}>
            <div className="flex items-center gap-3 mb-5">
              <SlidersHorizontal className={`w-5 h-5 ${darkMode ? 'text-purple-300' : 'text-[#7163BA]'}`} />
              <h2 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Filter Visualizations</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
              {loading ? (
                <>
                  <div className={`w-full h-12 rounded-lg ${darkMode ? 'bg-[#4a3f66]/50' : 'bg-gray-200'} animate-pulse`}></div>
                  <div className={`w-full h-12 rounded-lg ${darkMode ? 'bg-[#4a3f66]/50' : 'bg-gray-200'} animate-pulse`}></div>
                </>
              ) : (
                <>
                  <div className="relative">
                    <label className={`absolute -top-2 left-3 px-1 text-xs font-medium ${darkMode ? 'bg-[#3d3559] text-gray-400' : 'bg-white text-gray-500'}`}>Office</label>
                    <select
                      value={selectedOffice}
                      onChange={(e) => setSelectedOffice(e.target.value)}
                      className={`w-full appearance-none px-4 py-3 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}
                      disabled={loading}
                    >
                      {offices.map((office) => (
                        <option key={office.office_id} value={office.office_id} className={darkMode ? 'bg-[#3d3559]' : 'bg-white'}>
                          {office.name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className={`w-5 h-5 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  </div>
                  <div className="relative">
                    <label className={`absolute -top-2 left-3 px-1 text-xs font-medium ${darkMode ? 'bg-[#3d3559] text-gray-400' : 'bg-white text-gray-500'}`}>Cycle</label>
                    <select
                      value={selectedCycle}
                      onChange={(e) => setSelectedCycle(e.target.value)}
                      className={`w-full appearance-none px-4 py-3 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}
                      disabled={loading}
                    >
                      {cycles.map((cycle) => (
                        <option key={cycle.cycle_id} value={cycle.cycle_id} className={darkMode ? 'bg-[#3d3559]' : 'bg-white'}>
                          {cycle.name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className={`w-5 h-5 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  </div>
                </>
              )}
            </div>
          </div>

          {(loading || (selectedOffice && selectedCycle)) ? (
            <div className="space-y-8">
              {/* Stat Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  { title: "Total IE Spending", value: totalIE, icon: DollarSign, color: darkMode ? '#c084fc' : '#800080' },
                  { title: "Total Support", value: totalSupport, icon: TrendingUp, color: darkMode ? '#4ade80' : '#16a34a' },
                  { title: "Total Oppose", value: totalOppose, icon: TrendingDown, color: darkMode ? '#f87171' : '#ef4444' }
                ].map((stat, idx) => (
                  <div key={idx} className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 border shadow-sm`}>
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-xl" style={{ backgroundColor: `${stat.color}20`}}>
                        <stat.icon className="w-6 h-6" style={{ color: stat.color }} />
                      </div>
                      <div>
                        <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{stat.title}</p>
                        {chartsLoading ? <div className={`h-8 w-32 mt-1 rounded-md ${darkMode ? 'bg-[#4a3f66]/50' : 'bg-gray-200'} animate-pulse`}></div> :
                          <h3 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>${stat.value.toLocaleString('en-US', { minimumFractionDigits: 0 })}</h3>
                        }
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Charts Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
                {/* Bar Chart */}
                <div className={`xl:col-span-3 ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 sm:p-8 border shadow-sm`}>
                  <div className="flex items-center gap-3 mb-6">
                    <BarChart3 className={`w-5 h-5 ${darkMode ? 'text-purple-300' : 'text-[#7163BA]'}`} />
                    <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Top 10 Candidates by IE</h3>
                  </div>
                  {chartsLoading ? <ChartSkeleton className="h-[400px]" /> :
                    topCandidates.length > 0 ? (
                      <div className="h-[400px]">
                        <Bar data={barChartData} options={chartOptions} />
                      </div>
                    ) : (
                      <div className={`h-[400px] flex items-center justify-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>No data available for this selection.</div>
                    )
                  }
                </div>

                {/* Money Flow Sankey */}
                <div className={`xl:col-span-2 ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-6 sm:p-8 border shadow-sm`}>
                  <div className="mb-6">
                    <div className="flex items-center gap-3 mb-1">
                      <GitMerge className={`w-5 h-5 ${darkMode ? 'text-purple-300' : 'text-[#7163BA]'}`} />
                      <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>Top Donors Money Flow</h3>
                    </div>
                    <p className={`text-xs ml-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Track how money flows from top donors through IE committees to candidates (each color represents a different donor)
                    </p>
                  </div>
                  {chartsLoading ? <ChartSkeleton className="h-[400px]" /> :
                    <MoneyFlowSankey
                      officeId={selectedOffice}
                      cycleId={selectedCycle}
                      limit={12}
                      height="400px"
                    />
                  }
                </div>
              </div>
            </div>
          ) : (
            <div className={`text-center py-20 rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>
              <LayoutGrid className={`w-12 h-12 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
              <h3 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>Select an Office and Cycle</h3>
              <p className={`${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Your visualizations will appear here.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}