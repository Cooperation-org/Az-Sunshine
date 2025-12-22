import React from 'react';
import { DollarSign, Users, ExternalLink } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';

export default function RaceSummaryPanel({ raceData, topDonors }) {
  const { darkMode } = useDarkMode();

  // Calculate total IE spending (sum of all FOR and AGAINST spending)
  const totalIE = raceData?.candidates?.reduce(
    (sum, c) => {
      const ieFor = Math.abs(parseFloat(c.ie_for || 0));
      const ieAgainst = Math.abs(parseFloat(c.ie_against || 0));
      return sum + ieFor + ieAgainst;
    },
    0
  ) || 0;

  // Generate OpenSecrets link
  const getOpenSecretsLink = (donorName) => {
    const query = encodeURIComponent(donorName);
    return `https://www.opensecrets.org/search?q=${query}&type=donors`;
  };

  return (
    <div className={`p-6 rounded-2xl border ${
      darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
    }`}>
      <h3 className={`text-sm font-bold uppercase tracking-widest mb-6 ${
        darkMode ? 'text-gray-400' : 'text-gray-500'
      }`}>
        Race Summary
      </h3>

      {/* Total IE */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-[#7163BA]/10">
            <DollarSign size={20} className="text-[#7163BA]" />
          </div>
          <div>
            <p className="text-xs text-gray-500">Total IE Spending</p>
            <p className={`text-2xl font-bold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              ${totalIE.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Top IE Spenders / Donors */}
      <div className="mb-6">
        <h4 className="text-xs font-bold text-gray-500 mb-3 flex items-center gap-2">
          <Users size={14} />
          Top IE Donors
        </h4>
        <div className="space-y-2">
          {topDonors?.slice(0, 5).map((donor, idx) => {
            const donorName = donor.entity_name ||
                            `${donor.entity__first_name || ''} ${donor.entity__last_name || ''}`.trim();

            return (
              <a
                key={idx}
                href={getOpenSecretsLink(donorName)}
                target="_blank"
                rel="noopener noreferrer"
                className={`flex items-center justify-between p-2 rounded-lg transition-colors group ${
                  darkMode
                    ? 'hover:bg-[#1F1B31]'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-semibold truncate ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    {donorName}
                  </p>
                  <p className="text-xs text-gray-500">
                    {donor.entity_occupation || donor.occupation || 'Individual'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-bold text-[#7163BA]">
                    ${parseFloat(donor.total_contributed || 0).toLocaleString()}
                  </span>
                  <ExternalLink size={14} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {/* Help Text */}
      <div className={`p-3 rounded-lg ${
        darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
      }`}>
        <p className="text-xs text-gray-400">
          Click any donor to view their OpenSecrets profile and verify data.
        </p>
      </div>
    </div>
  );
}
