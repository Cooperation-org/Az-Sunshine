import React, { useState } from "react";
import { Search, Bell, X } from "lucide-react";
import { useDarkMode } from "../context/DarkModeContext";

export default function Header() {
  const { darkMode } = useDarkMode();
  const [searchOpen, setSearchOpen] = useState(false);
  
  return (
    <header className={`${darkMode ? 'bg-[#4a4169]' : 'bg-white'} border-b ${darkMode ? 'border-[#5f5482]' : 'border-gray-200'} sticky top-0 z-40`}>
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Title */}
          <div>
            <h1 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>Arizona Sunshine</h1>
            <p className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Finance Transparency</p>
          </div>

          {/* Right Side - Search, Notification & Profile */}
          <div className="flex items-center gap-4">
            {/* Search - Expandable */}
            <div className="relative">
              <div
                className={`flex items-center overflow-hidden transition-all duration-300 ease-in-out ${
                  searchOpen ? 'w-80' : 'w-10'
                }`}
              >
                <input
                  type="text"
                  placeholder="Search campaigns, candidates..."
                  className={`w-full pl-4 pr-10 py-2 border ${
                    darkMode 
                      ? 'bg-[#5f5482] border-[#6d5f8d] text-white placeholder-gray-400' 
                      : 'bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-500'
                  } rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-opacity duration-300 ${
                    searchOpen ? 'opacity-100' : 'opacity-0'
                  }`}
                  style={{ pointerEvents: searchOpen ? 'auto' : 'none' }}
                />
                <button
                  onClick={() => setSearchOpen(!searchOpen)}
                  className={`absolute right-0 p-2 rounded-lg transition-colors ${
                    darkMode ? 'hover:bg-[#5f5482]' : 'hover:bg-gray-50'
                  }`}
                >
                  {searchOpen ? (
                    <X className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`} />
                  ) : (
                    <Search className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`} />
                  )}
                </button>
              </div>
            </div>

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
                src="https://ui-avatars.com/api/?name=Emos+Moka&background=8b5cf6&color=fff&bold=true"
                alt="Emos Moka"
                className="w-10 h-10 rounded-full"
              />
              <div className="text-right">
                <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>Emos Moka</p>
                <p className={`text-xs ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>Admin User</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}