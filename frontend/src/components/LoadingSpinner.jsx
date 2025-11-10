import React from "react";
import { Loader } from "lucide-react";

/**
 * Dynamic loading spinner component with customizable size and message
 */
export default function LoadingSpinner({ 
  size = "lg", 
  message = "Loading...", 
  fullScreen = false,
  className = "" 
}) {
  const sizeClasses = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-12 h-12",
    xl: "w-16 h-16",
  };

  const spinner = (
    <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
      <div className="relative">
        <Loader 
          className={`${sizeClasses[size]} animate-spin text-purple-600`}
        />
        <div className="absolute inset-0 border-4 border-purple-200 rounded-full animate-pulse"></div>
      </div>
      {message && (
        <p className="text-gray-600 font-medium animate-pulse">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

/**
 * Inline loading spinner for tables and lists
 */
export function InlineLoader({ message = "Loading data..." }) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="flex flex-col items-center gap-3">
        <Loader className="w-8 h-8 animate-spin text-purple-600" />
        <p className="text-sm text-gray-500">{message}</p>
      </div>
    </div>
  );
}

/**
 * Skeleton loader for table rows
 */
export function TableSkeleton({ rows = 5 }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, idx) => (
        <tr key={idx} className="animate-pulse">
          <td className="px-6 py-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </td>
          <td className="px-6 py-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </td>
          <td className="px-6 py-4">
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </td>
          <td className="px-6 py-4">
            <div className="h-6 bg-gray-200 rounded-full w-20"></div>
          </td>
          <td className="px-6 py-4">
            <div className="h-8 bg-gray-200 rounded w-24"></div>
          </td>
        </tr>
      ))}
    </>
  );
}

