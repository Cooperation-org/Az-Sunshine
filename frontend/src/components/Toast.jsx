import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, X, AlertCircle, Info } from "lucide-react";

/**
 * Toast Notification Component
 * Displays temporary success/error/info messages
 */
export default function Toast({ message, type = "success", onClose, duration = 3000 }) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info,
  };

  const colors = {
    success: "bg-green-50 border-green-200 text-green-800",
    error: "bg-red-50 border-red-200 text-red-800",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
  };

  const iconColors = {
    success: "text-green-600",
    error: "text-red-600",
    warning: "text-yellow-600",
    info: "text-blue-600",
  };

  const Icon = icons[type] || CheckCircle;

  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${colors[type]} animate-slide-in-right max-w-md`}
      role="alert"
    >
      <Icon className={`w-5 h-5 flex-shrink-0 ${iconColors[type]}`} />
      <p className="text-sm font-medium flex-1">{message}</p>
      <button
        onClick={onClose}
        className={`flex-shrink-0 ${iconColors[type]} hover:opacity-70 transition-opacity`}
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

/**
 * Toast Container - Manages multiple toasts
 */
export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
            duration={toast.duration}
          />
        </div>
      ))}
    </div>
  );
}

/**
 * Hook for managing toasts
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = "success", duration = 3000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type, duration }]);
    return id;
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const success = (message, duration) => showToast(message, "success", duration);
  const error = (message, duration) => showToast(message, "error", duration);
  const warning = (message, duration) => showToast(message, "warning", duration);
  const info = (message, duration) => showToast(message, "info", duration);

  return {
    toasts,
    showToast,
    addToast: showToast,  // alias for compatibility
    removeToast,
    success,
    error,
    warning,
    info,
  };
}

