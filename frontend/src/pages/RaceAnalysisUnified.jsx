import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { useDarkMode } from "../context/DarkModeContext";
import {
  ChevronDown, TrendingUp, TrendingDown, ExternalLink,
  Search, Filter, Target, Users, DollarSign, Loader
} from "lucide-react";
import api from "../api/api";

const Banner = ({
  offices, cycles, parties,
  selectedOffice, setSelectedOffice,
  selectedCycle, setSelectedCycle,
  selectedParty, setSelectedParty,
  raceType, setRaceType
}) => {
  const { darkMode } = useDarkMode();

  return (
    <div
      className="w-full rounded-2xl p-6 md:p-10 mb-8 transition-colors duration-300 text-white"
      style={darkMode
        ? { background: '#2D2844' }
        : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }
      }
    >
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
            Race <span style={{ color: '#A78BFA' }}>Analysis</span>
          </h1>
          <p className="text-white/70 text-sm mt-1 max-w-xl">
            Deep dive into electoral races with IE spending, donors, and candidate analysis
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Race Type Filter */}
          <div className="relative">
            <select
              value={raceType}
              onChange={(e) => setRaceType(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              <option value="all" className="bg-[#2D2844]">All Races</option>
              <option value="primary" className="bg-[#2D2844]">Primary Only</option>
              <option value="general" className="bg-[#2D2844]">General Only</option>
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          {/* Party Filter (for primaries) */}
          <div className="relative">
            <select
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              <option value="" className="bg-[#2D2844]">All Parties</option>
              {parties.map((p) => (
                <option key={p} value={p} className="bg-[#2D2844]">{p}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          {/* Office */}
          <div className="relative">
            <select
              value={selectedOffice}
              onChange={(e) => setSelectedOffice(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              <option value="" className="bg-[#2D2844]">Select Office</option>
              {offices.map((o) => (
                <option key={o.office_id} value={o.name} className="bg-[#2D2844]">{o.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>

          {/* Cycle */}
          <div className="relative">
            <select
              value={selectedCycle}
              onChange={(e) => setSelectedCycle(e.target.value)}
              className="w-full appearance-none px-4 py-2.5 rounded-full text-sm text-white border-none outline-none focus:ring-1 focus:ring-[#7667C1] transition-all"
              style={darkMode
                ? { background: '#1F1B31' }
                : { background: 'rgba(255, 255, 255, 0.15)' }
              }
            >
              <option value="" className="bg-[#2D2844]">Select Cycle</option>
              {cycles.map((c) => (
                <option key={c.cycle_id} value={c.name} className="bg-[#2D2844]">{c.name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default function RaceAnalysisUnified() {
  const { darkMode } = useDarkMode();
  const [offices, setOffices] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [parties] = useState(['Democratic', 'Republican']);

  const [selectedOffice, setSelectedOffice] = useState("");
  const [selectedCycle, setSelectedCycle] = useState("");
  const [selectedParty, setSelectedParty] = useState("");
  const [raceType, setRaceType] = useState("all");

  const [raceData, setRaceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load offices and cycles
  useEffect(() => {
    loadDropdowns();
  }, []);

  // Load race data when selections change
  useEffect(() => {
    if (selectedOffice && selectedCycle) {
      loadRaceData();
    }
  }, [selectedOffice, selectedCycle, selectedParty]);

  const loadDropdowns = async () => {
    try {
      const [officesRes, cyclesRes] = await Promise.all([
        api.get('/offices/'),
        api.get('/cycles/')
      ]);
      setOffices(officesRes.data || []);
      setCycles(cyclesRes.data || []);
    } catch (err) {
      console.error('Error loading dropdowns:', err);
    }
  };

  const loadRaceData = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        office: selectedOffice,
        cycle: selectedCycle
      };

      if (selectedParty) {
        params.party = selectedParty;
      }

      const response = await api.get('/races/primary/', { params });
      setRaceData(response.data);
    } catch (err) {
      console.error('Error loading race data:', err);
      setError(err.response?.data?.error || 'Failed to load race data');
      setRaceData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const getOpenSecretsLink = (committeeName) => {
    const searchQuery = encodeURIComponent(committeeName);
    return `https://www.opensecrets.org/search?q=${searchQuery}&type=committees`;
  };

  return (
    <div className={`flex min-h-screen ${darkMode ? 'bg-[#1A1625]' : 'bg-gray-50'}`}>
      <Sidebar />

      <main className="flex-1 min-w-0">
        <div className="p-4 sm:p-6 lg:p-8">
          <Banner
            offices={offices}
            cycles={cycles}
            parties={parties}
            selectedOffice={selectedOffice}
            setSelectedOffice={setSelectedOffice}
            selectedCycle={selectedCycle}
            setSelectedCycle={setSelectedCycle}
            selectedParty={selectedParty}
            setSelectedParty={setSelectedParty}
            raceType={raceType}
            setRaceType={setRaceType}
          />

          {!selectedOffice || !selectedCycle ? (
            <div className={`rounded-2xl p-12 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
              <div className="text-center">
                <Filter size={48} className={`mx-auto mb-4 ${darkMode ? 'text-gray-600' : 'text-gray-400'}`} />
                <p className={`text-lg ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Select an office and cycle to analyze a race
                </p>
              </div>
            </div>
          ) : loading ? (
            <div className={`rounded-2xl p-12 shadow-xl flex items-center justify-center ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
              <Loader size={48} className="animate-spin text-[#7163BA]" />
            </div>
          ) : error ? (
            <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
              <p className="text-red-500 text-center">{error}</p>
            </div>
          ) : raceData ? (
            <div className="space-y-6">
              {/* Race Header */}
              <div className={`rounded-2xl p-6 shadow-xl ${darkMode ? 'bg-[#2D2844]' : 'bg-white'}`}>
                <h2 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {raceData.race.office}
                </h2>
                <div className="flex items-center gap-4 text-sm">
                  {raceData.race.party && (
                    <span className={`font-bold ${
                      raceData.race.party === 'Democratic' ? 'text-blue-500' : 'text-red-500'
                    }`}>
                      {raceData.race.party} {raceData.race.candidate_count >= 2 ? 'Primary' : 'Race'}
                    </span>
                  )}
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    {raceData.race.cycle}
                  </span>
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    {raceData.race.candidate_count} Candidate{raceData.race.candidate_count !== 1 ? 's' : ''}
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
              {raceData.biggest_ie_spenders && raceData.biggest_ie_spenders.length > 0 && (
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
              {raceData.biggest_donors_to_ies && raceData.biggest_donors_to_ies.length > 0 && (
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
          ) : null}
        </div>
      </main>
    </div>
  );
}
