import React, { useState, useEffect } from "react";
import {
  Mail, Send, Eye, MousePointerClick, Users, Search, 
  Loader, RefreshCw, Inbox, CheckSquare, Square
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { StatsGridSkeleton } from "../components/SkeletonLoader";
import { getSOICandidates } from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import { ToastContainer, useToast } from "../components/Toast";

// --- REFINED BANNER COMPONENT ---
const Banner = ({ controls, searchTerm, setSearchTerm, onSearch }) => {
  const { darkMode } = useDarkMode();

  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Email <span style={{ color: '#A78BFA' }}>Campaigns</span>
            </h1>
            <p className="text-white/70 text-sm mt-1 max-w-xl">
              Design, target, and monitor your candidate outreach performance.
            </p>
          </div>
          <div className="flex-shrink-0">{controls}</div>
        </div>

        <div className="flex justify-start">
          <form onSubmit={(e) => { e.preventDefault(); onSearch(); }} className="relative w-full max-w-md">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="text-gray-400" size={16} />
            </div>
            <input
              type="text"
              placeholder="Search recipients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border-none rounded-full py-2.5 pl-11 pr-4 text-sm text-white placeholder-gray-400 outline-none transition-all focus:ring-1 focus:ring-[#7667C1]"
              style={darkMode
                ? { background: 'rgba(31, 27, 49, 0.8)' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            />
          </form>
        </div>
      </div>
    </div>
  );
};

export default function EmailCampaign() {
  const { darkMode } = useDarkMode();
  const { toasts, addToast, removeToast } = useToast();
  
  // State
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [recipients, setRecipients] = useState([]);
  const [selectedRecipients, setSelectedRecipients] = useState(new Set());
  const [recipientFilter, setRecipientFilter] = useState("uncontacted");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sendProgress, setSendProgress] = useState({ sent: 0, total: 0 });

  // Mock Stats - to be replaced by API
  const statsData = [
    { title: "Total Sent", value: "245", icon: Send, color: "#7667C1" },
    { title: "Open Rate", value: "77.1%", icon: Eye, color: "#0ea5e9" },
    { title: "Click Rate", value: "27.3%", icon: MousePointerClick, color: "#22c55e" },
    { title: "Selected", value: selectedRecipients.size.toString(), icon: Users, color: "#fbbf24" },
  ];

  useEffect(() => {
    loadRecipients();
  }, [recipientFilter, searchTerm]);

  async function loadRecipients() {
    setLoading(true);
    try {
      const params = { page_size: 50, search: searchTerm || undefined };
      if (recipientFilter !== "all") params.status = recipientFilter;
      const data = await getSOICandidates(params);
      setRecipients(data.results || []);
    } catch (err) {
      addToast("Failed to load recipients", "error");
    } finally {
      setLoading(false);
    }
  }

  const handleSendEmails = async () => {
    if (selectedRecipients.size === 0) return addToast("Select recipients first", "warning");
    setSending(true);
    // Logic for sending...
    setTimeout(() => {
        setSending(false);
        addToast(`Successfully sent to ${selectedRecipients.size} candidates`, "success");
    }, 2000);
  };

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className={`${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'} p-5 rounded-2xl border shadow-sm flex items-center gap-4`}>
      <div className="p-3 rounded-xl" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color: color }} />
      </div>
      <div>
        <p className={`text-xs font-medium uppercase tracking-wider ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{title}</p>
        <p className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{value}</p>
      </div>
    </div>
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner 
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            onSearch={loadRecipients}
            controls={
              <button 
                onClick={() => addToast("Stats refreshed", "info")}
                className="flex items-center gap-2 bg-[#7667C1] hover:bg-[#6556b0] text-white px-5 py-2 rounded-full text-sm font-medium transition-all"
              >
                <RefreshCw size={14} /> Refresh Stats
              </button>
            }
          />

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {statsData.map((s, i) => <StatCard key={i} {...s} />)}
          </div>

          <div className="flex flex-col xl:flex-row gap-6">
            {/* --- RECIPIENT LIST --- */}
            <div className={`xl:w-1/3 rounded-2xl border overflow-hidden flex flex-col ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
              <div className="p-4 border-b border-gray-700/50">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-sm uppercase tracking-widest text-gray-500">Recipients</h3>
                  <button 
                    onClick={() => setSelectedRecipients(selectedRecipients.size === recipients.length ? new Set() : new Set(recipients.map(r => r.id)))}
                    className="text-xs text-purple-400 hover:underline"
                  >
                    Select All
                  </button>
                </div>
                <div className="flex gap-1 p-1 rounded-lg bg-[#1F1B31]">
                    {["uncontacted", "contacted", "all"].map(f => (
                        <button 
                            key={f}
                            onClick={() => setRecipientFilter(f)}
                            className={`flex-1 py-1 text-[10px] font-bold uppercase rounded-md transition-all ${recipientFilter === f ? 'bg-[#7667C1] text-white' : 'text-gray-400 hover:text-white'}`}
                        >
                            {f}
                        </button>
                    ))}
                </div>
              </div>
              <div className="overflow-y-auto max-h-[500px] divide-y divide-gray-700/30">
                {loading ? <div className="p-10 text-center"><Loader className="animate-spin mx-auto text-purple-500" /></div> : recipients.map(r => (
                   <div 
                    key={r.id} 
                    onClick={() => {
                        const next = new Set(selectedRecipients);
                        next.has(r.id) ? next.delete(r.id) : next.add(r.id);
                        setSelectedRecipients(next);
                    }}
                    className={`p-4 flex items-center gap-3 cursor-pointer transition-colors ${selectedRecipients.has(r.id) ? 'bg-purple-500/10' : 'hover:bg-white/5'}`}
                   >
                     {selectedRecipients.has(r.id) ? <CheckSquare size={16} className="text-[#7667C1]" /> : <Square size={16} className="text-gray-500" />}
                     <div className="min-w-0">
                        <p className={`text-sm font-medium truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>{r.candidate_name}</p>
                        <p className="text-xs text-gray-500 truncate">{r.email}</p>
                     </div>
                   </div>
                ))}
              </div>
            </div>

            {/* --- COMPOSER --- */}
            <div className="xl:flex-1 space-y-6">
              <div className={`p-6 rounded-2xl border ${darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'}`}>
                <h3 className="font-bold text-sm uppercase tracking-widest text-gray-500 mb-6">Campaign Composer</h3>
                <div className="space-y-4">
                  <input 
                    type="text" 
                    placeholder="Campaign Subject Line" 
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className={`w-full px-4 py-3 rounded-xl border-none text-sm ${darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50'}`} 
                  />
                  <textarea 
                    rows={10}
                    placeholder="Write your message here... Use {{candidate_name}} for personalization."
                    value={emailBody}
                    onChange={(e) => setEmailBody(e.target.value)}
                    className={`w-full px-4 py-4 rounded-xl border-none text-sm resize-none ${darkMode ? 'bg-[#1F1B31] text-white' : 'bg-gray-50'}`}
                  />
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">Targeting {selectedRecipients.size} selected recipients</p>
                    <button 
                        onClick={handleSendEmails}
                        disabled={sending}
                        className="flex items-center gap-2 bg-[#7667C1] hover:bg-[#6556b0] text-white px-8 py-3 rounded-full text-sm font-bold transition-all shadow-lg active:scale-95 disabled:opacity-50"
                    >
                        {sending ? <Loader size={16} className="animate-spin" /> : <Send size={16} />}
                        {sending ? "Sending..." : "Launch Campaign"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      <ToastContainer toasts={toasts} removeToast={removeToast} darkMode={darkMode} />
    </div>
  );
}