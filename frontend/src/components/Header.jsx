import React from "react";
import { Search, Bell } from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

export default function Header() {
  const { darkMode } = useDarkMode();
  
  return (
    <header className={`${darkMode ? 'bg-[#4a4169]' : 'bg-white'} border-b ${darkMode ? 'border-[#5f5482]' : 'border-gray-200'} sticky top-0 z-40`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-xl">
            <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-400'}`} />
            <input
              type="text"
              placeholder="Search campaigns, candidates, etc..."
              className={`pl-10 pr-4 py-2.5 w-full border ${
                darkMode 
                  ? 'bg-[#5f5482] border-[#6d5f8d] text-white placeholder-gray-400' 
                  : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400'
              } rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
            />
          </div>

          {/* Right Side - Notification & Profile */}
          <div className="flex items-center gap-4 ml-6">
            {/* Notifications */}
            <button className={`relative p-2 rounded-lg transition-colors ${
              darkMode ? 'hover:bg-[#5f5482]' : 'hover:bg-gray-50'
            }`}>
              <Bell className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {/* User Profile */}
            <div className="flex items-center gap-3">
              <img
                src="https://ui-avatars.com/api/?name=Manik+Jinage&background=8b5cf6&color=fff&bold=true"
                alt="Manik Jinage"
                className="w-10 h-10 rounded-full"
              />
              <div className="text-right">
                <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>Manik Jinage</p>
                <p className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Admin User</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}