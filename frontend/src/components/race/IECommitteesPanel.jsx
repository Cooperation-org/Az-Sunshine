import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Building2 } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';

export default function IECommitteesPanel({ committees = [], title = "Super PAC & Dark Money Spending" }) {
  const { darkMode } = useDarkMode();

  if (!committees || committees.length === 0) {
    return null;
  }

  // Calculate totals
  const totalFor = committees.reduce((sum, c) => sum + Math.abs(c.ie_for || c.support_amount || 0), 0);
  const totalAgainst = committees.reduce((sum, c) => sum + Math.abs(c.ie_against || c.oppose_amount || 0), 0);
  const totalSpending = totalFor + totalAgainst;

  return (
    <div className={`p-5 rounded-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${darkMode ? 'bg-[#373052]' : 'bg-purple-100'}`}>
            <Building2 className="text-[#7163BA]" size={20} />
          </div>
          <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            {title}
          </h3>
        </div>
        <span className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ${Math.abs(totalSpending).toLocaleString()}
        </span>
      </div>

      {/* Summary Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-green-500 font-medium">
            For: ${Math.abs(totalFor).toLocaleString()}
          </span>
          <span className="text-red-500 font-medium">
            Against: ${Math.abs(totalAgainst).toLocaleString()}
          </span>
        </div>
        {totalSpending > 0 && (
          <div className="h-3 rounded-full overflow-hidden bg-gray-200 flex">
            <div
              className="bg-green-500 h-full"
              style={{ width: `${(totalFor / totalSpending) * 100}%` }}
            />
            <div
              className="bg-red-500 h-full"
              style={{ width: `${(totalAgainst / totalSpending) * 100}%` }}
            />
          </div>
        )}
      </div>

      {/* Committee List */}
      <div className="space-y-3 max-h-80 overflow-y-auto">
        {committees.map((committee, index) => {
          const ieFor = Math.abs(committee.ie_for || committee.support_amount || 0);
          const ieAgainst = Math.abs(committee.ie_against || committee.oppose_amount || 0);
          const total = ieFor + ieAgainst;

          return (
            <div
              key={committee.committee_id || index}
              className={`p-3 rounded-lg ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}
            >
              <div className="flex items-start justify-between mb-2">
                <span className={`font-medium text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {committee.name || committee.committee_name || 'Unknown Committee'}
                </span>
                <span className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  ${Math.abs(total).toLocaleString()}
                </span>
              </div>

              {/* Stacked Bar for this committee */}
              {total > 0 && (
                <div className="h-2 rounded-full overflow-hidden bg-gray-300 flex mb-2">
                  {ieFor > 0 && (
                    <div
                      className="bg-green-500 h-full"
                      style={{ width: `${(ieFor / total) * 100}%` }}
                    />
                  )}
                  {ieAgainst > 0 && (
                    <div
                      className="bg-red-500 h-full"
                      style={{ width: `${(ieAgainst / total) * 100}%` }}
                    />
                  )}
                </div>
              )}

              {/* For/Against breakdown */}
              <div className="flex justify-between text-xs">
                <div className="flex items-center gap-1 text-green-500">
                  <TrendingUp size={12} />
                  <span>${Math.abs(ieFor).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-1 text-red-500">
                  <TrendingDown size={12} />
                  <span>${Math.abs(ieAgainst).toLocaleString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
