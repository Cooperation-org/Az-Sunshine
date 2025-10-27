import { Link, useLocation } from 'react-router-dom'
import { LayoutGrid, Users, DollarSign, FileText, BarChart3, LogOut } from 'lucide-react'
import React from 'react'

function SideBar() {
  const location = useLocation()

  return (
    <aside className="w-20 rounded-3xl bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] flex flex-col items-center py-8 fixed h-full z-20">
      <div className="flex flex-col items-center space-y-8 flex-1">
        <div className=" rounded-xl p-1 mb-1">
          <svg width="49" height="49" viewBox="0 0 49 49" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M28.5832 38.7501C28.5832 37.6671 28.153 36.6285 27.3872 35.8627C26.6214 35.097 25.5828 34.6667 24.4998 34.6667C23.4169 34.6667 22.3783 35.097 21.6125 35.8627C20.8467 36.6285 20.4165 37.6671 20.4165 38.7501" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M38.7918 24.4582L34.4839 10.8668C34.2953 10.324 33.9943 9.82716 33.6006 9.40867C33.2068 8.99018 32.7291 8.65951 32.1988 8.43829C31.6685 8.21706 31.0974 8.11025 30.523 8.12485C29.9485 8.13945 29.3837 8.27513 28.8652 8.52301L26.2601 9.76843C25.7105 10.0307 25.1092 10.1667 24.5002 10.1666H17.3543C16.4649 10.1664 15.5997 10.4566 14.8903 10.9932C14.1809 11.5298 13.6661 12.2833 13.4241 13.1392L10.2085 24.4582" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M4.0835 24.4583H44.9168" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M34.7085 44.875C38.0912 44.875 40.8335 42.1327 40.8335 38.75C40.8335 35.3673 38.0912 32.625 34.7085 32.625C31.3258 32.625 28.5835 35.3673 28.5835 38.75C28.5835 42.1327 31.3258 44.875 34.7085 44.875Z" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M14.2915 44.875C17.6742 44.875 20.4165 42.1327 20.4165 38.75C20.4165 35.3673 17.6742 32.625 14.2915 32.625C10.9088 32.625 8.1665 35.3673 8.1665 38.75C8.1665 42.1327 10.9088 44.875 14.2915 44.875Z" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
          </svg>

        </div>
        <hr className="w-1/2 border-white/20 p-1" />

        <nav className="flex flex-col items-center space-y-6">
          <Link to="/" className={location.pathname === '/' ? 'p-3 rounded-xl bg-white/20 transition' : 'p-3 rounded-xl hover:bg-white/10 transition'} title="Dashboard">
            <LayoutGrid className="w-6 h-6 text-white" />
          </Link>

          <Link to="/candidates" className={location.pathname === '/candidates' ? 'p-3 rounded-xl bg-white/20 transition' : 'p-3 rounded-xl hover:bg-white/10 transition'} title="Candidates">
            <Users className="w-6 h-6 text-white" />
          </Link>

          <Link to="/donors" className={location.pathname === '/donors' ? 'p-3 rounded-xl bg-white/20 transition' : 'p-3 rounded-xl hover:bg-white/10 transition'} title="Donors">
            <DollarSign className="w-6 h-6 text-white" />
          </Link>

          <Link to="/expenditures" className={location.pathname === '/expenditures' ? 'p-3 rounded-xl bg-white/20 transition' : 'p-3 rounded-xl hover:bg-white/10 transition'} title="Expenditures">
            <FileText className="w-6 h-6 text-white" />
          </Link>

          {/* <Link to="/reports" className={location.pathname === '/reports' ? 'p-3 rounded-xl bg-white/20 transition' : 'p-3 rounded-xl hover:bg-white/10 transition'} title="Reports">
            <BarChart3 className="w-6 h-6 text-white" />
          </Link> */}
        </nav>
      </div>

      {/* Logout button at the bottom */}
      <hr className="w-1/2 border-white/20 p-1 mb-2" />
      <button 
        onClick={() => console.log('Logout clicked')} 
        className="p-3 transition bg-white/20 rounded-xl"
        title="Logout"
      >
        <LogOut className="w-6 h-6 text-white" />
      </button>
    </aside>
  )
}

export default SideBar