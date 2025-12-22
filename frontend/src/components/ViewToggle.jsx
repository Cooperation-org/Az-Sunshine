import React from 'react';
import { Users, Grid } from 'lucide-react';
import { useDarkMode } from '../context/DarkModeContext';

export default function ViewToggle({ view, onViewChange }) {
  const { darkMode } = useDarkMode();

  return (
    <div className={`inline-flex rounded-full p-1 ${
      darkMode ? 'bg-[#1F1B31]' : 'bg-gray-100'
    }`}>
      <button
        onClick={() => onViewChange('candidate')}
        className={`px-3 md:px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
          view === 'candidate'
            ? darkMode
              ? 'bg-[#7163BA] text-white'
              : 'bg-[#7163BA] text-white'
            : darkMode
            ? 'text-gray-400 hover:text-gray-300'
            : 'text-gray-600 hover:text-gray-900'
        }`}
        aria-label="Candidate View"
      >
        <Users size={16} />
        <span className="hidden sm:inline">Candidate View</span>
      </button>
      <button
        onClick={() => onViewChange('race')}
        className={`px-3 md:px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
          view === 'race'
            ? darkMode
              ? 'bg-[#7163BA] text-white'
              : 'bg-[#7163BA] text-white'
            : darkMode
            ? 'text-gray-400 hover:text-gray-300'
            : 'text-gray-600 hover:text-gray-900'
        }`}
        aria-label="Race View"
      >
        <Grid size={16} />
        <span className="hidden sm:inline">Race View</span>
      </button>
    </div>
  );
}
