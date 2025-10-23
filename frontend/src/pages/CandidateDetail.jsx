// frontend/src/pages/CandidateDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getCandidate,
  getExpenditures,
  getSupportOpposeByCandidate,
} from "../api/api";
import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [expenditures, setExpenditures] = useState([]);
  const [supportOppose, setSupportOppose] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadCandidate() {
      setLoading(true);
      try {
        const [candData, expData, soData] = await Promise.all([
          getCandidate(id),
          getExpenditures({ candidate_id: id }),
          getSupportOpposeByCandidate({ candidate_id: id }),
        ]);

        setCandidate(candData);
        setExpenditures(expData.results || expData || []);
        setSupportOppose(soData || []);
      } catch (err) {
        console.error("Error loading candidate detail:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCandidate();
  }, [id]);

  if (!candidate) return <div className="container"><p>Loading candidate data...</p></div>;

  // --- prepare chart data ---
  const spendByCommittee = expenditures.reduce((acc, e) => {
    const committeeName = e.committee?.name || e.ie_committee?.name || "Unknown Committee";
    acc[committeeName] = (acc[committeeName] || 0) + Number(e.amount || 0);
    return acc;
  }, {});

  const committeeLabels = Object.keys(spendByCommittee);
  const committeeTotals = Object.values(spendByCommittee);

  const barData = {
    labels: committeeLabels,
    datasets: [
      {
        label: "Total IE Spending by Committee (USD)",
        data: committeeTotals,
      },
    ],
  };

  const totalsByType = supportOppose.reduce((acc, row) => {
    const key = row.support_oppose || "Unknown";
    acc[key] = (acc[key] || 0) + Number(row.total || 0);
    return acc;
  }, {});

  const pieData = {
    labels: Object.keys(totalsByType),
    datasets: [{ data: Object.values(totalsByType) }],
  };

  // --- candidate details for header ---
  const infoPairs = [
    ["Race", candidate.race?.name || "—"],
    ["Office", candidate.race?.office || "—"],
    ["Party", candidate.party || "—"],
    ["Contacted", candidate.contact_status || "—"],
    ["Filing Date", candidate.filing_date || "—"],
    ["External ID", candidate.external_id || "—"],
    ["Email", candidate.email || "—"],
  ];

  return (
    <div className="container">
      <header className="header card">
        <h1>{candidate.name}</h1>
        <p className="lead">Candidate details and Independent Expenditure overview</p>
      </header>

      <div className="card">
        <h3>Candidate Information</h3>
        <table className="info-table">
          <tbody>
            {infoPairs.map(([label, val]) => (
              <tr key={label}>
                <td className="label">{label}</td>
                <td>{val}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid two-col">
        <div className="card">
          <h3>IE Spending by Committee</h3>
          {committeeLabels.length > 0 ? (
            <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} />
          ) : (
            <p>No IE spending data for this candidate.</p>
          )}
        </div>

        <div className="card">
          <h3>Support vs Oppose</h3>
          {Object.keys(totalsByType).length > 0 ? (
            <div style={{ height: 260 }}>
              <Pie data={pieData} />
            </div>
          ) : (
            <p>No support/oppose data.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Independent Expenditures for {candidate.name}</h3>
        <div className="table-wrap">
          <table className="recent-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Committee</th>
                <th>Donor</th>
                <th>Amount</th>
                <th>Purpose</th>
                <th>Support/Oppose</th>
              </tr>
            </thead>
            <tbody>
              {expenditures.length === 0 && (
                <tr><td colSpan="6">No expenditures recorded.</td></tr>
              )}
              {expenditures.map(e => (
                <tr key={e.id}>
                  <td>{e.date || "—"}</td>
                  <td>{e.committee?.name || e.ie_committee?.name || "—"}</td>
                  <td>{e.donor?.name || "—"}</td>
                  <td>${Number(e.amount || 0).toLocaleString()}</td>
                  <td>{e.purpose || "—"}</td>
                  <td>{e.support_oppose || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <footer className="footer card">
        <Link to="/">← Back to Dashboard</Link>
      </footer>
    </div>
  );
}
