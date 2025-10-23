import { useState, useEffect } from 'react'
import axios from 'axios'
import './Candidates.css'

function Candidates() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCandidates()
  }, [])

  const fetchCandidates = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/candidates/')
      setCandidates(response.data.results || response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load candidates. Make sure the backend is running.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const markAsContacted = async (candidateId) => {
    try {
      await axios.post(`/api/candidates/${candidateId}/mark_contacted/`)
      fetchCandidates()
    } catch (err) {
      console.error('Failed to mark as contacted:', err)
    }
  }

  if (loading) {
    return <div className="loading">Loading candidates...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="candidates-page">
      <div className="page-header">
        <h1>Candidates</h1>
        <p>Browse all candidates and their campaign information</p>
      </div>

      {candidates.length === 0 ? (
        <div className="empty-state">
          <p>No candidates found. Add candidates through the admin panel.</p>
          <a href="http://localhost:8000/admin" className="btn btn-primary" target="_blank" rel="noopener noreferrer">
            Go to Admin
          </a>
        </div>
      ) : (
        <div className="candidates-grid">
          {candidates.map((candidate) => (
            <div key={candidate.id} className="candidate-card">
              <div className="candidate-header">
                <h3>{candidate.name}</h3>
                {candidate.party && (
                  <span className={`party-badge ${candidate.party.toLowerCase()}`}>
                    {candidate.party}
                  </span>
                )}
              </div>
              
              {candidate.race && (
                <div className="candidate-info">
                  <strong>Race:</strong> {candidate.race}
                </div>
              )}
              
              {candidate.committee_name && (
                <div className="candidate-info">
                  <strong>Committee:</strong> {candidate.committee_name}
                </div>
              )}
              
              {candidate.contact_info && (
                <div className="candidate-info">
                  <strong>Contact:</strong> {candidate.contact_info}
                </div>
              )}

              <button 
                className="btn-contact"
                onClick={() => markAsContacted(candidate.id)}
              >
                Mark as Contacted
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Candidates

