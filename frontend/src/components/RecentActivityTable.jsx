// frontend/src/components/RecentActivityTable.jsx
import React from "react";
import { Link } from "react-router-dom";

export default function RecentActivityTable({ rows = [] }) {
  return (
    <div className="card">
      <h3>Recent Expenditures</h3>
      <div className="table-wrap">
        <table className="recent-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Committee</th>
              <th>Donor</th>
              <th>Candidate</th>
              <th>Purpose</th>
              <th>Support/Oppose</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan="7">No recent expenditures found</td></tr>
            )}
            {rows.map(r => (
              <tr key={r.id}>
                <td>{r.date || "—"}</td>
                <td>${Number(r.amount || 0).toLocaleString()}</td>
                <td>{r.committee?.name || r.ie_committee?.name || "—"}</td>
                <td>{r.donor?.name || "—"}</td>
                <td>
                  {r.candidate ? (
                    <Link to={`/candidate/${r.candidate.id}`}>{r.candidate.name}</Link>
                  ) : (r.candidate_name || "—")}
                </td>
                <td>{r.purpose || "—"}</td>
                <td>{r.support_oppose || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
