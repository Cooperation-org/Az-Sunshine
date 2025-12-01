import React from "react";
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
} from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

export default function Sidebar() {
  const location = useLocation();
  const { darkMode, toggleDarkMode } = useDarkMode();

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
    { path: "/workflow", icon: Workflow, label: "Workflow Automation", badge: null },
    { path: "/data-validation", icon: Database, label: "Data Validation", badge: null },
  ];

  return (
    <aside className={`w-64 ${darkMode ? 'bg-[#332D54]' : 'bg-gradient-to-b from-[#685994] to-[#4c3e7c]'} flex flex-col h-screen sticky top-0`}>
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <img 
            src="/Arizona_logo.png" 
            alt="Arizona Sunshine" 
            className="w-12 h-12 object-contain"
          />
          <div>
            <h1 className="text-lg font-bold text-white">Arizona Sunshine</h1>
            <p className="text-xs text-white/70">Finance Transparency</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-hidden">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                  ${active 
                    ? 'bg-white/20 text-white font-medium shadow-lg' 
                    : 'text-white/70 hover:bg-white/10 hover:text-white hover:shadow-md'
                  }
                `}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-white' : 'text-white/60'}`} />
                <span className="flex-1 text-sm">{item.label}</span>
                {item.badge && (
                  <span className="px-2 py-0.5 bg-[#800080] text-white text-xs font-semibold rounded-full">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-white/10 space-y-2">
        <button
          onClick={toggleDarkMode}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        
        <Link
          to="/settings"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </Link>
        
        <Link
          to="/help"
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-colors text-sm"
        >
          <HelpCircle className="w-5 h-5" />
          <span>Help Center</span>
        </Link>
      </div>
    </aside>
  );
}