import React, { useState, useEffect, useMemo } from "react";
import {
  Mail, Send, Eye, MousePointerClick, Users, Filter, CheckCircle, Clock,
  AlertCircle, Search, X, ChevronRight, ChevronLeft, Loader, BarChart3, TrendingUp, Inbox
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { StatsGridSkeleton } from "../components/SkeletonLoader";
import { getSOICandidates } from "../api/api";
import { useDarkMode } from "../context/DarkModeContext";
import { ToastContainer, useToast } from "../components/Toast";

const API_BASE_URL = "http://167.172.30.134/api/v1/";

// Mock Data (as in original file)
const mockEmailStats = {
  total_sent: 245, total_opened: 189, total_clicked: 67,
  open_rate: 77.1, click_rate: 27.3,
  recent_campaigns: [
    { id: 1, subject: "Statement of Interest Request", sent: 45, opened: 38, clicked: 12, date: "2024-11-05" },
    { id: 2, subject: "Follow-up: SOI Pledge", sent: 32, opened: 25, clicked: 8, date: "2024-11-03" },
    { id: 3, subject: "November Newsletter", sent: 168, opened: 126, clicked: 47, date: "2024-11-01" },
  ],
};
const emailTemplates = [
  { id: "soi_initial", name: "Initial SOI Request", subject: "Statement of Interest Request - {{candidate_name}}", body: `Dear {{candidate_name}},

We hope this message finds you well. We are reaching out regarding your candidacy for {{office}}.

We would like to request your Statement of Interest (SOI) to better understand your campaign priorities and how we might work together.

Please let us know if you have any questions or would like to discuss this further.

Best regards,
Arizona Sunshine Team`},
  { id: "soi_followup", name: "SOI Follow-up", subject: "Follow-up: Statement of Interest Request - {{candidate_name}}", body: `Dear {{candidate_name}},

We wanted to follow up on our previous request for your Statement of Interest regarding your campaign for {{office}}.

Your input is valuable to us, and we would appreciate the opportunity to learn more about your campaign priorities.

Please feel free to reach out if you have any questions.

Best regards,
Arizona Sunshine Team`},
  { id: "pledge_reminder", name: "Pledge Reminder", subject: "Reminder: SOI Pledge - {{candidate_name}}", body: `Dear {{candidate_name}},

This is a friendly reminder about your pending Statement of Interest pledge for {{office}}.

We look forward to receiving your response and continuing our collaboration.

Thank you for your time and consideration.

Best regards,
Arizona Sunshine Team`},
];


export default function EmailCampaign() {
  const { darkMode } = useDarkMode();
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState("");
  
  const [recipients, setRecipients] = useState([]);
  const [selectedRecipients, setSelectedRecipients] = useState(new Set());
  const [recipientFilter, setRecipientFilter] = useState("uncontacted");
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sendProgress, setSendProgress] = useState({ sent: 0, total: 0 });
  
  const [emailStats, setEmailStats] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { toasts, addToast, removeToast } = useToast();

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    loadRecipients();
    loadEmailStats();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
    loadRecipients(1);
  }, [recipientFilter, debouncedSearch]);
  
  useEffect(() => {
    if (currentPage > 1) loadRecipients(currentPage);
  }, [currentPage]);

  async function loadRecipients(page = 1) {
    setLoading(true);
    try {
      const params = { page, page_size: 50, search: debouncedSearch || undefined };
      if (recipientFilter === "uncontacted") params.status = "uncontacted";
      if (recipientFilter === "pending") params.status = "contacted";

      const data = await getSOICandidates(params);
      const candidatesList = data.results || [];
      setRecipients(candidatesList);
      if (data.count) setTotalPages(Math.ceil(data.count / 50));
    } catch (err) { console.error("Error loading recipients:", err); setRecipients([]); }
    finally { setLoading(false); }
  }

  async function loadEmailStats() {
    setEmailStats(mockEmailStats); // Replace with real API call
  }

  const handleTemplateSelect = (templateId) => {
    const template = emailTemplates.find((t) => t.id === templateId);
    if (template) {
      setSelectedTemplate(templateId);
      setEmailSubject(template.subject);
      setEmailBody(template.body);
    } else {
      setSelectedTemplate("");
      setEmailSubject("");
      setEmailBody("");
    }
  };

  const replaceTemplateVariables = (text, candidate) => {
    return text
      .replace(/{{\candidate_name}} /g, candidate.candidate_name || "Candidate")
      .replace(/{{\office}} /g, candidate.office?.name || "their office");
  };

  const toggleRecipient = (recipientId) => {
    const newSelection = new Set(selectedRecipients);
    if (newSelection.has(recipientId)) newSelection.delete(recipientId);
    else newSelection.add(recipientId);
    setSelectedRecipients(newSelection);
  };
  
  const toggleSelectAll = () => {
    if (selectedRecipients.size === recipients.length) setSelectedRecipients(new Set());
    else setSelectedRecipients(new Set(recipients.map(r => r.id)));
  };

  const handleSendEmails = async () => {
    if (selectedRecipients.size === 0 || !emailSubject.trim() || !emailBody.trim()) return;
    if (!confirm(`Send email to ${selectedRecipients.size} recipient(s)?`)) return;

    setSending(true);
    setSendProgress({ sent: 0, total: selectedRecipients.size });

    try {
      const recipientsToSend = recipients.filter(r => selectedRecipients.has(r.id));
      for (let i = 0; i < recipientsToSend.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 50)); // Simulate API call
        setSendProgress({ sent: i + 1, total: recipientsToSend.length });
      }
      alert(`Successfully sent ${recipientsToSend.length} email(s)!`);
      setSelectedRecipients(new Set());
      loadEmailStats();
    } catch (err) { alert("Error sending emails."); } 
    finally { setSending(false); }
  };
  
  const previewCandidate = recipients.find(r => selectedRecipients.has(r.id)) || recipients[0] || {};
  const statsData = [
    { title: "Total Sent", value: emailStats?.total_sent, icon: Send, color: darkMode ? '#a78bfa' : '#7163BA' },
    { title: "Open Rate", value: `${emailStats?.open_rate || 0}%`, icon: Eye, color: darkMode ? '#38bdf8' : '#0ea5e9' },
    { title: "Click Rate", value: `${emailStats?.click_rate || 0}%`, icon: MousePointerClick, color: darkMode ? '#4ade80' : '#22c55e' },
    { title: "Selected", value: selectedRecipients.size, icon: Users, color: darkMode ? '#fbbf24' : '#f59e0b' },
  ];

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="p-4 sm:p-6 lg:p-8 space-y-8">
          <div>
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Email Campaigns</h1>
            <p className={`mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Create, send, and monitor outreach campaigns.</p>
          </div>
          
          {emailStats ? <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
            {statsData.map(stat => (
              <div key={stat.title} className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl p-6 border shadow-sm`}>
                <div className="flex items-center gap-4"><div className="p-3 rounded-xl" style={{ backgroundColor: `${stat.color}20`}}><stat.icon className="w-6 h-6" style={{ color: stat.color }} /></div>
                <div><p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{stat.title}</p><h3 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{stat.value ?? '-'}</h3></div></div>
              </div>
            ))}
          </div> : <StatsGridSkeleton count={4} />}

          <div className="flex flex-col xl:flex-row gap-8">
            {/* --- Column 1: Recipients --- */}
            <div className={`xl:w-1/3 ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl border shadow-sm flex flex-col h-full`}>
              <div className="p-4 border-b" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                <h2 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-gray-800'}`}>Recipients</h2>
                <div className="relative mt-3"><Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} /><input type="text" placeholder="Search recipients..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className={`w-full pl-10 pr-4 py-2.5 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}/></div>
                <div className="flex items-center justify-center gap-1 mt-3 p-1 rounded-lg" style={{backgroundColor: darkMode ? 'rgba(0,0,0,0.1)' : 'rgba(0,0,0,0.05)'}}>
                  {[{id: "uncontacted", label: "New"}, {id: "pending", label: "Pending"}, {id: "all", label: "All"}].map(f => (
                    <button key={f.id} onClick={() => setRecipientFilter(f.id)} className={`w-full text-center text-sm font-semibold py-1.5 rounded-md transition-colors ${recipientFilter === f.id ? (darkMode ? 'bg-[#7163BA] text-white' : 'bg-white shadow-sm text-purple-700') : (darkMode ? 'text-gray-300 hover:bg-white/5' : 'text-gray-500 hover:bg-gray-200/50')}`}>{f.label}</button>
                  ))}
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                {loading && <div className="flex justify-center items-center h-full"><Loader className="animate-spin text-purple-400"/></div>}
                {!loading && recipients.length === 0 && <div className="text-center py-16"><Inbox className="mx-auto w-12 h-12 text-gray-400 mb-2"/><p className="font-medium text-gray-500">No recipients found.</p></div>}
                {!loading && recipients.map(r => (
                  <div key={r.id} onClick={() => toggleRecipient(r.id)} className={`px-4 py-3 flex items-center gap-3 cursor-pointer border-b ${selectedRecipients.has(r.id) ? (darkMode ? 'bg-purple-500/20' : 'bg-purple-50') : (darkMode ? 'hover:bg-white/5' : 'hover:bg-gray-50/50')}`} style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                    <input type="checkbox" readOnly checked={selectedRecipients.has(r.id)} className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"/>
                    <div>
                      <p className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>{r.candidate_name}</p>
                      <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{r.email || 'No email'}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-2 border-t flex justify-between items-center" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}><button onClick={toggleSelectAll} className={`text-xs font-semibold py-1 px-2 rounded-md ${darkMode ? 'text-purple-300 hover:bg-white/10' : 'text-purple-600 hover:bg-purple-50'}`}>Select/Deselect All</button></div>
            </div>

            {/* --- Column 2: Composer & Preview --- */}
            <div className="xl:w-2/3 space-y-8">
              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl border shadow-sm`}>
                <div className="p-6">
                  <h2 className={`font-bold text-lg mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>Compose</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <select onChange={e => handleTemplateSelect(e.target.value)} className={`w-full appearance-none px-4 py-3 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}><option value="">Select a template...</option>{emailTemplates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select>
                    <input type="text" value={emailSubject} onChange={e => setEmailSubject(e.target.value)} placeholder="Email subject" className={`w-full px-4 py-3 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}/>
                  </div>
                  <textarea value={emailBody} onChange={e => setEmailBody(e.target.value)} placeholder="Email body..." rows={8} className={`w-full p-4 border rounded-xl transition-colors resize-y ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}/>
                  <div className="mt-4 flex justify-end">
                    <button onClick={handleSendEmails} disabled={sending || selectedRecipients.size === 0} className={`px-6 py-3 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-sm disabled:opacity-50 ${darkMode ? 'bg-[#7163BA] text-white hover:bg-[#8b7cb8]' : 'bg-[#7163BA] text-white hover:bg-[#5b509a]'}`}>
                      {sending ? <><Loader className="w-5 h-5 animate-spin"/>Sending ({sendProgress.sent}/{sendProgress.total})</> : <><Send className="w-5 h-5"/>Send to {selectedRecipients.size} Recipient(s)</>}</button>
                  </div>
                </div>
              </div>

              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl border shadow-sm`}>
                <div className="p-6">
                  <h2 className={`font-bold text-lg mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>Preview</h2>
                  <div className={`p-4 rounded-xl border ${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-gray-50 border-gray-200'}`}>
                    <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>To: {previewCandidate.email || '[Recipient Email]'}</p>
                    <p className={`font-semibold mt-2 pb-2 border-b ${darkMode ? 'text-white border-[#4a3f66]' : 'text-gray-800 border-gray-200'}`}>{replaceTemplateVariables(emailSubject, previewCandidate) || '(Subject)'}</p>
                    <div className={`mt-3 text-sm whitespace-pre-wrap ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{replaceTemplateVariables(emailBody, previewCandidate) || '(Body)'}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl border shadow-sm`}>
            <div className="p-4 sm:p-6"><h2 className={`text-lg sm:text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Recent Campaigns</h2></div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className={`${darkMode ? 'border-b-0' : 'bg-gray-50/80 border-b'}`} style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Campaign</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Performance</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">Sent</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                  {emailStats?.recent_campaigns.map(c => (
                    <tr key={c.id} className={`${darkMode ? 'hover:bg-white/5' : 'hover:bg-gray-50/80'}`}>
                      <td className="px-6 py-4 whitespace-nowrap"><p className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>{c.subject}</p></td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-4">
                          <div className="text-right"><p className="text-sm font-bold" style={{color: darkMode ? '#38bdf8' : '#0ea5e9'}}>{((c.opened / c.sent) * 100).toFixed(1)}%</p><p className="text-xs text-gray-500">Open</p></div>
                          <div className="text-right"><p className="text-sm font-bold" style={{color: darkMode ? '#4ade80' : '#22c55e'}}>{((c.clicked / c.sent) * 100).toFixed(1)}%</p><p className="text-xs text-gray-500">Click</p></div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right"><p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{c.sent}</p></td>
                      <td className="px-6 py-4 text-right"><p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{new Date(c.date).toLocaleDateString()}</p></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
      <ToastContainer toasts={toasts} removeToast={removeToast} darkMode={darkMode} />
    </div>
  );
}