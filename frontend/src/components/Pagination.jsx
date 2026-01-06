import React from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

/**
 * Modern Pagination Component
 * Sleek design with smart page windowing
 */
export default function Pagination({
  currentPage,
  totalPages,
  totalCount,
  onPageChange,
  loading = false
}) {
  const { darkMode } = useDarkMode();

  if (totalPages <= 1) return null;

  // Generate page numbers with ellipsis
  const getPageNumbers = () => {
    const pages = [];

    if (totalPages <= 7) {
      // Show all pages if 7 or less
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // Show pages around current
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) {
          pages.push(i);
        }
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      if (!pages.includes(totalPages)) {
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const pages = getPageNumbers();

  const buttonBase = `flex items-center justify-center transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed`;

  const navButton = `${buttonBase} w-8 h-8 rounded-lg ${
    darkMode
      ? 'text-gray-400 hover:text-white hover:bg-white/10'
      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
  }`;

  const pageButton = (isActive) => `${buttonBase} min-w-[36px] h-9 px-3 rounded-lg text-sm font-medium ${
    isActive
      ? 'bg-[#7667C1] text-white shadow-lg shadow-purple-500/25'
      : darkMode
        ? 'text-gray-400 hover:text-white hover:bg-white/10'
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
  }`;

  return (
    <div className="mt-6 flex items-center justify-between">
      {/* Results count */}
      <div className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
        <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {((currentPage - 1) * 10 + 1).toLocaleString()}
          {' - '}
          {Math.min(currentPage * 10, totalCount).toLocaleString()}
        </span>
        {' of '}
        <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {totalCount.toLocaleString()}
        </span>
      </div>

      {/* Page controls */}
      <div className="flex items-center gap-1">
        {/* First page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1 || loading}
          className={navButton}
          title="First page"
        >
          <ChevronsLeft className="w-4 h-4" />
        </button>

        {/* Previous */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1 || loading}
          className={navButton}
          title="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Page numbers */}
        <div className="flex items-center gap-1 mx-1">
          {pages.map((page, idx) => (
            page === '...' ? (
              <span
                key={`ellipsis-${idx}`}
                className={`px-2 text-sm ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}
              >
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                disabled={loading}
                className={pageButton(currentPage === page)}
              >
                {page}
              </button>
            )
          ))}
        </div>

        {/* Next */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages || loading}
          className={navButton}
          title="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>

        {/* Last page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages || loading}
          className={navButton}
          title="Last page"
        >
          <ChevronsRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
