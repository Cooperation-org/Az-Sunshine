import React, { useState, useEffect } from 'react';
import { getPendingAdBuys, verifyAdBuy, rejectAdBuy } from '../api/api';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import {
  CheckCircle, XCircle, Calendar, User, ExternalLink,
  TrendingUp, TrendingDown, AlertCircle, Loader, Clock
} from 'lucide-react';

export default function AdBuyReview() {
  const { darkMode } = useDarkMode();
  const [pendingAds, setPendingAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [error, setError] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(null);

  useEffect(() => {
    loadPendingAds();
  }, []);

  async function loadPendingAds() {
    setLoading(true);
    setError('');
    try {
      const data = await getPendingAdBuys();
      setPendingAds(data.results || data);
    } catch (e) {
      console.error('Failed to load pending ads:', e);
      setError('Failed to load pending ad buy submissions');
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(adBuyId) {
    setProcessing(adBuyId);
    setError('');
    try {
      await verifyAdBuy(adBuyId);
      setPendingAds(prev => prev.filter(ad => ad.id !== adBuyId));
    } catch (e) {
      console.error('Failed to verify ad:', e);
      setError('Failed to approve ad buy');
    } finally {
      setProcessing(null);
    }
  }

  async function handleReject(adBuyId) {
    if (!rejectReason.trim()) {
      setError('Please provide a reason for rejection');
      return;
    }

    setProcessing(adBuyId);
    setError('');
    try {
      await rejectAdBuy(adBuyId, rejectReason);
      setPendingAds(prev => prev.filter(ad => ad.id !== adBuyId));
      setShowRejectModal(null);
      setRejectReason('');
    } catch (e) {
      console.error('Failed to reject ad:', e);
      setError('Failed to reject ad buy');
    } finally {
      setProcessing(null);
    }
  }

  const platformIcons = {
    tv: '📺',
    radio: '📻',
    digital: '💻',
    print: '📰',
    mail: '✉️',
    billboard: '🪧',
    other: '📢'
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Header */}
          <div
            className="w-full rounded-2xl p-6 md:p-10 mb-8 text-white"
            style={darkMode
              ? { background: '#2D2844' }
              : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
            }
          >
            <div className="max-w-7xl mx-auto">
              <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
                Ad Buy <span style={{ color: '#A78BFA' }}>Review Queue</span>
              </h1>
              <p className="text-white/70 text-sm mt-1">
                Review and approve volunteer-submitted political ad reports
              </p>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
              <AlertCircle className="text-red-600" size={20} />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Stats */}
          <div className="mb-6">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              darkMode ? 'bg-[#2D2844]' : 'bg-white'
            } border ${darkMode ? 'border-gray-700' : 'border-gray-100'}`}>
              <Clock size={16} className="text-[#7163BA]" />
              <span className={`text-sm font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                {pendingAds.length} pending review{pendingAds.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          {/* Loading State */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader className="animate-spin text-[#7163BA]" size={40} />
            </div>
          ) : pendingAds.length === 0 ? (
            <div className={`text-center py-20 rounded-2xl border ${
              darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
            }`}>
              <CheckCircle size={48} className="mx-auto mb-4 text-green-500 opacity-50" />
              <p className={`text-lg font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                All caught up!
              </p>
              <p className="text-gray-500 text-sm mt-1">
                No pending ad buy submissions to review
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {pendingAds.map((ad) => (
                <div
                  key={ad.id}
                  className={`rounded-2xl border overflow-hidden ${
                    darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
                  }`}
                >
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
                    {/* Image Section */}
                    <div>
                      <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden mb-3">
                        <img
                          src={ad.image_url}
                          alt="Ad submission"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <a
                        href={ad.image_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-sm text-[#7163BA] hover:underline"
                      >
                        View Full Size <ExternalLink size={14} />
                      </a>
                    </div>

                    {/* Details Section */}
                    <div className="space-y-4">
                      {/* Platform & Date */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{platformIcons[ad.platform] || '📢'}</span>
                          <div>
                            <p className={`text-lg font-bold ${
                              darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              {ad.paid_for_by}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <Calendar size={14} className="text-gray-500" />
                              <span className="text-sm text-gray-500">
                                {new Date(ad.ad_date).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Support/Oppose Badge */}
                        <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${
                          ad.support_oppose === 'support'
                            ? 'bg-green-500/10 text-green-500'
                            : ad.support_oppose === 'oppose'
                            ? 'bg-red-500/10 text-red-500'
                            : 'bg-gray-500/10 text-gray-500'
                        }`}>
                          {ad.support_oppose === 'support' ? (
                            <TrendingUp size={14} />
                          ) : ad.support_oppose === 'oppose' ? (
                            <TrendingDown size={14} />
                          ) : null}
                          <span className="text-xs font-bold uppercase">
                            {ad.support_oppose}
                          </span>
                        </div>
                      </div>

                      {/* Candidate */}
                      <div className={`p-3 rounded-lg ${
                        darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                      }`}>
                        <p className="text-xs text-gray-500 mb-1">CANDIDATE</p>
                        <p className={`text-sm font-semibold ${
                          darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {ad.candidate_name}
                        </p>
                      </div>

                      {/* Metadata Grid */}
                      <div className="grid grid-cols-2 gap-3">
                        {ad.approximate_spend && (
                          <div className={`p-3 rounded-lg ${
                            darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                          }`}>
                            <p className="text-xs text-gray-500 mb-1">EST. SPEND</p>
                            <p className={`text-sm font-mono font-bold ${
                              darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              ${parseFloat(ad.approximate_spend).toLocaleString()}
                            </p>
                          </div>
                        )}

                        <div className={`p-3 rounded-lg ${
                          darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                        }`}>
                          <p className="text-xs text-gray-500 mb-1">PLATFORM</p>
                          <p className={`text-sm font-semibold capitalize ${
                            darkMode ? 'text-white' : 'text-gray-900'
                          }`}>
                            {ad.platform}
                          </p>
                        </div>

                        {ad.how_known && (
                          <div className={`p-3 rounded-lg ${
                            darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                          }`}>
                            <p className="text-xs text-gray-500 mb-1">SOURCE</p>
                            <p className={`text-sm capitalize ${
                              darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              {ad.how_known.replace('_', ' ')}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* URL */}
                      {ad.url && (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">AD URL</p>
                          <a
                            href={ad.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-[#7163BA] hover:underline truncate block"
                          >
                            {ad.url}
                          </a>
                        </div>
                      )}

                      {/* Reporter */}
                      <div className={`flex items-center gap-2 p-3 rounded-lg ${
                        darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'
                      }`}>
                        <User size={14} className="text-gray-500" />
                        <div className="flex-1">
                          <p className="text-xs text-gray-500">REPORTED BY</p>
                          <p className={`text-sm font-medium ${
                            darkMode ? 'text-white' : 'text-gray-900'
                          }`}>
                            {ad.reported_by}
                          </p>
                        </div>
                        <p className="text-xs text-gray-500">
                          {new Date(ad.reported_at).toLocaleDateString()}
                        </p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-3 pt-2">
                        <button
                          onClick={() => handleVerify(ad.id)}
                          disabled={processing === ad.id}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {processing === ad.id ? (
                            <Loader size={18} className="animate-spin" />
                          ) : (
                            <CheckCircle size={18} />
                          )}
                          Approve
                        </button>

                        <button
                          onClick={() => setShowRejectModal(ad.id)}
                          disabled={processing === ad.id}
                          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <XCircle size={18} />
                          Reject
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className={`max-w-md w-full p-6 rounded-2xl ${
            darkMode ? 'bg-[#2D2844]' : 'bg-white'
          }`}>
            <h3 className={`text-xl font-bold mb-2 ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Reject Ad Buy Submission
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Please provide a reason for rejecting this submission. This will help improve future submissions.
            </p>

            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g., Image quality too low, incorrect candidate information, duplicate submission..."
              rows={4}
              className={`w-full px-4 py-3 rounded-lg border mb-4 ${
                darkMode
                  ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'
              } focus:ring-2 focus:ring-[#7163BA] outline-none resize-none`}
            />

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowRejectModal(null);
                  setRejectReason('');
                  setError('');
                }}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                  darkMode
                    ? 'bg-[#1F1B31] text-white hover:bg-[#16131F]'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={() => handleReject(showRejectModal)}
                disabled={!rejectReason.trim() || processing === showRejectModal}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processing === showRejectModal ? 'Rejecting...' : 'Confirm Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
