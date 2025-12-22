import React, { useState } from "react";
import Sidebar from '../components/Sidebar';
import { useDarkMode } from "../context/DarkModeContext";
import { 
  Upload, File, CheckCircle, XCircle, Database, 
  ShieldCheck, AlertTriangle, FileText, Info 
} from "lucide-react";

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
              Data <span style={{ color: '#A78BFA' }}>Import</span>
            </h1>
            <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/50 text-blue-400 text-[10px] font-bold uppercase tracking-widest rounded-full">
              CSV Loader
            </div>
          </div>
          <p className="text-white/70 text-sm max-w-xl">
            Manually upload campaign finance datasets. Supports Independent Expenditures and
            Statements of Interest with built-in duplicate detection and validation.
          </p>
        </div>
        <div className="hidden lg:block opacity-20">
          <Upload size={80} strokeWidth={1} />
        </div>
      </div>
    </div>
  );
};

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
    if (!file) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("source", source);
    formData.append("import_type", importType);
    formData.append("dry_run", dryRun);

    try {
      const response = await fetch("/api/import_data/", { method: "POST", body: formData });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ success: false, message: "An error occurred during import.", error: error.toString() });
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

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* --- CONFIGURATION COLUMN --- */}
            <div className="xl:col-span-2 space-y-6">
              <div className={`p-6 md:p-8 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} shadow-sm`}>
                <h3 className={`text-sm font-bold uppercase tracking-widest mb-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Import Parameters
                </h3>

                <div className="space-y-8">
                  {/* File Upload Zone */}
                  <div className="group relative">
                    <label className={`block text-xs font-bold uppercase tracking-widest mb-3 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Target Dataset (CSV)
                    </label>
                    <div className={`relative flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-2xl transition-all duration-200 ${
                      file 
                      ? 'border-green-500 bg-green-500/5' 
                      : (darkMode ? 'border-gray-700 bg-[#1F1B31] hover:border-[#7667C1]' : 'border-gray-200 bg-gray-50 hover:border-[#7667C1]')
                    }`}>
                      <input 
                        id="file-upload" 
                        type="file" 
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                        onChange={handleFileChange} 
                        accept=".csv"
                      />
                      <div className="text-center">
                        <div className={`inline-flex p-4 rounded-full mb-4 ${darkMode ? 'bg-gray-800' : 'bg-white shadow-sm'}`}>
                          {file ? <FileText className="text-green-500" size={32} /> : <Upload className="text-[#7667C1]" size={32} />}
                        </div>
                        <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          {file ? file.name : "Click to browse or drag and drop"}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">Maximum file size: 100MB</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Source ID */}
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase tracking-widest text-gray-500 flex items-center gap-2">
                        <Info size={14} /> Source Identifier
                      </label>
                      <input
                        type="text"
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        placeholder="e.g. 2024 General Election"
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm outline-none focus:ring-1 focus:ring-[#7667C1] ${
                          darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50 text-gray-900'
                        }`}
                      />
                    </div>

                    {/* Import Type */}
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase tracking-widest text-gray-500 flex items-center gap-2">
                        <Database size={14} /> Record Type
                      </label>
                      <select
                        value={importType}
                        onChange={(e) => setImportType(e.target.value)}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm outline-none focus:ring-1 focus:ring-[#7667C1] appearance-none ${
                          darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50 text-gray-900'
                        }`}
                      >
                        <option value="expenditures">Independent Expenditures</option>
                        <option value="soi">Statements of Interest</option>
                      </select>
                    </div>
                  </div>

                  {/* Dry Run Toggle */}
                  <div className={`p-4 rounded-xl border flex items-center justify-between ${
                    dryRun 
                    ? (darkMode ? 'bg-blue-500/5 border-blue-500/30' : 'bg-blue-50 border-blue-100')
                    : (darkMode ? 'bg-orange-500/5 border-orange-500/30' : 'bg-orange-50 border-orange-100')
                  }`}>
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${dryRun ? 'bg-blue-500/20 text-blue-400' : 'bg-orange-500/20 text-orange-400'}`}>
                        {dryRun ? <ShieldCheck size={18} /> : <AlertTriangle size={18} />}
                      </div>
                      <div>
                        <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          {dryRun ? "Dry Run Active" : "Live Import Mode"}
                        </p>
                        <p className="text-xs text-gray-500">Preview changes before writing to database</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => setDryRun(!dryRun)}
                      className={`w-12 h-6 rounded-full relative transition-colors ${dryRun ? 'bg-blue-500' : 'bg-orange-500'}`}
                    >
                      <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${dryRun ? 'left-7' : 'left-1'}`} />
                    </button>
                  </div>

                  <button
                    onClick={handleImport}
                    disabled={loading || !file}
                    className="w-full py-4 rounded-2xl bg-[#7667C1] hover:bg-[#6556b0] text-white font-bold flex items-center justify-center gap-3 transition-all shadow-lg shadow-purple-500/20 active:scale-95 disabled:opacity-50"
                  >
                    {loading ? <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" /> : <Upload size={20} />}
                    {loading ? "Processing Dataset..." : dryRun ? "Start Validation Sync" : "Commit Live Import"}
                  </button>
                </div>
              </div>
            </div>

            {/* --- STATUS/RESULTS COLUMN --- */}
            <div className="space-y-6">
              {result && (
                <div className={`p-6 rounded-2xl border animate-in fade-in slide-in-from-right-4 duration-500 ${
                  result.success 
                  ? (darkMode ? 'bg-[#2D2844] border-green-500/50' : 'bg-white border-green-200') 
                  : (darkMode ? 'bg-[#2D2844] border-red-500/50' : 'bg-white border-red-200')
                }`}>
                  <div className="flex items-center gap-3 mb-6">
                    {result.success ? <CheckCircle className="text-green-500" /> : <XCircle className="text-red-500" />}
                    <h3 className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {result.success ? "Import Results" : "Import Blocked"}
                    </h3>
                  </div>

                  {result.dry_run_summary && (
                    <div className="space-y-3 mb-6">
                      {[
                        { label: "New Records", val: result.dry_run_summary.new, color: "text-blue-400" },
                        { label: "Duplicates", val: result.dry_run_summary.duplicates, color: "text-orange-400" },
                        { label: "Total Rows", val: result.dry_run_summary.total, color: "text-gray-400" }
                      ].map((stat) => (
                        <div key={stat.label} className="flex justify-between items-center text-sm">
                          <span className="text-gray-500">{stat.label}</span>
                          <span className={`font-mono font-bold ${stat.color}`}>{stat.val}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <p className={`text-xs p-4 rounded-xl leading-relaxed ${darkMode ? 'bg-[#1F1B31] text-gray-400' : 'bg-gray-50 text-gray-600'}`}>
                    {result.message}
                  </p>
                </div>
              )}

              {!result && !loading && (
                <div className={`p-8 rounded-2xl border border-dashed border-gray-700 flex flex-col items-center text-center justify-center h-full min-h-[400px]`}>
                  <File className="text-gray-700 mb-4" size={48} />
                  <p className="text-gray-500 text-sm max-w-[200px]">
                    Waiting for CSV upload to begin validation session.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DataImport;