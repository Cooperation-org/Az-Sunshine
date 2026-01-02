import React, { useState, useEffect } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, Filler,
} from "chart.js";
import Sidebar from "../components/Sidebar";
import MoneyFlowSankey from "../components/MoneyFlowSankey";
import { getOffices, getCycles, getTopCandidatesByIE } from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import {
  BarChart3, GitMerge, DollarSign, TrendingUp, TrendingDown, ChevronDown, SlidersHorizontal
} from "lucide-react";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, Filler);

// --- REFINED BANNER WITH INTEGRATED FILTERS ---
const Banner = ({ offices, cycles, selectedOffice, setSelectedOffice, selectedCycle, setSelectedCycle, loading }) => {
  const { darkMode } = useDarkMode();

  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Data <span style={{ color: '#A78BFA' }}>Visualizations</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Analyze Independent Expenditure flows and candidate support through interactive datasets.
            </p>
          </div>
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/5"
            style={{ background: 'rgba(255, 255, 255, 0.1)' }}
          >
            <SlidersHorizontal size={14} className="text-purple-300" />
            <span className="text-xs font-bold uppercase tracking-wider text-gray-200">Live Filters</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
          <div className="relative">
            <select
              value={selectedOffice}
              onChange={(e) => setSelectedOffice(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              {offices.map((o) => (
                <option key={o.office_id} value={o.office_id} className="bg-[#2D2844]">{o.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          <div className="relative">
            <select
              value={selectedCycle}
              onChange={(e) => setSelectedCycle(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              {cycles.map((c) => (
                <option key={c.cycle_id} value={c.cycle_id} className="bg-[#2D2844]">{c.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>
        </div>
      </div>
    </div>
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

  useEffect(() => { loadDropdowns(); }, []);
  useEffect(() => { if (selectedOffice && selectedCycle) loadChartData(); }, [selectedOffice, selectedCycle]);

  async function loadDropdowns() {
    try {
      const [oData, cData] = await Promise.all([getOffices(), getCycles()]);
      const oList = Array.isArray(oData) ? oData : (oData?.results || []);
      const cList = Array.isArray(cData) ? cData : (cData?.results || []);
      setOffices(oList); setCycles(cList);
      setSelectedOffice(oList.find(o => o.office_id === 2000)?.office_id || oList[0]?.office_id);
      setSelectedCycle(cList.find(c => c.cycle_id === 27)?.cycle_id || cList[0]?.cycle_id);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function loadChartData() {
    setChartsLoading(true);
    try {
      const data = await getTopCandidatesByIE({ office_id: selectedOffice, cycle_id: selectedCycle, limit: 10 });
      setTopCandidates(data.results || data || []);
    } catch (e) { console.error(e); } finally { setChartsLoading(false); }
  }

  const totalIE = topCandidates.reduce((sum, c) => sum + Math.abs(parseFloat(c.total_ie || 0)), 0);
  const totalSupport = topCandidates.reduce((sum, c) => c.is_for_benefit ? sum + Math.abs(parseFloat(c.total_ie || 0)) : sum, 0);
  const totalOppose = totalIE - totalSupport;

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} p-5 rounded-2xl border shadow-sm flex items-center gap-4`}>
      <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color: color }} />
      </div>
      <div>
        <p className={`text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{title}</p>
        <p className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </p>
      </div>
    </div>
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner 
            offices={offices} cycles={cycles} 
            selectedOffice={selectedOffice} setSelectedOffice={setSelectedOffice}
            selectedCycle={selectedCycle} setSelectedCycle={setSelectedCycle}
            loading={loading}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <StatCard title="Total IE Spending" value={totalIE} icon={DollarSign} color="#7667C1" />
            <StatCard title="Total Support" value={totalSupport} icon={TrendingUp} color="#22c55e" />
            <StatCard title="Total Oppose" value={totalOppose} icon={TrendingDown} color="#ef4444" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Chart Container 1 */}
            <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
              <div className="flex items-center gap-3 mb-6">
                <BarChart3 size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Independent Expenditure Breakdown</h3>
              </div>
              <div className="h-[400px]">
                {/* Your Bar Component logic remains same */}
                <Bar 
                   data={{
                    labels: topCandidates.map(c => c.subject_committee__name__last_name || 'Unknown'),
                    datasets: [{ label: 'Expenditure', data: topCandidates.map(c => Math.abs(c.total_ie)), backgroundColor: '#7667C1' }]
                   }} 
                   options={{ maintainAspectRatio: false }}
                />
              </div>
            </div>

            {/* Chart Container 2 */}
            <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
              <div className="flex items-center gap-3 mb-6">
                <GitMerge size={18} className="text-[#7667C1]" />
                <h3 className={`text-sm font-bold uppercase tracking-widest ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Top Donors Money Flow</h3>
              </div>
              <div className="h-[400px]">
                <MoneyFlowSankey officeId={selectedOffice} cycleId={selectedCycle} limit={12} height="100%" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}