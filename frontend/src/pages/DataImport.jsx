import React, { useState } from "react";
import Sidebar from '../components/Sidebar';

import { useDarkMode } from "../context/DarkModeContext";
import { Upload, File, CheckCircle, XCircle } from "lucide-react";

const DataImport = () => {
  const [file, setFile] = useState(null);
  const [source, setSource] = useState("");
  const [importType, setImportType] = useState("expenditures");
  const [dryRun, setDryRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const { darkMode } = useDarkMode();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
  };

  const handleImport = async () => {
    if (!file) {
      alert("Please select a file to import.");
      return;
    }
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source", source);
    formData.append("import_type", importType);
    formData.append("dry_run", dryRun);

    try {
      const response = await fetch("/api/import_data/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error importing data:", error);
      setResult({ success: false, message: "An error occurred during import.", error: error.toString() });
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
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Data Import</h1>
            <p className={`text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
              Upload and import campaign finance data directly into the database.
            </p>
          </header>

          {/* Configuration Card */}
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-8 border shadow-sm max-w-5xl mx-auto`}>
            <div className="mb-8 text-center">
              <h3 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Import Configuration</h3>
              <p className={`text-sm mt-2 ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                Select a file and set the import parameters.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
              {/* Left Column: File Upload & Options */}
              <div className="space-y-6">
                {/* File Upload */}
                <div>
                  <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Upload CSV File
                  </label>
                  <div className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 ${darkMode ? 'border-gray-600' : 'border-gray-300'} border-dashed rounded-md`}>
                    <div className="space-y-1 text-center">
                      <File className={`mx-auto h-12 w-12 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
                      <div className="flex text-sm text-gray-600">
                        <label
                          htmlFor="file-upload"
                          className={`relative cursor-pointer rounded-md font-medium ${darkMode ? 'text-[#8b7cb8] hover:text-[#a092d6]' : 'text-[#7163BA] hover:text-[#5b4fa8]'} focus-within:outline-none`}
                        >
                          <span>Upload a file</span>
                          <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".csv"/>
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                        {file ? file.name : 'CSV up to 100MB'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Data Source */}
                <div>
                  <label htmlFor="source" className={`block text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Data Source Identifier
                  </label>
                  <input
                    type="text"
                    id="source"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 border ${darkMode ? 'bg-[#2c2646] border-gray-600 text-white' : 'bg-white border-gray-300'} rounded-md shadow-sm focus:outline-none focus:ring-[#7163BA] focus:border-[#7163BA] sm:text-sm`}
                    placeholder="e.g., 'Maricopa County Q1 2024'"
                  />
                </div>
              </div>

              {/* Right Column: Import Type & Mode */}
              <div className="space-y-6">
                {/* Import Type */}
                <div>
                  <label htmlFor="importType" className={`block text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Import Type
                  </label>
                  <select
                    id="importType"
                    value={importType}
                    onChange={(e) => setImportType(e.target.value)}
                    className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border ${darkMode ? 'bg-[#2c2646] border-gray-600 text-white' : 'bg-white border-gray-300'} focus:outline-none focus:ring-[#7163BA] focus:border-[#7163BA] sm:text-sm rounded-md`}
                  >
                    <option value="expenditures">Independent Expenditures</option>
                    <option value="soi">Statements of Interest</option>
                  </select>
                </div>

                {/* Dry Run Toggle */}
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Dry Run Mode
                    <p className={`text-xs font-normal ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Preview changes without saving</p>
                  </span>
                  <label htmlFor="dry-run-toggle" className="inline-flex relative items-center cursor-pointer">
                    <input type="checkbox" id="dry-run-toggle" className="sr-only peer" checked={dryRun} onChange={() => setDryRun(!dryRun)} />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#7163BA]"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Execute Button */}
            <div className="flex justify-center pt-8">
              <button
                onClick={handleImport}
                disabled={loading || !file}
                className={`px-8 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95
                  ${darkMode ? 'bg-gradient-to-r from-[#7d6fa3] to-[#8b7cb8] hover:from-[#8b7cb8] hover:to-[#9a8bc7] text-white' : 'bg-gradient-to-r from-[#7163BA] to-[#8b5cf6] hover:from-[#5b4fa8] hover:to-[#7d4fd4] text-white'}`}
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Importing...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    {dryRun ? 'Run Dry Run Import' : 'Execute Live Import'}
                  </div>
                )}
              </button>
            </div>
          </div>

          {/* Result Display */}
          {result && (
            <div className={`mt-8 p-6 rounded-2xl border ${result.success ? (darkMode ? 'bg-green-900/20 border-green-500/50' : 'bg-green-50 border-green-200') : (darkMode ? 'bg-red-900/20 border-red-500/50' : 'bg-red-50 border-red-200')} shadow-sm`}>
              <div className="flex items-start gap-4">
                {result.success ? (
                  <CheckCircle className={`h-6 w-6 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
                ) : (
                  <XCircle className={`h-6 w-6 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                )}
                <div>
                  <h4 className={`text-lg font-semibold ${result.success ? (darkMode ? 'text-green-300' : 'text-green-800') : (darkMode ? 'text-red-300' : 'text-red-800')}`}>
                    Import {result.success ? 'Successful' : 'Failed'}
                  </h4>
                  <p className={`mt-1 text-sm ${result.success ? (darkMode ? 'text-green-400' : 'text-green-700') : (darkMode ? 'text-red-400' : 'text-red-700')}`}>
                    {result.message}
                  </p>
                  {result.dry_run_summary && (
                    <div className={`mt-4 text-sm p-4 rounded-lg ${darkMode ? 'bg-[#2c2646]' : 'bg-white'}`}>
                      <h5 className="font-bold mb-2">Dry Run Summary:</h5>
                      <p>New Records: <span className="font-mono">{result.dry_run_summary.new}</span></p>
                      <p>Duplicates Found: <span className="font-mono">{result.dry_run_summary.duplicates}</span></p>
                      <p>Total Rows: <span className="font-mono">{result.dry_run_summary.total}</span></p>
                    </div>
                  )}
                  {result.error && (
                    <pre className={`mt-2 text-xs p-3 rounded ${darkMode ? 'bg-[#2c2646]' : 'bg-gray-100'} overflow-x-auto`}>
                      {result.error}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DataImport;
