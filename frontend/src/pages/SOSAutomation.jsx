import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import { sosAPI, handleAdminError } from '../api/admin';
import { 
  Download, Database, Calendar, Monitor, 
  CheckCircle2, AlertCircle, Server,
  Terminal, ShieldCheck, ChevronRight, Activity
} from 'lucide-react';

// --- SOS SPECIALIZED BANNER ---
const Banner = () => {
  const { darkMode } = useDarkMode();
  return (
    <div
      className="w-full rounded-3xl p-8 md:p-12 mb-10 transition-all duration-500 relative overflow-hidden text-white"
      style={darkMode
        ? { background: '#2D2844', borderColor: 'rgba(255, 255, 255, 0.05)' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      {/* Background Graphic - Resized and repositioned for visibility */}
      <div className="absolute top-0 right-0 opacity-10 pointer-events-none translate-x-4 translate-y-4">
        <Server size={180} strokeWidth={0.5} className="text-white" />
      </div>

      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-8 relative z-10">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
              AZ SOS <span style={{ color: '#A78BFA' }}>Automation</span>
            </h1>
            <span className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
              <ShieldCheck size={12} className="text-blue-400" />
              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Official Source</span>
            </span>
          </div>
          <p className="text-white/70 text-sm max-w-lg leading-relaxed">
            Direct integration with the Arizona Secretary of State campaign finance database.
            Automate the retrieval and indexing of statewide filing records and committee reports.
          </p>
        </div>
      </div>
    </div>
  );
};

export default function SOSAutomation() {
  const { darkMode } = useDarkMode();
  const [year, setYear] = useState(new Date().getFullYear());
  const [quarter, setQuarter] = useState('');
  const [headless, setHeadless] = useState(true);
  const [operation, setOperation] = useState('sync'); 
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const yearValue = year || null;
      const quarterValue = quarter ? parseInt(quarter) : null;

      let response = operation === 'sync'
        ? await sosAPI.sync(yearValue, quarterValue, headless)
        : await sosAPI.download(yearValue, quarterValue, false, headless);

      setResult(response);
    } catch (err) {
      const errorData = handleAdminError(err);
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#14111D]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 min-w-0">
        <div className="p-6 md:p-10">
          <Banner />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {/* Configuration Panel */}
            <div className="lg:col-span-7 space-y-8">
              <div className={`p-8 rounded-3xl border transition-all ${
                darkMode ? 'bg-[#1C1829] border-white/5' : 'bg-white border-gray-100 shadow-xl shadow-gray-200/50'
              }`}>
                <header className="flex items-center justify-between mb-10">
                  <h3 className={`text-xs font-bold uppercase tracking-widest ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Task Parameters
                  </h3>
                  <div className={`p-2.5 rounded-xl ${darkMode ? 'bg-gray-800 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
                    <Server size={18} />
                  </div>
                </header>

                <div className="space-y-8">
                  {/* Operation Toggle Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    {[
                      { id: 'sync', title: 'Sync & Index', sub: 'Download + DB Import', icon: Database },
                      { id: 'download', title: 'Archival Only', sub: 'CSV Download Only', icon: Download }
                    ].map((op) => (
                      <button
                        key={op.id}
                        onClick={() => setOperation(op.id)}
                        className={`group p-6 rounded-2xl border-2 transition-all duration-300 text-left ${
                          operation === op.id
                            ? (darkMode ? 'bg-purple-600/10 border-purple-500 shadow-lg shadow-purple-900/10' : 'bg-purple-50 border-[#7163BA]')
                            : (darkMode ? 'bg-[#252033] border-transparent hover:border-gray-700' : 'bg-gray-50 border-transparent hover:border-gray-200')
                        }`}
                      >
                        <div className={`p-3 w-fit rounded-xl mb-4 transition-colors ${
                          operation === op.id ? 'bg-purple-500 text-white' : (darkMode ? 'bg-gray-800 text-gray-500' : 'bg-white text-gray-400 shadow-sm')
                        }`}>
                          <op.icon size={20} />
                        </div>
                        <p className={`font-bold text-sm ${operation === op.id ? (darkMode ? 'text-white' : 'text-[#5b4fa8]') : (darkMode ? 'text-gray-300' : 'text-gray-700')}`}>
                          {op.title}
                        </p>
                        <p className="text-[10px] text-gray-500 uppercase tracking-tighter mt-1">{op.sub}</p>
                      </button>
                    ))}
                  </div>

                  {/* Year/Quarter Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
                    <div className="space-y-3">
                      <label className={`text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Calendar size={14} /> Fiscal Year
                      </label>
                      <input
                        type="number"
                        value={year}
                        onChange={(e) => setYear(parseInt(e.target.value) || '')}
                        className={`w-full px-5 py-3.5 rounded-xl text-sm outline-none transition-all ${
                          darkMode ? 'bg-[#14111D] text-white focus:ring-1 focus:ring-purple-500' : 'bg-gray-100 text-gray-900 focus:ring-1 focus:ring-purple-600 shadow-inner'
                        }`}
                        placeholder="Current Cycle"
                      />
                    </div>

                    <div className="space-y-3">
                      <label className={`text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                        <ChevronRight size={14} /> Filing Quarter
                      </label>
                      <div className="relative">
                        <select
                          value={quarter}
                          onChange={(e) => setQuarter(e.target.value)}
                          className={`w-full px-5 py-3.5 rounded-xl text-sm outline-none transition-all appearance-none ${
                            darkMode ? 'bg-[#14111D] text-white focus:ring-1 focus:ring-purple-500' : 'bg-gray-100 text-gray-900 focus:ring-1 focus:ring-purple-600 shadow-inner'
                          }`}
                        >
                          <option value="">Consolidated (All)</option>
                          <option value="1">Q1 (Jan 1 - Mar 31)</option>
                          <option value="2">Q2 (Apr 1 - Jun 30)</option>
                          <option value="3">Q3 (Jul 1 - Sep 30)</option>
                          <option value="4">Q4 (Oct 1 - Dec 31)</option>
                        </select>
                        <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-gray-500 pointer-events-none" size={14} />
                      </div>
                    </div>
                  </div>

                  {/* Browser Mode Toggle */}
                  <div className={`p-4 rounded-2xl border flex items-center justify-between ${
                    darkMode ? 'bg-[#14111D] border-white/5' : 'bg-gray-50 border-gray-100'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${darkMode ? 'bg-gray-800 text-purple-400' : 'bg-white text-purple-600 shadow-sm'}`}>
                        <Monitor size={18} />
                      </div>
                      <div>
                        <p className={`text-xs font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Execution Environment</p>
                        <p className="text-[10px] text-gray-500 italic">Headless mode is recommended for stability</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => setHeadless(!headless)}
                      className={`w-10 h-5 rounded-full relative transition-colors ${headless ? 'bg-emerald-500' : 'bg-gray-600'}`}
                    >
                      <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${headless ? 'left-6' : 'left-1'}`} />
                    </button>
                  </div>

                  <button
                    onClick={handleExecute}
                    disabled={loading}
                    className="w-full py-5 rounded-2xl bg-[#7163BA] hover:bg-[#5b4fa8] text-white font-bold text-sm flex items-center justify-center gap-3 transition-all active:scale-[0.98] disabled:opacity-50 shadow-lg shadow-purple-500/20"
                  >
                    {loading ? <Activity className="animate-spin" size={18} /> : <Download size={18} />}
                    {loading ? "COMMUNICATING WITH SOS PORTAL..." : "EXECUTE AUTOMATION SEQUENCE"}
                  </button>
                </div>
              </div>
            </div>

            {/* Console Output (5 COLS) */}
            <div className="lg:col-span-5 flex flex-col h-full">
              <div className={`flex-1 min-h-[500px] flex flex-col p-8 rounded-3xl border ${
                darkMode ? 'bg-[#1C1829] border-white/5' : 'bg-white border-gray-100 shadow-sm'
              }`}>
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    <Terminal size={14} /> Session Console
                  </div>
                  {result && <span className="animate-pulse flex items-center gap-1.5 text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded">LIVE_FEED</span>}
                </div>

                <div className={`flex-1 rounded-2xl p-6 font-mono text-[11px] leading-relaxed overflow-y-auto ${
                  darkMode ? 'bg-[#0F0D16] text-blue-400/80' : 'bg-gray-900 text-blue-300'
                }`}>
                  {loading && (
                    <div className="space-y-1 opacity-80">
                      <p className="text-gray-500">[{new Date().toLocaleTimeString()}] Handshake: SOS_STATE_API</p>
                      <p className="text-gray-500">[{new Date().toLocaleTimeString()}] Auth: Session authenticated</p>
                      <p className="animate-pulse text-purple-400">[{new Date().toLocaleTimeString()}] Buffering CSV stream for {year}...</p>
                    </div>
                  )}
                  
                  {result && <pre className="whitespace-pre-wrap">{result.output || result.message}</pre>}

                  {error && (
                    <div className="flex items-start gap-2 text-red-400">
                      <AlertCircle size={14} className="mt-0.5 shrink-0" />
                      <div>
                        <p className="font-bold mb-1 underline">GATEWAY_TIMEOUT_OR_FAILURE</p>
                        <p className="opacity-80">{error}</p>
                      </div>
                    </div>
                  )}

                  {!loading && !result && !error && (
                    <div className="h-full flex flex-col items-center justify-center opacity-10">
                      <Activity size={48} className="mb-4" />
                      <p className="text-sm font-bold tracking-tighter uppercase">Waiting for Command</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}