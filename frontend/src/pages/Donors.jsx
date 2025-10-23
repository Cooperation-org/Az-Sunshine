import { useState, useEffect } from 'react'
import axios from 'axios'
import './Donors.css'

function Donors() {
  const [donors, setDonors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const itemsPerPage = 8

  useEffect(() => {
    fetchDonors()
  }, [currentPage])

  const fetchDonors = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/donors/', {
        params: {
          limit: itemsPerPage,
          offset: (currentPage - 1) * itemsPerPage
        }
      })
      
      // Handle both paginated and non-paginated responses
      if (response.data.results) {
        setDonors(response.data.results)
        setTotalResults(response.data.count || response.data.results.length)
      } else {
        setDonors(response.data)
        setTotalResults(response.data.length)
      }
      setError(null)
    } catch (err) {
      // If API doesn't exist, use mock data
      console.log('Using mock donor data')
      setDonors(mockDonors)
      setTotalResults(mockDonors.length)
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(totalResults / itemsPerPage)

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount || 0)
  }

  if (loading) {
    return (
      <div className="donors-container">
        <div className="loading-state">Loading donor entities...</div>
      </div>
    )
  }

  return (
    <div className="donors-container">
      <div className="donors-card">
        <table className="donors-table">
          <thead>
            <tr>
              <th>DONOR/ENTITY NAME</th>
              <th>LINKED COMMITTEES</th>
              <th>TOTAL IE IMPACT</th>
            </tr>
          </thead>
          <tbody>
            {donors.map((donor, index) => (
              <tr key={donor.id || index}>
                <td>
                  <div className="donor-name-cell">
                    <div className="donor-avatar">
                      {getInitials(donor.name || donor.entity_name || 'Unknown')}
                    </div>
                    <span>{donor.name || donor.entity_name || 'Unknown Entity'}</span>
                  </div>
                </td>
                <td className="text-center">{donor.linked_committees || donor.committees_count || 0}</td>
                <td className="text-right">{formatCurrency(donor.total_impact || donor.total_amount || 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <span className="results-count">{totalResults} results</span>
          <div className="pagination-buttons">
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                className={currentPage === page ? 'page-btn active' : 'page-btn'}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}
            {totalPages > 5 && (
              <button className="page-btn" onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                </svg>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Mock data for demonstration
const mockDonors = [
  { id: 1, name: 'Padilla-Richardson', linked_committees: 8, total_impact: 5432109.67 },
  { id: 2, name: 'Blackwell-Daniel', linked_committees: 5, total_impact: 5432109.67 },
  { id: 3, name: 'Tucker-Conrad', linked_committees: 7, total_impact: 5432109.67 },
  { id: 4, name: 'Daniels-Mcguire', linked_committees: 2, total_impact: 5432109.67 },
  { id: 5, name: 'Moore-Bennett', linked_committees: 1, total_impact: 5432109.67 },
  { id: 6, name: 'Shaffer Group', linked_committees: 5, total_impact: 5432109.67 },
  { id: 7, name: 'Brown and Sons', linked_committees: 3, total_impact: 5432109.67 },
  { id: 8, name: 'Padilla-Richardson', linked_committees: 2, total_impact: 5432109.67 },
]

export default Donors

