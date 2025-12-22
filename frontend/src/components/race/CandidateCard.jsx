import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';

export default function CandidateCard({ candidate }) {
  const { darkMode } = useDarkMode();

  // Parse IE spending data
  const ieFor = parseFloat(candidate.ie_for || 0);
  const ieAgainst = parseFloat(candidate.ie_against || 0);
  const netBenefit = ieFor - ieAgainst;

  return (
    <div className={`min-w-[280px] p-5 rounded-2xl border transition-all hover:scale-105 ${
      darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
    }`}>
      {/* Candidate Name */}
      <div className="mb-4">
        <h3 className={`text-lg font-bold ${
          darkMode ? 'text-white' : 'text-gray-900'
        }`}>
          {candidate.subject_committee__name__first_name} {candidate.subject_committee__name__last_name}
        </h3>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-xs px-2 py-1 rounded-full ${
            darkMode ? 'bg-purple-900/30 text-purple-300' : 'bg-purple-100 text-purple-700'
          }`}>
            {candidate.subject_committee__candidate_party__name || 'Independent'}
          </span>
        </div>
      </div>

      {/* IE Spending */}
      <div className="space-y-3">
        {/* IE For */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-green-500" />
            <span className="text-xs font-medium text-gray-500">IE For</span>
          </div>
          <span className="text-sm font-bold text-green-500">
            ${ieFor.toLocaleString()}
          </span>
        </div>

        {/* IE Against */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingDown size={16} className="text-red-500" />
            <span className="text-xs font-medium text-gray-500">IE Against</span>
          </div>
          <span className="text-sm font-bold text-red-500">
            ${ieAgainst.toLocaleString()}
          </span>
        </div>

        {/* Net Benefit */}
        <div className={`pt-3 border-t ${
          darkMode ? 'border-gray-700' : 'border-gray-100'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign size={16} className="text-[#7163BA]" />
              <span className="text-xs font-medium text-gray-500">Net Benefit</span>
            </div>
            <span className={`text-lg font-bold ${
              netBenefit >= 0 ? 'text-green-500' : 'text-red-500'
            }`}>
              {netBenefit >= 0 ? '+' : ''}${netBenefit.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
