import React from "react";

/**
 * Utility functions for search functionality
 */

/**
 * Highlight search terms in text
 * @param {string} text - The text to highlight
 * @param {string} searchTerm - The search term to highlight
 * @returns {JSX.Element} - React element with highlighted text
 */
export function highlightText(text, searchTerm) {
  if (!text || !searchTerm) return text;
  
  const parts = text.split(new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi'));
  
  return parts.map((part, index) => 
    part.toLowerCase() === searchTerm.toLowerCase() ? (
      <mark key={index} className="bg-yellow-200 text-gray-900 font-medium px-0.5 rounded">
        {part}
      </mark>
    ) : (
      part
    )
  );
}

/**
 * Escape special regex characters
 */
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Get recent searches from localStorage
 * @param {string} key - Storage key
 * @param {number} maxItems - Maximum number of recent searches to store
 * @returns {string[]} - Array of recent search terms
 */
export function getRecentSearches(key = 'soi_recent_searches', maxItems = 10) {
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return [];
    const searches = JSON.parse(stored);
    return Array.isArray(searches) ? searches.slice(0, maxItems) : [];
  } catch (error) {
    console.error('Error reading recent searches:', error);
    return [];
  }
}

/**
 * Save search term to recent searches
 * @param {string} searchTerm - The search term to save
 * @param {string} key - Storage key
 * @param {number} maxItems - Maximum number of recent searches to store
 */
export function saveRecentSearch(searchTerm, key = 'soi_recent_searches', maxItems = 10) {
  if (!searchTerm || searchTerm.trim().length === 0) return;
  
  try {
    const recent = getRecentSearches(key, maxItems);
    const trimmed = searchTerm.trim();
    
    // Remove if already exists
    const filtered = recent.filter(s => s.toLowerCase() !== trimmed.toLowerCase());
    
    // Add to beginning
    const updated = [trimmed, ...filtered].slice(0, maxItems);
    
    localStorage.setItem(key, JSON.stringify(updated));
  } catch (error) {
    console.error('Error saving recent search:', error);
  }
}

/**
 * Clear recent searches
 * @param {string} key - Storage key
 */
export function clearRecentSearches(key = 'soi_recent_searches') {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error clearing recent searches:', error);
  }
}

/**
 * Generate search suggestions based on current search term and candidates
 * @param {string} searchTerm - Current search term
 * @param {Array} candidates - List of candidates
 * @param {number} maxSuggestions - Maximum number of suggestions
 * @returns {Array} - Array of suggestion objects
 */
export function generateSearchSuggestions(searchTerm, candidates = [], maxSuggestions = 5) {
  if (!searchTerm || searchTerm.trim().length < 2) return [];
  
  const term = searchTerm.toLowerCase().trim();
  const suggestions = [];
  
  // Get unique names, emails, and offices
  const names = new Set();
  const emails = new Set();
  const offices = new Set();
  
  candidates.forEach(candidate => {
    const name = candidate.name || candidate.candidate_name || '';
    const email = candidate.email || '';
    const office = candidate.office || '';
    
    if (name.toLowerCase().includes(term)) {
      names.add(name);
    }
    if (email.toLowerCase().includes(term)) {
      emails.add(email);
    }
    if (office.toLowerCase().includes(term)) {
      offices.add(office);
    }
  });
  
  // Combine and limit suggestions
  const allSuggestions = [
    ...Array.from(names).slice(0, 2),
    ...Array.from(emails).slice(0, 2),
    ...Array.from(offices).slice(0, 1),
  ];
  
  return allSuggestions.slice(0, maxSuggestions).map(suggestion => ({
    text: suggestion,
    type: emails.has(suggestion) ? 'email' : offices.has(suggestion) ? 'office' : 'name',
  }));
}

