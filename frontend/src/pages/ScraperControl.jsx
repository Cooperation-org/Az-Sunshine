import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';

import { useDarkMode } from '../context/DarkModeContext';
import { scraperAPI, handleAdminError } from '../api/admin';
import { Cpu } from 'lucide-react';

const COUNTIES = [
  { value: 'maricopa', label: 'Maricopa County', description: 'Phoenix area - largest county' },
  { value: 'pima', label: 'Pima County', description: 'Tucson area - second largest' },
  { value: 'tucson', label: 'City of Tucson', description: 'City elections and candidates' },
  { value: 'all', label: 'All Jurisdictions', description: 'Run all scrapers sequentially' },
];

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
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        
        <div className="p-4 md:p-8">
          <header className="mb-8">
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>County Scrapers</h1>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
              Scrape candidate and campaign finance data from county election websites.
            </p>
          </header>

          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm max-w-5xl mx-auto`}>
            <div className="mb-8 text-center">
              <h3 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Scraper Configuration</h3>
              <p className={`text-sm mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                Select a jurisdiction and configure scraping parameters.
              </p>
            </div>

            <div className="space-y-8">
              {/* County Selection */}
              <div>
                <label className={`block text-sm font-medium mb-3 text-center ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  Select Jurisdiction
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {COUNTIES.map((county) => (
                    <button
                      key={county.value}
                      onClick={() => setSelectedCounty(county.value)}
                      className={`p-4 rounded-xl border text-left transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1
                        ${selectedCounty === county.value
                          ? darkMode
                            ? 'bg-gradient-to-r from-[#7d6fa3] to-[#8b7cb8] border-[#8b7cb8] text-white shadow-xl'
                            : 'bg-gradient-to-r from-[#7163BA] to-[#8b5cf6] border-[#8b5cf6] text-white shadow-xl'
                          : darkMode
                            ? 'bg-[#4a3f66] border-[#5f5482] text-gray-200 hover:bg-[#5f5482]'
                            : 'bg-white border-gray-200 text-gray-900 hover:bg-gray-50'
                        }`}
                    >
                      <p className="font-semibold">{county.label}</p>
                      <p className={`text-sm mt-1 ${selectedCounty === county.value ? 'text-white/80' : darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        {county.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                {/* Year Input */}
                <div>
                  <label htmlFor="year-input" className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    Year
                  </label>
                  <input
                    id="year-input"
                    type="number"
                    value={year}
                    onChange={(e) => setYear(parseInt(e.target.value))}
                    min="2020"
                    max="2030"
                    className={`w-full px-4 py-2 rounded-lg border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500
                      ${darkMode
                        ? 'bg-[#2c2646] border-gray-600 text-white'
                        : 'bg-white border-gray-300 text-gray-900'
                      }`}
                  />
                </div>

                {/* Headless Option */}
                <div className="flex items-center">
                  <label htmlFor="headless-toggle" className="inline-flex relative items-center cursor-pointer">
                    <input type="checkbox" id="headless-toggle" className="sr-only peer" checked={headless} onChange={() => setHeadless(!headless)} />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#7163BA]"></div>
                    <span className={`ml-3 text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      Headless Mode
                    </span>
                  </label>
                </div>
              </div>

              {/* Run Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={handleRunScraper}
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
                      Scraping...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Cpu className="w-5 h-5" />
                      Run Scraper
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
                  {result.status === 'completed' ? '✓ Scraping Completed' : '⏳ Scraping Status'}
                </h3>
                <p className={`text-sm mt-0.5 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                  {result.county} - {result.year || 'Current year'}
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
                  <h4 className="font-semibold text-red-500">Scraper Failed</h4>
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