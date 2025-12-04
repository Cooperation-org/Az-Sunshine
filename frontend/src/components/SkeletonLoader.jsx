import React from "react";

/**
 * Skeleton Loader Components with Shimmer Effect
 * Provides better perceived performance than spinners
 */

// NOTE: The shimmer effect can be GPU-intensive. A simple pulse is often sufficient.
const shimmerClass = "animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]";

/**
 * Card Skeleton - For metric cards and info cards
 */
export function CardSkeleton({ lines = 2, showIcon = true, className = "" }) {
  return (
    <div className={`bg-white rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100 ${className}`}>
      {showIcon && (
        <div className="flex items-start justify-between mb-4">
          <div className={`w-12 h-12 rounded-xl bg-gray-200 animate-pulse`}></div>
          <div className={`h-6 w-16 rounded-full bg-gray-200 animate-pulse`}></div>
        </div>
      )}
      <div className={`h-8 sm:h-10 w-1/2 rounded bg-gray-200 animate-pulse mb-2`}></div>
      {lines > 1 && (
        <div className={`h-4 w-2/3 rounded bg-gray-200 animate-pulse`}></div>
      )}
    </div>
  );
}

/**
 * Table Skeleton - For data tables. Renders valid <tr> elements for use inside a <tbody>.
 */
export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <tr key={rowIndex} className="animate-pulse">
          {Array.from({ length: cols }).map((_, colIndex) => (
            <td key={colIndex} className="px-6 py-5 whitespace-nowrap">
              <div className="h-4 bg-gray-200 rounded w-full"></div>
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}


/**
 * Chart Skeleton - For charts and graphs
 */
export function ChartSkeleton({ height = "200px", className = "" }) {
  return (
    <div className={`bg-gray-50 rounded-xl p-4 sm:p-6 ${className}`}>
      <div className="mb-4 animate-pulse">
        <div className={`h-6 w-1/3 rounded bg-gray-200 mb-2`}></div>
        <div className={`h-4 w-1/2 rounded bg-gray-200`}></div>
      </div>
      <div
        className={`w-full rounded-xl bg-gray-200 animate-pulse`}
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
    <div className="flex items-center gap-3 p-3 animate-pulse">
      {showAvatar && (
        <div className={`w-10 h-10 rounded-full bg-gray-200 flex-shrink-0`}></div>
      )}
      <div className="flex-1 space-y-2">
        <div className={`h-4 w-3/4 rounded bg-gray-200`}></div>
        {lines > 1 && (
          <div className={`h-3 w-1/2 rounded bg-gray-200`}></div>
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
            <div className={`h-8 w-64 rounded bg-gray-200 animate-pulse mb-2`}></div>
            <div className={`h-4 w-48 rounded bg-gray-200 animate-pulse`}></div>
          </div>
        )}
        <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
          {showStats && <StatsGridSkeleton />}
          {showTable && <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"><TableSkeleton /></div>}
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
    <div className={`h-6 ${width} rounded-full bg-gray-200 animate-pulse`}></div>
  );
}

/**
 * Button Skeleton
 */
export function ButtonSkeleton({ width = "w-24" }) {
  return (
    <div className={`h-10 ${width} rounded-lg bg-gray-200 animate-pulse`}></div>
  );
}
