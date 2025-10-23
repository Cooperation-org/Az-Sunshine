// frontend/src/components/FilterPanel.jsx
import React, { useEffect, useState } from "react";
import { getRaces } from "../api/api";

export default function FilterPanel({ filters, setFilters }) {
  const [races, setRaces] = useState([]);

  useEffect(() => {
    async function loadRaces() {
      const r = await getRaces();
      setRaces(r || []);
    }
    loadRaces();
  }, []);

  function onChange(e) {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  }

  function clearFilters() {
    setFilters({ race_id: "", year: "", q: "" });
  }

  return (
    <div className="filter-panel card">
      <div className="filter-row">
        <label>
          Race
          <select name="race_id" value={filters.race_id || ""} onChange={onChange}>
            <option value="">All races</option>
            {races.map(r => (
              <option key={r.id} value={r.id}>{r.name}{r.office ? ` — ${r.office}` : ""}</option>
            ))}
          </select>
        </label>

        <label>
          Year
          <input
            name="year"
            type="number"
            min="2000"
            max="2100"
            placeholder="2024"
            value={filters.year || ""}
            onChange={onChange}
          />
        </label>

        <label style={{flex:1}}>
          Search
          <input
            name="q"
            type="search"
            placeholder="candidate, committee, donor..."
            value={filters.q || ""}
            onChange={onChange}
          />
        </label>

        <div style={{display:"flex", alignItems:"flex-end", gap:8}}>
          <button onClick={() => setFilters({...filters})}>Apply</button>
          <button onClick={clearFilters} className="muted">Clear</button>
        </div>
      </div>
    </div>
  );
}
