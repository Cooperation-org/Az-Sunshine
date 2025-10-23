import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './Home.css';

function Home() {
  const [stats, setStats] = useState({
    totalSpending: 0,
    totalCandidates: 0,
    totalExpenditures: 0
  });
  
  const [latestExpenditures, setLatestExpenditures] = useState([]);
  const [topCommittees, setTopCommittees] = useState([]);
  const [supportVsOppose, setSupportVsOppose] = useState({ support: 50, oppose: 50 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel from backend
      const [
        expendituresRes,
        candidatesRes,
        committeesRes
      ] = await Promise.all([
        axios.get('/api/expenditures/').catch(() => ({ data: { results: [] } })),
        axios.get('/api/candidates/').catch(() => ({ data: { results: [] } })),
        axios.get('/api/iecommittees/').catch(() => ({ data: { results: [] } }))
      ]);

      // Process expenditures
      const expenditures = expendituresRes.data.results || expendituresRes.data || [];
      if (expenditures.length > 0) {
        setLatestExpenditures(expenditures.slice(0, 4));
      }
      
      // Calculate total spending from expenditures
      const totalSpending = expenditures.reduce((sum, exp) => {
        const amount = parseFloat(exp.amount) || 0;
        return sum + amount;
      }, 0);
      
      // Process candidates
      const candidates = candidatesRes.data.results || candidatesRes.data || [];
      const totalCandidates = candidatesRes.data.count || candidates.length || 0;
      
      // Process committees
      const committees = committeesRes.data.results || committeesRes.data || [];
      if (committees.length > 0) {
        setTopCommittees(committees.slice(0, 8));
      }
      
      // Calculate support vs oppose percentages
      const supportCount = expenditures.filter(e => 
        (e.support_oppose || '').toLowerCase().includes('support')
      ).length;
      const opposeCount = expenditures.filter(e => 
        (e.support_oppose || '').toLowerCase().includes('oppose')
      ).length;
      const total = supportCount + opposeCount || 1;
      
      if (supportCount > 0 || opposeCount > 0) {
        setSupportVsOppose({
          support: Math.round((supportCount / total) * 100),
          oppose: Math.round((opposeCount / total) * 100)
        });
      }
      
      // Set stats with real data (fallback to mock if no data)
      setStats({
        totalSpending: totalSpending > 0 ? totalSpending : 420000,
        totalCandidates: totalCandidates > 0 ? totalCandidates : 20000,
        totalExpenditures: expenditures.length > 0 ? expenditures.length : 900000
      });
      
      console.log('Dashboard data loaded:', {
        expenditures: expenditures.length,
        candidates: totalCandidates,
        committees: committees.length
      });
      
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      // Use mock data as fallback
      setStats({
        totalSpending: 420000,
        totalCandidates: 20000,
        totalExpenditures: 900000
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-text">Loading dashboard...</div>
      </div>
    );
  }

  // Mock data as fallback
  const mockExpenditures = [
    { date: '2025-10-22', committee: 'Ball LLC', candidate: 'Cynthia Bradley', amount: 5000, support_oppose: 'Support' },
    { date: '2025-10-21', committee: 'Scott-Swanson', candidate: 'Julie Grimes', amount: 300, support_oppose: 'Oppose' },
    { date: '2025-10-20', committee: 'Oneal-Sharp', candidate: 'Erin Phelps', amount: 1000, support_oppose: 'Support' },
    { date: '2025-10-19', committee: 'Mendez-Bean', candidate: 'Kathryn Drake', amount: 2000, support_oppose: 'Oppose' },
  ];

  const mockCommittees = [
    { name: 'Simmons PLC Committee', total_spending: 42000000 },
    { name: 'Austin Group Committee', total_spending: 1000000 },
    { name: 'Simmons PLC Committee', total_spending: 920000 },
    { name: 'Simmons PLC Committee', total_spending: 800000 },
    { name: 'Simmons PLC Committee', total_spending: 42000000 },
    { name: 'Austin Group Committee', total_spending: 1000000 },
    { name: 'Simmons PLC Committee', total_spending: 920000 },
    { name: 'Simmons PLC Committee', total_spending: 800000 },
  ];

  // Use real data if available, otherwise use mock data
  const displayExpenditures = latestExpenditures.length > 0 ? latestExpenditures : mockExpenditures;
  const displayCommittees = topCommittees.length > 0 ? topCommittees : mockCommittees;

  return (
    <div className="home-container">
      {/* Top Row: Chart and Donut */}
      <div className="top-row">
        {/* Top 10 Donors Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Top 10 Donors</h3>
          <p className="chart-subtitle">Total Contribution</p>
          <div className="chart-placeholder"></div>
        </div>

        {/* Support vs Oppose Spending */}
        <div className="donut-card">
          <h3 className="donut-title">Support vs Oppose<br />Spending</h3>
          <div className="donut-container">
            <svg className="donut-svg" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#D1D5DB"
                strokeWidth="12"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#6366F1"
                strokeWidth="12"
                strokeDasharray={`${supportVsOppose.support * 2.51} 251.2`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
              />
            </svg>
          </div>
          <div className="donut-legend">
            <div className="legend-item">
              <div className="legend-dot legend-support"></div>
              <span>{supportVsOppose.support}% support</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot legend-oppose"></div>
              <span>{supportVsOppose.oppose}% Oppose</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon"></div>
          <div className="stat-content">
            <div className="stat-label">Total IE Spending</div>
            <div className="stat-value">{formatCurrency(stats.totalSpending)}</div>
          </div>
          <button className="stat-menu">⋯</button>
        </div>

        <div className="stat-card">
          <div className="stat-icon"></div>
          <div className="stat-content">
            <div className="stat-label">Total Candidates</div>
            <div className="stat-value">{stats.totalCandidates.toLocaleString()}</div>
          </div>
          <button className="stat-menu">⋯</button>
        </div>

        <div className="stat-card">
          <div className="stat-icon"></div>
          <div className="stat-content">
            <div className="stat-label">Total Expenditures</div>
            <div className="stat-value">{formatCurrency(stats.totalExpenditures)}</div>
          </div>
          <button className="stat-menu">⋯</button>
        </div>
      </div>

      {/* Bottom Row: Table and Committee List */}
      <div className="bottom-row">
        {/* Latest Independent Expenditure Table */}
        <div className="table-card">
          <h3 className="table-title">Latest Independent Expenditure</h3>
          
          <table className="expenditure-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Committee</th>
                <th>Candidate</th>
                <th>Amount</th>
                <th>Support/Oppose</th>
              </tr>
            </thead>
            <tbody>
              {displayExpenditures.map((exp, index) => (
                <tr key={index}>
                  <td>{formatDate(exp.date || exp.filing_date)}</td>
                  <td>{exp.committee || exp.committee_name || 'N/A'}</td>
                  <td>{exp.candidate || exp.candidate_name || 'N/A'}</td>
                  <td>{formatCurrency(exp.amount || 0)}</td>
                  <td>
                    <span className={`badge ${(exp.support_oppose || '').toLowerCase().includes('support') ? 'badge-support' : 'badge-oppose'}`}>
                      {exp.support_oppose || 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="table-footer">
            <Link to="/expenditures" className="view-all-link">
              View All Independent Expenditure
            </Link>
          </div>
        </div>

        {/* Top 10 IE Committees */}
        <div className="committee-card">
          <h3 className="committee-title">Top 10 IE Committees by Spending</h3>
          <div className="committee-list">
            {displayCommittees.map((committee, index) => (
              <div key={index} className="committee-item">
                <div className="committee-icon"></div>
                <div className="committee-info">
                  <div className="committee-name">{committee.name || committee.committee_name || 'Committee'}</div>
                  <div className="committee-amount">{formatCurrency(committee.total_spending || committee.amount || 0)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
