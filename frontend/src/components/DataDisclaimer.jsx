import React from 'react';
import { AlertCircle } from 'lucide-react';
import { useDarkMode } from '../context/DarkModeContext';

/**
 * Data disclaimer component shown on pages with financial data
 * Warns users that data may be incomplete due to various factors
 */
export default function DataDisclaimer({ className = '' }) {
  const { darkMode } = useDarkMode();

  return (
    <div className={`flex items-start gap-2 text-xs italic ${
      darkMode ? 'text-gray-400' : 'text-gray-500'
    } ${className}`}>
      <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
      <p>
        <strong>Data Disclaimer:</strong> Reported figures may be incomplete due to delayed filings,
        data availability limitations, or ongoing data collection. Users should verify figures against
        official sources such as <a
          href="https://seethemoney.az.gov"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-purple-400"
        >SeeTheMoney.az.gov</a> and <a
          href="https://www.fec.gov"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-purple-400"
        >FEC.gov</a>.
      </p>
    </div>
  );
}
