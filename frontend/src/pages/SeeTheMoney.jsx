import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import { seeTheMoneyAPI, handleAdminError } from '../api/admin';
import { 
  Download, Database, Calendar, Monitor, 
  CheckCircle2, AlertCircle, Loader2, Sparkles, ExternalLink 
} from 'lucide-react';

// --- REFINED BANNER ---
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
              SeeTheMoney<span style={{ color: '#A78BFA' }}>.az.gov</span>
            </h1>
            <div className="px-3 py-1 bg-green-500/20 border border-green-500/50 text-green-400 text-[10px] font-bold uppercase tracking-widest rounded-full animate-pulse">
              Free Access
            </div>
          </div>
          <p className="text-white/70 text-sm max-w-xl">
            Direct synchronization with Arizona's public transparency portal. Download and import
            comprehensive campaign finance datasets into your local database.
          </p>
        </div>
        <div className="flex-shrink-0">
          <a
            href="https://seethemoney.az.gov"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-xs font-bold text-purple-300 hover:text-white transition-colors"
          >
            Visit Source Portal <ExternalLink size={14} />
          </a>
        </div>
      </div>
    </div>
  );
};

export default function SeeTheMoney() {
  const { darkMode } = useDarkMode();
  const [year, setYear] = useState(new Date().getFullYear());
  const [entityType, setEntityType] = useState('Candidate');
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
      let response = operation === 'sync' 
        ? await seeTheMoneyAPI.sync(yearValue, entityType, headless)
        : await seeTheMoneyAPI.download(yearValue, entityType, headless);
      setResult(response);
    } catch (err) {
      const errorData = handleAdminError(err);
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  const entityTypes = [
    { value: 'Candidate', label: 'Candidates', icon: Sparkles },
    { value: 'PAC', label: 'PACs', icon: Database },
    { value: 'Party', label: 'Parties', icon: Monitor },
    { value: 'All', label: 'All Entities', icon: Download },
  ];

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner />

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* --- CONFIGURATION COLUMN --- */}
            <div className="xl:col-span-2 space-y-6">
              <div className={`p-6 md:p-8 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} shadow-sm`}>
                <h3 className={`text-sm font-bold uppercase tracking-widest mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Sync Configuration
                </h3>

                <div className="space-y-8">
                  {/* Operation Toggle */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { id: 'sync', label: 'Sync & Import', sub: 'Update database automatically', icon: Database },
                      { id: 'download', label: 'Download Only', sub: 'Get CSV files to storage', icon: Download }
                    ].map((op) => (
                      <button
                        key={op.id}
                        onClick={() => setOperation(op.id)}
                        className={`p-5 rounded-2xl border text-left transition-all relative overflow-hidden group ${
                          operation === op.id 
                          ? (darkMode ? 'bg-purple-500/10 border-purple-500' : 'bg-purple-50 border-[#7667C1]')
                          : (darkMode ? 'bg-[#1F1B31] border-gray-700 hover:border-gray-500' : 'bg-gray-50 border-gray-200')
                        }`}
                      >
                        <op.icon size={20} className={operation === op.id ? 'text-[#7667C1]' : 'text-gray-500'} />
                        <p className={`font-bold mt-3 ${darkMode && operation === op.id ? 'text-white' : 'text-gray-900'}`}>{op.label}</p>
                        <p className="text-xs text-gray-500 mt-1">{op.sub}</p>
                      </button>
                    ))}
                  </div>

                  {/* Entity Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {entityTypes.map((type) => (
                      <button
                        key={type.value}
                        onClick={() => setEntityType(type.value)}
                        className={`py-3 px-4 rounded-xl text-xs font-bold transition-all border ${
                          entityType === type.value
                          ? 'bg-[#7667C1] border-[#7667C1] text-white shadow-lg'
                          : (darkMode ? 'bg-[#1F1B31] border-gray-700 text-gray-400 hover:text-gray-200' : 'bg-white border-gray-200 text-gray-600')
                        }`}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Year Input */}
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase tracking-widest text-gray-500 flex items-center gap-2">
                        <Calendar size={14} /> Fiscal Year
                      </label>
                      <input
                        type="number"
                        value={year}
                        onChange={(e) => setYear(parseInt(e.target.value) || '')}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm outline-none focus:ring-1 focus:ring-[#7667C1] ${
                          darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50 text-gray-900'
                        }`}
                      />
                    </div>

                    {/* Headless Toggle */}
                    <div className="space-y-2">
                       <label className="text-xs font-bold uppercase tracking-widest text-gray-500 flex items-center gap-2">
                        <Monitor size={14} /> Display Mode
                      </label>
                      <button 
                        onClick={() => setHeadless(!headless)}
                        className={`w-full px-4 py-3 rounded-xl text-left text-sm transition-all ${
                          darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={darkMode ? 'text-white' : 'text-gray-900'}>{headless ? "Background (Headless)" : "Interactive (Browser)"}</span>
                          <div className={`w-10 h-5 rounded-full relative transition-colors ${headless ? 'bg-green-500' : 'bg-gray-400'}`}>
                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${headless ? 'left-6' : 'left-1'}`} />
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={handleExecute}
                    disabled={loading}
                    className="w-full py-4 rounded-2xl bg-[#7667C1] hover:bg-[#6556b0] text-white font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-purple-500/20 active:scale-95 disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : <Database size={20} />}
                    {loading ? "Initializing Browser Session..." : "Execute Synchronization"}
                  </button>
                </div>
              </div>
            </div>

            {/* --- STATUS/OUTPUT COLUMN --- */}
            <div className="space-y-6">
              {result && (
                <div className={`p-6 rounded-2xl border animate-in fade-in slide-in-from-right-4 duration-500 ${
                  darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
                }`}>
                  <div className="flex items-center gap-3 mb-4">
                    <CheckCircle2 className="text-green-500" size={20} />
                    <h3 className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Execution Output</h3>
                  </div>
                  <div className={`p-4 rounded-xl font-mono text-[10px] leading-relaxed max-h-96 overflow-y-auto ${
                    darkMode ? 'bg-[#1F1B31] text-purple-200' : 'bg-gray-900 text-gray-300'
                  }`}>
                    <pre className="whitespace-pre-wrap">{result.output || result.message}</pre>
                  </div>
                </div>
              )}

              {error && (
                <div className={`p-6 rounded-2xl border border-red-500/50 bg-red-500/5 animate-in shake duration-300`}>
                  <div className="flex items-center gap-3 mb-2 text-red-500">
                    <AlertCircle size={20} />
                    <h3 className="font-bold">System Error</h3>
                  </div>
                  <p className="text-sm text-red-400 leading-relaxed">{error}</p>
                </div>
              )}

              {!result && !error && !loading && (
                <div className={`p-8 rounded-2xl border border-dashed border-gray-700 flex flex-col items-center text-center justify-center h-full min-h-[300px]`}>
                  <Monitor size={40} className="text-gray-700 mb-4" />
                  <p className="text-gray-500 text-sm">Ready for session. Select your parameters and execute the sync.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}