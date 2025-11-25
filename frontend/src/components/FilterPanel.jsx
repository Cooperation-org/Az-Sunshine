import React, { useState, useEffect } from "react";
import {
  Filter,
  X,
  Calendar,
  DollarSign,
  Building,
  Users,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { getOffices } from "../api/api";

export default function FilterPanel({
  filters = {},
  onFiltersChange,
  offices = [],
  parties = [],
  minAmount = 0,
  maxAmount = 1000000,
  isLoadingOffices = false,
}) {
  // Local filter state
  const [localFilters, setLocalFilters] = useState({
    dateFrom: filters.dateFrom || "",
    dateTo: filters.dateTo || "",
    amountMin: filters.amountMin || minAmount,
    amountMax: filters.amountMax || maxAmount,
    selectedOffices: filters.selectedOffices || [],
    selectedParties: filters.selectedParties || [],
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [showOfficeDropdown, setShowOfficeDropdown] = useState(false);
  const [showPartyDropdown, setShowPartyDropdown] = useState(false);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters({
      dateFrom: filters.dateFrom || "",
      dateTo: filters.dateTo || "",
      amountMin: filters.amountMin ?? minAmount,
      amountMax: filters.amountMax ?? maxAmount,
      selectedOffices: filters.selectedOffices || [],
      selectedParties: filters.selectedParties || [],
    });
  }, [filters, minAmount, maxAmount]);

  // Calculate active filter count
  const getActiveFilterCount = () => {
    let count = 0;
    if (localFilters.dateFrom) count++;
    if (localFilters.dateTo) count++;
    if (localFilters.amountMin !== minAmount) count++;
    if (localFilters.amountMax !== maxAmount) count++;
    if (localFilters.selectedOffices.length > 0) count++;
    if (localFilters.selectedParties.length > 0) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  // Handle filter changes
  const handleDateFromChange = (e) => {
    setLocalFilters({ ...localFilters, dateFrom: e.target.value });
  };

  const handleDateToChange = (e) => {
    setLocalFilters({ ...localFilters, dateTo: e.target.value });
  };

  const handleAmountMinChange = (e) => {
    const value = parseFloat(e.target.value) || minAmount;
    const newMin = Math.max(minAmount, Math.min(value, localFilters.amountMax - 1));
    setLocalFilters({
      ...localFilters,
      amountMin: newMin,
    });
  };

  const handleAmountMaxChange = (e) => {
    const value = parseFloat(e.target.value) || maxAmount;
    const newMax = Math.min(maxAmount, Math.max(value, localFilters.amountMin + 1));
    setLocalFilters({
      ...localFilters,
      amountMax: newMax,
    });
  };

  const toggleOffice = (officeId) => {
    const newOffices = localFilters.selectedOffices.includes(officeId)
      ? localFilters.selectedOffices.filter((id) => id !== officeId)
      : [...localFilters.selectedOffices, officeId];
    setLocalFilters({ ...localFilters, selectedOffices: newOffices });
  };

  const toggleParty = (partyName) => {
    const newParties = localFilters.selectedParties.includes(partyName)
      ? localFilters.selectedParties.filter((name) => name !== partyName)
      : [...localFilters.selectedParties, partyName];
    setLocalFilters({ ...localFilters, selectedParties: newParties });
  };

  // Apply filters
  const handleApply = () => {
    onFiltersChange(localFilters);
    setIsExpanded(false);
  };

  // Reset filters
  const handleReset = () => {
    const resetFilters = {
      dateFrom: "",
      dateTo: "",
      amountMin: minAmount,
      amountMax: maxAmount,
      selectedOffices: [],
      selectedParties: [],
    };
    setLocalFilters(resetFilters);
    onFiltersChange(resetFilters);
  };

  // Format currency for display
  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-4 sm:mb-6">
      {/* Filter Header - Always Visible */}
      <div
        className="flex items-center justify-between p-4 sm:p-6 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <Filter className="w-5 h-5 text-purple-600" />
            {activeFilterCount > 0 && (
              <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </div>
          <h3 className="text-base sm:text-lg font-semibold text-gray-900">
            Filters
          </h3>
          {activeFilterCount > 0 && (
            <span className="text-sm text-gray-500">
              ({activeFilterCount} active)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleReset();
              }}
              className="text-sm text-white bg-purple-600 hover:bg-purple-700 transition-colors"
            >
              Clear All
            </button>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Filter Content - Expandable */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 sm:p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Date Range Filter */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Calendar className="w-4 h-4" />
                Date Range
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    From
                  </label>
                  <input
                    type="date"
                    value={localFilters.dateFrom}
                    onChange={handleDateFromChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">To</label>
                  <input
                    type="date"
                    value={localFilters.dateTo}
                    onChange={handleDateToChange}
                    min={localFilters.dateFrom}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Amount Range Filter */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <DollarSign className="w-4 h-4" />
                Amount Range
              </label>
              <div className="space-y-3">
                {/* Amount Range Display */}
                <div className="flex items-center justify-between text-xs sm:text-sm font-medium text-gray-700 bg-gray-50 px-3 py-2 rounded-lg">
                  <span>{formatCurrency(localFilters.amountMin)}</span>
                  <span className="text-gray-400">to</span>
                  <span>{formatCurrency(localFilters.amountMax)}</span>
                </div>
                
                {/* Manual Input Fields - Show first for better UX */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Min Amount
                    </label>
                    <input
                      type="number"
                      min={minAmount}
                      max={maxAmount}
                      step="100"
                      value={localFilters.amountMin}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || minAmount;
                        const newMin = Math.max(minAmount, Math.min(value, localFilters.amountMax - 1));
                        setLocalFilters({ ...localFilters, amountMin: newMin });
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Max Amount
                    </label>
                    <input
                      type="number"
                      min={minAmount}
                      max={maxAmount}
                      step="100"
                      value={localFilters.amountMax}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || maxAmount;
                        const newMax = Math.min(maxAmount, Math.max(value, localFilters.amountMin + 1));
                        setLocalFilters({ ...localFilters, amountMax: newMax });
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm"
                    />
                  </div>
                </div>
                
                {/* Dual Range Slider - Improved implementation */}
                <div className="relative h-8">
                  {/* Track background */}
                  <div className="absolute top-1/2 left-0 right-0 h-2 bg-gray-200 rounded-lg -translate-y-1/2"></div>
                  
                  {/* Active range highlight */}
                  <div
                    className="absolute top-1/2 h-2 bg-purple-500 rounded-lg -translate-y-1/2"
                    style={{
                      left: `${((localFilters.amountMin - minAmount) / (maxAmount - minAmount)) * 100}%`,
                      width: `${((localFilters.amountMax - localFilters.amountMin) / (maxAmount - minAmount)) * 100}%`,
                    }}
                  ></div>
                  
                  {/* Min slider */}
                  <input
                    type="range"
                    min={minAmount}
                    max={maxAmount}
                    step={(maxAmount - minAmount) / 1000}
                    value={localFilters.amountMin}
                    onChange={handleAmountMinChange}
                    className="absolute top-1/2 left-0 right-0 w-full h-2 bg-transparent appearance-none cursor-pointer slider-min -translate-y-1/2"
                    style={{
                      zIndex: localFilters.amountMin > localFilters.amountMax - ((maxAmount - minAmount) * 0.05) ? 3 : 2,
                    }}
                  />
                  
                  {/* Max slider */}
                  <input
                    type="range"
                    min={minAmount}
                    max={maxAmount}
                    step={(maxAmount - minAmount) / 1000}
                    value={localFilters.amountMax}
                    onChange={handleAmountMaxChange}
                    className="absolute top-1/2 left-0 right-0 w-full h-2 bg-transparent appearance-none cursor-pointer slider-max -translate-y-1/2"
                    style={{ zIndex: 2 }}
                  />
                </div>
              </div>
            </div>

            {/* Offices Multi-Select */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Building className="w-4 h-4" />
                Offices
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setShowOfficeDropdown(!showOfficeDropdown);
                    setShowPartyDropdown(false);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm text-left flex items-center justify-between bg-white"
                >
                  <span className="text-gray-700">
                    {localFilters.selectedOffices.length === 0
                      ? "Select offices..."
                      : `${localFilters.selectedOffices.length} office(s) selected`}
                  </span>
                  <ChevronDown
                    className={`w-4 h-4 text-gray-400 transition-transform ${
                      showOfficeDropdown ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {showOfficeDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {isLoadingOffices ? (
                      <div className="p-4 text-center text-sm text-gray-500">
                        Loading offices...
                      </div>
                    ) : offices.length === 0 ? (
                      <div className="p-4 text-center text-sm text-gray-500">
                        No offices available
                      </div>
                    ) : (
                      offices.map((office) => (
                        <label
                          key={office.office_id}
                          className="flex items-center gap-2 p-3 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={localFilters.selectedOffices.includes(
                              office.office_id
                            )}
                            onChange={() => toggleOffice(office.office_id)}
                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                          />
                          <span className="text-sm text-gray-700 flex-1">
                            {office.name}
                          </span>
                          {localFilters.selectedOffices.includes(
                            office.office_id
                          ) && (
                            <Check className="w-4 h-4 text-purple-600" />
                          )}
                        </label>
                      ))
                    )}
                  </div>
                )}
              </div>
              {/* Selected Offices Tags */}
              {localFilters.selectedOffices.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {localFilters.selectedOffices.map((officeId) => {
                    const office = offices.find((o) => o.office_id === officeId);
                    if (!office) return null;
                    return (
                      <span
                        key={officeId}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium"
                      >
                        {office.name}
                        <button
                          onClick={() => toggleOffice(officeId)}
                          className="hover:text-purple-900"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Parties Multi-Select */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Users className="w-4 h-4" />
                Parties
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setShowPartyDropdown(!showPartyDropdown);
                    setShowOfficeDropdown(false);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-sm text-left flex items-center justify-between bg-white"
                >
                  <span className="text-gray-700">
                    {localFilters.selectedParties.length === 0
                      ? "Select parties..."
                      : `${localFilters.selectedParties.length} party(ies) selected`}
                  </span>
                  <ChevronDown
                    className={`w-4 h-4 text-gray-400 transition-transform ${
                      showPartyDropdown ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {showPartyDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {parties.length === 0 ? (
                      <div className="p-4 text-center text-sm text-gray-500">
                        No parties available
                      </div>
                    ) : (
                      parties.map((party) => (
                        <label
                          key={party}
                          className="flex items-center gap-2 p-3 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={localFilters.selectedParties.includes(party)}
                            onChange={() => toggleParty(party)}
                            className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                          />
                          <span className="text-sm text-gray-700 flex-1">
                            {party}
                          </span>
                          {localFilters.selectedParties.includes(party) && (
                            <Check className="w-4 h-4 text-purple-600" />
                          )}
                        </label>
                      ))
                    )}
                  </div>
                )}
              </div>
              {/* Selected Parties Tags */}
              {localFilters.selectedParties.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {localFilters.selectedParties.map((party) => (
                    <span
                      key={party}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium"
                    >
                      {party}
                      <button
                        onClick={() => toggleParty(party)}
                        className="hover:text-purple-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={handleApply}
              className="flex-1 px-4 py-2 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg hover:from-[#7C6BA6] hover:to-[#5B4D7D] transition-all duration-200 font-medium hover:shadow-md active:scale-95"
            >
              Apply Filters
            </button>
            <button
              onClick={handleReset}
              className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium active:scale-95"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Close dropdowns when clicking outside */}
      {isExpanded && (showOfficeDropdown || showPartyDropdown) && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => {
            setShowOfficeDropdown(false);
            setShowPartyDropdown(false);
          }}
        />
      )}

      {/* Range Slider Styles */}
      <style>{`
        .slider-min::-webkit-slider-thumb,
        .slider-max::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #6B5B95;
          cursor: pointer;
          border: 3px solid #fff;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          transition: all 0.2s ease;
        }
        .slider-min::-webkit-slider-thumb:hover,
        .slider-max::-webkit-slider-thumb:hover {
          background: #7C6BA6;
          transform: scale(1.1);
        }
        .slider-min::-moz-range-thumb,
        .slider-max::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #6B5B95;
          cursor: pointer;
          border: 3px solid #fff;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          transition: all 0.2s ease;
        }
        .slider-min::-moz-range-thumb:hover,
        .slider-max::-moz-range-thumb:hover {
          background: #7C6BA6;
          transform: scale(1.1);
        }
        .slider-min::-webkit-slider-track,
        .slider-max::-webkit-slider-track {
          height: 0;
          background: transparent;
        }
        .slider-min::-moz-range-track,
        .slider-max::-moz-range-track {
          height: 0;
          background: transparent;
        }
      `}</style>
    </div>
  );
}
