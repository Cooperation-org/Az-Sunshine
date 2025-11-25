import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutGrid,
  Users,
  DollarSign,
  FileText,
  LogOut,
  CheckSquare,
  TrendingUp,
  Menu,
  X,
  Mail,
} from 'lucide-react';

function SideBar() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  // Close mobile menu when route changes
  React.useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  React.useEffect(() => {
    if (isMobileMenuOpen) {
      // Store original styles
      const originalOverflow = document.body.style.overflow;
      const originalPosition = document.body.style.position;
      const originalWidth = document.body.style.width;
      
      // Lock body scroll
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
      
      // Cleanup: Restore original styles when menu closes
      return () => {
        document.body.style.overflow = originalOverflow;
        document.body.style.position = originalPosition;
        document.body.style.width = originalWidth;
      };
    } else {
      // Restore scroll when menu is closed
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
    }
  }, [isMobileMenuOpen]);

  return (
    <>
      {/* Mobile Menu Button - Only visible on small screens */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="lg:hidden fixed top-4 left-4 z-30 p-2.5 bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] text-white rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile Overlay - Shows when menu is open */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-20"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - Responsive: Hidden on mobile, drawer on tablet, fixed on desktop */}
      <aside
        className={`
          fixed lg:static
          top-0 left-0
          w-64 lg:w-20
          h-100%
          rounded-none lg:rounded-3xl
          bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D]
          flex flex-col items-center
          py-8
          z-30
          transform transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
      <div className="flex flex-col items-center space-y-8 flex-1">
        {/* Logo */}
        <div className="rounded-xl p-1 mb-1">
          <svg
            width="49"
            height="49"
            viewBox="0 0 49 49"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M28.5832 38.7501C28.5832 37.6671 28.153 36.6285 27.3872 35.8627C26.6214 35.097 25.5828 34.6667 24.4998 34.6667C23.4169 34.6667 22.3783 35.097 21.6125 35.8627C20.8467 36.6285 20.4165 37.6671 20.4165 38.7501"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M38.7918 24.4582L34.4839 10.8668C34.2953 10.324 33.9943 9.82716 33.6006 9.40867C33.2068 8.99018 32.7291 8.65951 32.1988 8.43829C31.6685 8.21706 31.0974 8.11025 30.523 8.12485C29.9485 8.13945 29.3837 8.27513 28.8652 8.52301L26.2601 9.76843C25.7105 10.0307 25.1092 10.1667 24.5002 10.1666H17.3543C16.4649 10.1664 15.5997 10.4566 14.8903 10.9932C14.1809 11.5298 13.6661 12.2833 13.4241 13.1392L10.2085 24.4582"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M4.0835 24.4583H44.9168"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M34.7085 44.875C38.0912 44.875 40.8335 42.1327 40.8335 38.75C40.8335 35.3673 38.0912 32.625 34.7085 32.625C31.3258 32.625 28.5835 35.3673 28.5835 38.75C28.5835 42.1327 31.3258 44.875 34.7085 44.875Z"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M14.2915 44.875C17.6742 44.875 20.4165 42.1327 20.4165 38.75C20.4165 35.3673 17.6742 32.625 14.2915 32.625C10.9088 32.625 8.1665 35.3673 8.1665 38.75C8.1665 42.1327 10.9088 44.875 14.2915 44.875Z"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <hr className="w-1/2 border-white/20 p-1" />

        {/* Navigation - Responsive: Show labels on mobile/tablet, icons only on desktop */}
        <nav className="flex flex-col items-center lg:items-center space-y-6 w-full px-4 lg:px-0">
          <Link
            to="/"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Dashboard"
          >
            <LayoutGrid className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Dashboard</span>
          </Link>

          <Link
            to="/soi"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/soi')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="SOI Tracking"
          >
            <CheckSquare className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">SOI Tracking</span>
          </Link>

          <Link
            to="/email-campaign"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/email-campaign')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Email Campaign"
          >
            <Mail className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Email Campaign</span>
          </Link>

          <Link
            to="/candidates"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/candidates')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Candidates"
          >
            <Users className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Candidates</span>
          </Link>

          <Link
            to="/races"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/races')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Race Analysis"
          >
            <TrendingUp className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Race Analysis</span>
          </Link>

          <Link
            to="/donors"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/donors')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Donors"
          >
            <DollarSign className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Donors</span>
          </Link>

          <Link
            to="/expenditures"
            className={`w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 rounded-xl transition-all duration-200 ${
              isActive('/expenditures')
                ? 'bg-white/20 shadow-md'
                : 'hover:bg-white/10 hover:shadow-sm'
            }`}
            title="Expenditures"
          >
            <FileText className="w-6 h-6 text-white flex-shrink-0" />
            <span className="lg:hidden text-white font-medium">Expenditures</span>
          </Link>
        </nav>
      </div>

      <hr className="w-1/2 border-white/20 p-1 mb-2" />

      {/* Logout - Responsive: Show text on mobile/tablet */}
      <button
        onClick={() => console.log('Logout clicked')}
        className="w-full lg:w-auto flex items-center gap-3 lg:justify-center p-3 transition-all duration-200 bg-white/20 rounded-xl hover:bg-white/30 hover:shadow-md active:scale-95"
        title="Logout"
      >
        <LogOut className="w-6 h-6 text-white flex-shrink-0" />
        <span className="lg:hidden text-white font-medium">Logout</span>
      </button>
    </aside>
    </>
  );
}

export default SideBar;