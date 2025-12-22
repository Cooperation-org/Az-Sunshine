import React from 'react';
import { RefreshCw } from 'lucide-react';
import { useDarkMode } from '../context/DarkModeContext';

const ArizonaSunshineBanner = ({ onRefresh, refreshing = false }) => {
  const { darkMode } = useDarkMode();

  return (
    <div
      className="relative rounded-3xl overflow-hidden mb-8 w-full flex flex-col md:flex-row items-center shadow-2xl border min-h-[200px] md:h-[30vh]"
      style={darkMode
        ? { borderColor: 'rgba(113, 99, 186, 0.2)', background: '#1A1625' }
        : { borderColor: 'rgba(113, 99, 186, 0.2)', background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >

      {/* Background: Subtle glow using brand #7163BA */}
      <div
        className="absolute top-[-50%] left-[-10%] w-[70%] h-[200%] blur-[120px] rounded-full pointer-events-none opacity-20"
        style={{ backgroundColor: '#7163BA' }}
      />

      {/* LEFT: Branding & Content */}
      <div className="relative z-10 w-full md:w-2/3 px-6 md:pl-12 py-8 md:py-0 flex flex-col justify-center">
        <div className="space-y-3 md:space-y-4">
          <div className="flex items-center gap-3">
            {/* Pulsing Dot */}
            <span
              className="w-2.5 h-2.5 rounded-full animate-pulse"
              style={{ backgroundColor: darkMode ? '#7b037c' : '#A21CAF' }}
            />
            <span
              className="text-[10px] md:text-[11px] font-bold text-white/60 uppercase tracking-wider md:tracking-[0.5em]"
            >
              Live Intelligence
            </span>
          </div>

          <h1
            className="text-2xl md:text-3xl lg:text-4xl font-light text-white tracking-tight"
            style={{ lineHeight: '1.1' }}
          >
            Political<span className="font-bold" style={{ color: darkMode ? '#7163BA' : '#A78BFA' }}> Accountability</span> Tracker
          </h1>

          <p
            className="text-xs md:text-sm font-medium max-w-lg leading-relaxed text-white/70"
          >
            Aggregating independent expenditures to correlate spending with legislative actions.
          </p>
        </div>
      </div>

      {/* RIGHT: Action Button */}
      <div className="relative w-full md:w-1/3 h-auto md:h-full flex items-center justify-start md:justify-end px-6 md:pr-16 pb-8 md:pb-0">
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 md:gap-3 px-6 md:px-8 py-3 md:py-3.5 rounded-full text-white text-xs md:text-sm font-bold transition-all active:scale-95 shadow-xl shadow-[#7163BA]/20 hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ backgroundColor: '#7163BA' }}
        >
          <RefreshCw className={`w-3.5 h-3.5 md:w-4 md:h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="tracking-wide md:tracking-wider">{refreshing ? 'Syncing...' : 'Sync Data'}</span>
        </button>
      </div>

    </div>
  );
};

export default ArizonaSunshineBanner;