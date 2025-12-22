import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Merge,
  RefreshCw,
  Loader,
  Database,
  Users,
  FileText,
  TrendingDown,
  Shield,
  AlertCircle,
  ChevronRight,
  ChevronLeft,
  Mail,
  Phone,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { useDarkMode } from "../context/DarkModeContext";
import { StatsGridSkeleton, TableSkeleton, CardSkeleton } from "../components/SkeletonLoader";
import ConfirmationModal from "../components/ConfirmationModal";
import {
  getDataQualityMetrics,
  getDuplicateEntities,
  mergeEntities
} from "../api/api";

export default function DataValidation() {
  const { darkMode } = useDarkMode();
  const [duplicates, setDuplicates] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [merging, setMerging] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [primaryEntity, setPrimaryEntity] = useState(null);
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 5;

  useEffect(() => {
    loadData();
  }, [currentPage]);

  async function loadData() {
    setLoading(true);
    try {
      const [duplicatesData, metricsData] = await Promise.all([
        getDuplicateEntities(),
        getDataQualityMetrics(),
      ]);

      // Backend returns { duplicates: [], total_found: N }
      const duplicatesList = duplicatesData?.duplicates || [];

      // Transform backend data to match frontend expectations
      // Add sequential IDs and entity_type field
      const transformedDuplicates = duplicatesList.map((dup, idx) => ({
        id: idx + 1,
        entities: dup.entities.map(entity => ({
          id: entity.id,
          name: entity.name,
          city: entity.city,
          state: 'AZ', // Backend doesn't return state, defaulting to AZ
          entity_type: 'Individual', // Backend doesn't return this
          total_contributions: 0, // Backend doesn't return this
          transaction_count: 0, // Backend doesn't return this
          confidence_score: dup.confidence_score || 0.85
        })),
        similarity_reason: dup.reason || 'Name similarity',
        confidence_score: dup.confidence_score || 0.85
      }));

      setDuplicates(transformedDuplicates);

      // Transform metrics data to match frontend expectations
      const transformedMetrics = {
        total_entities: metricsData?.total_records?.entities || 0,
        duplicate_entities: duplicatesData?.total_found || 0,
        entities_without_email: 0, // Not currently tracked
        entities_without_phone: 0, // Not currently tracked
        incomplete_addresses: metricsData?.missing_data?.entities_without_location || 0,
        missing_entity_types: 0, // Not currently tracked
        orphaned_transactions: 0, // Not currently tracked
        data_quality_score: metricsData?.transaction_completeness || 0,
        last_validated: new Date().toISOString(),
      };

      setMetrics(transformedMetrics);
      setTotalPages(Math.ceil(transformedDuplicates.length / pageSize));
    } catch (error) {
      console.error("Error loading validation data:", error);
      setDuplicates([]);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  }

  const handleMerge = async () => {
    if (!selectedGroup || !primaryEntity) return;

    setMerging(true);
    try {
      const duplicateIds = selectedGroup.entities
        .filter((e) => e.id !== primaryEntity.id)
        .map((e) => e.id);

      const result = await mergeEntities(primaryEntity.id, duplicateIds);

      // Remove merged group from list
      setDuplicates((prev) => prev.filter((g) => g.id !== selectedGroup.id));
      setShowMergeModal(false);
      setSelectedGroup(null);
      setPrimaryEntity(null);

      // Reload metrics
      await loadData();

      alert(`Successfully merged ${result.merged_count || duplicateIds.length} duplicate entities!`);
    } catch (error) {
      console.error("Error merging entities:", error);
      alert("Failed to merge entities. Please try again.");
    } finally {
      setMerging(false);
    }
  };

  const openMergeModal = (group) => {
    // Set primary entity to the one with highest confidence or most contributions
    const primary = group.entities.reduce((prev, current) =>
      prev.total_contributions > current.total_contributions ? prev : current
    );
    setSelectedGroup(group);
    setPrimaryEntity(primary);
    setShowMergeModal(true);
  };

  const getQualityBadgeColor = (score) => {
    if (score >= 90) return "bg-green-100 text-green-800";
    if (score >= 75) return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  };

  const getIssueSeverity = (count, total) => {
    const percentage = (count / total) * 100;
    if (percentage > 25) return "high";
    if (percentage > 10) return "medium";
    return "low";
  };

  const paginatedDuplicates = duplicates.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />
      <main className="flex-1 lg:ml-0 min-w-0">

        <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
          {/* Data Quality Metrics */}
          {loading && !metrics ? (
            <StatsGridSkeleton count={4} />
          ) : metrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {/* Overall Quality Score */}
              <div className={`rounded-xl p-4 sm:p-6 shadow-sm border ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
              }`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-purple-50 rounded-xl">
                    <Shield className="w-6 h-6 text-purple-600" />
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${getQualityBadgeColor(metrics.data_quality_score)}`}>
                    {metrics.data_quality_score.toFixed(1)}%
                  </span>
                </div>
                <div className={`text-2xl sm:text-3xl font-bold mb-1 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  {metrics.data_quality_score.toFixed(1)}%
                </div>
                <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Data Quality Score</div>
              </div>

              {/* Duplicate Entities */}
              <div className={`rounded-xl p-4 sm:p-6 shadow-sm border ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
              }`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-red-50 rounded-xl">
                    <Users className="w-6 h-6 text-red-600" />
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    metrics.duplicate_entities > 0 ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"
                  }`}>
                    {metrics.duplicate_entities > 0 ? "Issue" : "Clean"}
                  </span>
                </div>
                <div className={`text-2xl sm:text-3xl font-bold mb-1 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  {metrics.duplicate_entities}
                </div>
                <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Duplicate Entities</div>
              </div>

              {/* Missing Data */}
              <div className={`rounded-xl p-4 sm:p-6 shadow-sm border ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
              }`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-amber-50 rounded-xl">
                    <AlertTriangle className="w-6 h-6 text-amber-600" />
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    metrics.entities_without_email + metrics.entities_without_phone > 5000
                      ? "bg-red-100 text-red-800"
                      : "bg-amber-100 text-amber-800"
                  }`}>
                    {metrics.entities_without_email + metrics.entities_without_phone > 5000 ? "High" : "Medium"}
                  </span>
                </div>
                <div className={`text-2xl sm:text-3xl font-bold mb-1 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  {(metrics.entities_without_email + metrics.entities_without_phone).toLocaleString()}
                </div>
                <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Missing Contact Info</div>
              </div>

              {/* Total Entities */}
              <div className={`rounded-xl p-4 sm:p-6 shadow-sm border ${
                darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
              }`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-blue-50 rounded-xl">
                    <Database className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div className={`text-2xl sm:text-3xl font-bold mb-1 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  {metrics.total_entities.toLocaleString()}
                </div>
                <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Entities</div>
              </div>
            </div>
          ) : null}

          {/* Data Issues Alerts */}
          {metrics && (
            <div className={`rounded-xl shadow-sm border p-4 sm:p-6 ${
              darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
            }`}>
              <h3 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                <AlertCircle className="w-5 h-5 text-amber-600" />
                Data Quality Issues
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  {
                    label: "Entities without Email",
                    count: metrics.entities_without_email,
                    total: metrics.total_entities,
                    icon: Mail,
                  },
                  {
                    label: "Entities without Phone",
                    count: metrics.entities_without_phone,
                    total: metrics.total_entities,
                    icon: Phone,
                  },
                  {
                    label: "Incomplete Addresses",
                    count: metrics.incomplete_addresses,
                    total: metrics.total_entities,
                    icon: FileText,
                  },
                  {
                    label: "Missing Entity Types",
                    count: metrics.missing_entity_types,
                    total: metrics.total_entities,
                    icon: Database,
                  },
                ].map((issue, index) => {
                  const severity = getIssueSeverity(issue.count, issue.total);
                  const Icon = issue.icon;
                  return (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border-2 ${
                        severity === "high"
                          ? "bg-red-50 border-red-200"
                          : severity === "medium"
                          ? "bg-amber-50 border-amber-200"
                          : "bg-blue-50 border-blue-200"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Icon
                          className={`w-4 h-4 ${
                            severity === "high"
                              ? "text-red-600"
                              : severity === "medium"
                              ? "text-amber-600"
                              : "text-blue-600"
                          }`}
                        />
                        <span className="text-sm font-medium text-gray-900">{issue.label}</span>
                      </div>
                      <div className="text-2xl font-bold text-gray-900 mb-1">
                        {issue.count.toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-600">
                        {((issue.count / issue.total) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Duplicate Entities Section */}
          <div className={`rounded-xl shadow-sm border overflow-hidden ${
            darkMode ? 'bg-[#2D2844] border-gray-700' : 'bg-white border-gray-100'
          }`}>
            <div className={`p-4 sm:p-6 border-b flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
              darkMode ? 'border-gray-700' : 'border-gray-200'
            }`}>
              <div>
                <h3 className={`text-lg sm:text-xl font-semibold flex items-center gap-2 ${
                  darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  <Merge className="w-5 h-5 text-purple-600" />
                  Duplicate Entities
                </h3>
                <p className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {duplicates.length} duplicate group{duplicates.length !== 1 ? "s" : ""} found
                </p>
              </div>
              <button
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-[#7667C1] text-white rounded-lg hover:bg-[#6557B1] transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            {loading && currentPage === 1 ? (
              <div className="p-4 sm:p-6 space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <CardSkeleton key={i} lines={3} />
                ))}
              </div>
            ) : paginatedDuplicates.length === 0 ? (
              <div className="flex items-center justify-center h-64 text-center">
                <div>
                  <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
                  <div className={`text-lg font-semibold mb-1 ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}>No Duplicates Found</div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>All entities are unique</div>
                </div>
              </div>
            ) : (
              <div className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
                {paginatedDuplicates.map((group) => (
                  <div key={group.id} className="p-4 sm:p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
                            {group.entities.length} duplicates
                          </span>
                          <span className="text-sm text-gray-500">{group.similarity_reason}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => openMergeModal(group)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                      >
                        <Merge className="w-4 h-4" />
                        Merge
                      </button>
                    </div>

                    <div className="space-y-3">
                      {group.entities.map((entity, index) => (
                        <div
                          key={entity.id}
                          className={`p-4 rounded-lg border-2 ${
                            primaryEntity?.id === entity.id
                              ? "bg-purple-50 border-purple-300"
                              : "bg-gray-50 border-gray-200"
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-semibold text-gray-900">{entity.name}</h4>
                                {primaryEntity?.id === entity.id && (
                                  <span className="px-2 py-0.5 bg-purple-600 text-white rounded-full text-xs font-medium">
                                    Primary
                                  </span>
                                )}
                                <span className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded-full text-xs">
                                  {entity.entity_type}
                                </span>
                              </div>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm text-gray-600">
                                <div>
                                  <span className="font-medium">Location:</span> {entity.city}, {entity.state}
                                </div>
                                <div>
                                  <span className="font-medium">Contributions:</span> ${entity.total_contributions.toLocaleString()}
                                </div>
                                <div>
                                  <span className="font-medium">Transactions:</span> {entity.transaction_count}
                                </div>
                                <div>
                                  <span className="font-medium">Confidence:</span> {(entity.confidence_score * 100).toFixed(0)}%
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className={`p-4 sm:p-6 border-t flex items-center justify-between ${
                darkMode ? 'border-gray-700' : 'border-gray-200'
              }`}>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className={`w-10 h-10 rounded-lg border flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed ${
                      darkMode
                        ? 'bg-[#1F1B31] text-gray-300 hover:bg-[#16131F] border-gray-700'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'
                    }`}
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className={`w-10 h-10 rounded-lg border flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed ${
                      darkMode
                        ? 'bg-[#1F1B31] text-gray-300 hover:bg-[#16131F] border-gray-700'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'
                    }`}
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Merge Confirmation Modal */}
        <ConfirmationModal
          isOpen={showMergeModal}
          onClose={() => {
            setShowMergeModal(false);
            setSelectedGroup(null);
            setPrimaryEntity(null);
          }}
          onConfirm={handleMerge}
          title="Merge Duplicate Entities"
          message={
            selectedGroup && primaryEntity
              ? `Are you sure you want to merge ${selectedGroup.entities.length - 1} duplicate entity/entities into "${primaryEntity.name}"? This action cannot be undone. All transactions and data from duplicate entities will be consolidated into the primary entity.`
              : ""
          }
          confirmText={merging ? "Merging..." : "Confirm Merge"}
          cancelText="Cancel"
          type="warning"
        />
      </main>
    </div>
  );
}

