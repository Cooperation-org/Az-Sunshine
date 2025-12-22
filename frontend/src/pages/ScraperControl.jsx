import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import { scraperAPI, handleAdminError } from '../api/admin';
import { 
  Cpu, Activity, History, Settings2, 
  MapPin, Globe, Play, Terminal 
} from 'lucide-react';

const COUNTIES = [
  { value: 'maricopa', label: 'Maricopa County', description: 'Phoenix area - largest county', icon: '🌵' },
  { value: 'pima', label: 'Pima County', description: 'Tucson area - second largest', icon: '☀️' },
  { value: 'tucson', label: 'City of Tucson', description: 'City elections and candidates', icon: '🌵' },
  { value: 'all', label: 'All Jurisdictions', description: 'Run all scrapers sequentially', icon: '⚡' },
];

// --- SPECIALIZED SCRAPER BANNER ---
const Banner = () => {
  const { darkMode } = useDarkMode();
  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              County <span style={{ color: '#A78BFA' }}>Scrapers</span>
            </h1>
            <div className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 text-[10px] font-bold uppercase tracking-widest rounded-full flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              Engine Ready
            </div>
          </div>
          <p className="text-white/70 text-sm max-w-xl">
            Automated extraction engine for election data. Configure headless browser sessions
            to pull the latest campaign finance filings from specific Arizona jurisdictions.
          </p>
        </div>
        <div className="hidden lg:block opacity-20">
          <Cpu size={80} strokeWidth={1} />
        </div>
      </div>
    </div>
  );
};

export default function ScraperControl() {
  const { darkMode } = useDarkMode();
  const [selectedCounty, setSelectedCounty] = useState('maricopa');
  const [year, setYear] = useState(new Date().getFullYear());
  const [headless, setHeadless] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRunScraper = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await scraperAPI.runScraper(selectedCounty, year, headless);
      setResult(response);
    } catch (err) {
      const errorData = handleAdminError(err);
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner />

          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            {/* --- CONFIGURATION PANEL (7 COLS) --- */}
            <div className="xl:col-span-7 space-y-6">
              <div className={`p-6 md:p-8 rounded-2xl border transition-all ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100 shadow-sm'
              }`}>
                <div className="flex items-center justify-between mb-8">
                  <h3 className={`text-xs font-bold uppercase tracking-widest ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Jurisdiction Selection
                  </h3>
                  <div className={`p-2 rounded-lg ${darkMode ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500'}`}>
                    <MapPin size={16} />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {COUNTIES.map((county) => (
                    <button
                      key={county.value}
                      onClick={() => setSelectedCounty(county.value)}
                      className={`relative overflow-hidden group p-5 rounded-2xl border-2 text-left transition-all duration-300 ${
                        selectedCounty === county.value
                          ? (darkMode ? 'bg-purple-500/10 border-[#7667C1] ring-1 ring-[#7667C1]' : 'bg-purple-50 border-[#7163BA]')
                          : (darkMode ? 'bg-[#1F1B31] border-transparent hover:border-gray-600' : 'bg-gray-50 border-transparent hover:border-gray-200')
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-2xl">{county.icon}</span>
                        {selectedCounty === county.value && (
                          <div className="h-2 w-2 rounded-full bg-[#7667C1] animate-ping" />
                        )}
                      </div>
                      <p className={`font-bold text-sm ${selectedCounty === county.value ? (darkMode ? 'text-white' : 'text-[#5b4fa8]') : (darkMode ? 'text-gray-300' : 'text-gray-700')}`}>
                        {county.label}
                      </p>
                      <p className="text-[11px] leading-relaxed text-gray-500 mt-1 uppercase tracking-tighter">
                        {county.description}
                      </p>
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-10">
                  {/* Year Input */}
                  <div className="space-y-3">
                    <label className={`text-xs font-bold uppercase tracking-widest flex items-center gap-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      <History size={14} /> Election Year
                    </label>
                    <input
                      type="number"
                      value={year}
                      onChange={(e) => setYear(parseInt(e.target.value))}
                      className={`w-full px-4 py-3 rounded-xl border-none text-sm outline-none focus:ring-1 focus:ring-[#7667C1] ${
                        darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50 text-gray-900 shadow-inner'
                      }`}
                    />
                  </div>

                  {/* Browser Mode */}
                  <div className="space-y-3">
                    <label className={`text-xs font-bold uppercase tracking-widest flex items-center gap-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      <Settings2 size={14} /> Execution Mode
                    </label>
                    <div 
                      onClick={() => setHeadless(!headless)}
                      className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors ${
                        darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                      }`}
                    >
                      <span className="text-xs text-gray-500">{headless ? 'Headless (Background)' : 'GUI Mode (Visible)'}</span>
                      <div className={`w-10 h-5 rounded-full relative transition-colors ${headless ? 'bg-emerald-500' : 'bg-gray-600'}`}>
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all ${headless ? 'left-5.5' : 'left-0.5'}`} />
                      </div>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleRunScraper}
                  disabled={loading}
                  className="w-full mt-10 py-4 rounded-2xl bg-[#7667C1] hover:bg-[#6556b0] text-white font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-purple-500/20 active:scale-[0.98] disabled:opacity-50"
                >
                  {loading ? (
                    <Activity className="animate-spin" size={20} />
                  ) : (
                    <Play size={18} fill="currentColor" />
                  )}
                  {loading ? "Initializing Automation..." : "Execute Scraper Session"}
                </button>
              </div>
            </div>

            {/* --- CONSOLE / STATUS PANEL (5 COLS) --- */}
            <div className="xl:col-span-5 space-y-6">
              <div className={`h-full flex flex-col p-6 rounded-2xl border ${
                darkMode ? 'bg-[#1F1B31] border-gray-700' : 'bg-white border-gray-100 shadow-sm'
              }`}>
                <div className="flex items-center gap-2 mb-6 text-xs font-bold uppercase tracking-widest text-gray-500">
                  <Terminal size={14} /> Session Console
                </div>

                <div className={`flex-1 min-h-[400px] rounded-xl p-4 font-mono text-[11px] leading-relaxed overflow-y-auto ${
                  darkMode ? 'bg-[#0F0D16] text-emerald-400/80' : 'bg-gray-900 text-emerald-400'
                }`}>
                  {loading && (
                    <div className="flex flex-col gap-1">
                      <p className="text-gray-500">[{new Date().toLocaleTimeString()}] Establishing proxy connection...</p>
                      <p className="text-gray-500">[{new Date().toLocaleTimeString()}] Launching Chromium instance...</p>
                      <p className="animate-pulse">[{new Date().toLocaleTimeString()}] Navigating to {selectedCounty} portal...</p>
                    </div>
                  )}
                  
                  {result && (
                    <div className="space-y-2">
                      <p className="text-emerald-500 font-bold border-b border-emerald-900/50 pb-1 mb-2">SESSION SUCCESSFUL</p>
                      <pre className="whitespace-pre-wrap">{result.output || result.message}</pre>
                    </div>
                  )}

                  {error && (
                    <div className="text-red-400">
                      <p className="font-bold">CRITICAL_ENGINE_FAILURE:</p>
                      <p>{error}</p>
                    </div>
                  )}

                  {!loading && !result && !error && (
                    <div className="h-full flex flex-col items-center justify-center opacity-20 italic">
                      <Globe size={40} className="mb-4" />
                      <p>Idle. Awaiting command...</p>
                    </div>
                  )}
                </div>

                {result && (
                  <div className="mt-4 flex items-center gap-2">
                    <div className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-500 text-[10px] font-bold">
                      200 OK
                    </div>
                    <span className="text-[10px] text-gray-500 uppercase tracking-widest">
                      Runtime: {result.execution_time || '2.4s'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}