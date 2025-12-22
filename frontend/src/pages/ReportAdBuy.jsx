import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getOffices, getCandidates, submitAdBuy } from '../api/api';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import {
  Upload, Calendar, Check, X, AlertCircle, 
  Image as ImageIcon, Loader, Info, Megaphone
} from 'lucide-react';

// --- BANNER COMPONENT (Consistent with other pages) ---
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
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-2">
          <Megaphone size={28} style={{ color: '#A78BFA' }} />
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
            Report <span style={{ color: '#A78BFA' }}>Ad Buy</span>
          </h1>
        </div>
        <p className="text-white/70 text-sm max-w-2xl">
          Help us track political advertising in Arizona by reporting ads you've seen.
        </p>
      </div>
    </div>
  );
};

export default function ReportAdBuy() {
  const { darkMode } = useDarkMode();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    image: null,
    url: '',
    ad_date: '',
    platform: '',
    paid_for_by: '',
    approximate_spend: '',
    how_known: '',
    office_id: '',
    candidate_id: '',
    support_oppose: '',
    reported_by: ''
  });

  // UI state
  const [offices, setOffices] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingOffices, setLoadingOffices] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  // Load offices on mount
  useEffect(() => {
    async function loadOffices() {
      try {
        const data = await getOffices();
        setOffices(data);
      } catch (e) {
        console.error('Failed to load offices:', e);
        setError('Failed to load offices. Please refresh the page.');
      } finally {
        setLoadingOffices(false);
      }
    }
    loadOffices();
  }, []);

  // Load candidates when office changes
  useEffect(() => {
    async function loadCandidates() {
      if (formData.office_id) {
        try {
          const data = await getCandidates({ office_id: formData.office_id });
          setCandidates(data.results || data);
          setFormData(prev => ({ ...prev, candidate_id: '' }));
        } catch (e) {
          console.error('Failed to load candidates:', e);
          setError('Failed to load candidates for this office.');
        }
      } else {
        setCandidates([]);
      }
    }
    loadCandidates();
  }, [formData.office_id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleImageChange = (file) => {
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Please upload a JPG, PNG, GIF, or WebP image.');
      return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('Image must be less than 10MB.');
      return;
    }

    setFormData(prev => ({ ...prev, image: file }));
    setError('');

    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const onFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageChange(e.target.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageChange(e.dataTransfer.files[0]);
    }
  };

  const removeImage = () => {
    setFormData(prev => ({ ...prev, image: null }));
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const validateForm = () => {
    if (!formData.image) {
      setError('Please upload an image of the ad.');
      return false;
    }
    if (!formData.ad_date) {
      setError('Please select the date you saw this ad.');
      return false;
    }
    if (!formData.platform) {
      setError('Please select the platform where you saw this ad.');
      return false;
    }
    if (!formData.paid_for_by.trim()) {
      setError('Please enter who paid for this ad (from the disclaimer).');
      return false;
    }
    if (!formData.office_id) {
      setError('Please select the office for this ad.');
      return false;
    }
    if (!formData.candidate_id) {
      setError('Please select the candidate this ad is about.');
      return false;
    }
    if (!formData.support_oppose) {
      setError('Please indicate if this ad supports or opposes the candidate.');
      return false;
    }
    if (!formData.reported_by.trim()) {
      setError('Please enter your name or email.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formDataObj = new FormData();
      formDataObj.append('image', formData.image);
      formDataObj.append('ad_date', formData.ad_date);
      formDataObj.append('platform', formData.platform);
      formDataObj.append('paid_for_by', formData.paid_for_by);
      formDataObj.append('candidate', formData.candidate_id);
      formDataObj.append('support_oppose', formData.support_oppose);
      formDataObj.append('reported_by', formData.reported_by);

      if (formData.url) formDataObj.append('url', formData.url);
      if (formData.approximate_spend) formDataObj.append('approximate_spend', formData.approximate_spend);
      if (formData.how_known) formDataObj.append('how_known', formData.how_known);

      await submitAdBuy(formDataObj);
      setSuccess(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Submission error:', err);
      if (err.response?.data) {
        const errors = err.response.data;
        if (typeof errors === 'object') {
          const errorMessages = Object.entries(errors)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('; ');
          setError(errorMessages);
        } else {
          setError(errors.toString());
        }
      } else {
        setError('Failed to submit ad buy report. Please try again.');
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSuccess(false);
    setFormData({
      image: null,
      url: '',
      ad_date: '',
      platform: '',
      paid_for_by: '',
      approximate_spend: '',
      how_known: '',
      office_id: '',
      candidate_id: '',
      support_oppose: '',
      reported_by: ''
    });
    setImagePreview(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Success screen
  if (success) {
    return (
      <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
        <Sidebar />
        <main className="flex-1 min-w-0">
          <div className="p-4 sm:p-6 lg:p-8">
            <div className="max-w-2xl mx-auto">
              <div className={`p-8 md:p-12 rounded-2xl text-center border shadow-lg ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
              }`}>
                <div className="w-16 h-16 bg-green-500/20 border border-green-500/50 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Check size={32} className="text-green-500" strokeWidth={2.5} />
                </div>
                <h2 className={`text-2xl font-bold mb-3 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Report Submitted Successfully
                </h2>
                <p className={`text-sm mb-8 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Thank you for helping us track political advertising in Arizona. Our team will review your submission shortly.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={resetForm}
                    className="px-6 py-3 bg-[#7667C1] hover:bg-[#6556b0] text-white text-sm font-medium rounded-full transition-all active:scale-95"
                  >
                    Submit Another Report
                  </button>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className={`px-6 py-3 text-sm font-medium rounded-full transition-all active:scale-95 ${
                      darkMode 
                        ? 'bg-[#1F1B31] text-gray-300 hover:bg-[#252035]' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Back to Dashboard
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner />

          {/* Error Banner */}
          {error && (
            <div className={`max-w-5xl mx-auto mb-6 p-4 rounded-2xl border flex items-start gap-3 ${
              darkMode 
                ? 'bg-red-500/5 border-red-500/50' 
                : 'bg-red-50 border-red-200'
            }`}>
              <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className={`text-sm font-medium ${darkMode ? 'text-red-400' : 'text-red-800'}`}>{error}</p>
              </div>
              <button 
                onClick={() => setError('')} 
                className={`p-1 rounded-lg hover:bg-red-500/10 transition-colors ${
                  darkMode ? 'text-red-400' : 'text-red-600'
                }`}
              >
                <X size={18} />
              </button>
            </div>
          )}

          {/* Form */}
          <div className="max-w-5xl mx-auto">
            <form onSubmit={handleSubmit} className={`rounded-2xl border shadow-lg overflow-hidden ${
              darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
            }`}>
              <div className="p-6 md:p-8 space-y-8">
                
                {/* Section: Ad Details */}
                <div>
                  <h3 className={`text-xs font-bold uppercase tracking-widest mb-6 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Ad Information
                  </h3>

                  {/* Image Upload */}
                  <div className="mb-6">
                    <label className={`block text-sm font-medium mb-2 ${
                      darkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      Ad Screenshot or Photo <span className="text-red-400">*</span>
                    </label>
                    <p className={`text-xs mb-3 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Upload a clear photo or screenshot of the political ad (max 10MB)
                    </p>

                    {!imagePreview ? (
                      <div
                        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
                          dragActive
                            ? 'border-[#7667C1] bg-[#7667C1]/5'
                            : darkMode
                            ? 'border-gray-700 hover:border-gray-600'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <Upload size={40} className={`mx-auto mb-4 ${
                          dragActive ? 'text-[#7667C1]' : darkMode ? 'text-gray-500' : 'text-gray-400'
                        }`} />
                        <p className={`text-sm font-medium mb-1 ${
                          darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {dragActive ? 'Drop your file here' : 'Click to upload or drag and drop'}
                        </p>
                        <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                          JPG, PNG, GIF, or WebP (max 10MB)
                        </p>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/jpeg,image/png,image/gif,image/webp"
                          onChange={onFileInputChange}
                          className="hidden"
                        />
                      </div>
                    ) : (
                      <div className={`relative rounded-2xl overflow-hidden border ${
                        darkMode ? 'border-gray-700' : 'border-gray-200'
                      }`}>
                        <img src={imagePreview} alt="Ad preview" className="w-full" />
                        <button
                          type="button"
                          onClick={removeImage}
                          className="absolute top-3 right-3 p-2 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors shadow-lg"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Date and Platform Row */}
                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    {/* Date */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        Date You Saw This Ad <span className="text-red-400">*</span>
                      </label>
                      <div className="relative">
                        <Calendar size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 ${
                          darkMode ? 'text-gray-400' : 'text-gray-500'
                        }`} />
                        <input
                          type="date"
                          name="ad_date"
                          value={formData.ad_date}
                          onChange={handleChange}
                          max={getTodayDate()}
                          className={`w-full pl-11 pr-4 py-3 rounded-xl border-none text-sm ${
                            darkMode
                              ? 'bg-[#1F1B31] text-white'
                              : 'bg-gray-50 text-gray-900'
                          } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                        />
                      </div>
                    </div>

                    {/* Platform */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        Platform <span className="text-red-400">*</span>
                      </label>
                      <select
                        name="platform"
                        value={formData.platform}
                        onChange={handleChange}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                          darkMode
                            ? 'bg-[#1F1B31] text-white'
                            : 'bg-gray-50 text-gray-900'
                        } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                      >
                        <option value="">Select platform...</option>
                        <option value="tv">Television</option>
                        <option value="radio">Radio</option>
                        <option value="digital">Digital/Online</option>
                        <option value="print">Print (Newspaper/Magazine)</option>
                        <option value="mail">Direct Mail</option>
                        <option value="billboard">Billboard/Outdoor</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>

                  {/* Paid For By */}
                  <div className="mb-6">
                    <label className={`block text-sm font-medium mb-2 ${
                      darkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      Paid For By <span className="text-red-400">*</span>
                    </label>
                    <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Enter the committee name from the ad disclaimer
                    </p>
                    <input
                      type="text"
                      name="paid_for_by"
                      value={formData.paid_for_by}
                      onChange={handleChange}
                      placeholder="e.g., Friends of Candidate Smith"
                      className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                        darkMode
                          ? 'bg-[#1F1B31] text-white placeholder-gray-500'
                          : 'bg-gray-50 text-gray-900 placeholder-gray-400'
                      } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                    />
                  </div>
                </div>

                {/* Section: Candidate Information */}
                <div>
                  <h3 className={`text-xs font-bold uppercase tracking-widest mb-6 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Candidate Information
                  </h3>

                  {/* Office and Candidate Row */}
                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    {/* Office */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        Office <span className="text-red-400">*</span>
                      </label>
                      <select
                        name="office_id"
                        value={formData.office_id}
                        onChange={handleChange}
                        disabled={loadingOffices}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                          darkMode
                            ? 'bg-[#1F1B31] text-white'
                            : 'bg-gray-50 text-gray-900'
                        } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        <option value="">Select office...</option>
                        {offices.map(office => (
                          <option key={office.office_id} value={office.office_id}>
                            {office.name}
                          </option>
                        ))}
                      </select>
                      {loadingOffices && (
                        <p className={`text-xs mt-2 flex items-center gap-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          <Loader size={12} className="animate-spin" />
                          Loading offices...
                        </p>
                      )}
                    </div>

                    {/* Candidate */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        Candidate <span className="text-red-400">*</span>
                      </label>
                      <select
                        name="candidate_id"
                        value={formData.candidate_id}
                        onChange={handleChange}
                        disabled={!formData.office_id}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                          darkMode
                            ? 'bg-[#1F1B31] text-white'
                            : 'bg-gray-50 text-gray-900'
                        } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        <option value="">Select candidate...</option>
                        {candidates.map(candidate => (
                          <option key={candidate.committee_id} value={candidate.committee_id}>
                            {candidate.name__first_name} {candidate.name__last_name}
                          </option>
                        ))}
                      </select>
                      {!formData.office_id && (
                        <p className={`text-xs mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                          Please select an office first
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Support/Oppose */}
                  <div className="mb-6">
                    <label className={`block text-sm font-medium mb-2 ${
                      darkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      Does This Ad Support or Oppose the Candidate? <span className="text-red-400">*</span>
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'support', label: 'Support' },
                        { value: 'oppose', label: 'Oppose' },
                        { value: 'neutral', label: 'Neutral' }
                      ].map(option => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setFormData(prev => ({ ...prev, support_oppose: option.value }))}
                          className={`py-3 px-4 rounded-xl text-sm font-medium transition-all ${
                            formData.support_oppose === option.value
                              ? 'bg-[#7667C1] text-white shadow-lg'
                              : darkMode
                              ? 'bg-[#1F1B31] text-gray-400 hover:text-gray-200 hover:bg-[#252035]'
                              : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Section: Optional Details */}
                <div>
                  <h3 className={`text-xs font-bold uppercase tracking-widest mb-6 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Additional Details <span className="text-xs font-normal lowercase">(Optional)</span>
                  </h3>

                  {/* URL */}
                  <div className="mb-6">
                    <label className={`block text-sm font-medium mb-2 ${
                      darkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      Ad URL
                    </label>
                    <input
                      type="url"
                      name="url"
                      value={formData.url}
                      onChange={handleChange}
                      placeholder="https://..."
                      className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                        darkMode
                          ? 'bg-[#1F1B31] text-white placeholder-gray-500'
                          : 'bg-gray-50 text-gray-900 placeholder-gray-400'
                      } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                    />
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    {/* Approximate Spend */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        Estimated Cost
                      </label>
                      <div className="relative">
                        <span className={`absolute left-4 top-1/2 -translate-y-1/2 text-sm ${
                          darkMode ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          $
                        </span>
                        <input
                          type="number"
                          name="approximate_spend"
                          value={formData.approximate_spend}
                          onChange={handleChange}
                          placeholder="0.00"
                          step="0.01"
                          min="0"
                          className={`w-full pl-8 pr-4 py-3 rounded-xl border-none text-sm ${
                            darkMode
                              ? 'bg-[#1F1B31] text-white placeholder-gray-500'
                              : 'bg-gray-50 text-gray-900 placeholder-gray-400'
                          } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                        />
                      </div>
                    </div>

                    {/* How Known */}
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        darkMode ? 'text-white' : 'text-gray-900'
                      }`}>
                        How Do You Know?
                      </label>
                      <select
                        name="how_known"
                        value={formData.how_known}
                        onChange={handleChange}
                        className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                          darkMode
                            ? 'bg-[#1F1B31] text-white'
                            : 'bg-gray-50 text-gray-900'
                        } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                      >
                        <option value="">Select...</option>
                        <option value="disclaimer">From ad disclaimer</option>
                        <option value="research">Personal research</option>
                        <option value="estimate">Educated estimate</option>
                        <option value="unknown">Not sure</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Section: Your Information */}
                <div>
                  <h3 className={`text-xs font-bold uppercase tracking-widest mb-6 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Your Information
                  </h3>

                  <div>
                    <label className={`block text-sm font-medium mb-2 ${
                      darkMode ? 'text-white' : 'text-gray-900'
                    }`}>
                      Your Name or Email <span className="text-red-400">*</span>
                    </label>
                    <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      This helps us prevent spam and allows us to contact you if we have questions
                    </p>
                    <input
                      type="text"
                      name="reported_by"
                      value={formData.reported_by}
                      onChange={handleChange}
                      placeholder="John Doe or john@example.com"
                      className={`w-full px-4 py-3 rounded-xl border-none text-sm ${
                        darkMode
                          ? 'bg-[#1F1B31] text-white placeholder-gray-500'
                          : 'bg-gray-50 text-gray-900 placeholder-gray-400'
                      } outline-none focus:ring-1 focus:ring-[#7667C1] transition-all`}
                    />
                  </div>
                </div>
              </div>

              {/* Submit Footer */}
              <div className={`p-6 md:p-8 border-t ${
                darkMode ? 'bg-[#1F1B31] border-gray-700' : 'bg-gray-50 border-gray-100'
              }`}>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 bg-[#7667C1] hover:bg-[#6556b0] text-white rounded-2xl text-sm font-bold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20"
                >
                  {loading ? (
                    <>
                      <Loader size={20} className="animate-spin" />
                      Submitting Report...
                    </>
                  ) : (
                    'Submit Report'
                  )}
                </button>
                <p className={`text-center text-xs mt-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  All submissions are reviewed by our team before being added to the database
                </p>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}