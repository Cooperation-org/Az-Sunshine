import React, { useEffect, useState } from "react";
import { Bell, Search } from "lucide-react";
import { getOffices, getCycles, getRaceIESpending, getRaceTopDonors } from "../api/api";
import Sidebar from "../components/Sidebar";
import { Bar } from "react-chartjs-2";
import Header from "../components/Header";
import { ChartSkeleton, TableSkeleton } from "../components/SkeletonLoader";
import { useDarkMode } from "../context/DarkModeContext";

export default function RaceAnalysis() {
  const { darkMode } = useDarkMode();
  const [offices, setOffices] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [selectedOffice, setSelectedOffice] = useState("");
  const [selectedCycle, setSelectedCycle] = useState("");
  const [raceData, setRaceData] = useState(null);
  const [topDonors, setTopDonors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);

  useEffect(() => {
    async function loadDropdowns() {
      try {
        setLoading(true);
        const [officesData, cyclesData] = await Promise.all([
          getOffices(),
          getCycles()
        ]);
        setOffices(officesData);
        setCycles(cyclesData);
        
        if (cyclesData.length > 0) {
          setSelectedCycle(cyclesData[0].cycle_id);
        }
      } catch (error) {
        console.error("Error loading dropdowns:", error);
        setOffices([]);
        setCycles([]);
      } finally {
        setLoading(false);
        setInitialLoad(false);
      }
    }
    loadDropdowns();
  }, []);

  async function loadRaceData() {
    if (!selectedOffice || !selectedCycle) {
      setRaceData(null);
      setTopDonors([]);
      return;
    }
    
    setLoading(true);
    try {
      const [spending, donors] = await Promise.all([
        getRaceIESpending({ office_id: selectedOffice, cycle_id: selectedCycle }),
        getRaceTopDonors({ office_id: selectedOffice, cycle_id: selectedCycle })
      ]);
      setRaceData(spending);
      setTopDonors(donors.top_donors || []);
    } catch (error) {
      console.error("Error loading race data:", error);
      setRaceData(null);
      setTopDonors([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedOffice && selectedCycle) {
      loadRaceData();
    }
  }, [selectedOffice, selectedCycle]);

  const chartData = raceData?.candidates ? {
    labels: raceData.candidates.map(c =>
      `${c.subject_committee__name__first_name || ''} ${c.subject_committee__name__last_name || ''}`.trim()
    ),
    datasets: [
      {
        label: 'IE Spending',
        data: raceData.candidates.map(c => Math.abs(parseFloat(c.total_ie || 0))),
        backgroundColor: darkMode ? 'rgba(139, 124, 184, 0.6)' : 'rgba(107, 91, 149, 0.6)',
        borderColor: darkMode ? 'rgba(139, 124, 184, 1)' : 'rgba(107, 91, 149, 1)',
        borderWidth: 1
      }
    ]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: darkMode ? '#d8dbfc' : '#4B5563'
        }
      },
      tooltip: {
        backgroundColor: darkMode ? 'rgba(51, 45, 84, 0.98)' : 'rgba(255, 255, 255, 0.98)',
        titleColor: darkMode ? '#ffffff' : '#1F2937',
        bodyColor: darkMode ? '#ffffff' : '#1F2937',
        borderColor: darkMode ? '#4c3e7c' : '#E5E7EB',
        borderWidth: 1,
        callbacks: {
          label: (context) => `$${context.parsed.y.toLocaleString()}`
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: darkMode ? '#b8b3cc' : '#6B7280'
        },
        grid: {
          color: darkMode ? '#5f5482' : '#F3F4F6'
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: darkMode ? '#b8b3cc' : '#6B7280',
          callback: (value) => `$${value.toLocaleString()}`
        },
        grid: {
          color: darkMode ? '#5f5482' : '#F3F4F6'
        }
      }
    }
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#6b5f87]' : 'bg-gray-50'}`}>
      <Sidebar />
      
      <main className="flex-1 lg:ml-0 min-w-0">
        <Header />

        <div className="p-4 sm:p-6 lg:p-8">
          <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-4 sm:p-6 border shadow-lg mb-4 sm:mb-6`}>
            <h2 className={`text-base sm:text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Select Race</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Office</label>
                <select
                  value={selectedOffice}
                  onChange={(e) => setSelectedOffice(e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-200 ${
                    darkMode 
                      ? 'bg-[#5f5482] border-[#6d5f8d] text-white' 
                      : 'bg-white border-gray-300 text-gray-900 hover:border-gray-400'
                  }`}
                >
                  <option value="">Select Office</option>
                  {offices.map(office => (
                    <option key={office.office_id} value={office.office_id}>
                      {office.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={`block text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Election Cycle</label>
                <select
                  value={selectedCycle}
                  onChange={(e) => setSelectedCycle(e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-200 ${
                    darkMode 
                      ? 'bg-[#5f5482] border-[#6d5f8d] text-white' 
                      : 'bg-white border-gray-300 text-gray-900 hover:border-gray-400'
                  }`}
                >
                  <option value="">Select Cycle</option>
                  {cycles.map(cycle => (
                    <option key={cycle.cycle_id} value={cycle.cycle_id}>
                      {cycle.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {initialLoad ? (
            <>
              <div className="mb-6">
                <div className="h-12 w-48 rounded animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%] mb-4"></div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="h-10 rounded animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]"></div>
                  <div className="h-10 rounded animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 bg-[length:200%_100%]"></div>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <ChartSkeleton height="300px" className="lg:col-span-2" />
                <ChartSkeleton height="300px" />
              </div>
              <div className={`overflow-x-auto shadow-lg rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>
                <table className="min-w-full divide-y divide-gray-200">
                  <tbody>
                    <TableSkeleton rows={8} columns={5} />
                  </tbody>
                </table>
              </div>
            </>
          ) : loading && selectedOffice && selectedCycle ? (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <ChartSkeleton height="300px" className="lg:col-span-2" />
                <ChartSkeleton height="300px" />
              </div>
              <div className={`overflow-x-auto shadow-lg rounded-2xl ${darkMode ? 'bg-[#3d3559]' : 'bg-white'}`}>
                <table className="min-w-full divide-y divide-gray-200">
                  <tbody>
                    <TableSkeleton rows={5} columns={5} />
                  </tbody>
                </table>
              </div>
            </>
          ) : raceData ? (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-4 sm:p-6 border shadow-lg lg:col-span-2`}>
                  <h2 className={`text-base sm:text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    IE Spending by Candidate - {raceData.office} ({raceData.cycle})
                  </h2>
                  {chartData && (
                    <div className="h-[250px] sm:h-[300px] lg:h-[400px]">
                      <Bar data={chartData} options={chartOptions} />
                    </div>
                  )}
                </div>

                <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-4 sm:p-6 border shadow-lg`}>
                  <h2 className={`text-base sm:text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Top Donors in Race</h2>
                  <div className="space-y-2 sm:space-y-3">
                    {topDonors.slice(0, 10).map((donor, idx) => (
                      <div key={idx} className={`flex justify-between items-center pb-2 border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-100'}`}>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            {donor.entity__first_name} {donor.entity__last_name}
                          </p>
                          <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{donor.entity__occupation || 'N/A'}</p>
                        </div>
                        <p className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                          ${parseFloat(donor.total_contributed || 0).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className={`${darkMode ? 'bg-[#3d3559] border-[#4a3f66]' : 'bg-white border-gray-100'} rounded-2xl p-4 sm:p-6 border shadow-lg overflow-hidden`}>
                <h2 className={`text-base sm:text-lg font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Candidate Breakdown</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className={`${darkMode ? 'bg-[#4a3f66]' : 'bg-gray-50'} border-b ${darkMode ? 'border-[#4a3f66]' : 'border-gray-200'}`}>
                      <tr>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Candidate</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Party</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Total IE</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>IE For</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>IE Against</th>
                        <th className={`text-left py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>Net IE</th>
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${darkMode ? 'divide-[#4a3f66]' : 'divide-gray-100'}`}>
                      {raceData.candidates.map((candidate, idx) => {
                        const ieFor = parseFloat(candidate.is_for_benefit === true ? candidate.total_ie : 0);
                        const ieAgainst = parseFloat(candidate.is_for_benefit === false ? candidate.total_ie : 0);
                        const netIE = ieFor - ieAgainst;
                        
                        return (
                          <tr key={idx} className={`transition-colors duration-150 ${darkMode ? 'hover:bg-[#4a3f66]' : 'hover:bg-purple-50/50'}`}>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'} whitespace-nowrap`}>
                              {candidate.subject_committee__name__first_name} {candidate.subject_committee__name__last_name}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-nowrap`}>
                              {candidate.subject_committee__candidate_party__name || 'N/A'}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'} whitespace-nowrap`}>
                              ${parseFloat(candidate.total_ie || 0).toLocaleString()}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm whitespace-nowrap ${darkMode ? 'text-green-300' : 'text-green-600'}`}>
                              ${ieFor.toLocaleString()}
                            </td>
                            <td className={`py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm whitespace-nowrap ${darkMode ? 'text-red-300' : 'text-red-600'}`}>
                              ${ieAgainst.toLocaleString()}
                            </td>
                            <td className="py-3 sm:py-4 px-3 sm:px-6 text-xs sm:text-sm font-bold whitespace-nowrap">
                              <span className={netIE >= 0 ? (darkMode ? 'text-green-300' : 'text-green-600') : (darkMode ? 'text-red-300' : 'text-red-600')}>
                                ${netIE.toLocaleString()}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className={`text-center py-12 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              Select an office and cycle to view race analysis
            </div>
          )}
        </div>
      </main>
    </div>
  );
}