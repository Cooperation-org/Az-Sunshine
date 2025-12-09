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

import { StatsGridSkeleton, TableSkeleton, CardSkeleton } from "../components/SkeletonLoader";
import ConfirmationModal from "../components/ConfirmationModal";

// API Base URL
const API_BASE_URL = "http://167.172.30.134/api/v1/";

// Mock data - Replace with real API calls
const getDuplicateEntities = async () => {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}validation/duplicates/`);
  // return response.json();
  
  return {
    duplicates: [
      {
        id: 1,
        group_id: "group_1",
        entities: [
          {
            id: 101,
            name: "John Smith",
            name_id: 1001,
            entity_type: "Individual",
            city: "Phoenix",
            state: "AZ",
            total_contributions: 15000,
            transaction_count: 45,
            created_date: "2023-01-15",
            confidence_score: 0.95,
          },
          {
            id: 102,
            name: "John A. Smith",
            name_id: 1002,
            entity_type: "Individual",
            city: "Phoenix",
            state: "AZ",
            total_contributions: 8500,
            transaction_count: 23,
            created_date: "2023-02-20",
            confidence_score: 0.92,
          },
          {
            id: 103,
            name: "J. Smith",
            name_id: 1003,
            entity_type: "Individual",
            city: "Phoenix",
            state: "AZ",
            total_contributions: 3200,
            transaction_count: 12,
            created_date: "2023-03-10",
            confidence_score: 0.88,
          },
        ],
        similarity_reason: "Name similarity, same location",
      },
      {
        id: 2,
        group_id: "group_2",
        entities: [
          {
            id: 201,
            name: "Arizona Business Corp",
            name_id: 2001,
            entity_type: "Organization",
            city: "Tucson",
            state: "AZ",
            total_contributions: 50000,
            transaction_count: 120,
            created_date: "2022-11-05",
            confidence_score: 0.97,
          },
          {
            id: 202,
            name: "Arizona Business Corporation",
            name_id: 2002,
            entity_type: "Organization",
            city: "Tucson",
            state: "AZ",
            total_contributions: 25000,
            transaction_count: 67,
            created_date: "2023-01-12",
            confidence_score: 0.94,
          },
        ],
        similarity_reason: "Organization name variation",
      },
      {
        id: 3,
        group_id: "group_3",
        entities: [
          {
            id: 301,
            name: "Maria Garcia",
            name_id: 3001,
            entity_type: "Individual",
            city: "Scottsdale",
            state: "AZ",
            total_contributions: 8900,
            transaction_count: 34,
            created_date: "2023-04-18",
            confidence_score: 0.91,
          },
          {
            id: 302,
            name: "Maria G. Garcia",
            name_id: 3002,
            entity_type: "Individual",
            city: "Scottsdale",
            state: "AZ",
            total_contributions: 5600,
            transaction_count: 19,
            created_date: "2023-05-22",
            confidence_score: 0.89,
          },
        ],
        similarity_reason: "Name abbreviation, same location",
      },
    ],
    total_duplicate_groups: 3,
    total_duplicate_entities: 7,
  };
};

const getDataQualityMetrics = async () => {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}validation/phase1/`);
  // return response.json();
  
  return {
    total_entities: 15420,
    duplicate_entities: 7,
    entities_without_email: 3420,
    entities_without_phone: 2890,
    incomplete_addresses: 1560,
    missing_entity_types: 230,
    orphaned_transactions: 45,
    data_quality_score: 87.5,
    last_validated: new Date().toISOString(),
  };
};

const mergeDuplicateEntities = async (primaryId, duplicateIds) => {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}validation/merge-duplicates/`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ primary_id: primaryId, duplicate_ids: duplicateIds })
  // });
  // return response.json();
  
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, merged_count: duplicateIds.length });
    }, 1500);
  });
};

export default function DataValidation() {
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
      
      setDuplicates(duplicatesData.duplicates || []);
      setMetrics(metricsData);
      setTotalPages(Math.ceil((duplicatesData.duplicates || []).length / pageSize));
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

      await mergeDuplicateEntities(primaryEntity.id, duplicateIds);

      // Remove merged group from list
      setDuplicates((prev) => prev.filter((g) => g.id !== selectedGroup.id));
      setShowMergeModal(false);
      setSelectedGroup(null);
      setPrimaryEntity(null);

      // Reload metrics
      const metricsData = await getDataQualityMetrics();
      setMetrics(metricsData);

      alert(`Successfully merged ${duplicateIds.length} duplicate entities!`);
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
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 lg:ml-0 min-w-0">

        <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
          {/* Data Quality Metrics */}
          {loading && !metrics ? (
            <StatsGridSkeleton count={4} />
          ) : metrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {/* Overall Quality Score */}
              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-purple-50 rounded-xl">
                    <Shield className="w-6 h-6 text-purple-600" />
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${getQualityBadgeColor(metrics.data_quality_score)}`}>
                    {metrics.data_quality_score.toFixed(1)}%
                  </span>
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">
                  {metrics.data_quality_score.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Data Quality Score</div>
              </div>

              {/* Duplicate Entities */}
              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100">
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
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">
                  {metrics.duplicate_entities}
                </div>
                <div className="text-sm text-gray-600">Duplicate Entities</div>
              </div>

              {/* Missing Data */}
              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100">
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
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">
                  {(metrics.entities_without_email + metrics.entities_without_phone).toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Missing Contact Info</div>
              </div>

              {/* Total Entities */}
              <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-blue-50 rounded-xl">
                    <Database className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 mb-1">
                  {metrics.total_entities.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Entities</div>
              </div>
            </div>
          ) : null}

          {/* Data Issues Alerts */}
          {metrics && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
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
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 sm:p-6 border-b border-gray-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <Merge className="w-5 h-5 text-purple-600" />
                  Duplicate Entities
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {duplicates.length} duplicate group{duplicates.length !== 1 ? "s" : ""} found
                </p>
              </div>
              <button
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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
                  <div className="text-lg font-semibold text-gray-900 mb-1">No Duplicates Found</div>
                  <div className="text-sm text-gray-500">All entities are unique</div>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
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
              <div className="p-4 sm:p-6 border-t border-gray-200 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="w-10 h-10 rounded-lg bg-white text-gray-700 hover:bg-gray-100 border border-gray-300 flex items-center justify-center transition disabled:opacity-50 disabled:cursor-not-allowed"
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

