import React from "react";
import { Bell, Search } from "lucide-react";

export default function Header({ title, subtitle }) {
  return (
    <header className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-3 sm:py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 sticky top-0 z-10">
      {/* Title Section - Responsive: Full width on mobile, auto on desktop */}
      <div className="w-full sm:w-auto">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{title || "Arizona Sunshine"}</h1>
        <p className="text-xs sm:text-sm text-gray-500">{subtitle || "Dashboard"}</p>
      </div>
      
      {/* Search and Actions - Responsive: Full width on mobile, auto on desktop */}
      <div className="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
        <div className="relative flex-1 sm:flex-initial">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search"
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full sm:w-64 lg:w-80 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm sm:text-base"
          />
        </div>
        <button className="p-2 rounded-lg bg-gradient-to-b from-[#6B5B95] to-[#4C3D7D] transition flex-shrink-0">
          <Bell className="w-5 h-5 text-white" />
        </button>
      </div>
    </header>
  );
}

