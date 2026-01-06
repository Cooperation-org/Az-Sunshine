// frontend/src/components/race/IEAdBuyCorrelation.jsx
import React, { useState, useEffect } from 'react';
import { useDarkMode } from '../../context/DarkModeContext';
import { getAdBuys, getRaceIESpending } from '../../api/api';
import { TrendingUp, Image, Calendar, DollarSign, Tv, Radio, Smartphone, Mail, Loader, AlertTriangle } from 'lucide-react';

// Platform icon mapping
const PlatformIcon = ({ platform }) => {
  const icons = {
    'tv': Tv,
    'television': Tv,
    'radio': Radio,
    'digital': Smartphone,
    'mail': Mail,
    'print': Image,
  };
  const IconComponent = icons[platform?.toLowerCase()] || Image;
  return <IconComponent size={14} />;
};

export default function IEAdBuyCorrelation({ officeId, cycleId, candidateId }) {
  const { darkMode } = useDarkMode();
  const [adBuys, setAdBuys] = useState([]);
  const [ieData, setIEData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (officeId && cycleId) {
      loadData();
    }
  }, [officeId, cycleId, candidateId]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [adBuysData, ieSpending] = await Promise.all([
        getAdBuys({ office_id: officeId, verified: true }),
        getRaceIESpending({ office_id: officeId, cycle_id: cycleId })
      ]);

      setAdBuys(adBuysData.results || adBuysData || []);
      setIEData(ieSpending);
    } catch (err) {
      console.error('Error loading correlation data:', err);
      setError('Failed to load correlation data');
    } finally {
      setLoading(false);
    }
  }

  // Group ad buys by month for timeline
  const groupAdsByMonth = (ads) => {
    const grouped = {};
    ads.forEach(ad => {
      if (ad.ad_date) {
        const monthKey = ad.ad_date.substring(0, 7); // YYYY-MM
        if (!grouped[monthKey]) {
          grouped[monthKey] = { ads: [], totalSpend: 0, platforms: new Set() };
        }
        grouped[monthKey].ads.push(ad);
        grouped[monthKey].totalSpend += parseFloat(ad.approximate_spend || 0);
        if (ad.platform) grouped[monthKey].platforms.add(ad.platform);
      }
    });
    return grouped;
  };

  // Calculate correlation metrics
  const calculateCorrelation = () => {
    if (!ieData || !adBuys.length) return null;

    const totalIE = ieData.summary?.total_ie || 0;
    const totalAdSpend = adBuys.reduce((sum, ad) => sum + parseFloat(ad.approximate_spend || 0), 0);
    const adCount = adBuys.length;

    // Count ads by support/oppose
    const supportAds = adBuys.filter(ad => ad.support_oppose === 'support' || ad.support_oppose === true).length;
    const opposeAds = adBuys.filter(ad => ad.support_oppose === 'oppose' || ad.support_oppose === false).length;

    // Platform breakdown
    const platformBreakdown = {};
    adBuys.forEach(ad => {
      const platform = ad.platform || 'Unknown';
      if (!platformBreakdown[platform]) {
        platformBreakdown[platform] = { count: 0, spend: 0 };
      }
      platformBreakdown[platform].count++;
      platformBreakdown[platform].spend += parseFloat(ad.approximate_spend || 0);
    });

    return {
      totalIE,
      totalAdSpend,
      adCount,
      supportAds,
      opposeAds,
      platformBreakdown,
      adToIERatio: totalIE > 0 ? (totalAdSpend / totalIE * 100).toFixed(1) : 0,
    };
  };

  const correlation = calculateCorrelation();
  const groupedAds = groupAdsByMonth(adBuys);
  const sortedMonths = Object.keys(groupedAds).sort();

  if (loading) {
    return (
      <div className={`rounded-2xl p-8 flex items-center justify-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
        <Loader className="animate-spin text-purple-500" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-2xl p-8 flex flex-col items-center justify-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
        <AlertTriangle className="text-red-500 mb-2" size={32} />
        <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>{error}</p>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
      {/* Header */}
      <div className={`p-6 border-b ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${darkMode ? 'bg-purple-900/30' : 'bg-purple-100'}`}>
            <TrendingUp className={darkMode ? 'text-purple-400' : 'text-purple-600'} size={20} />
          </div>
          <div>
            <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              IE Spending & Ad Buy Correlation
            </h3>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Track how independent expenditures translate to actual advertisements
            </p>
          </div>
        </div>
      </div>

      {/* Correlation Summary Cards */}
      {correlation && (
        <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
            <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Total IE Spending
            </div>
            <div className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              ${correlation.totalIE.toLocaleString()}
            </div>
          </div>

          <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
            <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Tracked Ad Spend
            </div>
            <div className={`text-xl font-bold ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
              ${correlation.totalAdSpend.toLocaleString()}
            </div>
          </div>

          <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
            <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Ads Tracked
            </div>
            <div className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {correlation.adCount}
            </div>
            <div className="flex gap-2 mt-1">
              <span className="text-xs text-green-500">{correlation.supportAds} support</span>
              <span className="text-xs text-red-500">{correlation.opposeAds} oppose</span>
            </div>
          </div>

          <div className={`p-4 rounded-xl ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
            <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Coverage Rate
            </div>
            <div className={`text-xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
              {correlation.adToIERatio}%
            </div>
            <div className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              of IE tracked in ads
            </div>
          </div>
        </div>
      )}

      {/* Platform Breakdown */}
      {correlation && Object.keys(correlation.platformBreakdown).length > 0 && (
        <div className={`px-6 pb-6 border-b ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
          <h4 className={`text-sm font-bold uppercase tracking-wider mb-3 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Platform Breakdown
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(correlation.platformBreakdown).map(([platform, data]) => (
              <div
                key={platform}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                  darkMode ? 'bg-[#1F1B31]' : 'bg-gray-100'
                }`}
              >
                <PlatformIcon platform={platform} />
                <span className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {platform}
                </span>
                <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  ({data.count}) ${data.spend.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="p-6">
        <h4 className={`text-sm font-bold uppercase tracking-wider mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          Ad Activity Timeline
        </h4>

        {sortedMonths.length > 0 ? (
          <div className="space-y-3">
            {sortedMonths.map(month => {
              const monthData = groupedAds[month];
              const monthDate = new Date(month + '-01');
              const monthName = monthDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

              return (
                <div
                  key={month}
                  className={`flex items-center gap-4 p-3 rounded-lg ${
                    darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                  }`}
                >
                  <div className={`flex items-center gap-2 min-w-[100px] ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    <Calendar size={14} />
                    <span className="text-sm font-medium">{monthName}</span>
                  </div>

                  <div className="flex-1">
                    <div className={`h-2 rounded-full ${darkMode ? 'bg-[#2D2844]' : 'bg-gray-200'}`}>
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-purple-700"
                        style={{
                          width: `${Math.min((monthData.ads.length / Math.max(...Object.values(groupedAds).map(g => g.ads.length))) * 100, 100)}%`
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-4 min-w-[150px] justify-end">
                    <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {monthData.ads.length} ads
                    </span>
                    <span className={`text-sm font-bold ${darkMode ? 'text-purple-300' : 'text-purple-600'}`}>
                      ${monthData.totalSpend.toLocaleString()}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            <Image size={48} className="mx-auto mb-3 opacity-50" />
            <p>No verified ad buys tracked yet for this race.</p>
            <p className="text-sm mt-1">Report ads you see to help track campaign spending!</p>
          </div>
        )}
      </div>
    </div>
  );
}
