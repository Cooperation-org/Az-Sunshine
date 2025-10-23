import { useState, useEffect } from 'react'
import axios from 'axios'
import './Expenditures.css'

function Expenditures() {
  const [expenditures, setExpenditures] = useState([])
  const [summary, setSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchExpenditures()
    fetchSummary()
  }, [])

  const fetchExpenditures = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/expenditures/')
      setExpenditures(response.data.results || response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load expenditures. Make sure the backend is running.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await axios.get('/api/expenditures/summary_by_race/')
      setSummary(response.data)
    } catch (err) {
      console.error('Failed to load summary:', err)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) {
    return <div className="loading">Loading expenditures...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="expenditures-page">
      <div className="page-header">
        <h1>Independent Expenditures</h1>
        <p>Track campaign spending and financial data</p>
      </div>

      {summary.length > 0 && (
        <div className="summary-section">
          <h2>Summary by Race</h2>
          <div className="summary-grid">
            {summary.map((item, index) => (
              <div key={index} className="summary-card">
                <div className="summary-race">{item.race || 'Unknown Race'}</div>
                <div className="summary-amount">{formatCurrency(item.total)}</div>
                <div className="summary-label">Total Spending</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {expenditures.length === 0 ? (
        <div className="empty-state">
          <p>No expenditures found. Add expenditure data through the admin panel.</p>
          <a href="http://localhost:8000/admin" className="btn btn-primary" target="_blank" rel="noopener noreferrer">
            Go to Admin
          </a>
        </div>
      ) : (
        <div className="expenditures-section">
          <h2>All Expenditures</h2>
          <div className="expenditures-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Donor</th>
                  <th>Candidate</th>
                  <th>Amount</th>
                  <th>Support/Oppose</th>
                </tr>
              </thead>
              <tbody>
                {expenditures.map((exp) => (
                  <tr key={exp.id}>
                    <td>{formatDate(exp.date)}</td>
                    <td>{exp.donor || 'N/A'}</td>
                    <td>{exp.candidate_name || exp.candidate || 'N/A'}</td>
                    <td className="amount">{formatCurrency(exp.amount)}</td>
                    <td>
                      <span className={`support-badge ${exp.support_oppose?.toLowerCase()}`}>
                        {exp.support_oppose || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default Expenditures

