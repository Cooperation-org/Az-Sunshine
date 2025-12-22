import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { useDarkMode } from '../context/DarkModeContext';
import { Users, DollarSign, TrendingUp, TrendingDown, ExternalLink, Filter, Search, Loader } from 'lucide-react';
import api from '../api/api';

export default function PrimaryRaceView() {
  const { darkMode } = useDarkMode();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [availableRaces, setAvailableRaces] = useState([]);
  const [raceData, setRaceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedParty, setSelectedParty] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Get selected race from URL params
  const selectedOffice = searchParams.get('office');
  const selectedPartyParam = searchParams.get('party');
  const selectedCycle = searchParams.get('cycle');

  // Load available races on mount
  useEffect(() => {
    loadAvailableRaces();
  }, []);

  // Load race details when selection changes
  useEffect(() => {
    if (selectedOffice && selectedPartyParam && selectedCycle) {
      loadRaceDetails(selectedOffice, selectedPartyParam, selectedCycle);
    }
  }, [selectedOffice, selectedPartyParam, selectedCycle]);

  const loadAvailableRaces = async () => {
    try {
      const response = await api.get('/races/primary/available/');
      setAvailableRaces(response.data.races || []);
    } catch (err) {
      console.error('Error loading available races:', err);
      setError('Failed to load available races');
    }
  };

  const loadRaceDetails = async (office, party, cycle) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/races/primary/', {
        params: { office, party, cycle }
      });
      setRaceData(response.data);
    } catch (err) {
      console.error('Error loading race details:', err);
      setError(err.response?.data?.error || 'Failed to load race details');
      setRaceData(null);
    } finally {
      setLoading(false);
    }
  };

  const selectRace = (office, party, cycle) => {
    setSearchParams({ office, party, cycle });
  };

  // Filter races
  const filteredRaces = availableRaces.filter(race => {
    const matchesParty = selectedParty === 'all' || race.party === selectedParty;
    const matchesSearch = race.office.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesParty && matchesSearch && race.total_ie > 0; // Only show races with IE spending
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const getOpenSecretsLink = (committeeName) => {
    // Generate OpenSecrets search link
    const searchQuery = encodeURIComponent(committeeName);
    return `https://www.opensecrets.org/search?q=${searchQuery}&type=committees`;
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Primary Race Analysis
            </h1>
            <p className={`mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Detailed view of Independent Expenditure spending in primary races
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar: Race Selector */}
          <div className="lg:col-span-1">
            <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
              <h2 className={`text-xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Select Primary Race
              </h2>

              {/* Party Filter */}
              <div className="mb-4">
                <label className={`block text-sm font-bold mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Filter by Party
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedParty('all')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedParty === 'all'
                        ? 'bg-[#7163BA] text-white'
                        : darkMode
                        ? 'bg-[#1F1B31] text-gray-400 hover:bg-[#2D2844]'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setSelectedParty('Democratic')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedParty === 'Democratic'
                        ? 'bg-blue-600 text-white'
                        : darkMode
                        ? 'bg-[#1F1B31] text-gray-400 hover:bg-[#2D2844]'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Dem
                  </button>
                  <button
                    onClick={() => setSelectedParty('Republican')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedParty === 'Republican'
                        ? 'bg-red-600 text-white'
                        : darkMode
                        ? 'bg-[#1F1B31] text-gray-400 hover:bg-[#2D2844]'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Rep
                  </button>
                </div>
              </div>

              {/* Search */}
              <div className="mb-4">
                <div className="relative">
                  <Search size={18} className={`absolute left-3 top-3 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search races..."
                    className={`w-full pl-10 pr-4 py-2 rounded-lg border outline-none transition-all ${
                      darkMode
                        ? 'bg-[#1F1B31] border-gray-700 text-white placeholder-gray-500'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'
                    }`}
                  />
                </div>
              </div>

              {/* Race List */}
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {filteredRaces.length === 0 ? (
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    No races with IE spending found
                  </p>
                ) : (
                  filteredRaces.map((race, index) => (
                    <button
                      key={index}
                      onClick={() => selectRace(race.office, race.party, race.cycle)}
                      className={`w-full text-left p-3 rounded-lg transition-all ${
                        selectedOffice === race.office && selectedPartyParam === race.party && selectedCycle === race.cycle
                          ? 'bg-[#7163BA] text-white'
                          : darkMode
                          ? 'bg-[#1F1B31] text-gray-300 hover:bg-[#2D2844]'
                          : 'bg-gray-50 text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-bold text-sm truncate">{race.office}</div>
                      <div className="flex items-center justify-between mt-1">
                        <span className={`text-xs ${
                          race.party === 'Democratic' ? 'text-blue-400' : 'text-red-400'
                        }`}>
                          {race.party} {race.cycle}
                        </span>
                        <span className="text-xs font-bold">{formatCurrency(race.total_ie)}</span>
                      </div>
                      <div className="text-xs mt-1 opacity-70">
                        {race.candidate_count} candidates
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Main Content: Race Details */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className={`rounded-2xl p-12 shadow-xl flex items-center justify-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                <Loader size={48} className="animate-spin text-[#7163BA]" />
              </div>
            ) : error ? (
              <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                <p className="text-red-500 text-center">{error}</p>
              </div>
            ) : !raceData ? (
              <div className={`rounded-2xl p-12 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                <p className={`text-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Select a primary race to view details
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Race Header */}
                <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                  <h2 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {raceData.race.office}
                  </h2>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`font-bold ${
                      raceData.race.party === 'Democratic' ? 'text-blue-500' : 'text-red-500'
                    }`}>
                      {raceData.race.party} Primary
                    </span>
                    <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                      {raceData.race.cycle}
                    </span>
                    <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                      {raceData.race.candidate_count} Candidates
                    </span>
                  </div>

                  {/* Race Totals */}
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}>
                      <div className={`text-sm font-bold mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        Total IE
                      </div>
                      <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {formatCurrency(raceData.race.total_ie)}
                      </div>
                    </div>
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-green-900/20' : 'bg-green-50'}`}>
                      <div className={`text-sm font-bold mb-1 ${darkMode ? 'text-green-400' : 'text-green-700'}`}>
                        IE FOR
                      </div>
                      <div className={`text-2xl font-bold ${darkMode ? 'text-green-300' : 'text-green-600'}`}>
                        {formatCurrency(raceData.race.total_ie_for)}
                      </div>
                    </div>
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-red-900/20' : 'bg-red-50'}`}>
                      <div className={`text-sm font-bold mb-1 ${darkMode ? 'text-red-400' : 'text-red-700'}`}>
                        IE AGAINST
                      </div>
                      <div className={`text-2xl font-bold ${darkMode ? 'text-red-300' : 'text-red-600'}`}>
                        {formatCurrency(raceData.race.total_ie_against)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Candidates */}
                <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                  <h3 className={`text-xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    Candidates
                  </h3>
                  <div className="space-y-4">
                    {raceData.candidates.map((candidate, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-lg ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <h4 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            {candidate.name}
                          </h4>
                          <div className={`text-sm font-bold ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                            Total IE: {formatCurrency(candidate.total_ie)}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          {/* IE FOR */}
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <TrendingUp size={16} className="text-green-500" />
                              <span className={`text-sm font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                                IE FOR: {formatCurrency(candidate.ie_for)}
                              </span>
                            </div>
                            {candidate.ie_for_spenders.length > 0 && (
                              <ul className="space-y-1 ml-6">
                                {candidate.ie_for_spenders.map((spender, idx) => (
                                  <li key={idx} className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                    <a
                                      href={getOpenSecretsLink(spender.name)}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="hover:text-[#7163BA] flex items-center gap-1"
                                    >
                                      {spender.name}: {formatCurrency(spender.amount)}
                                      <ExternalLink size={12} />
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>

                          {/* IE AGAINST */}
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <TrendingDown size={16} className="text-red-500" />
                              <span className={`text-sm font-bold ${darkMode ? 'text-red-400' : 'text-red-600'}`}>
                                IE AGAINST: {formatCurrency(candidate.ie_against)}
                              </span>
                            </div>
                            {candidate.ie_against_spenders.length > 0 && (
                              <ul className="space-y-1 ml-6">
                                {candidate.ie_against_spenders.map((spender, idx) => (
                                  <li key={idx} className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                    <a
                                      href={getOpenSecretsLink(spender.name)}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="hover:text-[#7163BA] flex items-center gap-1"
                                    >
                                      {spender.name}: {formatCurrency(spender.amount)}
                                      <ExternalLink size={12} />
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Biggest IE Spenders */}
                {raceData.biggest_ie_spenders.length > 0 && (
                  <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                    <h3 className={`text-xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Biggest IE Spenders in This Race
                    </h3>
                    <div className="space-y-2">
                      {raceData.biggest_ie_spenders.map((spender, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg flex items-center justify-between ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}
                        >
                          <div className="flex-1">
                            <a
                              href={getOpenSecretsLink(spender.name)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`font-bold hover:text-[#7163BA] flex items-center gap-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}
                            >
                              {spender.name}
                              <ExternalLink size={14} />
                            </a>
                            <div className="text-sm mt-1">
                              <span className={spender.benefit === 'FOR' ? 'text-green-500' : 'text-red-500'}>
                                {spender.benefit}
                              </span>
                              <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                                {' '}{spender.candidate}
                              </span>
                            </div>
                          </div>
                          <div className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            {formatCurrency(spender.amount)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Biggest Donors to IEs */}
                {raceData.biggest_donors_to_ies.length > 0 && (
                  <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                    <h3 className={`text-xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      Biggest Donors to IE Committees
                    </h3>
                    <div className="space-y-2">
                      {raceData.biggest_donors_to_ies.map((donor, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg flex items-center justify-between ${darkMode ? 'bg-[#1F1B31]' : 'bg-gray-50'}`}
                        >
                          <div className="flex-1">
                            <Link
                              to={`/donors?entity_id=${donor.entity_id}`}
                              className={`font-bold hover:text-[#7163BA] ${darkMode ? 'text-white' : 'text-gray-900'}`}
                            >
                              {donor.name}
                            </Link>
                            <div className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                              {donor.contribution_count} contributions
                            </div>
                          </div>
                          <div className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                            {formatCurrency(donor.total_contributed)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        </div>
      </main>
    </div>
  );
}
