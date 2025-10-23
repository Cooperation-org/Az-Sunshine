// frontend/src/components/MetricCards.jsx
import React from "react";

export default function MetricCards({ metrics }) {
  // metrics expected:
  // { total_ie_spending, total_candidates, percent_support, grassroots_threshold, last_updated }
  if (!metrics) {
    return (
      <div className="metric-cards">
        <div className="card">Loading metrics…</div>
      </div>
    );
  }

  const {
    total_ie_spending = 0,
    total_candidates = 0,
    percent_support = 0,
    grassroots_threshold = null,
    last_updated = null,
  } = metrics;

  const formattedMoney = (v) => `$${Number(v || 0).toLocaleString()}`;

  return (
    <div className="metric-cards">
      <div className="card metric">
        <div className="metric-title">Total IE Spending</div>
        <div className="metric-value">{formattedMoney(total_ie_spending)}</div>
        {last_updated && <div className="metric-sub">Last updated: {new Date(last_updated).toLocaleString()}</div>}
      </div>

      <div className="card metric">
        <div className="metric-title">Tracked Candidates</div>
        <div className="metric-value">{Number(total_candidates).toLocaleString()}</div>
        <div className="metric-sub">Includes filings from SOS, county & other sources</div>
      </div>

      <div className="card metric">
        <div className="metric-title">% Support vs Oppose (by $)</div>
        <div className="metric-value">{Number(percent_support || 0).toFixed(1)}%</div>
        <div className="metric-sub">Percent supporting candidates (by spending)</div>
      </div>

      {grassroots_threshold !== null && (
        <div className="card metric">
          <div className="metric-title">Grassroots Threshold</div>
          <div className="metric-value">{formattedMoney(grassroots_threshold)}</div>
          <div className="metric-sub">Compare candidate totals to this threshold</div>
        </div>
      )}
    </div>
  );
}
