import React, { useState, useEffect, useMemo } from "react";
import { Play, RefreshCw, Settings, CheckCircle, AlertCircle, Clock, ExternalLink, AlertTriangle, Zap, X, Grid, List } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { useDarkMode } from "../context/DarkModeContext";

const N8N_URL = "http://167.172.30.134:5678";
const N8N_USER = "admin";
const N8N_PASS = "AZSunshine2024!";

const WorkflowCard = ({ workflow, onToggle, onEdit }) => {
  const { darkMode } = useDarkMode();
  const Icon = workflow.active ? Play : Play;
  const nodes = useMemo(() => Array.from({ length: Math.min(workflow.nodes?.length || 1, 10) }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
  })), [workflow.nodes]);

  return (
    <div className={`relative group border rounded-2xl p-6 overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${darkMode ? 'bg-[#3d3559] border-[#4a3f66] hover:border-purple-400/50' : 'bg-white border-gray-200 hover:border-purple-300'}`}>
      {/* SVG Background */}
      <div className="absolute inset-0 opacity-20 group-hover:opacity-40 transition-opacity duration-300">
        <svg width="100%" height="100%">
          {nodes.map((n, i) => (
            <React.Fragment key={i}>
              <circle cx={`${n.x}%`} cy={`${n.y}%`} r="2" fill={darkMode ? '#7163BA' : '#a78bfa'} className="opacity-50 group-hover:opacity-100" />
              {i > 0 && <line x1={`${nodes[i-1].x}%`} y1={`${nodes[i-1].y}%`} x2={`${n.x}%`} y2={`${n.y}%`} stroke={darkMode ? '#7163BA' : '#a78bfa'} strokeWidth="1" className="opacity-30 group-hover:opacity-60" />}
            </React.Fragment>
          ))}
        </svg>
      </div>

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex-1">
          <div className="flex items-start justify-between mb-3">
            <h3 className={`font-bold text-lg truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>{workflow.name}</h3>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0 ml-2 ${workflow.active ? (darkMode ? 'bg-green-500/20 text-green-300' : 'bg-green-100 text-green-800') : (darkMode ? 'bg-gray-500/20 text-gray-300' : 'bg-gray-100 text-gray-700')}`}>
              {workflow.active ? "Active" : "Inactive"}
            </span>
          </div>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {workflow.nodes?.length || 0} nodes • Updated {new Date(workflow.updatedAt).toLocaleDateString()}
          </p>
        </div>
        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={() => onToggle(workflow.id, !workflow.active)}
            className={`w-full text-sm font-semibold py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all ${workflow.active ? (darkMode ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30' : 'bg-red-100 text-red-700 hover:bg-red-200') : (darkMode ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30' : 'bg-[#7163BA] text-white hover:bg-[#5b509a]')}`}
          >
            <Icon className="w-4 h-4" />
            {workflow.active ? "Deactivate" : "Activate"}
          </button>
          <button
            onClick={() => window.open(`${N8N_URL}/workflow/${workflow.id}`, '_blank')}
            className={`p-2.5 rounded-lg transition-colors ${darkMode ? 'bg-white/5 text-gray-300 hover:bg-white/10' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};


const N8nModal = ({ onClose }) => (
  <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div className={`bg-[#2a2347] w-full h-full rounded-2xl border border-purple-500/20 shadow-2xl flex flex-col overflow-hidden`}>
      <div className="flex-shrink-0 p-4 border-b border-purple-500/20 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">n8n Workflow Editor</h3>
          <p className="text-sm text-gray-400">
            Running on <a href={N8N_URL} target="_blank" className="underline hover:text-purple-300">{N8N_URL}</a>
          </p>
        </div>
        <button onClick={onClose} className="p-2 rounded-full text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
          <X className="w-6 h-6" />
        </button>
      </div>
      <div className="flex-1 bg-gray-800 relative">
        <iframe
          src={N8N_URL}
          className="w-full h-full border-0"
          title="n8n Workflow Editor"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
        />
      </div>
    </div>
  </div>
);

export default function WorkflowAutomation() {
  const { darkMode } = useDarkMode();
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showN8nModal, setShowN8nModal] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  async function loadWorkflows() {
    setLoading(true);
    setApiError(null);
    try {
      const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
        headers: { 'Authorization': 'Basic ' + btoa(`${N8N_USER}:${N8N_PASS}`) }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to connect to n8n server.`);
      const data = await response.json();
      setWorkflows(data.data || []);
    } catch (err) {
      console.error("Error loading workflows:", err);
      setApiError(err.message);
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  }

  async function activateWorkflow(workflowId, active) {
    try {
      const response = await fetch(`${N8N_URL}/api/v1/workflows/${workflowId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': 'Basic ' + btoa(`${N8N_USER}:${N8N_PASS}`),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ active })
      });
      if (response.ok) loadWorkflows();
      else throw new Error(`Failed to ${active ? 'activate' : 'deactivate'}`);
    } catch (err) {
      console.error("Error toggling workflow:", err);
      alert(`Error: ${err.message}`);
    }
  }

  const stats = useMemo(() => ({
    total: workflows.length,
    active: workflows.filter(w => w.active).length,
    inactive: workflows.filter(w => !w.active).length,
  }), [workflows]);

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#2a2347]' : 'bg-gray-100'}`}>
      <Sidebar />
      {showN8nModal && <N8nModal onClose={() => setShowN8nModal(false)} />}
      
      <main className="flex-1 overflow-auto">
        
        <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-8">

          {/* Header Control Panel */}
          <div className={`relative rounded-2xl p-8 border overflow-hidden ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200'}`}>
            <div className="absolute -top-1/2 -right-1/4 w-96 h-96 bg-gradient-to-tr from-purple-600/30 to-purple-800/10 rounded-full blur-3xl opacity-50 animate-pulse"></div>
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row items-start justify-between gap-6">
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <div className={`p-3 rounded-xl ${darkMode ? 'bg-purple-500/20' : 'bg-purple-100'}`}>
                      <Zap className={`w-7 h-7 ${darkMode ? 'text-purple-300' : 'text-[#7163BA]'}`} />
                    </div>
                    <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Workflow Automation</h1>
                  </div>
                  <p className={`max-w-2xl ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Manage, execute, and monitor automated tasks for SOI scraping, candidate outreach, and data processing via n8n.
                  </p>
                </div>
                <div className="flex-shrink-0 flex items-center gap-3">
                  <button onClick={() => setShowN8nModal(true)} className={`px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 ${darkMode ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-white text-gray-800 hover:bg-gray-50 border'}`}>
                    <Grid className="w-5 h-5" /> Embed Editor
                  </button>
                  <button onClick={() => window.open(N8N_URL, '_blank')} className={`px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 ${darkMode ? 'bg-[#7163BA] text-white hover:bg-[#8b7cb8]' : 'bg-[#7163BA] text-white hover:bg-[#5b509a]'}`}>
                    <ExternalLink className="w-5 h-5" /> Open n8n
                  </button>
                </div>
              </div>
              <div className="mt-8 pt-6 border-t grid grid-cols-1 sm:grid-cols-3 gap-4 text-center md:text-left" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                {[
                  { title: "Total Workflows", value: stats.total, icon: Settings, color: darkMode ? 'text-purple-300' : 'text-purple-600' },
                  { title: "Active", value: stats.active, icon: CheckCircle, color: darkMode ? 'text-green-400' : 'text-green-600' },
                  { title: "Inactive", value: stats.inactive, icon: Clock, color: darkMode ? 'text-gray-400' : 'text-gray-600' }
                ].map(stat => (
                  <div key={stat.title} className="flex items-center justify-center md:justify-start gap-4">
                    <stat.icon className={`w-6 h-6 flex-shrink-0 ${stat.color}`} />
                    <div>
                      <p className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{loading ? '-' : stat.value}</p>
                      <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{stat.title}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {apiError && (
            <div className={`border rounded-lg p-4 flex items-start gap-4 ${darkMode ? 'bg-red-900/20 border-red-500/30' : 'bg-red-50 border-red-200'}`}>
              <AlertCircle className={`w-6 h-6 flex-shrink-0 mt-0.5 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
              <div>
                <h3 className={`font-semibold ${darkMode ? 'text-red-300' : 'text-red-900'}`}>Cannot Connect to n8n</h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-red-400' : 'text-red-700'}`}>{apiError}</p>
                <button onClick={loadWorkflows} className={`mt-3 text-sm font-semibold py-2 px-4 rounded-lg transition flex items-center gap-2 ${darkMode ? 'bg-red-500/20 text-red-300 hover:bg-red-500/30' : 'bg-red-100 text-red-700 hover:bg-red-200'}`}>
                  <RefreshCw className="w-4 h-4" /> Retry
                </button>
              </div>
            </div>
          )}
          
          <div>
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Workflows</h3>
              <button onClick={loadWorkflows} disabled={loading} className={`flex items-center gap-2 text-sm font-medium transition disabled:opacity-50 ${darkMode ? 'text-purple-300 hover:text-purple-200' : 'text-[#7163BA] hover:text-[#5b509a]'}`}>
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </button>
            </div>
            
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({length: 3}).map((_, i) => (
                  <div key={i} className={`rounded-2xl p-6 h-48 animate-pulse ${darkMode ? 'bg-[#3d3559]' : 'bg-gray-200'}`}></div>
                ))}
              </div>
            ) : workflows.length === 0 && !apiError ? (
              <div className={`text-center py-20 rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>
                <Settings className={`w-12 h-12 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
                <h3 className={`text-lg font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>No workflows found</h3>
                <p className={`mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Create your first workflow in the n8n editor.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {workflows.map((workflow) => (
                  <WorkflowCard key={workflow.id} workflow={workflow} onToggle={activateWorkflow} />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
