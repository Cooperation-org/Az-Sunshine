// frontend/src/components/GrassrootsThresholdBadge.jsx
import React from "react";
import { AlertTriangle, CheckCircle, TrendingUp } from "lucide-react";

/**
 * Grassroots Threshold Badge
 * Phase 1 Task 2d-2e: Compare candidate IE spending to grassroots threshold
 */
export default function GrassrootsThresholdBadge({ 
  ieFor = 0, 
  ieAgainst = 0, 
  threshold = 5000,
  detailed = false 
}) {
  const total = ieFor + ieAgainst;
  const exceedsThreshold = total > threshold;
  const percentage = ((total / threshold) * 100).toFixed(0);

  // Simple badge version (for tables)
  if (!detailed) {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
          exceedsThreshold
            ? "bg-red-100 text-red-800"
            : "bg-green-100 text-green-800"
        }`}
      >
        {exceedsThreshold ? (
          <>
            <AlertTriangle className="w-3 h-3" />
            Exceeds ${(total - threshold).toLocaleString()}
          </>
        ) : (
          <>
            <CheckCircle className="w-3 h-3" />
            Below Threshold
          </>
        )}
      </span>
    );
  }

  // Detailed card version (for candidate detail pages)
  return (
    <div
      className={`rounded-xl p-6 border-2 ${
        exceedsThreshold
          ? "bg-red-50 border-red-300"
          : "bg-green-50 border-green-300"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Grassroots Threshold Analysis
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-bold ${
            exceedsThreshold
              ? "bg-red-600 text-white"
              : "bg-green-600 text-white"
          }`}
        >
          {exceedsThreshold ? "⚠️ EXCEEDED" : "✓ BELOW"}
        </span>
      </div>

      <div className="space-y-3">
        {/* Threshold vs Total */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 font-medium">Threshold:</span>
          <span className="font-bold text-gray-900">
            ${threshold.toLocaleString()}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 font-medium">Total IE Spending:</span>
          <span
            className={`font-bold text-lg ${
              exceedsThreshold ? "text-red-600" : "text-green-600"
            }`}
          >
            ${total.toLocaleString()}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600">
            <span>Progress</span>
            <span>{percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                exceedsThreshold ? "bg-red-600" : "bg-green-600"
              }`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Status Message */}
        <div
          className={`text-xs font-medium p-3 rounded-lg ${
            exceedsThreshold
              ? "bg-red-100 text-red-800"
              : "bg-green-100 text-green-800"
          }`}
        >
          {exceedsThreshold ? (
            <>
              ⚠️ Exceeds threshold by $
              {(total - threshold).toLocaleString()}
            </>
          ) : (
            <>
              ✓ ${(threshold - total).toLocaleString()} below threshold
            </>
          )}
        </div>

        {/* Breakdown */}
        <div className="pt-3 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 block mb-1">IE Support:</span>
              <p className="font-bold text-green-600">
                ${ieFor.toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-gray-500 block mb-1">IE Oppose:</span>
              <p className="font-bold text-red-600">
                ${ieAgainst.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}