// frontend/src/components/TopEntities.jsx
import React from "react";

export default function TopEntities({ topDonors = [], topCommittees = [] }) {
  return (
    <div className="top-entities">
      <div className="card">
        <h3>Top Donors</h3>
        <ol className="entity-list">
          {topDonors.length === 0 && <li>No donor data</li>}
          {topDonors.slice(0,10).map(d => (
            <li key={d.id}>
              <div className="entity-row">
                <div className="entity-name">{d.name}</div>
                <div className="entity-amount">${Number(d.total_contribution || d.total || 0).toLocaleString()}</div>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <h3>Top Committees</h3>
        <ol className="entity-list">
          {topCommittees.length === 0 && <li>No committee data</li>}
          {topCommittees.slice(0,10).map(c => (
            <li key={c.id}>
              <div className="entity-row">
                <div className="entity-name">{c.name}</div>
                <div className="entity-amount">${Number(c.total || c.total_expenditure || 0).toLocaleString()}</div>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
