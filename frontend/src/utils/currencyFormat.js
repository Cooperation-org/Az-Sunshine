/**
 * Currency formatting utilities for consistent display across the application
 */

/**
 * Format a number as currency with two decimal places
 * @param {number|string} value - The value to format
 * @param {boolean} includeSign - Whether to include +/- sign (default: false)
 * @returns {string} - Formatted currency string (e.g., "$1,234,567.00")
 */
export function formatCurrency(value, includeSign = false) {
  const numValue = Math.abs(parseFloat(value || 0));
  const formatted = numValue.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  if (includeSign) {
    const originalValue = parseFloat(value || 0);
    const sign = originalValue >= 0 ? '+' : '-';
    return `${sign}$${formatted}`;
  }

  return `$${formatted}`;
}

/**
 * Format a number as currency without dollar sign (for use in components that add it separately)
 * @param {number|string} value - The value to format
 * @returns {string} - Formatted number string (e.g., "1,234,567.00")
 */
export function formatNumber(value) {
  const numValue = Math.abs(parseFloat(value || 0));
  return numValue.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

export default {
  formatCurrency,
  formatNumber
};
