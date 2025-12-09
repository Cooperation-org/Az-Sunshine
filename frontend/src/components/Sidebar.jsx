import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutGrid,
  Users,
  DollarSign,
  FileText,
  Mail,
  BarChart3,
  CheckSquare,
  Database,
  GitBranch,
  Settings,
  HelpCircle,
  Moon,
  Sun,
  Workflow,
  Upload,
  Globe,
  Download,
  Eye,
  FileCheck,
  PanelLeftClose,
  PanelLeft,
  Bell,
  ChevronUp,
} from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

export default function Sidebar() {
  const location = useLocation();
  const { darkMode, toggleDarkMode } = useDarkMode();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: "/", icon: LayoutGrid, label: "Dashboard", badge: null },
    { path: "/candidates", icon: Users, label: "Candidates", badge: null },
    { path: "/donors", icon: DollarSign, label: "Donors", badge: null },
    { path: "/expenditures", icon: FileText, label: "Expenditures", badge: null },
    { path: "/soi", icon: CheckSquare, label: "SOI Tracking", badge: "New" },
    { path: "/email-campaign", icon: Mail, label: "Email Campaign", badge: null },
    { path: "/visualizations", icon: BarChart3, label: "Visualizations", badge: null },
    { path: "/race-analysis", icon: GitBranch, label: "Race Analysis", badge: null },
  ];

  const adminItems = [
    { path: "/admin/seethemoney", icon: Eye, label: "SeeTheMoney", badge: "FREE" },
    { path: "/admin/import", icon: Upload, label: "Data Import", badge: null },
    { path: "/admin/scrapers", icon: Globe, label: "County Scrapers", badge: null },
    { path: "/admin/sos", icon: FileCheck, label: "AZ SOS Automation", badge: null },
  ];

  return (
    <aside className={`${isCollapsed ? 'w-16' : 'w-64'} ${darkMode ? 'bg-[#332D54]' : 'bg-gradient-to-b from-[#685994] to-[#4c3e7c]'} flex flex-col h-screen sticky top-0 transition-all duration-300`}>
      {/* Logo and Toggle */}
      <div className={`p-4 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'pl-3'}`}>
          <img 
            src="/Arizona_logo.png" 
            alt="Arizona Sunshine" 
            className="w-8 h-8 object-contain"
          />
        </div>
        {!isCollapsed && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors"
          >
            <PanelLeftClose className="w-5 h-5" />
          </button>
        )}
      </div>

      {isCollapsed && (
        <div className="px-4 pb-4 flex justify-center">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors"
          >
            <PanelLeft className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);

            return (
              <div key={item.path} className="relative group">
                <Link
                  to={item.path}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                    ${active
                      ? 'bg-white/20 text-white font-medium shadow-lg'
                      : 'text-white/70 hover:bg-white/10 hover:text-white hover:shadow-md'
                    }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                >
                  <Icon className={`w-5 h-5 ${active ? 'text-white' : 'text-white/60'} flex-shrink-0`} />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1 text-sm">{item.label}</span>
                      {item.badge && (
                        <span className="px-2 py-0.5 bg-[#800080] text-white text-xs font-semibold rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </Link>
                {isCollapsed && (
                  <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity z-50">
                    {item.label}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Admin Tools Section */}
        <div className="mt-6 pt-6 border-t border-white/10">
          {!isCollapsed && (
            <h3 className="px-3 mb-2 text-xs font-semibold text-white/50 uppercase tracking-wider">
              Admin Tools
            </h3>
          )}
          <div className="space-y-1">
            {adminItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <div key={item.path} className="relative group">
                  <Link
                    to={item.path}
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                      ${active
                        ? 'bg-white/20 text-white font-medium shadow-lg'
                        : 'text-white/70 hover:bg-white/10 hover:text-white hover:shadow-md'
                      }
                      ${isCollapsed ? 'justify-center' : ''}
                    `}
                  >
                    <Icon className={`w-5 h-5 ${active ? 'text-white' : 'text-white/60'} flex-shrink-0`} />
                    {!isCollapsed && (
                      <>
                        <span className="flex-1 text-sm">{item.label}</span>
                        {item.badge && (
                          <span className="px-2 py-0.5 bg-[#800080] text-white text-xs font-semibold rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                  {isCollapsed && (
                    <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity z-50">
                      {item.label}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="relative p-4 border-t border-white/10">
        {/* Profile Menu Expandable - Overlay style */}
        {isProfileMenuOpen && !isCollapsed && (
          <div className="absolute bottom-full left-0 right-0 mb-2 mx-4 space-y-1 bg-black/40 backdrop-blur-md rounded-lg p-2 shadow-xl border border-white/10">
            {/* Notification */}
            <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm">
              <Bell className="w-5 h-5 flex-shrink-0" />
              <span>Notifications</span>
              <span className="ml-auto w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* Dark/Light Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
            >
              {darkMode ? <Sun className="w-5 h-5 flex-shrink-0" /> : <Moon className="w-5 h-5 flex-shrink-0" />}
              <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
            </button>

            {/* Settings */}
            <Link
              to="/settings"
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
            >
              <Settings className="w-5 h-5 flex-shrink-0" />
              <span>Settings</span>
            </Link>

            {/* Help Center */}
            <Link
              to="/help"
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
            >
              <HelpCircle className="w-5 h-5 flex-shrink-0" />
              <span>Help Center</span>
            </Link>
          </div>
        )}

        {/* User Profile Button */}
        <div className="relative">
          <button
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors group ${isCollapsed ? 'justify-center px-0' : ''}`}
          >
            <img
              src="https://ui-avatars.com/api/?name=Emos+Moka&background=8b5cf6&color=fff&bold=true"
              alt="Emos Moka"
              className="w-8 h-8 rounded-full flex-shrink-0"
            />
            {!isCollapsed && (
              <>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-white">Emos Moka</p>
                  <p className="text-xs text-white/60">Admin User</p>
                </div>
                <ChevronUp className={`w-4 h-4 transition-transform ${isProfileMenuOpen ? '' : 'rotate-180'}`} />
              </>
            )}
            
            {/* Tooltip for collapsed state */}
            {isCollapsed && (
              <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap transition-opacity z-50">
                Emos Moka
              </div>
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}