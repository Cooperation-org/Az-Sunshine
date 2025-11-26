import React from "react";

/**
 * Skeleton Loader Components with Shimmer Effect
 * Provides better perceived performance than spinners
 */

/**
 * Base shimmer effect - add to any skeleton element
 */
const shimmerClass = "animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]";

/**
 * Card Skeleton - For metric cards and info cards
 */
export function CardSkeleton({ lines = 2, showIcon = true, className = "" }) {
  return (
    <div className={`bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100 ${className}`}>
      {showIcon && (
        <div className="flex items-start justify-between mb-4">
          <div className={`w-12 h-12 rounded-xl ${shimmerClass}`}></div>
          <div className={`h-6 w-16 rounded-full ${shimmerClass}`}></div>
        </div>
      )}
      <div className={`h-8 sm:h-10 w-1/2 rounded ${shimmerClass} mb-2`}></div>
      {lines > 1 && (
        <div className={`h-4 w-2/3 rounded ${shimmerClass}`}></div>
      )}
    </div>
  );
}

/**
 * Table Skeleton - For data tables
 */
export function TableSkeleton({ rows = 5, columns = 5, showHeader = true }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {showHeader && (
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <div className="flex gap-4">
            {Array.from({ length: columns }).map((_, i) => (
              <div key={i} className={`h-4 flex-1 rounded ${shimmerClass}`}></div>
            ))}
          </div>
        </div>
      )}
      <div className="divide-y divide-gray-100">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="p-4">
            <div className="flex gap-4">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <div
                  key={colIndex}
                  className={`h-4 flex-1 rounded ${shimmerClass}`}
                  style={{ width: colIndex === 0 ? "30%" : "auto" }}
                ></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Chart Skeleton - For charts and graphs
 */
export function ChartSkeleton({ height = "200px", className = "" }) {
  return (
    <div className={`bg-gray-50 rounded-xl p-4 sm:p-6 ${className}`}>
      <div className="mb-4">
        <div className={`h-6 w-1/3 rounded ${shimmerClass} mb-2`}></div>
        <div className={`h-4 w-1/2 rounded ${shimmerClass}`}></div>
      </div>
      <div
        className={`w-full rounded-xl ${shimmerClass}`}
        style={{ height }}
      ></div>
    </div>
  );
}

/**
 * List Item Skeleton - For lists and menu items
 */
export function ListItemSkeleton({ showAvatar = true, lines = 2 }) {
  return (
    <div className="flex items-center gap-3 p-3">
      {showAvatar && (
        <div className={`w-10 h-10 rounded-full ${shimmerClass} flex-shrink-0`}></div>
      )}
      <div className="flex-1">
        <div className={`h-4 w-3/4 rounded ${shimmerClass} mb-2`}></div>
        {lines > 1 && (
          <div className={`h-3 w-1/2 rounded ${shimmerClass}`}></div>
        )}
      </div>
    </div>
  );
}

/**
 * Stats Grid Skeleton - For metric grids
 */
export function StatsGridSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Page Skeleton - Full page skeleton layout
 */
export function PageSkeleton({ showHeader = true, showStats = true, showTable = true }) {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="flex-1 lg:ml-0 min-w-0">
        {showHeader && (
          <div className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-3 sm:py-4 mb-4">
            <div className={`h-8 w-64 rounded ${shimmerClass} mb-2`}></div>
            <div className={`h-4 w-48 rounded ${shimmerClass}`}></div>
          </div>
        )}
        <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
          {showStats && <StatsGridSkeleton />}
          {showTable && <TableSkeleton />}
        </div>
      </div>
    </div>
  );
}

/**
 * Badge Skeleton - For badges and tags
 */
export function BadgeSkeleton({ width = "w-16" }) {
  return (
    <div className={`h-6 ${width} rounded-full ${shimmerClass}`}></div>
  );
}

/**
 * Button Skeleton
 */
export function ButtonSkeleton({ width = "w-24" }) {
  return (
    <div className={`h-10 ${width} rounded-lg ${shimmerClass}`}></div>
  );
}

