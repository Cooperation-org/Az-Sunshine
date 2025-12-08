/**
 * AZ Secretary of State Automation
 * Download and import campaign finance database from AZ SOS
 */

import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { useDarkMode } from '../context/DarkModeContext';
import { sosAPI, handleAdminError } from '../api/admin';
import { Download, CheckCircle, XCircle } from 'lucide-react';

export default function SOSAutomation() {
  const { darkMode } = useDarkMode();
  const [year, setYear] = useState(new Date().getFullYear());
  const [quarter, setQuarter] = useState('');
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
      const quarterValue = quarter ? parseInt(quarter) : null;

      let response;
      if (operation === 'sync') {
        response = await sosAPI.sync(yearValue, quarterValue, headless);
      } else {
        response = await sosAPI.download(yearValue, quarterValue, false, headless);
      }

      setResult(response);
    } catch (err) {
      const errorData = handleAdminError(err);
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <Header />

        <div className="p-4 md:p-8">
          {/* Header */}
          <header className="mb-8">
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              AZ SOS Automation
            </h1>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-200' : 'text-gray-500'}`}>
              Download and import campaign finance data from Arizona Secretary of State
            </p>
          </header>

          {/* Configuration Card */}
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm max-w-5xl mx-auto`}>
            <div className="mb-8 text-center">
              <h3 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Configuration</h3>
              <p className={`text-sm mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                Configure download and import parameters for AZ SOS data.
              </p>
            </div>

            <div className="space-y-8">
              {/* Operation Type */}
              <div>
                <label className={`block text-sm font-medium mb-3 text-center ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  Select Operation
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setOperation('sync')}
                    className={`p-4 rounded-xl border text-left transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1
                      ${operation === 'sync'
                        ? darkMode
                          ? 'bg-gradient-to-r from-[#7d6fa3] to-[#8b7cb8] border-[#8b7cb8] text-white shadow-xl'
                          : 'bg-gradient-to-r from-[#7163BA] to-[#8b5cf6] border-[#8b5cf6] text-white shadow-xl'
                        : darkMode
                          ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                          : 'bg-white border-gray-200 text-gray-900 hover:bg-gray-50'
                      }`}
                  >
                    <p className="font-semibold">Download & Import</p>
                    <p className={`text-sm mt-1 ${operation === 'sync' ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Download CSV and import to database
                    </p>
                  </button>

                  <button
                    onClick={() => setOperation('download')}
                    className={`p-4 rounded-xl border text-left transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1
                      ${operation === 'download'
                        ? darkMode
                          ? 'bg-gradient-to-r from-[#7d6fa3] to-[#8b7cb8] border-[#8b7cb8] text-white shadow-xl'
                          : 'bg-gradient-to-r from-[#7163BA] to-[#8b5cf6] border-[#8b5cf6] text-white shadow-xl'
                        : darkMode
                          ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                          : 'bg-white border-gray-200 text-gray-900 hover:bg-gray-50'
                      }`}
                  >
                    <p className="font-semibold">Download Only</p>
                    <p className={`text-sm mt-1 ${operation === 'download' ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Download CSV without importing
                    </p>
                  </button>
                </div>
              </div>

              {/* Year and Quarter */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                <div>
                  <label htmlFor="year-input" className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    Year (optional)
                  </label>
                  <input
                    id="year-input"
                    type="number"
                    value={year}
                    onChange={(e) => setYear(parseInt(e.target.value) || '')}
                    placeholder="Leave empty for all"
                    min="2020"
                    max="2030"
                    className={`w-full px-4 py-2 rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500
                      ${darkMode
                        ? 'bg-[#2c2646] border-gray-600 text-white placeholder-gray-400'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'
                      }`}
                  />
                </div>

                <div>
                  <label htmlFor="quarter-select" className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    Quarter (optional)
                  </label>
                  <select
                    id="quarter-select"
                    value={quarter}
                    onChange={(e) => setQuarter(e.target.value)}
                    className={`w-full px-4 py-2 rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500
                      ${darkMode
                        ? 'bg-[#2c2646] border-gray-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                      }`}
                  >
                    <option value="">All Quarters</option>
                    <option value="1">Q1 (Jan-Mar)</option>
                    <option value="2">Q2 (Apr-Jun)</option>
                    <option value="3">Q3 (Jul-Sep)</option>
                    <option value="4">Q4 (Oct-Dec)</option>
                  </select>
                </div>
              </div>

              {/* Headless Option */}
              <div className="flex items-center">
                  <label htmlFor="headless-toggle-sos" className="inline-flex relative items-center cursor-pointer">
                    <input type="checkbox" id="headless-toggle-sos" className="sr-only peer" checked={headless} onChange={() => setHeadless(!headless)} />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#7163BA]"></div>
                    <span className={`ml-3 text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      Headless Mode
                      <p className={`text-xs font-normal ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Run browser in background. Disable if CAPTCHA or payment is required.</p>
                    </span>
                  </label>
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
                      <Download className="w-5 h-5" />
                      {operation === 'sync' ? 'Download & Import Data' : 'Download Data Only'}
                    </div>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Results Card */}
          {result && (
            <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-300 mt-8 max-w-5xl mx-auto`}>
              <div className="mb-6">
                <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {result.status === 'completed' ? '✓ Operation Completed' : '⏳ Operation Status'}
                </h3>
                <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                  {result.year && `Year: ${result.year}`}
                  {result.quarter && ` Q${result.quarter}`}
                </p>
              </div>

              <div className={`p-4 rounded-lg font-mono text-sm overflow-x-auto max-h-96 ${darkMode ? 'bg-[#2c2646] text-gray-300' : 'bg-gray-100 text-gray-800'}`}>
                <pre>{result.output || result.message}</pre>
              </div>
            </div>
          )}

          {/* Error Card */}
          {error && (
            <div className={`${darkMode ? 'bg-red-900/20 border-red-500/50' : 'bg-red-50 border-red-200'} rounded-2xl p-6 border shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-300 mt-8 max-w-5xl mx-auto`}>
              <div className="flex items-start gap-4">
                <div className="text-red-500 text-xl mt-1">✕</div>
                <div>
                  <h4 className="font-semibold text-red-500">Operation Failed</h4>
                  <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Warning Card */}
          <div className={`${darkMode ? 'bg-yellow-900/20 border-yellow-500/50' : 'bg-yellow-50 border-yellow-200'} rounded-2xl p-8 border shadow-sm mt-8 max-w-5xl mx-auto`}>
            <div className="flex items-start gap-3">
              <div className="text-yellow-500 text-xl">⚠</div>
              <div>
                <h4 className={`font-semibold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  Important Information
                </h4>
                <ul className={`space-y-1 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  <li>• Requires AZ SOS credentials in environment variables (AZ_SOS_USERNAME, AZ_SOS_PASSWORD)</li>
                  <li>• Database purchase costs $25 - payment info must be on file with AZ SOS</li>
                  <li>• Process may take several minutes depending on data size</li>
                  <li>• If CAPTCHA appears, disable headless mode and solve manually</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}