import React, { useState, useEffect } from "react";
import {
  Mail,
  Send,
  Eye,
  MousePointerClick,
  Users,
  Filter,
  CheckCircle,
  Clock,
  AlertCircle,
  Search,
  X,
  ChevronRight,
  ChevronLeft,
  Loader,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
import { getSOICandidates } from "../api/api";

// API Base URL
const API_BASE_URL = "http://167.172.30.134/api/v1/";

// Mock email statistics (replace with real API calls)
const mockEmailStats = {
  total_sent: 245,
  total_opened: 189,
  total_clicked: 67,
  open_rate: 77.1,
  click_rate: 27.3,
  recent_campaigns: [
    {
      id: 1,
      subject: "Statement of Interest Request",
      sent: 45,
      opened: 38,
      clicked: 12,
      date: "2024-11-05",
    },
    {
      id: 2,
      subject: "Follow-up: SOI Pledge",
      sent: 32,
      opened: 25,
      clicked: 8,
      date: "2024-11-03",
    },
  ],
};

// Email template presets
const emailTemplates = [
  {
    id: "soi_initial",
    name: "Initial SOI Request",
    subject: "Statement of Interest Request - {{candidate_name}}",
    body: `Dear {{candidate_name}},

We hope this message finds you well. We are reaching out regarding your candidacy for {{office}}.

We would like to request your Statement of Interest (SOI) to better understand your campaign priorities and how we might work together.

Please let us know if you have any questions or would like to discuss this further.

Best regards,
Arizona Sunshine Team`,
  },
  {
    id: "soi_followup",
    name: "SOI Follow-up",
    subject: "Follow-up: Statement of Interest Request - {{candidate_name}}",
    body: `Dear {{candidate_name}},

We wanted to follow up on our previous request for your Statement of Interest regarding your campaign for {{office}}.

Your input is valuable to us, and we would appreciate the opportunity to learn more about your campaign priorities.

Please feel free to reach out if you have any questions.

Best regards,
Arizona Sunshine Team`,
  },
  {
    id: "pledge_reminder",
    name: "Pledge Reminder",
    subject: "Reminder: SOI Pledge - {{candidate_name}}",
    body: `Dear {{candidate_name}},

This is a friendly reminder about your pending Statement of Interest pledge for {{office}}.

We look forward to receiving your response and continuing our collaboration.

Thank you for your time and consideration.

Best regards,
Arizona Sunshine Team`,
  },
];

export default function EmailCampaign() {
  // Form state
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  
  // Recipients state
  const [recipients, setRecipients] = useState([]);
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [recipientFilter, setRecipientFilter] = useState("uncontacted"); // uncontacted, pending, all
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  // Loading and sending state
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [sendProgress, setSendProgress] = useState({ sent: 0, total: 0 });
  
  // Statistics state
  const [emailStats, setEmailStats] = useState(mockEmailStats);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Load recipients based on filter
  useEffect(() => {
    loadRecipients();
  }, [recipientFilter, debouncedSearch, currentPage]);

  async function loadRecipients() {
    setLoading(true);
    try {
      const params = {
        page: currentPage,
        page_size: 20,
        search: debouncedSearch || undefined,
      };

      // Map filter to API status
      if (recipientFilter === "uncontacted") {
        params.status = "uncontacted";
      } else if (recipientFilter === "pending") {
        params.status = "contacted";
        // Note: You may need to add a separate endpoint for pending pledges
      }

      const data = await getSOICandidates(params);
      
      // Handle both array and paginated response
      const candidatesList = Array.isArray(data) 
        ? data 
        : (data.results || []);
      
      setRecipients(candidatesList);
      
      if (data.count !== undefined) {
        setTotalPages(Math.ceil(data.count / 20));
      } else {
        setTotalPages(1);
      }
    } catch (err) {
      console.error("Error loading recipients:", err);
      setRecipients([]);
    } finally {
      setLoading(false);
    }
  }

  // Load email statistics
  useEffect(() => {
    loadEmailStats();
  }, []);

  async function loadEmailStats() {
    // TODO: Replace with real API call
    // const stats = await getEmailStatistics();
    // setEmailStats(stats);
    setEmailStats(mockEmailStats);
  }

  // Handle template selection
  const handleTemplateSelect = (templateId) => {
    const template = emailTemplates.find((t) => t.id === templateId);
    if (template) {
      setSelectedTemplate(templateId);
      setEmailSubject(template.subject);
      setEmailBody(template.body);
    }
  };

  // Replace template variables with actual data
  const replaceTemplateVariables = (text, candidate) => {
    return text
      .replace(/\{\{candidate_name\}\}/g, candidate.name || candidate.candidate_name || "Candidate")
      .replace(/\{\{office\}\}/g, candidate.office?.name || candidate.office_name || "Office");
  };

  // Toggle recipient selection
  const toggleRecipient = (recipientId) => {
    setSelectedRecipients((prev) => {
      if (prev.includes(recipientId)) {
        return prev.filter((id) => id !== recipientId);
      } else {
        return [...prev, recipientId];
      }
    });
  };

  // Select all visible recipients
  const selectAllRecipients = () => {
    const allIds = recipients.map((r) => r.id);
    setSelectedRecipients(allIds);
  };

  // Deselect all recipients
  const deselectAllRecipients = () => {
    setSelectedRecipients([]);
  };

  // Send emails
  const handleSendEmails = async () => {
    if (selectedRecipients.length === 0) {
      alert("Please select at least one recipient.");
      return;
    }

    if (!emailSubject.trim() || !emailBody.trim()) {
      alert("Please fill in both subject and body.");
      return;
    }

    if (!confirm(`Send email to ${selectedRecipients.length} recipient(s)?`)) {
      return;
    }

    setSending(true);
    setSendProgress({ sent: 0, total: selectedRecipients.length });

    try {
      // TODO: Replace with real API call
      // Simulate sending emails
      for (let i = 0; i < selectedRecipients.length; i++) {
        const recipient = recipients.find((r) => r.id === selectedRecipients[i]);
        
        // Simulate API call delay
        await new Promise((resolve) => setTimeout(resolve, 500));
        
        // TODO: Replace with actual API call
        // await sendEmail({
        //   recipient_id: recipient.id,
        //   subject: replaceTemplateVariables(emailSubject, recipient),
        //   body: replaceTemplateVariables(emailBody, recipient),
        // });

        setSendProgress({ sent: i + 1, total: selectedRecipients.length });
      }

      alert(`Successfully sent ${selectedRecipients.length} email(s)!`);
      setSelectedRecipients([]);
      setEmailSubject("");
      setEmailBody("");
      setSelectedTemplate("");
      loadEmailStats(); // Refresh statistics
    } catch (err) {
      console.error("Error sending emails:", err);
      alert("Error sending emails. Please try again.");
    } finally {
      setSending(false);
      setSendProgress({ sent: 0, total: 0 });
    }
  };

  // Filter recipients based on search
  const filteredRecipients = recipients.filter((recipient) => {
    if (!debouncedSearch) return true;
    const searchLower = debouncedSearch.toLowerCase();
    const name = (recipient.name || recipient.candidate_name || "").toLowerCase();
    const office = (recipient.office?.name || recipient.office_name || "").toLowerCase();
    return name.includes(searchLower) || office.includes(searchLower);
  });

  // Show preloader on initial load
  if (loading && currentPage === 1) {
    return <Preloader message="Loading email campaign..." />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />

      <main className="flex-1 lg:ml-0 min-w-0">
        <Header title="Arizona Sunshine" subtitle="Email Campaign" />

        <div className="p-4 sm:p-6 lg:p-8">
          {/* Email Statistics Cards - Responsive: 1 column on mobile, 4 on desktop */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-4 sm:mb-6">
            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-xs sm:text-sm">Total Sent</p>
                <Mail className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                {emailStats.total_sent}
              </p>
            </div>

            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-xs sm:text-sm">Opened</p>
                <Eye className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                {emailStats.total_opened}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {emailStats.open_rate}% open rate
              </p>
            </div>

            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-xs sm:text-sm">Clicked</p>
                <MousePointerClick className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                {emailStats.total_clicked}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {emailStats.click_rate}% click rate
              </p>
            </div>

            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gray-500 text-xs sm:text-sm">Recipients</p>
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                {selectedRecipients.length}
              </p>
              <p className="text-xs text-gray-500 mt-1">Selected</p>
            </div>
          </div>

          {/* Main Content Grid - Responsive: 1 column on mobile, 2 on desktop */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
            {/* Email Composition Form */}
            <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4">
                Compose Email
              </h2>

              {/* Template Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Template
                </label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => handleTemplateSelect(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 hover:border-gray-400"
                >
                  <option value="">Select a template...</option>
                  {emailTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Subject */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject
                </label>
                <input
                  type="text"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  placeholder="Email subject..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 hover:border-gray-400"
                />
              </div>

              {/* Body */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Body
                </label>
                <textarea
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  placeholder="Email body... (Use {{candidate_name}} and {{office}} for variables)"
                  rows={10}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 hover:border-gray-400 resize-y"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Variables: {"{{candidate_name}}"}, {"{{office}}"}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                <button
                  onClick={() => setShowPreview(!showPreview)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium"
                >
                  <Eye className="w-4 h-4 inline mr-2" />
                  {showPreview ? "Hide" : "Show"} Preview
                </button>
                <button
                  onClick={handleSendEmails}
                  disabled={sending || selectedRecipients.length === 0}
                  className="flex-1 px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md active:scale-95"
                >
                  {sending ? (
                    <>
                      <Loader className="w-4 h-4 inline mr-2 animate-spin" />
                      Sending... ({sendProgress.sent}/{sendProgress.total})
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 inline mr-2" />
                      Send ({selectedRecipients.length})
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Email Preview */}
            {showPreview && (
              <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6">
                <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4">
                  Email Preview
                </h2>
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="mb-4 pb-4 border-b border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">To: [Recipient Email]</p>
                    <p className="text-xs text-gray-500 mb-1">Subject:</p>
                    <p className="font-semibold text-gray-900">
                      {emailSubject || "(No subject)"}
                    </p>
                  </div>
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {emailBody || "(No body)"}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Recipients Selection */}
          <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
              <h2 className="text-lg sm:text-xl font-bold text-gray-900">
                Select Recipients
              </h2>

              {/* Filter Tabs */}
              <div className="flex gap-2 flex-wrap">
                {[
                  { id: "uncontacted", label: "Uncontacted", icon: AlertCircle },
                  { id: "pending", label: "Pending", icon: Clock },
                  { id: "all", label: "All", icon: Users },
                ].map((filter) => {
                  const Icon = filter.icon;
                  return (
                    <button
                      key={filter.id}
                      onClick={() => {
                        setRecipientFilter(filter.id);
                        setCurrentPage(1);
                      }}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                        recipientFilter === filter.id
                          ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200 active:scale-95"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {filter.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Search */}
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search recipients..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 hover:border-gray-400 text-sm sm:text-base"
                />
              </div>
            </div>

            {/* Select All / Deselect All */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={selectAllRecipients}
                  className="text-sm text-white bg-purple-600 hover:bg-purple-700 font-medium"
                >
                  Select All
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={deselectAllRecipients}
                  className="text-sm text-white bg-purple-600 hover:bg-purple-700 font-medium"
                >
                  Deselect All
                </button>
              </div>
              <p className="text-sm text-gray-600">
                {selectedRecipients.length} selected
              </p>
            </div>

            {/* Recipients List */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="max-h-[400px] overflow-y-auto">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader className="w-6 h-6 animate-spin text-purple-600" />
                  </div>
                ) : filteredRecipients.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    No recipients found.
                  </div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 w-12">
                          <input
                            type="checkbox"
                            checked={
                              filteredRecipients.length > 0 &&
                              filteredRecipients.every((r) =>
                                selectedRecipients.includes(r.id)
                              )
                            }
                            onChange={(e) => {
                              if (e.target.checked) {
                                selectAllRecipients();
                              } else {
                                deselectAllRecipients();
                              }
                            }}
                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                          />
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                          Candidate
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                          Office
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                          Email
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {filteredRecipients.map((recipient) => {
                        const isSelected = selectedRecipients.includes(recipient.id);
                        const status = recipient.pledge_received
                          ? "pledged"
                          : recipient.contacted
                          ? "pending"
                          : "uncontacted";

                        return (
                          <tr
                            key={recipient.id}
                            className={`hover:bg-purple-50/50 transition-colors duration-150 ${
                              isSelected ? "bg-purple-50" : ""
                            }`}
                          >
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleRecipient(recipient.id)}
                                className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                                  {(recipient.name || recipient.candidate_name || "?").charAt(0).toUpperCase()}
                                </div>
                                <span className="text-sm font-medium text-gray-900">
                                  {recipient.name || recipient.candidate_name || "Unknown"}
                                </span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-700">
                              {recipient.office?.name || recipient.office_name || "N/A"}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-700">
                              {recipient.email || "N/A"}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  status === "pledged"
                                    ? "bg-green-100 text-green-700"
                                    : status === "pending"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-red-100 text-red-700"
                                }`}
                              >
                                {status === "pledged"
                                  ? "Pledged"
                                  : status === "pending"
                                  ? "Pending"
                                  : "Uncontacted"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Recent Campaigns Statistics */}
          <div className="bg-white rounded-2xl shadow-lg p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-bold text-gray-900 mb-4">
              Recent Campaigns
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      Subject
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      Sent
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      Opened
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      Clicked
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {emailStats.recent_campaigns.map((campaign) => (
                    <tr
                      key={campaign.id}
                      className="hover:bg-purple-50/50 transition-colors duration-150"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {campaign.subject}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {campaign.sent}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {campaign.opened} (
                        {((campaign.opened / campaign.sent) * 100).toFixed(1)}%)
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {campaign.clicked} (
                        {((campaign.clicked / campaign.sent) * 100).toFixed(1)}%)
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {new Date(campaign.date).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

