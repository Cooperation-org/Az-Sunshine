import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, DollarSign, ExternalLink } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';
import { getPartyInfo } from '../../utils/partyUtils';

export default function CandidateCard({ candidate }) {
  const { darkMode } = useDarkMode();

  // Parse IE spending data
  const ieFor = parseFloat(candidate.ie_for || 0);
  const ieAgainst = parseFloat(candidate.ie_against || 0);
  const netBenefit = ieFor - ieAgainst;

  // Get party info with abbreviation and colors
  const partyInfo = getPartyInfo(candidate.subject_committee__candidate_party__name);

  // Get candidate ID for linking (API returns subject_committee__committee_id)
  const candidateId = candidate.subject_committee__committee_id || candidate.subject_committee_id || candidate.committee_id;

  const cardClasses = `min-w-[280px] p-5 rounded-2xl border transition-all ${
    candidateId ? 'hover:scale-105 hover:border-[#7163BA] cursor-pointer' : ''
  } ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`;

  const CardContent = () => (
    <>
      {/* Candidate Name */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            {candidate.subject_committee__name__first_name} {candidate.subject_committee__name__last_name}
          </h3>
          {candidateId && (
            <ExternalLink size={14} className={`${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-xs font-bold px-2 py-1 rounded-full ${partyInfo.colors.bgLight} ${partyInfo.colors.text}`}>
            ({partyInfo.abbr}) {partyInfo.fullName}
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
        <div className={`pt-3 border-t ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign size={16} className="text-[#7163BA]" />
              <span className="text-xs font-medium text-gray-500">Net Benefit</span>
            </div>
            <span className={`text-lg font-bold ${netBenefit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {netBenefit >= 0 ? '+' : ''}${netBenefit.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* View Details Link */}
      {candidateId && (
        <div className={`mt-4 pt-3 border-t text-center ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
          <span className="text-xs font-medium text-[#7163BA]">
            Click to view candidate details
          </span>
        </div>
      )}
    </>
  );

  // Wrap in Link if we have a candidate ID
  if (candidateId) {
    return (
      <Link to={`/candidate/${candidateId}`} className={cardClasses}>
        <CardContent />
      </Link>
    );
  }

  return (
    <div className={cardClasses}>
      <CardContent />
    </div>
  );
}
