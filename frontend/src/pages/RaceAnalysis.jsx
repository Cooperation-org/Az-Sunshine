import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getOffices, getCycles, getRaceIESpending, getRaceTopDonors, getAdBuys } from "../api/api";
import Sidebar from "../components/Sidebar";
import { Bar } from "react-chartjs-2";
import { ChartSkeleton, TableSkeleton } from "../components/SkeletonLoader";
import { useDarkMode } from "../context/DarkModeContext";
import {
  ChevronDown, SlidersHorizontal, BarChart3, Users,
  TrendingUp, TrendingDown, DollarSign, Target, Calendar, ToggleLeft, ToggleRight
} from "lucide-react";
import ViewToggle from "../components/ViewToggle";
import CandidateCard from "../components/race/CandidateCard";
import RaceSummaryPanel from "../components/race/RaceSummaryPanel";
import AdBuyCard from "../components/race/AdBuyCard";
import IEAdBuyCorrelation from "../components/race/IEAdBuyCorrelation";
import { getPartyInfo } from "../utils/partyUtils";

// Arizona Primary Election Dates (day before primary to capture all pre-primary spending)
const AZ_PRIMARY_DATES = {
  '2028': '2028-08-01', // Estimated - typically first Tuesday in August
  '2026': '2026-08-04', // Estimated
  '2024': '2024-07-30', // Primary was Aug 6, 2024
  '2022': '2022-08-02', // Primary was Aug 2, 2022
  '2020': '2020-08-04', // Primary was Aug 4, 2020
  '2018': '2018-08-28', // Primary was Aug 28, 2018
  '2016': '2016-08-30', // Primary was Aug 30, 2016
  '2014': '2014-08-26', // Primary was Aug 26, 2014
  '2012': '2012-08-28', // Primary was Aug 28, 2012
};

// Get primary cutoff date for a cycle
const getPrimaryCutoffDate = (cycleName) => {
  return AZ_PRIMARY_DATES[cycleName] || null;
};

// Extract district numbers from offices for filtering
const extractDistricts = (offices) => {
  const districtSet = new Set();
  offices.forEach(o => {
    const match = o.name.match(/District\s*(?:No\.\s*)?(\d+)/i);
    if (match) {
      districtSet.add(parseInt(match[1]));
    }
  });
  return Array.from(districtSet).sort((a, b) => a - b);
};

// Filter offices by district
const filterOfficesByDistrict = (offices, district) => {
  if (!district) return offices;
  return offices.filter(o => {
    const match = o.name.match(/District\s*(?:No\.\s*)?(\d+)/i);
    return match && parseInt(match[1]) === parseInt(district);
  });
};

// --- REFINED BANNER WITH INTEGRATED FILTERS ---
const Banner = ({
  offices,
  cycles,
  selectedOffice,
  setSelectedOffice,
  selectedCycle,
  setSelectedCycle,
  view,
  setView,
  selectedDistrict,
  setSelectedDistrict,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  primaryOnly,
  setPrimaryOnly,
  selectedCycleName
}) => {
  const { darkMode } = useDarkMode();
  const districts = extractDistricts(offices);
  const filteredOffices = filterOfficesByDistrict(offices, selectedDistrict);
  const primaryDate = getPrimaryCutoffDate(selectedCycleName);

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

        {/* Primary Filters Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-4xl mb-4">
          {/* District Filter */}
          <div className="relative">
            <select
              value={selectedDistrict}
              onChange={(e) => {
                setSelectedDistrict(e.target.value);
                setSelectedOffice(""); // Reset office when district changes
              }}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              <option value="" className="bg-[#2D2844]">All Districts</option>
              {districts.map((d) => (
                <option key={d} value={d} className="bg-[#2D2844]">District {d}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          {/* Office Filter */}
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
              {filteredOffices.map((o) => (
                <option key={o.office_id} value={o.office_id} className="bg-[#2D2844]">{o.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          {/* Cycle Filter */}
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

        {/* Date Range Filters Row */}
        <div className="flex flex-col sm:flex-row gap-4 max-w-3xl">
          {/* Primary Only Toggle */}
          <button
            onClick={() => setPrimaryOnly(!primaryOnly)}
            disabled={!primaryDate}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-medium transition-all ${
              primaryOnly
                ? 'bg-purple-600 text-white'
                : darkMode
                  ? 'bg-[#1F1B31] text-white/70 hover:text-white'
                  : 'bg-white/15 text-white/70 hover:text-white'
            } ${!primaryDate ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={primaryDate ? `Filter to before ${primaryDate}` : 'Primary date not available for this cycle'}
          >
            {primaryOnly ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
            <span>Primary Only</span>
          </button>

          <div className="flex gap-4 flex-1">
            <div className="relative flex-1">
              <Calendar size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                placeholder="From Date"
                disabled={primaryOnly}
                className={`w-full appearance-none pl-10 pr-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all [color-scheme:dark] ${primaryOnly ? 'opacity-50' : ''}`}
                style={darkMode
                  ? { background: '#1F1B31' }
                  : { background: 'rgba(255, 255, 255, 0.15)' }
                }
              />
            </div>
            <div className="relative flex-1">
              <Calendar size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                placeholder="To Date"
                disabled={primaryOnly}
                className={`w-full appearance-none pl-10 pr-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all [color-scheme:dark] ${primaryOnly ? 'opacity-50' : ''}`}
                style={darkMode
                  ? { background: '#1F1B31' }
                  : { background: 'rgba(255, 255, 255, 0.15)' }
                }
              />
            </div>
          </div>
        </div>

        {/* Primary Only indicator */}
        {primaryOnly && primaryDate && (
          <div className="mt-3 text-xs text-purple-300">
            Showing spending before primary election ({primaryDate})
          </div>
        )}
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
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [primaryOnly, setPrimaryOnly] = useState(false);
  const [raceData, setRaceData] = useState(null);
  const [topDonors, setTopDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('candidate');
  const [adBuys, setAdBuys] = useState([]);

  // Get cycle name for primary date lookup
  const selectedCycleName = cycles.find(c => String(c.cycle_id) === String(selectedCycle))?.name || '';
  const primaryCutoffDate = getPrimaryCutoffDate(selectedCycleName);

  // Compute effective date filters (primaryOnly overrides manual dates)
  const effectiveDateTo = primaryOnly && primaryCutoffDate ? primaryCutoffDate : dateTo;

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

  // Reset primaryOnly when cycle changes (if new cycle doesn't have primary date)
  useEffect(() => {
    if (primaryOnly && !primaryCutoffDate) {
      setPrimaryOnly(false);
    }
  }, [selectedCycle, primaryCutoffDate]);

  useEffect(() => {
    if (selectedOffice && selectedCycle) {
      loadRaceData();
      if (view === 'race') {
        loadAdBuys();
      }
    }
  }, [selectedOffice, selectedCycle, view, dateFrom, effectiveDateTo, primaryOnly]);

  async function loadRaceData() {
    setLoading(true);
    try {
      const params = { office_id: selectedOffice, cycle_id: selectedCycle };
      if (dateFrom) params.date_from = dateFrom;
      if (effectiveDateTo) params.date_to = effectiveDateTo;

      // Fetch race spending first (fast) - don't block on slow top-donors query
      const spending = await getRaceIESpending(params);
      setRaceData(spending);
      setLoading(false);

      // Then fetch top donors separately (can be slow) with timeout
      try {
        const donorsPromise = getRaceTopDonors(params);
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Top donors request timed out')), 10000)
        );
        const donors = await Promise.race([donorsPromise, timeoutPromise]);
        setTopDonors(donors.top_donors || []);
      } catch (donorError) {
        console.warn('Top donors fetch failed or timed out:', donorError.message);
        setTopDonors([]);
      }
    } catch (e) {
      console.error('Race data load error:', e);
      setLoading(false);
    }
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
            selectedDistrict={selectedDistrict} setSelectedDistrict={setSelectedDistrict}
            dateFrom={dateFrom} setDateFrom={setDateFrom}
            dateTo={dateTo} setDateTo={setDateTo}
            primaryOnly={primaryOnly} setPrimaryOnly={setPrimaryOnly}
            selectedCycleName={selectedCycleName}
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
                          borderRadius: 8,
                          minBarLength: 5 // Ensure tiny bars are still visible and hoverable
                        }]
                      }}
                      options={{
                        maintainAspectRatio: false,
                        interaction: {
                          mode: 'index', // Hover works on entire vertical slice, not just bar
                          intersect: false // Don't require exact bar intersection
                        },
                        plugins: {
                          tooltip: {
                            callbacks: {
                              label: (ctx) => `$${ctx.parsed.y.toLocaleString()}`
                            }
                          }
                        }
                      }}
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

              {/* IE & Ad Buy Correlation */}
              <IEAdBuyCorrelation officeId={selectedOffice} cycleId={selectedCycle} />

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
                    {raceData.candidates.map((c, i) => {
                      const partyInfo = getPartyInfo(c.subject_committee__candidate_party__name);
                      const candidateId = c.subject_committee__committee_id || c.subject_committee_id || c.committee_id;
                      return (
                        <tr key={i} className="hover:bg-purple-50/5 transition-colors">
                          <td className={`px-6 py-4 text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            {candidateId ? (
                              <Link
                                to={`/candidate/${candidateId}`}
                                className="hover:text-[#7163BA] hover:underline transition-colors"
                              >
                                {c.subject_committee__name__first_name} {c.subject_committee__name__last_name}
                              </Link>
                            ) : (
                              <span>{c.subject_committee__name__first_name} {c.subject_committee__name__last_name}</span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`text-xs font-bold px-2 py-1 rounded-full ${partyInfo.colors.bgLight} ${partyInfo.colors.text}`}>
                              ({partyInfo.abbr}) {partyInfo.fullName}
                            </span>
                          </td>
                          <td className={`px-6 py-4 text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            ${parseFloat(c.total_ie || 0).toLocaleString()}
                          </td>
                          <td className="px-6 py-4">
                            {(() => {
                              const ieFor = parseFloat(c.ie_for || 0);
                              const ieAgainst = parseFloat(c.ie_against || 0);
                              const netIE = ieFor - ieAgainst;
                              return (
                                <span className={`text-sm font-bold ${netIE >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                  {netIE >= 0 ? '+' : ''}${Math.abs(netIE).toLocaleString()}
                                </span>
                              );
                            })()}
                          </td>
                        </tr>
                      );
                    })}
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