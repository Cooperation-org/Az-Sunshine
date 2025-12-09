import React, { useEffect, useState } from "react";
import { Bell, Search, ChevronRight, Download, Loader } from "lucide-react";
import { getCandidates } from "../api/api";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";

import { TableSkeleton } from "../components/SkeletonLoader";
import { exportToCSV } from "../utils/csvExport";
import { useDarkMode } from "../context/DarkModeContext";

// Refactored Banner component to accept controls and children
const Banner = ({ controls, children }) => {
  const { darkMode } = useDarkMode();
  const [searchTerm, setSearchTerm] = useState("");

  return (
    <div className={`relative rounded-2xl overflow-hidden shadow-2xl mb-8 ${darkMode ? 'bg-gradient-to-br from-[#4C3D7D] to-[#3d3559]' : 'bg-gradient-to-br from-[#6B5B95] to-[#4C3D7D]'}`}>
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="pattern-circles" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse" patternContentUnits="userSpaceOnUse">
              <circle id="pattern-circle" cx="20" cy="20" r="2" fill="white"></circle>
            </pattern>
            <pattern id="pattern-squares" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="4" height="4" fill="white" opacity="0.5"></rect>
              <rect x="10" y="10" width="4" height="4" fill="white" opacity="0.5"></rect>
            </pattern>
          </defs>
          <rect x="0" y="0" width="100%" height="100%" fill="url(#pattern-circles)"></rect>
          <rect x="0" y="0" width="100%" height="100%" fill="url(#pattern-squares)" mask="url(#pattern-circles)"></rect>
        </svg>
      </div>
      <div className="relative p-8 sm:p-12 lg:p-16 text-center">
        {/* Controls positioned top-right */}
        {controls && (
          <div className="absolute top-4 right-4 sm:top-8 sm:right-8 z-10">
            {controls}
          </div>
        )}

        <h1 className="text-3xl sm:text-3xl lg:text-3xl font-extrabold text-white tracking-tight">
          Explore the Candidates
        </h1>
        <p className="mt-4 text-lg sm:text-xl text-gray-200 max-w-2xl mx-auto">
          Your guide to the political landscape.
        </p>
        <div className="mt-8 max-w-md mx-auto">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search candidates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-3 rounded-full text-lg ${darkMode ? 'bg-[#3d3559] text-white placeholder-gray-400 border border-transparent focus:ring-2 focus:ring-[#7d6fa3]' : 'bg-white text-gray-900 placeholder-gray-500 border border-gray-300 focus:ring-2 focus:ring-[#6B5B95]'}`}
            />
          </div>
        </div>
        {children}
      </div>
    </div>
  );
};


export default function Candidates() {
  const { darkMode } = useDarkMode();
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadCandidates(currentPage);
  }, [currentPage]);

  async function loadCandidates(page) {
    setLoading(true);
    try {
      const candidatesData = await getCandidates({ page, page_size: 10 });
      
      const candidatesList = candidatesData.results || [];
      
      setCandidates(candidatesList);
      setTotalCount(candidatesData.count || 0);
      setTotalPages(Math.ceil((candidatesData.count || 0) / 10));
    } catch (err) {
      console.error("Error loading candidates:", err);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }

  const getContactedStatus = (candidate) => {
    return { label: "Active", color: darkMode ? "bg-green-900/30 text-green-300" : "bg-green-100 text-green-700" };
  };

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      
      const allCandidatesData = await getCandidates({ page_size: totalCount || 1000 });
      const allCandidates = allCandidatesData.results || [];
      
      const columns = [
        { key: 'candidate.full_name', label: 'Candidate Name' },
        { key: 'name.full_name', label: 'Candidate Name (Alt)' },
        { key: 'candidate_office.name', label: 'Race' },
        { key: 'candidate_party.name', label: 'Party' },
        { key: 'election_cycle.name', label: 'Election Cycle' },
        { key: 'is_incumbent', label: 'Status' },
      ];
      
      const csvData = allCandidates.map(candidate => ({
        ...candidate,
        'is_incumbent': candidate.is_incumbent ? 'Incumbent' : 'Challenger',
      }));
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `candidates_${timestamp}.csv`;
      
      await exportToCSV(csvData, columns, filename, setExporting);
      
    } catch (error) {
      console.error("Error exporting CSV:", error);
      alert("Failed to export CSV. Please try again.");
      setExporting(false);
    }
  };

  // The Export Button JSX, moved up to be passed into the Banner
  const ExportButton = (
    <button
      onClick={handleExportCSV}
      disabled={exporting || candidates.length === 0}
      className={`flex items-center gap-2 px-3 py-2 ${darkMode ? 'bg-white/10 hover:bg-white/20 backdrop-blur-sm' : 'bg-white/30 backdrop-blur-sm hover:bg-white/50'} text-white rounded-xl transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg active:scale-95 text-sm sm:text-base border border-white/20`}
    >
      {exporting ? (
        <>
          <Loader className="w-4 h-4 animate-spin" />
          <span>Exporting...</span>
        </>
      ) : (
        <>
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </>
      )}
    </button>
  );

    return (

      <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>

        <Sidebar />

  

        <main className="flex-1 lg:ml-0 min-w-0">

          

          <div className="p-4 sm:p-6 lg:p-8">

          {/* Pass the ExportButton to the Banner controls prop */}
          <Banner controls={ExportButton} />

            {loading && currentPage === 1 ? (

              <>

                {/* Removed the loading button placeholder */}

                <div className={`overflow-x-auto shadow-lg rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>

                  <table className="min-w-full divide-y divide-gray-200">

                    <tbody>

                      <TableSkeleton rows={8} columns={6} />

                    </tbody>

                  </table>

                </div>

              </>

            ) : (

              <>

                {/* --- REMOVED THE ORIGINAL BUTTON CODE HERE --- */}

  

                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl border shadow-lg overflow-hidden`}>

                  <div className="overflow-x-auto">

                    <table className="min-w-full divide-y divide-gray-200">

                      <thead className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'} border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>

                        <tr>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Candidate Name

                          </th>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Race

                          </th>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Party

                          </th>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Contacted Status

                          </th>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Election Cycle

                          </th>

                          <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                            Status

                          </th>

                        </tr>

                      </thead>

                      <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-100'}`}>

                        {candidates.length === 0 ? (

                          <tr>

                            <td colSpan="6" className={`py-12 text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>

                              No candidates found.

                            </td>

                          </tr>

                        ) : (

                          candidates.map((candidate, idx) => {

                            const status = getContactedStatus(candidate);

                            const candidateName = candidate.candidate?.full_name || candidate.name?.full_name || "Unknown";

                            return (

                              <tr key={candidate.committee_id || idx} className={`transition-colors duration-150 ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50/50'}`}>

                                <td className="py-3 sm:py-5 px-3 sm:px-6">

                                  <div className="flex items-center gap-2 sm:gap-4">

                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] flex items-center justify-center text-white text-xs sm:text-sm font-semibold flex-shrink-0 shadow-sm">

                                      {candidateName.charAt(0).toUpperCase()}

                                    </div>

                                    <Link 

                                      to={`/candidate/${candidate.committee_id}`}

                                      className={`${darkMode ? 'text-white hover:text-purple-300' : 'text-gray-900 hover:text-purple-600'} text-xs sm:text-sm lg:text-base font-medium transition truncate`}

                                    >

                                      {candidateName}

                                    </Link>

                                  </div>

                                </td>

                                <td className={`py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                                  {candidate.candidate_office?.name || "N/A"}

                                </td>

                                <td className={`py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                                  {candidate.candidate_party?.name || "N/A"}

                                </td>

                                <td className="py-3 sm:py-5 px-3 sm:px-6">

                                  <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${status.color}`}>

                                    {status.label}

                                  </span>

                                </td>

                                <td className={`py-3 sm:py-5 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>

                                  {candidate.election_cycle?.name || "N/A"}

                                </td>

                                <td className="py-3 sm:py-5 px-3 sm:px-6">

                                  {candidate.is_incumbent ? (

                                    <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${darkMode ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>

                                      Incumbent

                                    </span>

                                  ) : (

                                    <span className={`text-xs sm:text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Challenger</span>

                                  )}

                                </td>

                              </tr>

                            );

                          })

                        )}

                      </tbody>

                    </table>

                  </div>

                </div>

  

                <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">

                  <p className={`text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>

                    {totalCount} Results

                  </p>

                  <div className="flex items-center gap-1 sm:gap-2 flex-wrap">

                    {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (

                      <button

                        key={page}

                        onClick={() => setCurrentPage(page)}

                        className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${

                          currentPage === page

                            ? darkMode ? 'bg-[#7d6fa3] text-white shadow-md' : 'bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white shadow-md'

                            : darkMode ? 'bg-[#4a3f66] text-gray-300 hover:bg-[#5f5482]' : 'bg-white text-gray-700 hover:bg-gray-100 hover:shadow-sm border border-gray-300 active:scale-95'

                        }`}

                      >

                        {page}

                      </button>

                    ))}

                    {totalPages > 5 && (

                      <button

                        onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}

                        className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg ${darkMode ? 'bg-[#4a3f66] text-gray-300 hover:bg-[#5f5482]' : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'} flex items-center justify-center transition`}

                      >

                        <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />

                      </button>

                    )}

                  </div>

                </div>

              </>

            )}

          </div>

        </main>

      </div>

    );

  }