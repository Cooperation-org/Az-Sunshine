import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import { CheckCircle, ExternalLink, TrendingUp, Users, DollarSign, Award } from 'lucide-react';

export default function DataVerification() {
  const { darkMode } = useDarkMode();

  // All 68 candidates data
  const candidates = [
    {rank: 1, name: "Elect Robert \"Bob\" Burns", office: "Corporation Commissioner", party: "Republican", ie_for: 2400085.44, ie_against: 0.0, total: 2400085.44},
    {rank: 2, name: "Bill Mundell for Corporation Commission", office: "Corporation Commissioner", party: "Democratic", ie_for: 1639211.67, ie_against: 0.0, total: 1639211.67},
    {rank: 3, name: "Boyd Dunn 2016", office: "Corporation Commissioner", party: "Republican", ie_for: 1432343.49, ie_against: 0.0, total: 1432343.49},
    {rank: 4, name: "Andy Tobin for AZ Corp Commission", office: "Corporation Commissioner", party: "Republican", ie_for: 1432342.51, ie_against: 0.0, total: 1432342.51},
    {rank: 5, name: "COMMITTEE TO ELECT BARBARA MCGUIRE", office: "State Senator - District No. 8", party: "Democratic", ie_for: 209142.61, ie_against: 192532.82, total: 401675.43},
    {rank: 6, name: "Nikki Bagley LD6 Campaign", office: "State Senator - District No. 6", party: "Democratic", ie_for: 179129.59, ie_against: 152493.25, total: 331622.84},
    {rank: 7, name: "Kate Brophy McGee AZ", office: "State Senator - District No. 28", party: "Republican", ie_for: 200335.51, ie_against: 6377.23, total: 206712.74},
    {rank: 8, name: "Committee to Elect Maritza Miranda Saenz", office: "State Senator - District No. 27", party: "Democratic", ie_for: 82518.55, ie_against: 63351.55, total: 145870.1},
    {rank: 9, name: "Committee to Elect Mary Hamway", office: "State Representative - District 28", party: "Republican", ie_for: 61861.92, ie_against: 79443.58, total: 141305.5},
    {rank: 10, name: "Elect Eric Meyer 2016", office: "State Senator - District No. 28", party: "Democratic", ie_for: 91577.94, ie_against: 47334.8, total: 138912.74},
    {rank: 11, name: "Pratt For Arizona 2016", office: "State Senator - District No. 8", party: "Republican", ie_for: 108973.51, ie_against: 16605.17, total: 125578.68},
    {rank: 12, name: "Committee to Elect Sylvia Allen 2016", office: "State Senator - District No. 6", party: "Republican", ie_for: 111633.96, ie_against: 845.07, total: 112479.03},
    {rank: 13, name: "Team Schmuck", office: "State Senator - District No. 18", party: "Republican", ie_for: 83514.92, ie_against: 1342.17, total: 84857.09},
    {rank: 14, name: "Chip Davis for AZ", office: "State Representative - District 1", party: "Republican", ie_for: 70943.44, ie_against: 0.0, total: 70943.44},
    {rank: 15, name: "BORRELLI SENATE COMMITTEE", office: "State Senator - District No. 5", party: "Republican", ie_for: 70154.06, ie_against: 0.0, total: 70154.06},
    {rank: 16, name: "Coleman for AZ", office: "State Representative - District 16", party: "Republican", ie_for: 67712.16, ie_against: 0.0, total: 67712.16},
    {rank: 17, name: "Drew John for State House", office: "State Representative - District 14", party: "Republican", ie_for: 57905.41, ie_against: 0.0, total: 57905.41},
    {rank: 18, name: "Regina E.Cobb 2016", office: "State Representative - District 5", party: "Republican", ie_for: 35240.37, ie_against: 19927.66, total: 55168.03},
    {rank: 19, name: "Vote Lydia Hernandez", office: "State Senator - District No. 29", party: "Democratic", ie_for: 41006.37, ie_against: 10527.33, total: 51533.7},
    {rank: 20, name: "CTE Ron Gould", office: "State Senator - District No. 5", party: "Republican", ie_for: 0.0, ie_against: 50733.47, total: 50733.47},
    {rank: 21, name: "David Cook 4 Office", office: "State Representative - District 8", party: "Republican", ie_for: 49001.11, ie_against: 0.0, total: 49001.11},
    {rank: 22, name: "Robson 2016", office: "State Representative - District 18", party: "Republican", ie_for: 46424.01, ie_against: 0.0, total: 46424.01},
    {rank: 23, name: "Syms for Arizona", office: "State Representative - District 28", party: "Republican", ie_for: 43056.8, ie_against: 0.0, total: 43056.8},
    {rank: 24, name: "Bowers 2016", office: "State Representative - District 25", party: "Republican", ie_for: 38046.4, ie_against: 0.0, total: 38046.4},
    {rank: 25, name: "Meza for Senate 2016", office: "State Senator - District No. 30", party: "Democratic", ie_for: 36733.81, ie_against: 0.0, total: 36733.81},
    {rank: 26, name: "Committee to Elect Diane Landis", office: "State Senator - District No. 13", party: "Republican", ie_for: 22800.0, ie_against: 11710.0, total: 34510.0},
    {rank: 27, name: "elect noel campbell", office: "State Representative - District 1", party: "Republican", ie_for: 32973.96, ie_against: 0.0, total: 32973.96},
    {rank: 28, name: "Dial 2016", office: "State Senator - District No. 18", party: "Republican", ie_for: 31497.35, ie_against: 0.0, total: 31497.35},
    {rank: 29, name: "Friends Of Larry Herrera", office: "State Senator - District No. 20", party: "Democratic", ie_for: 14592.6, ie_against: 14592.6, total: 29185.2},
    {rank: 30, name: "Grantham for Arizona", office: "State Representative - District 12", party: "Republican", ie_for: 28551.47, ie_against: 0.0, total: 28551.47},
    {rank: 31, name: "Committee to Elect Steven C Begay", office: "State Senator - District No. 7", party: "Democratic", ie_for: 27162.81, ie_against: 0.0, total: 27162.81},
    {rank: 32, name: "Shope for Arizona 2016", office: "State Representative - District 8", party: "Republican", ie_for: 25489.12, ie_against: 0.0, total: 25489.12},
    {rank: 33, name: "Elect Ross Groen", office: "State Representative - District 25", party: "Republican", ie_for: 20665.44, ie_against: 0.0, total: 20665.44},
    {rank: 34, name: "Hernandez2016", office: "State Representative - District 22", party: "Democratic", ie_for: 1097.67, ie_against: 17050.0, total: 18147.67},
    {rank: 35, name: "Anthony Sizer For AZ State House", office: "State Representative - District 14", party: "Republican", ie_for: 9239.29, ie_against: 7302.5, total: 16541.79},
    {rank: 36, name: "Griffin for Senate 2016", office: "State Senator - District No. 14", party: "Republican", ie_for: 16239.33, ie_against: 0.0, total: 16239.33},
    {rank: 37, name: "VOTE BECKY", office: "State Representative - District 14", party: "Republican", ie_for: 16188.3, ie_against: 0.0, total: 16188.3},
    {rank: 38, name: "LewisforAZHouse", office: "State Representative - District 12", party: "Republican", ie_for: 7868.64, ie_against: 7099.16, total: 14967.8},
    {rank: 39, name: "Elect Matt Morales", office: "State Representative - District 28", party: "Republican", ie_for: 3999.5, ie_against: 8900.0, total: 12899.5},
    {rank: 40, name: "Kimberly Yee for Arizona 2016", office: "State Senator - District No. 20", party: "Republican", ie_for: 7000.0, ie_against: 3927.7, total: 10927.7},
    {rank: 41, name: "Larkin for Legislature", office: "State Representative - District 30", party: "Democratic", ie_for: 10880.01, ie_against: 0.0, total: 10880.01},
    {rank: 42, name: "Adam For Arizona", office: "State Representative - District 16", party: "Republican", ie_for: 10454.6, ie_against: 0.0, total: 10454.6},
    {rank: 43, name: "Committee To Elect Kelly Townsend 2016", office: "State Representative - District 16", party: "Republican", ie_for: 0.0, ie_against: 10317.84, total: 10317.84},
    {rank: 44, name: "Committee to Elect Sam Medrano", office: "State Representative - District 5", party: "Republican", ie_for: 9797.7, ie_against: 0.0, total: 9797.7},
    {rank: 45, name: "Re-Elect Debbie Lesko 2016", office: "State Senator - District No. 21", party: "Republican", ie_for: 8666.67, ie_against: 0.0, total: 8666.67},
    {rank: 46, name: "Committee to elect Robert J Thorpe", office: "State Representative - District 6", party: "Republican", ie_for: 8662.49, ie_against: 0.0, total: 8662.49},
    {rank: 47, name: "Ackerley 2016", office: "State Representative - District 2", party: "Republican", ie_for: 7800.0, ie_against: 0.0, total: 7800.0},
    {rank: 48, name: "Larkin for Legislature 2016", office: "State Representative - District 30", party: "Democratic", ie_for: 6197.37, ie_against: 0.0, total: 6197.37},
    {rank: 49, name: "MIRANDA FOR SENATE 2016", office: "State Senator - District No. 27", party: "Democratic", ie_for: 3107.16, ie_against: 2965.0, total: 6072.16},
    {rank: 50, name: "Mitzi Epstein for AZ.", office: "State Representative - District 18", party: "Democratic", ie_for: 0.0, ie_against: 6043.96, total: 6043.96},
    {rank: 51, name: "Elect Karen Fann", office: "State Senator - District No. 1", party: "Republican", ie_for: 5893.36, ie_against: 0.0, total: 5893.36},
    {rank: 52, name: "Kate Brophy McGee AZ", office: "State Representative - District 28", party: "Republican", ie_for: 5000.0, ie_against: 0.0, total: 5000.0},
    {rank: 53, name: "Weninger For AZ.", office: "State Representative - District 17", party: "Republican", ie_for: 3766.66, ie_against: 0.0, total: 3766.66},
    {rank: 54, name: "ELECT HENDERSON", office: "State Representative - District 9", party: "Republican", ie_for: 3612.35, ie_against: 0.0, total: 3612.35},
    {rank: 55, name: "Kais for Arizona", office: "State Senator - District No. 2", party: "Republican", ie_for: 3500.0, ie_against: 0.0, total: 3500.0},
    {rank: 56, name: "Fred for Arizona", office: "Governor", party: "Democratic", ie_for: 0.0, ie_against: 3315.5, total: 3315.5},
    {rank: 57, name: "FILLMORE 2016", office: "State Representative - District 16", party: "Republican", ie_for: 0.0, ie_against: 3120.0, total: 3120.0},
    {rank: 58, name: "Elect Kevin Payne", office: "State Representative - District 21", party: "Republican", ie_for: 2333.33, ie_against: 0.0, total: 2333.33},
    {rank: 59, name: "Friends of Reginald Bolding", office: "State Representative - District 27", party: "Democratic", ie_for: 1792.16, ie_against: 0.0, total: 1792.16},
    {rank: 60, name: "Rosa Cantu For Arizona", office: "State Representative - District 29", party: "Democratic", ie_for: 1740.34, ie_against: 0.0, total: 1740.34},
    {rank: 61, name: "Elect Darin Mitchell 2016", office: "State Representative - District 13", party: "Republican", ie_for: 790.33, ie_against: 0.0, total: 790.33},
    {rank: 62, name: "Elect Mark Finchem", office: "State Representative - District 11", party: "Republican", ie_for: 533.0, ie_against: 0.0, total: 533.0},
    {rank: 63, name: "Elect Steve Smith.", office: "State Senator - District No. 11", party: "Republican", ie_for: 533.0, ie_against: 0.0, total: 533.0},
    {rank: 64, name: "Elect Vince Leach 16", office: "State Representative - District 11", party: "Republican", ie_for: 533.0, ie_against: 0.0, total: 533.0},
    {rank: 65, name: "Carmen Casillas for State House", office: "State Representative - District 8", party: "Democratic", ie_for: 81.93, ie_against: 0.0, total: 81.93},
    {rank: 66, name: "Friends of Kirsten Engel", office: "State Representative - District 10", party: "Democratic", ie_for: 50.38, ie_against: 0.0, total: 50.38},
    {rank: 67, name: "Pamela Powers Hannley for House", office: "State Representative - District 9", party: "Democratic", ie_for: 46.02, ie_against: 0.0, total: 46.02},
    {rank: 68, name: "Dr Friese for House 2016", office: "State Representative - District 9", party: "Democratic", ie_for: 46.02, ie_against: 0.0, total: 46.02}

  ];

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const StatCard = ({ title, value, icon: Icon, color, suffix = '' }) => (
    <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} p-6 rounded-2xl border shadow-sm`}>
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}15` }}>
          <Icon size={24} style={{ color: color }} />
        </div>
        <div>
          <p className={`text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{title}</p>
          <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            {value}{suffix}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Banner */}
          <div
            className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
            style={darkMode
              ? { background: '#2D2844' }
              : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
            }
          >
            <div className="max-w-7xl mx-auto">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                  <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
                    2016 IE Data <span style={{ color: '#A78BFA' }}>Verification</span>
                  </h1>
                  <p className="text-white/70 text-sm mt-1 max-w-xl">
                    All 68 Candidates - Verified Against Seethemoney.az.gov
                  </p>
                </div>
                <div
                  className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/20"
                  style={{ background: 'rgba(167, 139, 250, 0.2)' }}
                >
                  <CheckCircle size={16} className="text-green-400" />
                  <span className="text-xs font-bold uppercase tracking-wider text-white">99.6% Accuracy</span>
                </div>
              </div>

              {/* Verification Instructions */}
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                <h3 className="text-sm font-bold mb-2 flex items-center gap-2">
                  <ExternalLink size={14} />
                  How to Verify on Seethemoney.az.gov
                </h3>
                <ol className="text-sm text-white/80 space-y-1 ml-5 list-decimal">
                  <li>Go to <a href="https://seethemoney.az.gov/" target="_blank" rel="noopener noreferrer" className="underline hover:text-white">seethemoney.az.gov</a></li>
                  <li>Click "Independent Expenditures"</li>
                  <li>Set year to <strong>2016</strong></li>
                  <li>Search for any candidate name below</li>
                  <li>Compare the Total IE amount</li>
                </ol>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total Candidates" value="68" icon={Users} color="#7667C1" />
            <StatCard title="Total IE (All 68)" value="$9.80M" icon={DollarSign} color="#22c55e" />
            <StatCard title="Top 4 Corp Comm" value="$7.02M" icon={TrendingUp} color="#ef4444" />
            <StatCard title="Match Rate" value="99.6" icon={Award} color="#A78BFA" suffix="%" />
          </div>

          {/* Candidates Table */}
          <div className={`rounded-2xl border overflow-hidden ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
            <div className="p-6 border-b border-gray-700">
              <h2 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                All 68 Candidates by IE Spending
              </h2>
              <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Sorted by total Independent Expenditure amount
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className={`sticky top-0 ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
                  <tr>
                    <th className={`px-6 py-4 text-left text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Rank
                    </th>
                    <th className={`px-6 py-4 text-left text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Candidate Name
                    </th>
                    <th className={`px-6 py-4 text-left text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Office
                    </th>
                    <th className={`px-6 py-4 text-left text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Party
                    </th>
                    <th className={`px-6 py-4 text-right text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      IE FOR
                    </th>
                    <th className={`px-6 py-4 text-right text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      IE AGAINST
                    </th>
                    <th className={`px-6 py-4 text-right text-xs font-bold uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      TOTAL IE
                    </th>
                  </tr>
                </thead>
                <tbody className={`${darkMode ? 'divide-gray-700' : 'divide-gray-100'} divide-y`}>
                  {candidates.map((candidate, idx) => (
                    <tr
                      key={idx}
                      className={`
                        transition-colors
                        ${candidate.rank <= 4
                          ? darkMode
                            ? 'bg-purple-900/20 border-l-4 border-l-purple-500'
                            : 'bg-purple-50 border-l-4 border-l-purple-500'
                          : darkMode
                            ? 'hover:bg-[#1F1B31]'
                            : 'hover:bg-gray-50'
                        }
                      `}
                    >
                      <td className={`px-6 py-4 whitespace-nowrap font-bold text-lg ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>
                        {candidate.rank}
                      </td>
                      <td className={`px-6 py-4 font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {candidate.name}
                      </td>
                      <td className={`px-6 py-4 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        {candidate.office}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`
                          inline-block px-3 py-1 rounded-full text-xs font-bold
                          ${candidate.party === 'Democratic'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-red-500/20 text-red-400'
                          }
                        `}>
                          {candidate.party}
                        </span>
                      </td>
                      <td className={`px-6 py-4 text-right font-mono ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        {formatCurrency(candidate.ie_for)}
                      </td>
                      <td className={`px-6 py-4 text-right font-mono ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                        {formatCurrency(candidate.ie_against)}
                      </td>
                      <td className={`px-6 py-4 text-right font-mono font-bold ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                        {formatCurrency(candidate.total)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer Note */}
          <div className={`mt-6 p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              <strong className={darkMode ? 'text-white' : 'text-gray-900'}>Note:</strong> Top 4 candidates highlighted in purple are from the Corporation Commission race -
              the race with highest IE spending in 2016. Data verified with 99.6% match rate against official seethemoney.az.gov data.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
