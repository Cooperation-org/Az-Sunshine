import React, { useState, useEffect } from 'react';
import { AlertTriangle, ExternalLink, DollarSign, Calendar, Building2 } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';
import { getDarkMoneyDisclosures } from '../../api/api';

export default function DarkMoneyDisclosurePanel({ officeId, electionYear }) {
  const { darkMode } = useDarkMode();
  const [disclosures, setDisclosures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDisclosures() {
      if (!officeId || !electionYear) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await getDarkMoneyDisclosures({
          office_id: officeId,
          election_year: electionYear
        });
        setDisclosures(data?.disclosures || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch dark money disclosures:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDisclosures();
  }, [officeId, electionYear]);

  // Don't render if no disclosures
  if (!loading && disclosures.length === 0) {
    return null;
  }

  if (loading) {
    return (
      <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'} animate-pulse`}>
        <div className="h-6 bg-gray-300 rounded w-1/3 mb-4"></div>
        <div className="h-20 bg-gray-300 rounded"></div>
      </div>
    );
  }

  if (error) {
    return null; // Silently fail - don't show errors for optional data
  }

  const totalAmount = disclosures.reduce((sum, d) => sum + d.amount, 0);

  return (
    <div className={`p-5 rounded-xl border-2 border-amber-500/50 ${darkMode ? 'bg-amber-900/20' : 'bg-amber-50'}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-amber-500/20">
          <AlertTriangle className="text-amber-500" size={24} />
        </div>
        <div>
          <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Dark Money Disclosure
          </h3>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Retroactive funding source revelations for this race
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className={`p-4 rounded-lg mb-4 ${darkMode ? 'bg-[#1A1625]' : 'bg-white'}`}>
        <div className="flex items-center justify-between">
          <span className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Total Disclosed Dark Money
          </span>
          <span className="text-2xl font-bold text-amber-500">
            ${Math.abs(totalAmount).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Disclosure List */}
      <div className="space-y-3">
        {disclosures.map((disclosure) => (
          <div
            key={disclosure.id}
            className={`p-4 rounded-lg ${darkMode ? 'bg-[#1A1625]' : 'bg-white'}`}
          >
            {/* Funding Source */}
            <div className="flex items-start gap-3 mb-3">
              <Building2 className="text-amber-500 mt-1" size={18} />
              <div className="flex-1">
                <p className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {disclosure.funding_source}
                </p>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Funded: {disclosure.ie_committee?.name || 'Unknown IE Committee'}
                </p>
              </div>
              <span className="text-lg font-bold text-amber-500">
                ${Math.abs(disclosure.amount).toLocaleString()}
              </span>
            </div>

            {/* Target Candidates */}
            {disclosure.target_candidates && (
              <div className={`text-sm mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                <span className="font-medium">Target: </span>
                {disclosure.target_candidates}
                {disclosure.is_for_benefit !== null && (
                  <span className={disclosure.is_for_benefit ? 'text-green-500' : 'text-red-500'}>
                    {' '}({disclosure.is_for_benefit ? 'Support' : 'Oppose'})
                  </span>
                )}
              </div>
            )}

            {/* Disclosure Info */}
            <div className="flex items-center gap-4 text-xs">
              <div className={`flex items-center gap-1 ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                <Calendar size={12} />
                <span>Disclosed: {disclosure.disclosure_date}</span>
              </div>
              {disclosure.source_url && (
                <a
                  href={disclosure.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[#7163BA] hover:underline"
                >
                  <ExternalLink size={12} />
                  <span>Source</span>
                </a>
              )}
            </div>

            {/* Disclosure Source */}
            {disclosure.disclosure_source && (
              <p className={`text-xs mt-2 italic ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                {disclosure.disclosure_source}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Warning Footer */}
      <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-amber-500/30' : 'border-amber-200'}`}>
        <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
          This spending was originally undisclosed "dark money" at the time of the election.
          The funding sources were later revealed through lawsuits, investigations, or voluntary disclosures.
        </p>
      </div>
    </div>
  );
}
