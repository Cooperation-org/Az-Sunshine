import React from "react";
import { AlertTriangle, X } from "lucide-react";

/**
 * Confirmation Modal Component
 * Displays a confirmation dialog before performing bulk actions
 */
export default function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  type = "warning",
}) {
  if (!isOpen) return null;

  const colors = {
    warning: "bg-yellow-50 border-yellow-200",
    danger: "bg-red-50 border-red-200",
    info: "bg-blue-50 border-blue-200",
  };

  const buttonColors = {
    warning: "bg-yellow-600 hover:bg-yellow-700",
    danger: "bg-red-600 hover:bg-red-700",
    info: "bg-blue-600 hover:bg-blue-700",
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 transform transition-all ${colors[type] || colors.warning} border-2`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              type === "danger" ? "bg-red-100" : 
              type === "info" ? "bg-blue-100" : 
              "bg-yellow-100"
            }`}>
              <AlertTriangle className={`w-6 h-6 ${
                type === "danger" ? "text-red-600" : 
                type === "info" ? "text-blue-600" : 
                "text-yellow-600"
              }`} />
            </div>
            <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message */}
        <p className="text-gray-700 mb-6 ml-14">{message}</p>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium"
          >
            {cancelText}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2 text-white rounded-lg transition-all duration-200 font-medium ${buttonColors[type || "warning"]}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

