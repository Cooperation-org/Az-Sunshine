import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import {
  Play, CheckCircle, Clock, AlertCircle, Search, Mail, Phone, Loader, RefreshCw, Users,
  Target, Award, ChevronRight, ChevronLeft, CheckSquare, Square, X, MoreVertical,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { TableSkeleton, CardSkeleton, StatsGridSkeleton } from "../components/SkeletonLoader";
import ConfirmationModal from "../components/ConfirmationModal";
import { ToastContainer, useToast } from "../components/Toast";
import { useDarkMode } from "../context/DarkModeContext";

// ==================== API CALLS ====================
const API_BASE_URL = "http://167.172.30.134/api/v1/";

const getSOICandidates = async (params) => {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page);
  if (params.page_size) queryParams.append('page_size', params.page_size);
  if (params.status) queryParams.append('status', params.status);
  if (params.search) queryParams.append('search', params.search);
  const response = await fetch(`${API_BASE_URL}soi/candidates/?${queryParams}`);
  if (!response.ok) throw new Error("Failed to fetch candidates");
  return response.json();
};
const getSOIDashboardStats = async () => {
  const response = await fetch(`${API_BASE_URL}soi/dashboard-stats/`);
  if (!response.ok) throw new Error("Failed to fetch stats");
  return response.json();
};
const markCandidateContacted = async (id) => {
  const response = await fetch(`${API_BASE_URL}candidate-soi/${id}/mark_contacted/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
  if (!response.ok) throw new Error("Failed to mark contacted");
  return response.json();
};
const markPledgeReceived = async (id) => {
  const response = await fetch(`${API_BASE_URL}candidate-soi/${id}/mark_pledge_received/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
  if (!response.ok) throw new Error("Failed to mark pledge received");
  return response.json();
};
const bulkMarkContacted = async (ids) => Promise.allSettled(ids.map(id => markCandidateContacted(id)));
const bulkMarkAcknowledged = async (ids) => Promise.allSettled(ids.map(id => markPledgeReceived(id)));


// ==================== SCRAPING MODAL ====================
function ScrapingModal({ isOpen, onClose, onComplete }) {
  const { darkMode } = useDarkMode();
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen && status === 'idle') startScraping();
  }, [isOpen, status]);

  useEffect(() => {
    if (!isOpen) {
      const timer = setTimeout(() => { setStatus('idle'); setMessage(''); }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const startScraping = async () => {
    setStatus('running');
    setMessage('Connecting to Arizona Secretary of State...');
    try {
      const response = await fetch(`${API_BASE_URL}trigger-scrape/`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const result = await response.json();
      if (result.success) {
        setStatus('success');
        setMessage('Successfully synced candidate filings!');
        setTimeout(() => { onComplete(); onClose(); }, 2000);
      } else {
        setStatus('error');
        setMessage(`Error: ${result.error}`);
      }
    } catch (error) {
      setStatus('error');
      setMessage(`Connection failed: ${error.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className={`${darkMode ? 'bg-[#3d3559] border border-purple-500/20' : 'bg-white'} rounded-3xl shadow-2xl max-w-md w-full p-8`}>
         <div className="text-center">
          {status === 'running' && ( <>
            <div className="relative w-20 h-20 mx-auto mb-6"> <Loader className={`w-20 h-20 animate-spin ${darkMode ? 'text-purple-300' : 'text-purple-600'}`} /> </div>
            <h3 className={`text-2xl font-bold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Syncing Data</h3>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{message}</p>
          </> )}
          {status === 'success' && ( <>
            <div className={`w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center ${darkMode ? 'bg-green-500/20' : 'bg-green-100'}`}> <CheckCircle className={`w-12 h-12 ${darkMode ? 'text-green-300' : 'text-green-600'}`} /> </div>
            <h3 className={`text-2xl font-bold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Success!</h3>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{message}</p>
          </> )}
          {status === 'error' && ( <>
            <div className={`w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center ${darkMode ? 'bg-red-500/20' : 'bg-red-100'}`}> <AlertCircle className={`w-12 h-12 ${darkMode ? 'text-red-300' : 'text-red-600'}`} /> </div>
            <h3 className={`text-2xl font-bold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Error</h3>
            <p className={`mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{message}</p>
            <button onClick={onClose} className="px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium transition">Close</button>
          </> )}
        </div>
      </div>
    </div>
  );
}

// ==================== MAIN COMPONENT ====================
export default function SOIManagement() {
  const { darkMode } = useDarkMode();
  const [candidates, setCandidates] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(15);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [showScrapingModal, setShowScrapingModal] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingBulkAction, setPendingBulkAction] = useState(null);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const { toasts, addToast, removeToast } = useToast();

  const reloadData = async () => {
    // A full reload, including stats
    setLoading(true);
    try {
      const [statsData, candidatesData] = await Promise.all([
        getSOIDashboardStats(),
        getSOICandidates({ page: 1, page_size: pageSize, status: 'all', search: '' }),
      ]);
      setStats(statsData);
      setCandidates(candidatesData.results || []);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / pageSize));
      setCurrentPage(1);
      setSearchTerm('');
      setStatusFilter('all');
    } catch (err) { addToast('Failed to reload data', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    if (currentPage !== 1) {
      setCurrentPage(1);
    } else {
      fetchData(true);
    }
  }, [debouncedSearch, statusFilter]);
  
  useEffect(() => {
    // This effect is now only for subsequent page changes.
    // The initial load and filter changes are handled by the effect above.
    if (currentPage > 1) {
        fetchData(false);
    }
  }, [currentPage, pageSize]);
  
  useEffect(() => {
    // Initial load for both stats and page 1 data.
    const initialLoad = async () => {
        setLoading(true);
        try {
            const [statsData, candidatesData] = await Promise.all([
                getSOIDashboardStats(),
                getSOICandidates({
                    page: 1,
                    page_size: pageSize,
                    status: statusFilter !== 'all' ? statusFilter : null,
                    search: debouncedSearch || null,
                })
            ]);
            setStats(statsData);
            setCandidates(candidatesData.results || []);
            setTotalCount(candidatesData.count || 0);
            setTotalPages(Math.ceil((candidatesData.count || 0) / pageSize));
        } catch (err) {
            addToast('Failed to load initial data', 'error');
        } finally {
            setLoading(false);
        }
    };
    initialLoad();
  }, []);
  
  const fetchData = async (isFilterChange = false) => {
    setLoading(true);
    if (isFilterChange) {
      setSelectedIds(new Set());
    }
    try {
      const candidatesData = await getSOICandidates({
        page: currentPage, page_size: pageSize,
        status: statusFilter !== 'all' ? statusFilter : null,
        search: debouncedSearch || null,
      });
      setCandidates(candidatesData.results || []);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / pageSize));
    } catch (err) { addToast('Failed to load candidates', 'error'); } 
    finally { setLoading(false); }
  };

  const optimisticUpdate = (id, updates) => setCandidates(candidates.map(c => c.id === id ? { ...c, ...updates } : c));

  const handleMarkContacted = async (id) => {
    optimisticUpdate(id, { contacted: true });
    try { await markCandidateContacted(id); addToast('Candidate marked as contacted', 'success'); } 
    catch (error) { addToast('Failed to update candidate', 'error'); optimisticUpdate(id, { contacted: false }); }
  };

  const handleMarkPledged = async (id) => {
    optimisticUpdate(id, { contacted: true, pledge_received: true });
    try { await markPledgeReceived(id); addToast('Pledge received marked', 'success'); } 
    catch (error) { addToast('Failed to update pledge status', 'error'); optimisticUpdate(id, { pledge_received: false }); }
  };
  
  const handleSelectCandidate = (id) => {
    const newSelected = new Set(selectedIds);
    newSelected.has(id) ? newSelected.delete(id) : newSelected.add(id);
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedIds.size >= candidates.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(candidates.map(c => c.id)));
  };

  const handleBulkAction = (action) => {
    if (selectedIds.size === 0) return addToast('Please select candidates first', 'warning');
    setPendingBulkAction(action);
    setShowConfirmModal(true);
  };
  
  const executeBulkAction = async () => {
    setBulkActionLoading(true);
    const ids = Array.from(selectedIds);
    const actionPromise = pendingBulkAction === 'contacted' ? bulkMarkContacted(ids) : bulkMarkAcknowledged(ids);
    try {
      await actionPromise;
      addToast(`${ids.length} candidates updated successfully`, 'success');
      fetchData(true); // Refetch current page and clear selections
    } catch (error) { addToast('Bulk action failed', 'error'); } 
    finally {
      setBulkActionLoading(false);
      setShowConfirmModal(false);
      setPendingBulkAction(null);
    }
  };

  const StatusBadge = ({ candidate }) => {
    if (candidate.pledge_received) return <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${darkMode ? 'bg-green-500/20 text-green-300' : 'bg-green-100 text-green-800'}`}><CheckCircle className="w-3.5 h-3.5" />Pledge Received</span>;
    if (candidate.contacted) return <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${darkMode ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-800'}`}><Clock className="w-3.5 h-3.5" />Contacted</span>;
    return <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${darkMode ? 'bg-red-500/20 text-red-300' : 'bg-red-100 text-red-800'}`}><AlertCircle className="w-3.5 h-3.5" />New</span>;
  };

  const statCards = [
    { title: "Total Candidates", value: stats?.total_candidates, icon: Users, color: darkMode ? '#a78bfa' : '#7163BA' },
    { title: "Needs Contact", value: stats?.uncontacted, icon: Target, color: darkMode ? '#f87171' : '#ef4444' },
    { title: "Awaiting Pledge", value: stats?.contacted, icon: Clock, color: darkMode ? '#fbbf24' : '#f59e0b' },
    { title: "Pledges Received", value: stats?.pledged, icon: Award, color: darkMode ? '#4ade80' : '#22c55e' },
  ];

  if (!stats) return (
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 overflow-auto"><div className="p-8"><StatsGridSkeleton count={4}/></div></main>
    </div>
  );

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        
        <div className="p-4 sm:p-6 lg:p-8 space-y-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>SOI Management</h1>
              <p className={`mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Track Statement of Interest filings and manual outreach.</p>
            </div>
            <button onClick={() => setShowScrapingModal(true)} className={`px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-sm ${darkMode ? 'bg-[#7163BA] text-white hover:bg-[#8b7cb8]' : 'bg-[#7163BA] text-white hover:bg-[#5b509a]'}`}>
              <RefreshCw className="w-4 h-4" /> Run Scraper
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {statCards.map(stat => (
              <div key={stat.title} className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl p-6 border shadow-sm`}>
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl" style={{ backgroundColor: `${stat.color}20`}}>
                    <stat.icon className="w-6 h-6" style={{ color: stat.color }} />
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{stat.title}</p>
                    <h3 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{stat.value ?? '-'}</h3>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-200/80'} rounded-2xl border shadow-sm`}>
            <div className="p-4 sm:p-6 flex flex-col md:flex-row items-center justify-between gap-4 border-b" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
              <div className="w-full md:w-auto flex-grow flex items-center gap-3">
                 <div className="relative w-full max-w-sm">
                  <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  <input type="text" placeholder="Search candidates..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className={`w-full pl-10 pr-4 py-2.5 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}/>
                </div>
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={`appearance-none px-4 py-2.5 border rounded-xl transition-colors ${darkMode ? 'bg-transparent text-white border-[#5f5482] focus:border-purple-400' : 'bg-white text-gray-900 border-gray-300 focus:border-[#7163BA]'} focus:outline-none focus:ring-0`}>
                  <option value="all">All Statuses</option>
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="pledged">Pledged</option>
                </select>
              </div>
              {selectedIds.size > 0 && (
                <div className="flex items-center gap-3">
                  <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} text-sm font-medium`}>{selectedIds.size} selected</span>
                  <button onClick={() => handleBulkAction('contacted')} className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${darkMode ? 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30' : 'bg-blue-100 text-blue-700 hover:bg-blue-200'}`}>Mark Contacted</button>
                  <button onClick={() => handleBulkAction('acknowledged')} className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${darkMode ? 'bg-green-500/20 text-green-300 hover:bg-green-500/30' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}>Pledge Received</button>
                </div>
              )}
            </div>

            {/* Responsive container for both table and mobile cards */}
            <div>
              {/* Desktop Table */}
              <div className="overflow-x-auto hidden md:block">
                <table className="w-full min-w-[768px]">
                  <thead className={`${darkMode ? 'border-b-0' : 'bg-gray-50/80 border-b'}`} style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                    <tr>
                      <th className="p-4 w-12 text-left"><button onClick={handleSelectAll} className="p-2">{selectedIds.size >= candidates.length && candidates.length > 0 ? <CheckSquare className="w-5 h-5 text-purple-400" /> : <Square className="w-5 h-5 text-gray-400" />}</button></th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Candidate</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Contact</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 w-48">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                    {loading ? <TableSkeleton rows={10} cols={5} /> : candidates.length === 0 ? (
                      <tr><td colSpan="5" className="text-center py-20"><AlertCircle className="mx-auto w-12 h-12 text-gray-400 mb-2" /><p className={`font-medium ${darkMode ? 'text-white' : 'text-gray-700'}`}>No candidates found</p><p className="text-sm text-gray-500">Try adjusting your filters.</p></td></tr>
                    ) : candidates.map((candidate) => (
                      <tr key={candidate.id} className={`transition-colors ${selectedIds.has(candidate.id) ? (darkMode ? 'bg-purple-900/30' : 'bg-purple-50') : (darkMode ? 'hover:bg-white/5' : 'hover:bg-gray-50/80')}`}>
                        <td className="p-4 w-12"><button onClick={() => handleSelectCandidate(candidate.id)} className="p-2">{selectedIds.has(candidate.id) ? <CheckSquare className="w-5 h-5 text-purple-400" /> : <Square className="w-5 h-5 text-gray-400" />}</button></td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${darkMode ? 'bg-purple-500/20 text-purple-300' : 'bg-purple-100 text-purple-700'}`}>{(candidate.candidate_name || '?').charAt(0)}</div>
                            <div>
                              <p className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{candidate.candidate_name || 'Unknown'}</p>
                              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{candidate.office?.name || 'Not specified'}{candidate.party ? ` • ${candidate.party}` : ''}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {candidate.email && <div className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}><Mail className="w-4 h-4 text-gray-400" /><span>{candidate.email}</span></div>}
                          {candidate.phone && <div className={`flex items-center gap-2 text-sm mt-1 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}><Phone className="w-4 h-4 text-gray-400" /><span>{candidate.phone}</span></div>}
                        </td>
                        <td className="px-4 py-3"><StatusBadge candidate={candidate} /></td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {!candidate.contacted && <button onClick={() => handleMarkContacted(candidate.id)} className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${darkMode ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>Contacted</button>}
                            {!candidate.pledge_received && <button onClick={() => handleMarkPledged(candidate.id)} className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${darkMode ? 'bg-green-500/10 text-green-300 hover:bg-green-500/20' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}>Pledged</button>}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Card View */}
              <div className="md:hidden divide-y" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                {loading ? Array.from({length: 5}).map((_, i) => <CardSkeleton key={i} className="rounded-none shadow-none border-0"/>) :
                 candidates.length === 0 ? <div className="text-center py-20"><AlertCircle className="mx-auto w-12 h-12 text-gray-400 mb-2" /><p className={`font-medium ${darkMode ? 'text-white' : 'text-gray-700'}`}>No candidates found</p><p className="text-sm text-gray-500">Try adjusting your filters.</p></div> :
                 candidates.map(candidate => (
                  <div key={candidate.id} className={`p-4 ${selectedIds.has(candidate.id) ? (darkMode ? 'bg-purple-900/30' : 'bg-purple-50') : ''}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <button onClick={() => handleSelectCandidate(candidate.id)} className="p-1 mt-1">{selectedIds.has(candidate.id) ? <CheckSquare className="w-5 h-5 text-purple-400" /> : <Square className="w-5 h-5 text-gray-400" />}</button>
                        <div>
                          <p className={`font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>{candidate.candidate_name || 'Unknown'}</p>
                          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{candidate.office?.name || 'Not specified'}{candidate.party ? ` • ${candidate.party}` : ''}</p>
                        </div>
                      </div>
                      <StatusBadge candidate={candidate} />
                    </div>
                    <div className="mt-4 pl-9 space-y-2">
                       {candidate.email && <div className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}><Mail className="w-4 h-4 text-gray-400" /><span>{candidate.email}</span></div>}
                       {candidate.phone && <div className={`flex items-center gap-2 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}><Phone className="w-4 h-4 text-gray-400" /><span>{candidate.phone}</span></div>}
                    </div>
                    <div className="mt-4 pl-9 flex items-center gap-2">
                        {!candidate.contacted && <button onClick={() => handleMarkContacted(candidate.id)} className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${darkMode ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>Mark Contacted</button>}
                        {!candidate.pledge_received && <button onClick={() => handleMarkPledged(candidate.id)} className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${darkMode ? 'bg-green-500/10 text-green-300 hover:bg-green-500/20' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}>Mark as Pledged</button>}
                    </div>
                  </div>
                 ))}
              </div>
            </div>

            {totalPages > 1 && (
              <div className="p-4 flex items-center justify-between border-t" style={{borderColor: darkMode ? '#4a3f66' : '#e5e7eb'}}>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Page {currentPage} of {totalPages}</p>
                <div className="flex items-center gap-2">
                  <button onClick={() => setCurrentPage(c => Math.max(1, c - 1))} disabled={currentPage === 1} className={`p-2 rounded-md transition ${darkMode ? 'text-gray-300 hover:bg-white/10 disabled:opacity-30' : 'text-gray-600 hover:bg-gray-100 disabled:opacity-40'}`}><ChevronLeft className="w-5 h-5" /></button>
                  <button onClick={() => setCurrentPage(c => Math.min(totalPages, c + 1))} disabled={currentPage === totalPages} className={`p-2 rounded-md transition ${darkMode ? 'text-gray-300 hover:bg-white/10 disabled:opacity-30' : 'text-gray-600 hover:bg-gray-100 disabled:opacity-40'}`}><ChevronRight className="w-5 h-5" /></button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      <ScrapingModal isOpen={showScrapingModal} onClose={() => setShowScrapingModal(false)} onComplete={reloadData} />
      <ConfirmationModal isOpen={showConfirmModal} onClose={() => { setShowConfirmModal(false); setPendingBulkAction(null); }} onConfirm={executeBulkAction} title={`Confirm Bulk Action`} message={`Are you sure you want to mark ${selectedIds.size} candidate(s) as ${pendingBulkAction}?`} confirmText={bulkActionLoading ? "Processing..." : "Confirm"} type="warning" darkMode={darkMode}/>
      <ToastContainer toasts={toasts} removeToast={removeToast} darkMode={darkMode} />
    </div>
  );
}
