// frontend/src/utils/csvExport.js
/**
 * CSV Export Utility
 * Handles client-side CSV generation and download
 */

/**
 * Convert array of objects to CSV string
 * @param {Array} data - Array of objects to export
 * @param {Array} columns - Array of column definitions: [{ key: 'name', label: 'Name' }]
 * @returns {string} CSV string
 */
export function convertToCSV(data, columns) {
  if (!data || data.length === 0) {
    return '';
  }

  // Create header row
  const headers = columns.map(col => `"${col.label}"`).join(',');
  
  // Create data rows
  const rows = data.map(item => {
    return columns.map(col => {
      // Get value using dot notation (e.g., 'user.name')
      const value = getNestedValue(item, col.key);
      
      // Escape and format value
      return formatCSVValue(value);
    }).join(',');
  });
  
  // Combine header and rows
  return [headers, ...rows].join('\n');
}

/**
 * Get nested object value using dot notation
 * @param {Object} obj - Object to get value from
 * @param {string} path - Path to value (e.g., 'user.name.first')
 * @returns {*} Value at path
 */
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => {
    return current?.[key];
  }, obj);
}

/**
 * Format value for CSV (escape quotes, handle nulls, etc.)
 * @param {*} value - Value to format
 * @returns {string} Formatted value
 */
function formatCSVValue(value) {
  if (value === null || value === undefined) {
    return '""';
  }
  
  // Convert to string
  let stringValue = String(value);
  
  // Escape quotes
  stringValue = stringValue.replace(/"/g, '""');
  
  // Wrap in quotes
  return `"${stringValue}"`;
}

/**
 * Trigger browser download of CSV file
 * @param {string} csvContent - CSV content
 * @param {string} filename - Name for downloaded file
 */
export function downloadCSV(csvContent, filename) {
  // Create blob
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create download link
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  // Trigger download
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Main export function - handles full export process
 * @param {Array} data - Data to export
 * @param {Array} columns - Column definitions
 * @param {string} filename - Output filename
 * @param {Function} setLoading - Optional loading state setter
 */
export async function exportToCSV(data, columns, filename, setLoading = null) {
  try {
    if (setLoading) setLoading(true);
    
    // Convert to CSV
    const csvContent = convertToCSV(data, columns);
    
    if (!csvContent) {
      throw new Error('No data to export');
    }
    
    // Trigger download
    downloadCSV(csvContent, filename);
    
    return true;
  } catch (error) {
    console.error('CSV export error:', error);
    throw error;
  } finally {
    if (setLoading) {
      // Small delay so user sees the loading state
      setTimeout(() => setLoading(false), 500);
    }
  }
}

/**
 * Export with custom formatting
 * @param {Array} data - Data to export
 * @param {Function} formatter - Custom formatter function
 * @param {string} filename - Output filename
 */
export async function exportWithFormatter(data, formatter, filename) {
  try {
    const formattedData = data.map(formatter);
    const csvContent = convertToCSV(formattedData, Object.keys(formattedData[0] || {}));
    downloadCSV(csvContent, filename);
    return true;
  } catch (error) {
    console.error('CSV export error:', error);
    throw error;
  }
}