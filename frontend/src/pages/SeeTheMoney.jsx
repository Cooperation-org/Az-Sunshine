/**
 * SeeTheMoney.az.gov FREE Data Portal
 * Download and import campaign finance data from Arizona's FREE public portal
 */

import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';

import { useDarkMode } from '../context/DarkModeContext';
import { seeTheMoneyAPI, handleAdminError } from '../api/admin';

export default function SeeTheMoney() {
  const { darkMode } = useDarkMode();
  const [year, setYear] = useState(new Date().getFullYear());
  const [entityType, setEntityType] = useState('Candidate');
  const [headless, setHeadless] = useState(true);
  const [operation, setOperation] = useState('sync'); // 'download' or 'sync'
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const yearValue = year || null;

      let response;
      if (operation === 'sync') {
        response = await seeTheMoneyAPI.sync(yearValue, entityType, headless);
      } else {
        response = await seeTheMoneyAPI.download(yearValue, entityType, headless);
      }

      setResult(response);
    } catch (err) {
      const errorData = handleAdminError(err);
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  const entityTypes = [
    { value: 'Candidate', label: 'Candidates', description: 'Campaign finance data for political candidates' },
    { value: 'PAC', label: 'PACs', description: 'Political Action Committee data' },
    { value: 'Party', label: 'Parties', description: 'Political party committee data' },
    { value: 'All', label: 'All Entities', description: 'Complete dataset (Candidates + PACs + Parties)' },
  ];

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 overflow-auto">
        

        <div className="px-8 py-8 space-y-8">
          {/* Header */}
          <div>
            <div className="flex items-center gap-3">
              <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                SeeTheMoney.az.gov
              </h1>
              <span className="px-3 py-1 bg-green-500 text-white text-sm font-bold rounded-full shadow-lg animate-pulse">
                FREE!
              </span>
            </div>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-200' : 'text-gray-500'}`}>
              Download FREE campaign finance data from Arizona's public transparency portal
            </p>
          </div>


          {/* Configuration Card */}
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm max-w-5xl mx-auto`}>
            <div className="mb-8 text-center">
              <h3 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Download Configuration</h3>
              <p className={`text-sm mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                Configure download parameters for campaign finance data
              </p>
            </div>

            <div className="space-y-6">
              {/* Operation Type */}
              <div>
                <label className={`block text-sm font-medium mb-3 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  Operation
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <button
                    onClick={() => setOperation('sync')}
                    className={`p-4 rounded-lg border text-left transition-all duration-200 hover:shadow-md
                      ${operation === 'sync'
                        ? darkMode
                          ? 'bg-[#7d6fa3] border-[#8b7cb8] text-white shadow-lg'
                          : 'bg-[#7163BA] border-[#7163BA] text-white shadow-lg'
                        : darkMode
                          ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                          : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
                      }`}
                  >
                    <p className="font-semibold">Download & Import</p>
                    <p className={`text-sm mt-1 ${operation === 'sync' ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Download CSV and import to database
                    </p>
                  </button>

                  <button
                    onClick={() => setOperation('download')}
                    className={`p-4 rounded-lg border text-left transition-all duration-200 hover:shadow-md
                      ${operation === 'download'
                        ? darkMode
                          ? 'bg-[#7d6fa3] border-[#8b7cb8] text-white shadow-lg'
                          : 'bg-[#7163BA] border-[#7163BA] text-white shadow-lg'
                        : darkMode
                          ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                          : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
                      }`}
                  >
                    <p className="font-semibold">Download Only</p>
                    <p className={`text-sm mt-1 ${operation === 'download' ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Download CSV without importing
                    </p>
                  </button>
                </div>
              </div>

              {/* Entity Type Selection */}
              <div>
                <label className={`block text-sm font-medium mb-3 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  Entity Type
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {entityTypes.map((entity) => (
                    <button
                      key={entity.value}
                      onClick={() => setEntityType(entity.value)}
                      className={`p-4 rounded-lg border text-left transition-all duration-200 hover:shadow-md
                        ${entityType === entity.value
                          ? darkMode
                            ? 'bg-[#7d6fa3] border-[#8b7cb8] text-white shadow-lg'
                            : 'bg-[#7163BA] border-[#7163BA] text-white shadow-lg'
                          : darkMode
                            ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                            : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
                        }`}
                    >
                      <p className="font-semibold">{entity.label}</p>
                      <p className={`text-sm mt-1 ${entityType === entity.value ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {entity.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Year Input */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  Year
                </label>
                <input
                  type="number"
                  value={year}
                  onChange={(e) => setYear(parseInt(e.target.value) || '')}
                  placeholder="Leave empty for current year"
                  min="2002"
                  max={new Date().getFullYear() + 2}
                  className={`w-full px-4 py-2 rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500
                    ${darkMode
                      ? 'bg-[#4a3f66] border-[#5f5482] text-white placeholder-gray-400'
                      : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'
                    }`}
                />
                <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Available years: 2002 to {new Date().getFullYear() + 2}
                </p>
              </div>

              {/* Headless Option */}
              <div className={`flex items-start gap-3 p-4 rounded-lg ${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'}`}>
                <input
                  type="checkbox"
                  id="headless-stm"
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded"
                  style={{ accentColor: darkMode ? '#8b7cb8' : '#7163BA' }}
                />
                <div className="flex-1">
                  <label htmlFor="headless-stm" className={`text-sm font-medium cursor-pointer block ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    Headless Mode
                  </label>
                  <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Run browser in background (recommended). Disable to see browser UI during download.
                  </p>
                </div>
              </div>

              {/* Execute Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={handleExecute}
                  disabled={loading}
                  className={`px-8 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95
                    ${darkMode ? 'bg-gradient-to-r from-[#7d6fa3] to-[#8b7cb8] hover:from-[#8b7cb8] hover:to-[#9a8bc7] text-white' : 'bg-gradient-to-r from-[#7163BA] to-[#8b5cf6] hover:from-[#5b4fa8] hover:to-[#7d4fd4] text-white'}`}
                >
                  {loading ? (
                    <div className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      {operation === 'sync' ? 'Download & Import Data' : 'Download Data Only'}
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Results Card */}
          {result && (
            <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-300`}>
              <div className="mb-6">
                <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {result.status === 'completed' ? '✓ Operation Completed' : '⏳ Operation Status'}
                </h3>
                <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                  {result.year && `Year: ${result.year}`}
                  {result.entity_type && ` | ${result.entity_type}`}
                </p>
              </div>

              <div className="space-y-3">
                <div className={`p-3 rounded-lg font-mono text-sm overflow-x-auto max-h-96 overflow-y-auto ${darkMode ? 'bg-[#4a3f66] text-gray-300' : 'bg-gray-50 text-gray-700'}`}>
                  <pre>{result.output || result.message}</pre>
                </div>

                {result.status === 'completed' && (
                  <div className="flex items-center gap-2 text-sm text-green-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>
                      {operation === 'sync'
                        ? 'FREE data downloaded and imported successfully!'
                        : 'FREE data downloaded to backend/data/seethemoney_downloads/'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Card */}
          {error && (
            <div className={`${darkMode ? 'bg-red-900/20 border-red-500/50' : 'bg-red-50 border-red-200'} rounded-2xl p-8 border shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-300`}>
              <div className="flex items-start gap-3">
                <div className="text-red-500 text-xl">✕</div>
                <div>
                  <p className="font-medium text-red-500">
                    Operation Failed
                  </p>
                  <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
