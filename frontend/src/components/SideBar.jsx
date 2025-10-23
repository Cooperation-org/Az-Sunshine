import { Link } from 'react-router-dom'
import { Squares2X2Icon, UserGroupIcon, BanknotesIcon, UsersIcon, ChartBarIcon } from '@heroicons/react/24/outline'

import React from 'react'

function SideBar() {
  return (
    
        <nav className="sidebar-nav">
          <Link to="/" className={location.pathname === '/' ? 'nav-item active' : 'nav-item'} title="Dashboard">
            <Squares2X2Icon className="w-3 h-3" />
          </Link>

          <Link to="/candidates" className={location.pathname === '/candidates' ? 'nav-item active' : 'nav-item'} title="Candidates">
            <UserGroupIcon className="w-3 h-3" />
          </Link>

          <Link to="/expenditures" className={location.pathname === '/expenditures' ? 'nav-item active' : 'nav-item'} title="Expenditures">
            <BanknotesIcon className="w-3 h-3" />
          </Link>

        

          <Link to="/reports" className={location.pathname === '/donors' ? 'nav-item active' : 'nav-item'} title="Reports">
            <ChartBarIcon className="w-3 h-3" />
          </Link>
        </nav>
  )
}

export default SideBar

