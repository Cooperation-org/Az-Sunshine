import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutGrid, Users, DollarSign, FileText, Mail,
  BarChart3, CheckSquare, GitBranch, Settings,
  HelpCircle, Moon, Sun, Upload, Globe,
  FileCheck, PanelLeftClose, PanelLeft, Bell,
  ChevronUp, Eye, Megaphone, ShieldCheck, Database,
  Menu, X, LogOut, LogIn, Target, CheckCircle
} from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { darkMode, toggleDarkMode } = useDarkMode();
  const { user, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const profileMenuRef = useRef(null);

  const isActive = (path) => location.pathname === path;

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

  // Close profile menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false);
      }
    }

    if (isProfileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isProfileMenuOpen]);

  // Public navigation items (visible to everyone)
  const navItems = [
    { path: "/", icon: LayoutGrid, label: "Dashboard", badge: null },
    { path: "/candidates", icon: Users, label: "Candidates", badge: null },
    { path: "/donors", icon: DollarSign, label: "Donors", badge: null },
    { path: "/expenditures", icon: FileText, label: "Expenditures", badge: null },
    { path: "/visualizations", icon: BarChart3, label: "Visualizations", badge: null },
    { path: "/race-analysis", icon: GitBranch, label: "Race Analysis", badge: null },
    { path: "/primary-race", icon: Target, label: "Race View", badge: "Demo" },
    { path: "/verification", icon: CheckCircle, label: "Data Verification", badge: null },
    { path: "/report-ad", icon: Megaphone, label: "Report Ad Buy", badge: null },
  ];

  // Admin-only items (only visible when logged in)
  const adminItems = [
    { path: "/soi", icon: CheckSquare, label: "SOI Tracking", badge: null },
    { path: "/email-campaign", icon: Mail, label: "Email Campaign", badge: null },
    { path: "/data-validation", icon: Database, label: "Data Validation", badge: null },
    { path: "/admin/seethemoney", icon: Eye, label: "SeeTheMoney", badge: "FREE" },
    { path: "/admin/import", icon: Upload, label: "Data Import", badge: null },
    { path: "/admin/scrapers", icon: Globe, label: "County Scrapers", badge: null },
    { path: "/admin/sos", icon: FileCheck, label: "AZ SOS Automation", badge: null },
    { path: "/admin/ad-review", icon: ShieldCheck, label: "Ad Buy Review", badge: null },
  ];

  const SidebarContent = ({ isMobile = false }) => (
    <>
      {/* Header / Logo */}
      <div className="h-20 flex items-center px-6 py-5 border-b border-white/5">
        <div className={`flex items-center gap-3.5 w-full ${isCollapsed && !isMobile ? 'justify-center' : ''}`}>
          <div className="shrink-0 flex items-center">
            <img
              src="/Arizona_logo.png"
              alt="AZ"
              className="w-8 h-8 object-contain opacity-95"
            />
          </div>
          {(!isCollapsed || isMobile) && (
            <div className="flex-1">
              <div className="text-white">
                <div className="text-base font-semibold">Arizona Sunshine</div>
                <div className="text-xs text-gray-300">Finance Transparency</div>
              </div>
            </div>
          )}
          {isMobile && (
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          )}
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-6 overflow-y-auto custom-scrollbar">
        <div className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  relative flex items-center gap-3 px-3 py-3.5 rounded-xl transition-all duration-200 group
                  ${active
                    ? 'bg-purple-500/10 text-white'
                    : 'text-white/80 hover:text-white hover:bg-white/5'}
                  ${isCollapsed && !isMobile ? 'justify-center' : ''}
                `}
              >
                {active && (
                  <div className="absolute left-0 w-1 h-8 rounded-r-full bg-[#7667C1]" />
                )}

                <Icon size={20} className={active ? 'text-white' : 'text-white/80 group-hover:text-white'} />

                {(!isCollapsed || isMobile) && (
                  <>
                    <span className="flex-1 text-sm font-medium">{item.label}</span>
                    {item.badge && (
                      <span className="px-2.5 py-1 text-[10px] font-bold uppercase rounded-full text-white bg-[#A21CAF]">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}

                {/* Tooltip for collapsed state on desktop */}
                {isCollapsed && !isMobile && (
                  <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
        </div>

        {/* Dark Mode Toggle - Show here if NOT logged in */}
        {!user && (
          <div className="mt-8 pt-6 border-t border-white/5">
            <div className="space-y-1.5">
              <button
                onClick={toggleDarkMode}
                className={`
                  relative flex items-center gap-3 px-3 py-3.5 rounded-xl transition-all duration-200 group w-full
                  text-white/80 hover:text-white hover:bg-white/5
                  ${isCollapsed && !isMobile ? 'justify-center' : ''}
                `}
              >
                {darkMode ? (
                  <Sun size={20} className="text-white" />
                ) : (
                  <Moon size={20} className="text-indigo-400" />
                )}

                {(!isCollapsed || isMobile) && (
                  <span className="flex-1 text-sm font-medium text-left">
                    {darkMode ? 'Light Mode' : 'Dark Mode'}
                  </span>
                )}

                {isCollapsed && !isMobile && (
                  <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                    {darkMode ? 'Light Mode' : 'Dark Mode'}
                  </div>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Admin Section - Only visible when logged in */}
        {user && adminItems.length > 0 && (
          <div className="mt-10 pt-6 border-t border-white/5">
            {(!isCollapsed || isMobile) && (
              <p className="px-4 mb-5 text-[11px] font-bold uppercase tracking-widest text-white/60">
                Admin Suite
              </p>
            )}
            <div className="space-y-1.5">
              {adminItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`
                      relative flex items-center gap-3 px-3 py-3.5 rounded-xl transition-all duration-200 group
                      ${active
                        ? 'bg-purple-500/10 text-white'
                        : 'text-white/80 hover:text-white hover:bg-white/5'}
                      ${isCollapsed && !isMobile ? 'justify-center' : ''}
                    `}
                  >
                    {active && (
                      <div className="absolute left-0 w-1 h-8 rounded-r-full bg-[#7667C1]" />
                    )}

                    <Icon size={20} className={active ? 'text-white' : 'text-white/80 group-hover:text-white'} />
                    {(!isCollapsed || isMobile) && (
                      <>
                        <span className="flex-1 text-sm font-medium">{item.label}</span>
                        {item.badge && (
                          <span className="px-2.5 py-1 text-[10px] font-bold uppercase rounded-full text-white bg-[#A21CAF]">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                    {isCollapsed && !isMobile && (
                      <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                        {item.label}
                      </div>
                    )}
                  </Link>
                );
              })}

              {/* Dark Mode Toggle - Show here BELOW admin links when logged in */}
              <button
                onClick={toggleDarkMode}
                className={`
                  relative flex items-center gap-3 px-3 py-3.5 rounded-xl transition-all duration-200 group w-full
                  text-white/80 hover:text-white hover:bg-white/5
                  ${isCollapsed && !isMobile ? 'justify-center' : ''}
                `}
              >
                {darkMode ? (
                  <Sun size={20} className="text-white" />
                ) : (
                  <Moon size={20} className="text-indigo-400" />
                )}

                {(!isCollapsed || isMobile) && (
                  <span className="flex-1 text-sm font-medium text-left">
                    {darkMode ? 'Light Mode' : 'Dark Mode'}
                  </span>
                )}

                {isCollapsed && !isMobile && (
                  <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                    {darkMode ? 'Light Mode' : 'Dark Mode'}
                  </div>
                )}
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Bottom Profile Section / Login Button */}
      <div className="p-4 border-t border-white/5">
        {user ? (
          // Logged in - Show profile
          <div className="relative" ref={profileMenuRef}>
            {isProfileMenuOpen && (!isCollapsed || isMobile) && (
              <div className="absolute bottom-full left-0 right-0 mb-2 p-2 rounded-2xl shadow-2xl animate-in slide-in-from-bottom-2 border bg-[#2D2844] border-white/10">
                <Link to="/settings" className="w-full flex items-center gap-3 p-2 rounded-lg text-xs font-medium transition-colors text-gray-300 hover:bg-white/5">
                  <Settings size={14} /> Settings
                </Link>
                <button onClick={handleLogout} className="w-full flex items-center gap-3 p-2 rounded-lg text-xs font-medium transition-colors text-red-400 hover:bg-red-500/10">
                  <LogOut size={14} /> Logout
                </button>
              </div>
            )}

            <button
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              className={`flex items-center gap-3 w-full p-3 rounded-2xl transition-colors group ${isCollapsed && !isMobile ? 'justify-center' : ''} hover:bg-white/5`}
            >
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-[#7163BA] flex items-center justify-center text-white font-bold text-sm">
                  {user?.username?.substring(0, 2).toUpperCase() || 'AD'}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 border-2 rounded-full bg-emerald-500 border-[#1C1829]" />
              </div>
              {(!isCollapsed || isMobile) && (
                <div className="flex-1 text-left overflow-hidden">
                  <p className="text-sm font-bold truncate text-white">{user?.username || 'Admin'}</p>
                  <p className="text-[10px] font-medium truncate text-gray-400 uppercase">Admin Session</p>
                </div>
              )}
              {isCollapsed && !isMobile && (
                <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                  User Profile
                </div>
              )}
            </button>
          </div>
        ) : (
          // Not logged in - Show login button
          <Link
            to="/login"
            className={`flex items-center justify-center gap-3 w-full p-4 rounded-2xl transition-all bg-[#7163BA] hover:bg-[#5b4fa8] shadow-lg shadow-purple-500/20 group relative`}
          >
            <LogIn size={20} className="text-white" />
            {(!isCollapsed || isMobile) && (
              <span className="text-sm font-bold text-white">Admin Login</span>
            )}
            {isCollapsed && !isMobile && (
              <div className="absolute left-16 px-3 py-1.5 bg-gray-900 text-white text-[11px] font-medium rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-all transform group-hover:translate-x-1 shadow-xl border border-white/10">
                Admin Login
              </div>
            )}
          </Link>
        )}
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(true)}
        className="lg:hidden fixed top-4 right-4 z-50 p-2.5 text-white rounded-xl shadow-lg border border-white/10 transition-all"
        style={darkMode ? { backgroundColor: '#292438' } : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }}
        aria-label="Open menu"
      >
        <Menu size={22} />
      </button>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`
          lg:hidden fixed inset-y-0 left-0 z-[70] w-80
          transform transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          flex flex-col
        `}
        style={darkMode ? { backgroundColor: '#292438' } : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }}
      >
        <SidebarContent isMobile={true} />
      </aside>

      {/* Desktop Sidebar */}
      <aside
        className={`
          hidden lg:flex
          ${isCollapsed ? 'w-20' : 'w-64'}
          border-white/5
          flex-col h-screen sticky top-0 transition-all duration-300 border-r z-50
        `}
        style={darkMode ? { backgroundColor: '#292438' } : { background: 'linear-gradient(to bottom, #685994, #4c3e7c)' }}
      >
        {/* Desktop Navigation Toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-20 text-white p-1 rounded-full border-2 hover:scale-110 transition-transform shadow-xl z-50 bg-[#7163BA] border-[#14111D]"
        >
          {isCollapsed ? <PanelLeft size={14} /> : <PanelLeftClose size={14} />}
        </button>

        <SidebarContent isMobile={false} />
      </aside>
    </>
  );
}
