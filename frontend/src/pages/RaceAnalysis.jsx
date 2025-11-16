import React, { useEffect, useState } from "react";
import { Bell, Search } from "lucide-react";
import { getOffices, getCycles, getRaceIESpending, getRaceTopDonors } from "../api/api";
import Sidebar from "../components/Sidebar";
import { Bar } from "react-chartjs-2";
import Header from "../components/Header";
import Preloader from "../components/Preloader";
export default function RaceAnalysis() {
  const [offices, setOffices] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [selectedOffice, setSelectedOffice] = useState("");
  const [selectedCycle, setSelectedCycle] = useState("");
  const [raceData, setRaceData] = useState(null);
  const [topDonors, setTopDonors] = useState([]);
  const [loading, setLoading] = useState(true); // Changed to true for initial load
  const [initialLoad, setInitialLoad] = useState(true); // Track initial page load

  useEffect(() => {
    async function loadDropdowns() {
      try {
        setLoading(true);
        // Load dropdown options (offices and cycles) - these are fast lookups
        const [officesData, cyclesData] = await Promise.all([
          getOffices(),
          getCycles()
        ]);
        setOffices(officesData);
        setCycles(cyclesData);
        
        // Auto-select first cycle if available
        if (cyclesData.length > 0) {
          setSelectedCycle(cyclesData[0].cycle_id);
        }
      } catch (error) {
        console.error("Error loading dropdowns:", error);
        // Set empty arrays on error so page still renders
        setOffices([]);
        setCycles([]);
      } finally {
        // Always set loading to false after dropdowns load
        // This allows the page to render even if no office/cycle is selected yet
        setLoading(false);
        setInitialLoad(false);
      }
    }
    loadDropdowns();
  }, []);

  async function loadRaceData() {
    // Don't load race data if office or cycle is not selected
    if (!selectedOffice || !selectedCycle) {
      setRaceData(null);
      setTopDonors([]);
      return;
    }
    
    // Set loading state for race data (not initial page load)
    setLoading(true);
    try {
      // Load race spending and top donors data in parallel
      // These API calls might be slow if the database queries are complex
      const [spending, donors] = await Promise.all([
        getRaceIESpending(selectedOffice, selectedCycle),
        getRaceTopDonors(selectedOffice, selectedCycle)
      ]);
      setRaceData(spending);
      setTopDonors(donors.top_donors || []);
    } catch (error) {
      console.error("Error loading race data:", error);
      // Set empty data on error so page still renders
      setRaceData(null);
      setTopDonors([]);
    } finally {
      // Always set loading to false after race data loads
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
        label: 'IE For',
        data: raceData.candidates.map(c => parseFloat(c.total_ie || 0)),
        backgroundColor: 'rgba(34, 197, 94, 0.6)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1
      }
    ]
  } : null;

  // Show preloader ONLY on initial page load (while dropdowns are loading)
  // Once dropdowns are loaded, show the page even if race data is still loading
  if (initialLoad) {
    return <Preloader message="Loading race analysis..." />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      
      <main className="ml-20 flex-1">
        <Header title="Arizona Sunshine" subtitle="Race Analysis" />

        <div className="p-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Select Race</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Office</label>
                <select
                  value={selectedOffice}
                  onChange={(e) => setSelectedOffice(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Election Cycle</label>
                <select
                  value={selectedCycle}
                  onChange={(e) => setSelectedCycle(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
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

          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading race data...</div>
          ) : raceData ? (
            <>
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div className="bg-white rounded-2xl p-6 shadow-lg col-span-2">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">
                    IE Spending by Candidate - {raceData.office} ({raceData.cycle})
                  </h2>
                  {chartData && (
                    <div style={{ height: 400 }}>
                      <Bar 
                        data={chartData} 
                        options={{ 
                          responsive: true, 
                          maintainAspectRatio: false,
                          plugins: {
                            legend: { display: true },
                            tooltip: {
                              callbacks: {
                                label: (context) => `$${context.parsed.y.toLocaleString()}`
                              }
                            }
                          },
                          scales: {
                            y: {
                              beginAtZero: true,
                              ticks: {
                                callback: (value) => `$${value.toLocaleString()}`
                              }
                            }
                          }
                        }} 
                      />
                    </div>
                  )}
                </div>

                <div className="bg-white rounded-2xl p-6 shadow-lg">
                  <h2 className="text-lg font-bold text-gray-900 mb-4">Top Donors in Race</h2>
                  <div className="space-y-3">
                    {topDonors.slice(0, 10).map((donor, idx) => (
                      <div key={idx} className="flex justify-between items-center pb-2 border-b border-gray-100">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {donor.entity__first_name} {donor.entity__last_name}
                          </p>
                          <p className="text-xs text-gray-500">{donor.entity__occupation || 'N/A'}</p>
                        </div>
                        <p className="text-sm font-bold text-gray-900">
                          ${parseFloat(donor.total_contributed || 0).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Candidate Breakdown</h2>
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Candidate</th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Party</th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Total IE</th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">IE For</th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">IE Against</th>
                      <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700">Net IE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {raceData.candidates.map((candidate, idx) => {
                      const ieFor = parseFloat(candidate.is_for_benefit === true ? candidate.total_ie : 0);
                      const ieAgainst = parseFloat(candidate.is_for_benefit === false ? candidate.total_ie : 0);
                      const netIE = ieFor - ieAgainst;
                      
                      return (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="py-4 px-6 font-medium text-gray-900">
                            {candidate.subject_committee__name__first_name} {candidate.subject_committee__name__last_name}
                          </td>
                          <td className="py-4 px-6 text-gray-700">
                            {candidate.subject_committee__candidate_party__name || 'N/A'}
                          </td>
                          <td className="py-4 px-6 font-bold text-gray-900">
                            ${parseFloat(candidate.total_ie || 0).toLocaleString()}
                          </td>
                          <td className="py-4 px-6 text-green-600">
                            ${ieFor.toLocaleString()}
                          </td>
                          <td className="py-4 px-6 text-red-600">
                            ${ieAgainst.toLocaleString()}
                          </td>
                          <td className="py-4 px-6 font-bold">
                            <span className={netIE >= 0 ? 'text-green-600' : 'text-red-600'}>
                              ${netIE.toLocaleString()}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Select an office and cycle to view race analysis
            </div>
          )}
        </div>
      </main>
    </div>
  );
}