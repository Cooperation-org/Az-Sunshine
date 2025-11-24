import React, { useState, useEffect } from "react";
import { Play, RefreshCw, Settings, CheckCircle, AlertCircle, Clock, ExternalLink, AlertTriangle } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function WorkflowAutomation() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showN8n, setShowN8n] = useState(false);
  const [apiError, setApiError] = useState(null);

  // n8n server URL - using IP address
  const N8N_URL = "http://167.172.30.134/n8n";
  const N8N_USER = "admin";
  const N8N_PASS = "AZSunshine2024!";

  useEffect(() => {
    loadWorkflows();
  }, []);

  async function loadWorkflows() {
    try {
      setApiError(null);
      const response = await fetch(`${N8N_URL}/api/v1/workflows`, {
        headers: {
          'Authorization': 'Basic ' + btoa(`${N8N_USER}:${N8N_PASS}`)
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
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
      
      if (response.ok) {
        alert(`Workflow ${active ? 'activated' : 'deactivated'} successfully!`);
        loadWorkflows();
      } else {
        throw new Error(`Failed to ${active ? 'activate' : 'deactivate'} workflow`);
      }
    } catch (err) {
      console.error("Error toggling workflow:", err);
      alert(`Failed to toggle workflow: ${err.message}`);
    }
  }

  function openN8nExternal() {
    window.open(N8N_URL, '_blank', 'noopener,noreferrer');
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <main className="flex-1 lg:ml-0 min-w-0">
        <Header title="Arizona Sunshine" subtitle="Workflow Automation" />

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Info Banner - HTTP Warning */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">
              <p className="font-medium text-amber-900 mb-1">Development Mode (HTTP)</p>
              <p className="text-amber-700">
                Currently running over HTTP (no SSL). Browser warnings are expected. 
                For production, consider setting up a domain name and HTTPS.
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gradient-to-r from-[#6B5B95] to-[#4C3D7D] rounded-2xl shadow-xl overflow-hidden mb-6">
            <div className="p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                    <Settings className="w-6 h-6 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white">Workflow Manager</h2>
                </div>
                <p className="text-purple-100 text-sm">
                  Automate SOI scraping, candidate emails, and data processing
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowN8n(!showN8n)}
                  className="bg-white text-purple-700 px-6 py-3 rounded-xl text-base font-semibold hover:bg-purple-50 transition-all shadow-lg flex items-center gap-2"
                >
                  <Settings className="w-5 h-5" />
                  {showN8n ? "Hide" : "Embed"} Editor
                </button>
                <button
                  onClick={openN8nExternal}
                  className="bg-purple-800 text-white px-6 py-3 rounded-xl text-base font-semibold hover:bg-purple-900 transition-all shadow-lg flex items-center gap-2"
                >
                  <ExternalLink className="w-5 h-5" />
                  Open in New Tab
                </button>
              </div>
            </div>
          </div>

          {/* Connection Error Alert */}
          {apiError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900 mb-1">Cannot Connect to n8n</h3>
                  <p className="text-sm text-red-700 mb-2">{apiError}</p>
                  <p className="text-sm text-red-600 mb-3">
                    Make sure n8n is running: <code className="bg-red-100 px-2 py-1 rounded">docker ps | grep n8n</code>
                  </p>
                  <button
                    onClick={loadWorkflows}
                    className="text-sm bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Retry Connection
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Embedded n8n Editor */}
          {showN8n && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6">
              <div className="border-b border-gray-200 p-4 flex items-center justify-between bg-gray-50">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">n8n Workflow Editor</h3>
                  <p className="text-sm text-gray-600">
                    Running on <code className="bg-gray-200 px-2 py-0.5 rounded text-xs">http://167.172.30.134:5678</code>
                  </p>
                </div>
                <button
                  onClick={() => setShowN8n(false)}
                  className="text-gray-500 hover:text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-100 transition"
                >
                  Close
                </button>
              </div>
              <div className="relative">
                <iframe
                  src={N8N_URL}
                  className="w-full h-[800px] border-0"
                  title="n8n Workflow Editor"
                  sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
                />
                {/* Browser may block iframe - show warning */}
                <div className="absolute inset-0 bg-gray-900/5 pointer-events-none flex items-center justify-center">
                  <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-4 max-w-md text-center pointer-events-auto hidden" id="iframe-blocked">
                    <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
                    <h4 className="font-semibold text-gray-900 mb-2">Iframe Blocked?</h4>
                    <p className="text-sm text-gray-600 mb-3">
                      If the editor doesn't load, your browser may be blocking the iframe.
                    </p>
                    <button
                      onClick={openN8nExternal}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition"
                    >
                      Open in New Tab Instead
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Active Workflows */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900">Active Workflows</h3>
              <button
                onClick={loadWorkflows}
                disabled={loading}
                className="flex items-center gap-2 text-purple-600 hover:text-purple-700 font-medium text-sm transition disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
            
            {loading ? (
              <div className="text-center py-12">
                <RefreshCw className="w-12 h-12 text-purple-600 mx-auto mb-4 animate-spin" />
                <p className="text-gray-600">Loading workflows...</p>
              </div>
            ) : workflows.length === 0 ? (
              <div className="text-center py-12">
                <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">No workflows configured yet</p>
                <p className="text-sm text-gray-500 mb-4">Create your first workflow to automate tasks</p>
                <button
                  onClick={openN8nExternal}
                  className="text-purple-600 hover:text-purple-700 font-medium inline-flex items-center gap-2"
                >
                  Open n8n Editor
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{workflow.name}</h4>
                        <p className="text-sm text-gray-500">
                          {workflow.nodes?.length || 0} nodes • Updated {new Date(workflow.updatedAt).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium flex-shrink-0 ml-2 ${
                        workflow.active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-700"
                      }`}>
                        {workflow.active ? "Active" : "Inactive"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => activateWorkflow(workflow.id, !workflow.active)}
                        className={`flex-1 px-4 py-2 rounded-lg text-sm transition flex items-center justify-center gap-2 font-medium ${
                          workflow.active
                            ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                            : "bg-purple-600 text-white hover:bg-purple-700"
                        }`}
                      >
                        <Play className="w-4 h-4" />
                        {workflow.active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        onClick={openN8nExternal}
                        className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 transition font-medium"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-600 rounded-lg">
                  <Settings className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-purple-700 font-medium">Total Workflows</p>
                  <p className="text-2xl font-bold text-purple-900">{workflows.length}</p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-600 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-green-700 font-medium">Active</p>
                  <p className="text-2xl font-bold text-green-900">
                    {workflows.filter(w => w.active).length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-600 rounded-lg">
                  <Clock className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-700 font-medium">Inactive</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {workflows.filter(w => !w.active).length}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
