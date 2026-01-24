import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getFECRaces, getFECCommittees, getFECStatus } from "../api/api";
import Sidebar from "../components/Sidebar";
import { useDarkMode } from "../context/DarkModeContext";
import { formatCurrency } from "../utils/currencyFormat";
import {
  TrendingUp, TrendingDown, DollarSign, Users, Building2,
  ChevronDown, ChevronUp, ExternalLink, Flag, ArrowRight, Info
} from "lucide-react";

// Federal race display names
const RACE_NAMES = {
  'AZ-S1': 'U.S. Senate',
  'AZ-01': 'Congressional District 1',
  'AZ-02': 'Congressional District 2',
  'AZ-03': 'Congressional District 3',
  'AZ-04': 'Congressional District 4',
  'AZ-05': 'Congressional District 5',
  'AZ-06': 'Congressional District 6',
  'AZ-07': 'Congressional District 7',
  'AZ-08': 'Congressional District 8',
  'AZ-09': 'Congressional District 9',
};

// Summary Card Component
const SummaryCard = ({ title, value, icon: Icon, color, darkMode }) => (
  <div className={`p-5 rounded-2xl border transition-all ${
    darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100 shadow-sm'
  }`}>
    <div className="flex items-center justify-between mb-2">
      <span className={`text-xs font-medium uppercase tracking-wide ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
        {title}
      </span>
      <div className={`p-2 rounded-lg ${darkMode ? 'bg-[#1E1A2E]' : 'bg-gray-50'}`}>
        <Icon size={16} className={color} />
      </div>
    </div>
    <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
      {value}
    </div>
  </div>
);

// Race Card Component
const RaceCard = ({ race, cycles, totalSpending, supportAmount, opposeAmount, darkMode, expanded, onToggle }) => {
  const raceName = RACE_NAMES[race] || race;
  const isSenate = race.includes('-S');

  return (
    <div className={`rounded-2xl border transition-all overflow-hidden ${
      darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100 shadow-sm'
    }`}>
      <div
        className="p-5 cursor-pointer flex items-center justify-between hover:bg-opacity-80 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${isSenate ? 'bg-purple-500/10' : 'bg-blue-500/10'}`}>
            {isSenate ? (
              <Flag size={20} className="text-purple-500" />
            ) : (
              <Building2 size={20} className="text-blue-500" />
            )}
          </div>
          <div>
            <h3 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {raceName}
            </h3>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {cycles.length > 1 ? `${cycles.join(', ')}` : cycles[0]} {isSenate ? '(Statewide)' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <p className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {formatCurrency(totalSpending)}
            </p>
            <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Total IE Spending
            </p>
          </div>
          {expanded ? (
            <ChevronUp size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
          ) : (
            <ChevronDown size={20} className={darkMode ? 'text-gray-400' : 'text-gray-500'} />
          )}
        </div>
      </div>

      {expanded && (
        <div className={`px-5 pb-5 border-t ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
          <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Support vs Oppose */}
            <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1E1A2E]' : 'bg-gray-50'}`}>
              <h4 className={`text-sm font-medium mb-3 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Spending Breakdown
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <div className="flex items-center gap-2">
                      <TrendingUp size={14} className="text-green-500" />
                      <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Support</span>
                    </div>
                    <span className="text-sm font-bold text-green-500">{formatCurrency(supportAmount)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all"
                      style={{ width: `${totalSpending > 0 ? (supportAmount / totalSpending) * 100 : 0}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <div className="flex items-center gap-2">
                      <TrendingDown size={14} className="text-red-500" />
                      <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Oppose</span>
                    </div>
                    <span className="text-sm font-bold text-red-500">{formatCurrency(opposeAmount)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    <div
                      className="h-full bg-red-500 rounded-full transition-all"
                      style={{ width: `${totalSpending > 0 ? (opposeAmount / totalSpending) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Cycle Breakdown */}
            <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1E1A2E]' : 'bg-gray-50'}`}>
              <h4 className={`text-sm font-medium mb-3 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Election Cycles
              </h4>
              <div className="flex flex-wrap gap-2">
                {cycles.map(cycle => (
                  <span
                    key={cycle}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                      darkMode ? 'bg-[#2D2844] text-gray-300' : 'bg-white text-gray-600 border border-gray-200'
                    }`}
                  >
                    {cycle}
                  </span>
                ))}
              </div>
              <a
                href={`https://www.fec.gov/data/independent-expenditures/?data_type=processed&state=AZ&candidate_office=${isSenate ? 'S' : 'H'}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-3 text-sm text-[#7163BA] hover:underline"
              >
                View details on FEC.gov <ExternalLink size={12} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Committee Card Component
const CommitteeCard = ({ committee, darkMode }) => (
  <div className={`p-4 rounded-xl border transition-all hover:border-[#7163BA] ${
    darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100 shadow-sm'
  }`}>
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1 min-w-0">
        <h4
          className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}
          title={committee.committee_name}
        >
          {committee.committee_name}
        </h4>
        <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          {committee.races_targeted?.join(', ') || 'AZ races'}
        </p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          {formatCurrency(committee.total_spending)}
        </p>
        <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
          {committee.num_expenditures} filings
        </p>
      </div>
    </div>
    <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
      <div className="flex items-center gap-1">
        <TrendingUp size={12} className="text-green-500" />
        <span className="text-xs text-green-500">{formatCurrency(committee.support_amount)}</span>
      </div>
      <div className="flex items-center gap-1">
        <TrendingDown size={12} className="text-red-500" />
        <span className="text-xs text-red-500">{formatCurrency(committee.oppose_amount)}</span>
      </div>
    </div>
  </div>
);

export default function FederalRaces() {
  const { darkMode } = useDarkMode();
  const [loading, setLoading] = useState(true);
  const [races, setRaces] = useState([]);
  const [committees, setCommittees] = useState([]);
  const [status, setStatus] = useState({});
  const [expandedRace, setExpandedRace] = useState(null);
  const [selectedCycle, setSelectedCycle] = useState('all');
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [selectedCycle]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = selectedCycle !== 'all' ? { cycle: selectedCycle } : {};
      const [racesData, committeesData, statusData] = await Promise.all([
        getFECRaces(params),
        getFECCommittees(params),
        getFECStatus()
      ]);

      // Filter to only Arizona races and group by race code
      const azRaces = (racesData?.races || []).filter(r => r.race.startsWith('AZ'));

      // Group races by race code (combine cycles)
      const raceMap = new Map();
      azRaces.forEach(r => {
        if (raceMap.has(r.race)) {
          const existing = raceMap.get(r.race);
          existing.cycles.push(r.cycle);
          existing.totalSpending += r.total_spending;
          existing.supportAmount += r.support_amount;
          existing.opposeAmount += r.oppose_amount;
        } else {
          raceMap.set(r.race, {
            race: r.race,
            cycles: [r.cycle],
            totalSpending: r.total_spending,
            supportAmount: r.support_amount,
            opposeAmount: r.oppose_amount,
          });
        }
      });

      // Sort by total spending
      const groupedRaces = Array.from(raceMap.values())
        .sort((a, b) => b.totalSpending - a.totalSpending);

      // Backend already filters to AZ, just take top 10
      const azCommittees = (committeesData?.committees || []).slice(0, 10);

      setRaces(groupedRaces);
      setCommittees(azCommittees);
      setStatus(statusData || {});
    } catch (err) {
      console.error('Error loading FEC data:', err);
      setError('Failed to load federal election data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const cycles = ['all', '2024', '2022', '2020', '2018'];

  // Calculate totals from grouped races
  const totalSpending = races.reduce((sum, r) => sum + r.totalSpending, 0);
  const totalSupport = races.reduce((sum, r) => sum + r.supportAmount, 0);
  const totalOppose = races.reduce((sum, r) => sum + r.opposeAmount, 0);

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1E1A2E]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0 overflow-auto">
        <div className="p-4 md:p-6 lg:p-8">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-xl bg-[#7163BA]/10">
                <Flag size={24} className="text-[#7163BA]" />
              </div>
              <div>
                <h1 className={`text-2xl md:text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  Federal Elections
                </h1>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Independent expenditure data for Arizona's federal races from the FEC
                </p>
              </div>
            </div>
          </div>

          {/* Cross-link to State Races */}
          <Link
            to="/race-analysis"
            className={`flex items-center justify-between p-4 mb-6 rounded-xl border transition-all hover:border-[#7163BA] ${
              darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-200'
            }`}
          >
            <div className="flex items-center gap-3">
              <Info size={18} className="text-[#7163BA]" />
              <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Looking for <strong>state-level races</strong> (Governor, Legislature, Corporation Commission)?
              </span>
            </div>
            <div className="flex items-center gap-1 text-[#7163BA] font-medium text-sm">
              View Race Analysis <ArrowRight size={16} />
            </div>
          </Link>

          {/* Cycle Filter */}
          <div className="flex gap-2 mb-6 flex-wrap">
            {cycles.map(cycle => (
              <button
                key={cycle}
                onClick={() => setSelectedCycle(cycle)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCycle === cycle
                    ? 'bg-[#7163BA] text-white'
                    : darkMode
                      ? 'bg-[#2D2844] text-gray-300 hover:bg-[#3D3854]'
                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                {cycle === 'all' ? 'All Cycles' : cycle}
              </button>
            ))}
          </div>

          {error ? (
            <div className={`p-8 rounded-2xl text-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
              <p className={darkMode ? 'text-gray-400' : 'text-gray-500'}>{error}</p>
              <a
                href="https://www.fec.gov/data/independent-expenditures/?data_type=processed&most_recent=true&state=AZ"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 mt-4 text-[#7163BA] hover:underline"
              >
                View on FEC.gov <ExternalLink size={14} />
              </a>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <SummaryCard
                  title="Total IE Spending"
                  value={formatCurrency(totalSpending)}
                  icon={DollarSign}
                  color="text-[#7163BA]"
                  darkMode={darkMode}
                />
                <SummaryCard
                  title="Support Spending"
                  value={formatCurrency(totalSupport)}
                  icon={TrendingUp}
                  color="text-green-500"
                  darkMode={darkMode}
                />
                <SummaryCard
                  title="Oppose Spending"
                  value={formatCurrency(totalOppose)}
                  icon={TrendingDown}
                  color="text-red-500"
                  darkMode={darkMode}
                />
                <SummaryCard
                  title="Arizona Races"
                  value={races.length}
                  icon={Flag}
                  color="text-blue-500"
                  darkMode={darkMode}
                />
              </div>

              {/* Two Column Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Races Column */}
                <div className="lg:col-span-2 space-y-4">
                  <h2 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    Arizona Federal Races
                  </h2>
                  {loading ? (
                    <div className="space-y-4">
                      {[1, 2, 3].map(i => (
                        <div key={i} className={`p-6 rounded-2xl animate-pulse ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                          <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-1/3 mb-3"></div>
                          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                        </div>
                      ))}
                    </div>
                  ) : races.length === 0 ? (
                    <div className={`p-8 rounded-2xl text-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                      <Flag size={48} className={`mx-auto mb-4 ${darkMode ? 'text-gray-600' : 'text-gray-300'}`} />
                      <p className={`font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        No federal race data available
                      </p>
                      <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                        {selectedCycle !== 'all'
                          ? `No Arizona federal races found for ${selectedCycle}. Try selecting a different cycle.`
                          : 'No Arizona federal race data has been imported yet.'
                        }
                      </p>
                    </div>
                  ) : (
                    races.map((raceData) => (
                      <RaceCard
                        key={raceData.race}
                        race={raceData.race}
                        cycles={raceData.cycles.sort((a, b) => b - a)}
                        totalSpending={raceData.totalSpending}
                        supportAmount={raceData.supportAmount}
                        opposeAmount={raceData.opposeAmount}
                        darkMode={darkMode}
                        expanded={expandedRace === raceData.race}
                        onToggle={() => setExpandedRace(expandedRace === raceData.race ? null : raceData.race)}
                      />
                    ))
                  )}
                </div>

                {/* Committees Column */}
                <div>
                  <h2 className={`text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    Top PACs in Arizona
                  </h2>
                  <div className="space-y-3">
                    {loading ? (
                      <div className={`p-4 rounded-xl animate-pulse ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-2/3 mb-2"></div>
                        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                      </div>
                    ) : committees.length === 0 ? (
                      <div className={`p-4 rounded-xl text-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                          No committee data available for Arizona.
                        </p>
                      </div>
                    ) : (
                      committees.map((committee, idx) => (
                        <CommitteeCard
                          key={committee.committee_id || idx}
                          committee={committee}
                          darkMode={darkMode}
                        />
                      ))
                    )}
                  </div>

                  {/* FEC Link */}
                  <a
                    href="https://www.fec.gov/data/independent-expenditures/?data_type=processed&most_recent=true&state=AZ"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex items-center justify-center gap-2 mt-4 p-3 rounded-xl text-sm font-medium transition-all ${
                      darkMode
                        ? 'bg-[#2D2844] text-gray-300 hover:bg-[#3D3854]'
                        : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    View All on FEC.gov <ExternalLink size={14} />
                  </a>
                </div>
              </div>

              {/* Data Source Note */}
              <div className={`mt-8 p-4 rounded-xl ${darkMode ? 'bg-[#2D2844]/50' : 'bg-gray-100'}`}>
                <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  <strong>Data source:</strong> Federal Election Commission (FEC) Schedule E filings.
                  Independent expenditures are spending by outside groups to support or oppose federal candidates.
                  This data is separate from Arizona state election data. Last updated: {status.last_updated || 'N/A'}.
                  Total FEC records: {status.record_count?.toLocaleString() || 0}.
                </p>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
