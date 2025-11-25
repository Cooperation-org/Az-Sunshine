/**
 * Utility functions for CSV export
 */

/**
 * Convert array of objects to CSV string
 * @param {Array} data - Array of objects to convert
 * @param {Array} columns - Array of column definitions [{key: 'field', label: 'Header'}]
 * @returns {string} CSV string
 */
export function convertToCSV(data, columns) {
  if (!data || data.length === 0) {
    return '';
  }

  // Create header row
  const headers = columns.map(col => escapeCSVValue(col.label)).join(',');
  
  // Create data rows
  const rows = data.map(item => {
    return columns.map(col => {
      const value = getNestedValue(item, col.key);
      return escapeCSVValue(value);
    }).join(',');
  });

  // Combine header and rows
  return [headers, ...rows].join('\n');
}

/**
 * Get nested value from object using dot notation
 * @param {Object} obj - Object to get value from
 * @param {string} path - Dot notation path (e.g., 'user.name')
 * @returns {string} Value or empty string
 */
function getNestedValue(obj, path) {
  if (!path) return '';
  
  const keys = path.split('.');
  let value = obj;
  
  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      return '';
    }
  }
  
  // Handle null, undefined, or empty values
  if (value === null || value === undefined) {
    return '';
  }
  
  return String(value);
}

/**
 * Escape CSV value (handle commas, quotes, newlines)
 * @param {string} value - Value to escape
 * @returns {string} Escaped value
 */
function escapeCSVValue(value) {
  if (value === null || value === undefined) {
    return '';
  }
  
  const stringValue = String(value);
  
  // If value contains comma, quote, or newline, wrap in quotes and escape quotes
  if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  
  return stringValue;
}

/**
 * Download CSV file
 * @param {string} csvContent - CSV string content
 * @param {string} filename - Filename for download
 */
export function downloadCSV(csvContent, filename) {
  // Add BOM for UTF-8 to ensure Excel opens it correctly
  const BOM = '\uFEFF';
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create download link
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  // Trigger download
  document.body.appendChild(link);
  link.click();
  
  // Cleanup
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export data to CSV with loading state
 * @param {Array} data - Data to export
 * @param {Array} columns - Column definitions
 * @param {string} filename - Filename for download
 * @param {Function} setExporting - Function to set exporting state
 * @returns {Promise} Promise that resolves when export is complete
 */
export async function exportToCSV(data, columns, filename, setExporting) {
  try {
    setExporting(true);
    
    // Simulate processing delay for large datasets
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Convert to CSV
    const csvContent = convertToCSV(data, columns);
    
    if (!csvContent) {
      throw new Error('No data to export');
    }
    
    // Download file
    downloadCSV(csvContent, filename);
    
    return { success: true };
  } catch (error) {
    console.error('CSV Export Error:', error);
    throw error;
  } finally {
    setExporting(false);
  }
}

