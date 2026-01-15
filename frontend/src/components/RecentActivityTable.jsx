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
              <th>For/Not For Benefit</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan="7">No recent expenditures found</td></tr>
            )}
            {rows.map(r => (
              <tr key={r.id}>
                <td>{r.date || "—"}</td>
                <td>${Math.abs(Number(r.amount || 0)).toLocaleString()}</td>
                <td>{r.committee?.name || r.ie_committee?.name || "—"}</td>
                <td>{r.donor?.name || "—"}</td>
                <td>
                  {r.candidate ? (
                    <Link to={`/candidate/${r.candidate.id}`}>{r.candidate.name}</Link>
                  ) : (r.candidate_name || "—")}
                </td>
                <td>{r.purpose || "—"}</td>
                <td>{r.support_oppose === 'Support' || r.is_for_benefit === true ? 'For Benefit' : r.support_oppose === 'Oppose' || r.is_for_benefit === false ? 'Not For Benefit' : (r.support_oppose || "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
