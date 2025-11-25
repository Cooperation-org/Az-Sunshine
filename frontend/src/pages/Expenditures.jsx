import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, ChevronLeft, Download, Loader } from "lucide-react";
import { getExpenditures, getOffices, getParties } from "../api/api";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
import FilterPanel from "../components/FilterPanel";
import { exportToCSV } from "../utils/csvExport";

export default function Expenditures() {
  const [expenditures, setExpenditures] = useState([]);
  const [allExpenditures, setAllExpenditures] = useState([]); // Store all data for filtering
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);
  
  // Filter state
  const [filters, setFilters] = useState({
    dateFrom: "",
    dateTo: "",
    amountMin: 0,
    amountMax: 1000000,
    selectedOffices: [],
    selectedParties: [],
  });
  
  // Offices and parties for filter
  const [offices, setOffices] = useState([]);
  const [isLoadingOffices, setIsLoadingOffices] = useState(false);
  const [parties, setParties] = useState([]);

  // Load offices and parties on mount
  useEffect(() => {
    loadOffices();
    loadParties();
  }, []);

  async function loadParties() {
    try {
      const partiesData = await getParties();
      // Handle both array and object response
      const partiesList = Array.isArray(partiesData) 
        ? partiesData 
        : (partiesData.results || []);
      // Extract party names
      const partyNames = partiesList.map(p => p.name || p.abbreviation || p).filter(Boolean);
      setParties(partyNames.sort());
    } catch (err) {
      console.error("Error loading parties:", err);
      // If parties endpoint doesn't exist, try to extract from expenditures data
      // This is a fallback - ideally parties should come from API
      if (allExpenditures.length > 0) {
        // Extract unique parties from expenditures if available
        // Note: This requires party data in expenditure response
        setParties([]);
      } else {
        setParties([]);
      }
    }
  }

  // Load expenditures when page changes
  useEffect(() => {
    loadExpenditures(currentPage);
  }, [currentPage]);

  // Apply filters when filters or search term changes
  useEffect(() => {
    applyFilters();
  }, [filters, searchTerm, allExpenditures]);

  async function loadOffices() {
    setIsLoadingOffices(true);
    try {
      const officesData = await getOffices();
      // Handle both array and object response
      const officesList = Array.isArray(officesData) 
        ? officesData 
        : (officesData.results || []);
      setOffices(officesList);
    } catch (err) {
      console.error("Error loading offices:", err);
      setOffices([]);
    } finally {
      setIsLoadingOffices(false);
    }
  }

  async function loadExpenditures(page) {
    setLoading(true);
    try {
      // Load more data for filtering (load all or large page size)
      const data = await getExpenditures({ page_size: 1000 });
      const allData = data.results || [];
      setAllExpenditures(allData);
      
      // Set paginated data
      const pageSize = 25;
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      setExpenditures(allData.slice(startIndex, endIndex));
      setTotalCount(data.count || allData.length);
      setTotalPages(Math.ceil((data.count || allData.length) / pageSize));
      
      // Extract unique parties and offices from expenditures data
      // Parties and offices come from subject_committee data in the backend
      // Since the frontend receives simplified data, we'll extract from what's available
      const uniqueParties = new Set();
      const uniqueOffices = new Set();
      
      allData.forEach((exp) => {
        // Extract party if available in candidate_name or other fields
        // Note: The backend may need to include party in the response
        // For now, we'll keep parties empty and let user add via API later
      });
      
      setParties(Array.from(uniqueParties).sort());
    } catch (err) {
      console.error("Error loading expenditures:", err);
      setExpenditures([]);
      setAllExpenditures([]);
    } finally {
      setLoading(false);
    }
  }

  // Apply filters to expenditures
  const applyFilters = () => {
    let filtered = [...allExpenditures];

    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((exp) => {
        return (
          (exp.ie_committee?.name || "").toLowerCase().includes(searchLower) ||
          (exp.candidate_name || "").toLowerCase().includes(searchLower) ||
          (exp.support_oppose || "").toLowerCase().includes(searchLower)
        );
      });
    }

    // Date range filter
    if (filters.dateFrom) {
      filtered = filtered.filter((exp) => {
        if (!exp.date) return false;
        return new Date(exp.date) >= new Date(filters.dateFrom);
      });
    }

    if (filters.dateTo) {
      filtered = filtered.filter((exp) => {
        if (!exp.date) return false;
        const expDate = new Date(exp.date);
        const toDate = new Date(filters.dateTo);
        toDate.setHours(23, 59, 59, 999); // Include entire end date
        return expDate <= toDate;
      });
    }

    // Amount range filter
    filtered = filtered.filter((exp) => {
      const amount = parseFloat(exp.amount || 0);
      return amount >= filters.amountMin && amount <= filters.amountMax;
    });

    // Office filter (if offices are available in expenditure data)
    // Note: Office filtering requires office data in expenditure response
    // This is a placeholder - implement when office data is available
    if (filters.selectedOffices.length > 0) {
      // If expenditure has office information, filter by selected offices
      // For now, this filter is disabled until office data is in response
      // filtered = filtered.filter((exp) => {
      //   const expOfficeId = exp.office_id || exp.office?.office_id;
      //   return filters.selectedOffices.includes(expOfficeId);
      // });
    }

    // Party filter (if parties are available in expenditure data)
    // Note: Party filtering requires party data in expenditure response
    // This is a placeholder - implement when party data is available
    if (filters.selectedParties.length > 0) {
      // If expenditure has party information, filter by selected parties
      // For now, this filter is disabled until party data is in response
      // filtered = filtered.filter((exp) => {
      //   const expParty = exp.party || exp.subject_committee?.party;
      //   return filters.selectedParties.includes(expParty);
      // });
    }

    // Update displayed expenditures with pagination
    const pageSize = 25;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    setExpenditures(filtered.slice(startIndex, endIndex));
    setTotalCount(filtered.length);
    setTotalPages(Math.ceil(filtered.length / pageSize));
  };

  // Handle filter changes
  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  // Calculate min/max amounts from data
  const calculateAmountRange = () => {
    if (allExpenditures.length === 0) return { min: 0, max: 1000000 };
    
    const amounts = allExpenditures
      .map((exp) => parseFloat(exp.amount || 0))
      .filter((amt) => amt > 0);
    
    if (amounts.length === 0) return { min: 0, max: 1000000 };
    
    const min = Math.floor(Math.min(...amounts));
    const max = Math.ceil(Math.max(...amounts));
    
    return { min, max };
  };

  const amountRange = calculateAmountRange();
  
  // Initialize filters with calculated amount range
  useEffect(() => {
    if (amountRange.min !== 0 || amountRange.max !== 1000000) {
      setFilters(prev => ({
        ...prev,
        amountMin: prev.amountMin === 0 ? amountRange.min : prev.amountMin,
        amountMax: prev.amountMax === 1000000 ? amountRange.max : prev.amountMax,
      }));
    }
  }, [amountRange]);

  // Show preloader while initial data is loading
  if (loading && currentPage === 1) {
    return <Preloader message="Loading expenditures..." />;
  }

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  // Export expenditures to CSV
  const handleExportCSV = async () => {
    try {
      setExporting(true);
      
      // Load all expenditures for export (not just current page)
      const allExpendituresData = await getExpenditures({ page_size: totalCount || 1000 });
      const allExpenditures = allExpendituresData.results || [];
      
      // Apply all filters for export
      let dataToExport = [...allExpenditures];
      
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        dataToExport = dataToExport.filter((exp) => {
          return (
            (exp.ie_committee?.name || "").toLowerCase().includes(searchLower) ||
            (exp.candidate_name || "").toLowerCase().includes(searchLower) ||
            (exp.support_oppose || "").toLowerCase().includes(searchLower)
          );
        });
      }
      
      // Date filters
      if (filters.dateFrom) {
        dataToExport = dataToExport.filter((exp) => {
          if (!exp.date) return false;
          return new Date(exp.date) >= new Date(filters.dateFrom);
        });
      }
      if (filters.dateTo) {
        dataToExport = dataToExport.filter((exp) => {
          if (!exp.date) return false;
          const expDate = new Date(exp.date);
          const toDate = new Date(filters.dateTo);
          toDate.setHours(23, 59, 59, 999);
          return expDate <= toDate;
        });
      }
      
      // Amount filters
      dataToExport = dataToExport.filter((exp) => {
        const amount = parseFloat(exp.amount || 0);
        return amount >= filters.amountMin && amount <= filters.amountMax;
      });
      
      // Define CSV columns
      const columns = [
        { key: 'date', label: 'Date' },
        { key: 'ie_committee.name', label: 'Committee Name' },
        { key: 'candidate_name', label: 'Candidate' },
        { key: 'amount', label: 'Amount' },
        { key: 'support_oppose', label: 'Support/Oppose' },
        { key: 'purpose', label: 'Purpose' },
      ];
      
      // Transform data for CSV (format dates)
      const csvData = dataToExport.map(exp => ({
        ...exp,
        date: exp.date ? formatDate(exp.date) : 'N/A',
        'ie_committee.name': exp.ie_committee?.name || 'Unknown Committee',
        amount: parseFloat(exp.amount || 0).toFixed(2),
      }));
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `expenditures_${timestamp}.csv`;
      
      // Export to CSV
      await exportToCSV(csvData, columns, filename, setExporting);
      
    } catch (error) {
      console.error("Error exporting CSV:", error);
      alert("Failed to export CSV. Please try again.");
      setExporting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* === Sidebar === */}
      <Sidebar />

      {/* === Main Content - Responsive: No left margin on mobile === */}
      <main className="flex-1 lg:ml-0 min-w-0">
        {/* === Header === */}
        <Header title="Arizona Sunshine" subtitle="Expenditures" />

        {/* === Content - Responsive padding === */}
        <div className="p-4 sm:p-6 lg:p-8">
          {loading ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              Loading expenditures...
            </div>
          ) : (
            <>
              {/* === Filter Panel === */}
              <FilterPanel
                filters={filters}
                onFiltersChange={handleFiltersChange}
                offices={offices}
                parties={parties}
                minAmount={amountRange.min}
                maxAmount={amountRange.max}
                isLoadingOffices={isLoadingOffices}
              />

              {/* === Export Button - Responsive === */}
              <div className="mb-4 sm:mb-6 flex justify-end">
                <button
                  onClick={handleExportCSV}
                  disabled={exporting || expenditures.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md active:scale-95 text-sm sm:text-base"
                >
                  {exporting ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      <span>Exporting...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      <span>Export CSV</span>
                    </>
                  )}
                </button>
              </div>

              {/* === Summary Stats - Responsive: 1 column on mobile, 3 on desktop === */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
                {/* Stats Cards - Responsive padding and text sizes */}
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Total Expenditures</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {totalCount.toLocaleString()}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Total Amount</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    ${expenditures
                      .reduce((sum, exp) => sum + parseFloat(exp.amount || 0), 0)
                      .toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                  </p>
                </div>
                <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-lg">
                  <p className="text-gray-500 text-xs sm:text-sm mb-1">Showing</p>
                  <p className="text-2xl sm:text-3xl font-bold text-gray-900">
                    {expenditures.length} {expenditures.length === 1 ? "result" : "results"}
                  </p>
                </div>
              </div>

              {/* === Expenditures Table - Responsive: Horizontal scroll on mobile === */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                {/* Table Container - Horizontal scroll on mobile */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        {/* Table Headers - Responsive text sizes and padding */}
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Date
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Committee Name
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Candidate
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Amount
                        </th>
                        <th className="text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                          Purpose
                        </th>
                      </tr>
                    </thead>
                  <tbody className="divide-y divide-gray-100">
                    {expenditures.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-gray-500">
                          {searchTerm || Object.values(filters).some(v => 
                            (Array.isArray(v) && v.length > 0) || 
                            (typeof v === 'string' && v) ||
                            (typeof v === 'number' && (v !== amountRange.min && v !== amountRange.max))
                          )
                            ? "No expenditures found matching your filters."
                            : "No expenditures found."}
                        </td>
                      </tr>
                    ) : (
                      expenditures.map((exp, idx) => (
                        <tr key={idx} className="hover:bg-purple-50/50 transition-colors duration-150">
                          {/* Table Cells - Responsive padding and text sizes */}
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 whitespace-nowrap">
                            {formatDate(exp.date)}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex items-center gap-2 sm:gap-3">
                              {/* Avatar - Responsive size */}
                              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-[#7C6BA6] to-[#5B4D7D] flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0">
                                {(exp.ie_committee?.name || "?").charAt(0).toUpperCase()}
                              </div>
                              <span className="text-xs sm:text-sm lg:text-base text-gray-900 font-medium truncate max-w-[120px] sm:max-w-none">
                                {exp.ie_committee?.name || "Unknown Committee"}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-700 font-medium truncate max-w-[100px] sm:max-w-none">
                            {exp.candidate_name || "N/A"}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm text-gray-900 font-semibold whitespace-nowrap">
                            ${parseFloat(exp.amount || 0).toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </td>
                          <td className="py-3 sm:py-5 px-3 sm:px-6">
                            <div className="flex flex-col gap-1">
                              <span
                                className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium w-fit whitespace-nowrap ${
                                  exp.support_oppose === "Support"
                                    ? "bg-green-100 text-green-700"
                                    : exp.support_oppose === "Oppose"
                                    ? "bg-red-100 text-red-700"
                                    : "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {exp.support_oppose || "Unknown"}
                              </span>
                              {exp.purpose && (
                                <span className="text-xs text-gray-500 mt-1 truncate max-w-[150px] sm:max-w-none">
                                  {exp.purpose}
                                </span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* === Pagination - Responsive: Stack on mobile === */}
              {totalPages > 1 && (
                <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
                  <p className="text-xs sm:text-sm text-gray-600">
                    Showing page {currentPage} of {totalPages} ({totalCount} total results)
                  </p>
                  {/* Pagination - Responsive: Wrap on mobile */}
                  <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center transition-all duration-200 ${
                        currentPage === 1
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                      }`}
                    >
                      <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                    {Array.from(
                      { length: Math.min(totalPages, 5) },
                      (_, i) => {
                        let page;
                        if (totalPages <= 5) {
                          page = i + 1;
                        } else if (currentPage <= 3) {
                          page = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          page = totalPages - 4 + i;
                        } else {
                          page = currentPage - 2 + i;
                        }
                        return page;
                      }
                    ).map((page) => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${
                          currentPage === page
                            ? "bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md"
                            : "bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95"
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center transition ${
                        currentPage === totalPages
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                      }`}
                    >
                      <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

