/**
 * Party utility functions for displaying party labels and colors
 */

// Map of party names to abbreviations
const PARTY_ABBREVIATIONS = {
  'democratic': 'D',
  'democrat': 'D',
  'republican': 'R',
  'green': 'G',
  'libertarian': 'L',
  'independent': 'I',
  'no party': 'NP',
  'nonpartisan': 'NP',
  'other': 'O',
};

// Map of party abbreviations to colors
const PARTY_COLORS = {
  'D': { bg: 'bg-blue-500', bgLight: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500' },
  'R': { bg: 'bg-red-500', bgLight: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500' },
  'G': { bg: 'bg-green-500', bgLight: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500' },
  'L': { bg: 'bg-yellow-500', bgLight: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500' },
  'I': { bg: 'bg-purple-500', bgLight: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500' },
  'NP': { bg: 'bg-gray-500', bgLight: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500' },
  'O': { bg: 'bg-gray-500', bgLight: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500' },
};

/**
 * Get party abbreviation from full party name
 * @param {string} partyName - Full party name (e.g., "Democratic", "Republican")
 * @returns {string} - Abbreviated party label (e.g., "D", "R")
 */
export function getPartyAbbreviation(partyName) {
  if (!partyName) return 'I';
  const normalized = partyName.toLowerCase().trim();
  return PARTY_ABBREVIATIONS[normalized] || 'I';
}

/**
 * Get party colors for styling
 * @param {string} partyNameOrAbbr - Party name or abbreviation
 * @returns {object} - Object with bg, bgLight, text, border color classes
 */
export function getPartyColors(partyNameOrAbbr) {
  if (!partyNameOrAbbr) return PARTY_COLORS['I'];

  // Check if it's already an abbreviation
  const abbr = partyNameOrAbbr.length <= 2
    ? partyNameOrAbbr.toUpperCase()
    : getPartyAbbreviation(partyNameOrAbbr);

  return PARTY_COLORS[abbr] || PARTY_COLORS['I'];
}

/**
 * Get party display info with abbreviation and colors
 * @param {string} partyName - Full party name
 * @returns {object} - Object with abbr, fullName, and colors
 */
export function getPartyInfo(partyName) {
  const abbr = getPartyAbbreviation(partyName);
  const colors = getPartyColors(abbr);

  return {
    abbr,
    fullName: partyName || 'Independent',
    colors,
  };
}

export default {
  getPartyAbbreviation,
  getPartyColors,
  getPartyInfo,
};
