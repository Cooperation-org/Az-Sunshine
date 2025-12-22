import React from 'react';
import { Calendar, TrendingUp, TrendingDown } from 'lucide-react';
import { useDarkMode } from '../../context/DarkModeContext';

export default function AdBuyCard({ adBuy }) {
  const { darkMode } = useDarkMode();

  const platformIcons = {
    tv: '📺',
    radio: '📻',
    digital: '💻',
    print: '📰',
    mail: '✉️',
    billboard: '🪧',
    other: '📢'
  };

  const supportColor = adBuy.support_oppose === 'support' ? 'text-green-500' : 'text-red-500';
  const SupportIcon = adBuy.support_oppose === 'support' ? TrendingUp : TrendingDown;

  return (
    <div className={`rounded-xl border overflow-hidden ${
      darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
    }`}>
      {/* Image */}
      {adBuy.image_url && (
        <div className="aspect-video bg-gray-900 relative group">
          <img
            src={adBuy.image_url}
            alt="Ad buy screenshot"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <a
              href={adBuy.image_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-white text-gray-900 rounded-lg text-sm font-medium"
            >
              View Full Size
            </a>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{platformIcons[adBuy.platform] || '📢'}</span>
            <div>
              <p className={`text-sm font-bold ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {adBuy.paid_for_by}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Calendar size={12} className="text-gray-500" />
                <span className="text-xs text-gray-500">
                  {new Date(adBuy.ad_date).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <SupportIcon size={16} className={supportColor} />
            <span className={`text-xs font-bold ${supportColor}`}>
              {adBuy.support_oppose.toUpperCase()}
            </span>
          </div>
        </div>

        {adBuy.approximate_spend && (
          <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Est. Spend: <span className="font-mono font-bold">${parseFloat(adBuy.approximate_spend).toLocaleString()}</span>
          </div>
        )}

        {adBuy.url && (
          <div className="mt-2">
            <a
              href={adBuy.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-[#7163BA] hover:underline truncate block"
            >
              {adBuy.url}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
