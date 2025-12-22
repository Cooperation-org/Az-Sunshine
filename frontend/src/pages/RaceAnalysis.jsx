import React, { useEffect, useState } from "react";
import { getOffices, getCycles, getRaceIESpending, getRaceTopDonors, getAdBuys } from "../api/api";
import Sidebar from "../components/Sidebar";
import { Bar } from "react-chartjs-2";
import { ChartSkeleton, TableSkeleton } from "../components/SkeletonLoader";
import { useDarkMode } from "../context/DarkModeContext";
import {
  ChevronDown, SlidersHorizontal, BarChart3, Users,
  TrendingUp, TrendingDown, DollarSign, Target
} from "lucide-react";
import ViewToggle from "../components/ViewToggle";
import CandidateCard from "../components/race/CandidateCard";
import RaceSummaryPanel from "../components/race/RaceSummaryPanel";
import AdBuyCard from "../components/race/AdBuyCard";

// --- REFINED BANNER WITH INTEGRATED FILTERS ---
const Banner = ({ offices, cycles, selectedOffice, setSelectedOffice, selectedCycle, setSelectedCycle, view, setView }) => {
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
              Race <span style={{ color: '#A78BFA' }}>Analysis</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Deep dive into specific electoral races to compare candidate support and donor influence.
            </p>
          </div>
          <ViewToggle view={view} onViewChange={setView} />
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
              <option value="" className="bg-[#2D2844]">Select Office</option>
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
              <option value="" className="bg-[#2D2844]">Select Cycle</option>
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

export default function RaceAnalysis() {
  const { darkMode } = useDarkMode();
  const [offices, setOffices] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [selectedOffice, setSelectedOffice] = useState("");
  const [selectedCycle, setSelectedCycle] = useState("");
  const [raceData, setRaceData] = useState(null);
  const [topDonors, setTopDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('candidate');
  const [adBuys, setAdBuys] = useState([]);

  useEffect(() => {
    async function loadDropdowns() {
      try {
        const [oData, cData] = await Promise.all([getOffices(), getCycles()]);
        setOffices(oData);
        setCycles(cData);
        if (cData.length > 0) setSelectedCycle(cData[0].cycle_id);
      } catch (e) { console.error(e); } finally { setLoading(false); }
    }
    loadDropdowns();
  }, []);

  useEffect(() => {
    if (selectedOffice && selectedCycle) {
      loadRaceData();
      if (view === 'race') {
        loadAdBuys();
      }
    }
  }, [selectedOffice, selectedCycle, view]);

  async function loadRaceData() {
    setLoading(true);
    try {
      const [spending, donors] = await Promise.all([
        getRaceIESpending({ office_id: selectedOffice, cycle_id: selectedCycle }),
        getRaceTopDonors({ office_id: selectedOffice, cycle_id: selectedCycle })
      ]);
      setRaceData(spending);
      setTopDonors(donors.top_donors || []);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function loadAdBuys() {
    try {
      const data = await getAdBuys({
        office_id: selectedOffice,
        cycle_id: selectedCycle
      });
      setAdBuys(data.results || []);
    } catch (e) {
      console.error(e);
    }
  }

  // Statistics Calculation
  const totalSpending = raceData?.candidates?.reduce((sum, c) => sum + Math.abs(parseFloat(c.total_ie || 0)), 0) || 0;
  const topCandidate = raceData?.candidates?.sort((a, b) => b.total_ie - a.total_ie)[0];

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} p-5 rounded-2xl border shadow-sm flex items-center gap-4`}>
      <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color: color }} />
      </div>
      <div>
        <p className={`text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{title}</p>
        <p className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{value}</p>
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
            view={view} setView={setView}
          />

          {loading ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div className="h-24 bg-gray-200 animate-pulse rounded-2xl"></div></div>
              <ChartSkeleton height="400px" />
            </div>
          ) : raceData ? (
            view === 'race' ? (
              // ============ RACE VIEW ============
              <div className="space-y-8">
                {/* Candidate Cards - Horizontal Scroll */}
                <div>
                  <h3 className={`text-sm font-bold uppercase tracking-widest mb-4 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Candidates in This Race
                  </h3>
                  <div className="overflow-x-auto -mx-4 px-4">
                    <div className="flex gap-4 pb-4" style={{ scrollSnapType: 'x mandatory' }}>
                      {raceData.candidates.map((candidate, idx) => (
                        <div key={idx} style={{ scrollSnapAlign: 'start' }}>
                          <CandidateCard candidate={candidate} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Race Summary + Ad Buys Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <RaceSummaryPanel raceData={raceData} topDonors={topDonors} />

                  <div className="lg:col-span-2">
                    <h3 className={`text-sm font-bold uppercase tracking-widest mb-4 ${
                      darkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Ad Buys Timeline
                    </h3>
                    {adBuys.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {adBuys.map((ad, idx) => (
                          <AdBuyCard key={idx} adBuy={ad} />
                        ))}
                      </div>
                    ) : (
                      <div className={`text-center py-12 rounded-2xl border ${
                        darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
                      }`}>
                        <p className="text-gray-500">No ad buys reported for this race yet</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              // ============ CANDIDATE VIEW (original) ============
              <div className="space-y-8">
              {/* Stat Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard title="Total Race IE" value={`$${totalSpending.toLocaleString()}`} icon={DollarSign} color="#7667C1" />
                <StatCard title="Top Recipient" value={topCandidate ? topCandidate.subject_committee__name__last_name : "N/A"} icon={TrendingUp} color="#22c55e" />
                <StatCard title="Total Donors" value={topDonors.length} icon={Users} color="#3b82f6" />
              </div>

              {/* Chart & Donors Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className={`lg:col-span-2 p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
                  <div className="flex items-center gap-3 mb-6">
                    <BarChart3 size={18} className="text-[#7667C1]" />
                    <h3 className={`text-sm font-bold uppercase tracking-widest ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Spending by Candidate</h3>
                  </div>
                  <div className="h-[350px]">
                    <Bar 
                      data={{
                        labels: raceData.candidates.map(c => c.subject_committee__name__last_name),
                        datasets: [{ 
                          label: 'IE Spending', 
                          data: raceData.candidates.map(c => Math.abs(c.total_ie)),
                          backgroundColor: '#7667C1',
                          borderRadius: 8
                        }]
                      }} 
                      options={{ maintainAspectRatio: false }}
                    />
                  </div>
                </div>

                <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
                   <h3 className={`text-sm font-bold uppercase tracking-widest mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Top Race Donors</h3>
                   <div className="space-y-4">
                      {topDonors.slice(0, 6).map((donor, idx) => (
                        <div key={idx} className="flex justify-between items-center group">
                          <div className="min-w-0">
                            <p className={`text-sm font-semibold truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>{donor.entity__first_name} {donor.entity__last_name}</p>
                            <p className="text-xs text-gray-500">{donor.entity__occupation || "Individual"}</p>
                          </div>
                          <span className="text-sm font-mono font-bold text-[#7667C1]">${parseFloat(donor.total_contributed).toLocaleString()}</span>
                        </div>
                      ))}
                   </div>
                </div>
              </div>

              {/* Table Section */}
              <div className={`rounded-2xl border overflow-hidden ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
                <table className="w-full text-left border-collapse">
                  <thead className={darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}>
                    <tr>
                      {["Candidate", "Party", "Total IE", "Net IE"].map((h) => (
                        <th key={h} className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-gray-500">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-100'}`}>
                    {raceData.candidates.map((c, i) => (
                      <tr key={i} className="hover:bg-purple-50/5 transition-colors">
                        <td className={`px-6 py-4 text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          {c.subject_committee__name__first_name} {c.subject_committee__name__last_name}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">{c.subject_committee__candidate_party__name || "N/A"}</td>
                        <td className={`px-6 py-4 text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>${Math.abs(c.total_ie).toLocaleString()}</td>
                        <td className="px-6 py-4">
                          <span className={`text-sm font-bold ${c.is_for_benefit ? 'text-green-500' : 'text-red-500'}`}>
                            {c.is_for_benefit ? '+' : '-'}${Math.abs(c.total_ie).toLocaleString()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            )
          ) : (
            <div className={`text-center py-20 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              <Users size={48} className="mx-auto mb-4 opacity-20" />
              <p>Select an office and cycle to begin analysis</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}