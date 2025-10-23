import { MagnifyingGlassIcon, BellIcon } from '@heroicons/react/24/outline' 
import React from 'react'
import { useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()
  const getPageTitle = () => {
  switch(location.pathname) {
    case '/': return 'Dashboard'
    case '/donors': return 'Donor Entities'
    case '/candidates': return 'Candidates'
    case '/expenditures': return 'Expenditures'
    default: return 'Arizona Sunshine'
  }
}
  return (
    <div>  
      {/* Page Content */}
      <header className="top-header">
          <div className="header-left">
            <h1 className="page-title">Arizona Sunshine</h1>
            <p className="page-subtitle">{getPageTitle()}</p>
          </div>
          <div className="header-right">
            <div className="search-box">
              <MagnifyingGlassIcon className="icons" />
              <input type="text" placeholder="Search" />
            </div>
            <button className="notification-btn">
              <BellIcon className="w-3 h-3" />
            </button>
          </div>
        </header>
    </div> 
  )
}

export default Header