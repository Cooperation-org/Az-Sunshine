// frontend/src/components/TopCandidatesChart.jsx
/**
 * Top 20 Candidates by Independent Expenditure Activity
 * Phase 1 Requirement: Visualize IE spending for/against candidates
 * 
 * Based on PDF specification showing:
 * - Green bars: IE spending FOR candidate
 * - Red bars: IE spending AGAINST candidate
 * - Net IE spending shown in annotations
 */

import React, { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import api from "../api/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function TopCandidatesChart({ officeId, cycleId, limit = 20 }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTopCandidates();
  }, [officeId, cycleId, limit]);

  async function loadTopCandidates() {
    try {
      setLoading(true);
      setError(null);

      // Build query params
      const params = new URLSearchParams();
      if (officeId) params.append('office_id', officeId);
      if (cycleId) params.append('cycle_id', cycleId);
      params.append('limit', limit);

      const response = await api.get(`ie-analysis/top-candidates/?${params.toString()}`);
      setData(response.data);
    } catch (err) {
      console.error("Error loading top candidates:", err);
      setError("Failed to load candidate data");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading candidates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  if (!data || !data.candidates || data.candidates.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">No candidate data available</div>
      </div>
    );
  }

  // Sort by total IE (for + against) descending
  const sortedCandidates = [...data.candidates].sort(
    (a, b) => b.ie_total - a.ie_total
  );

  // Prepare chart data
  const chartData = {
    labels: sortedCandidates.map(c => c.candidate_name || 'Unknown'),
    datasets: [
      {
        label: 'IE For',
        data: sortedCandidates.map(c => c.ie_for || 0),
        backgroundColor: 'rgba(34, 197, 94, 0.8)', // Green
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 1,
      },
      {
        label: 'IE Against',
        data: sortedCandidates.map(c => -(c.ie_against || 0)), // Negative for opposite side
        backgroundColor: 'rgba(239, 68, 68, 0.8)', // Red
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    indexAxis: 'y', // Horizontal bars
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `Top ${sortedCandidates.length} Candidates by Independent Expenditure Activity`,
        font: {
          size: 16,
          weight: 'bold',
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const value = Math.abs(context.raw);
            const label = context.dataset.label || '';
            return `${label}: $${value.toLocaleString()}`;
          },
          afterLabel: function (context) {
            const candidate = sortedCandidates[context.dataIndex];
            const net = candidate.ie_net || 0;
            return `Net: $${net.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        stacked: false,
        ticks: {
          callback: function (value) {
            return '$' + Math.abs(value).toLocaleString();
          },
        },
        title: {
          display: true,
          text: 'Amount ($)',
        },
      },
      y: {
        stacked: false,
        ticks: {
          autoSkip: false,
          font: {
            size: 10,
          },
        },
      },
    },
  };

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg p-6 shadow-lg">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded p-4">
            <p className="text-sm text-gray-600">Total IE For</p>
            <p className="text-2xl font-bold text-green-600">
              ${(data.summary?.total_ie_for || 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-50 rounded p-4">
            <p className="text-sm text-gray-600">Total IE Against</p>
            <p className="text-2xl font-bold text-red-600">
              ${(data.summary?.total_ie_against || 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-50 rounded p-4">
            <p className="text-sm text-gray-600">Total Candidates</p>
            <p className="text-2xl font-bold text-gray-700">
              {data.summary?.num_candidates || 0}
            </p>
          </div>
        </div>

        {/* Chart */}
        <div style={{ height: '600px' }}>
          <Bar data={chartData} options={options} />
        </div>

        {/* Example Flow Annotation */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm font-semibold text-blue-900 mb-2">
            Example Flow: GOPAC ($25,000) → ACPA Action Committee → IE spending on candidates
          </p>
          <p className="text-xs text-blue-700">
            This chart shows the top {sortedCandidates.length} candidates by total IE spending 
            (both for and against). Green bars represent spending <strong>for</strong> the candidate, 
            red bars represent spending <strong>against</strong>. Net IE spending is shown in the annotations.
          </p>
        </div>
      </div>
    </div>
  );
}