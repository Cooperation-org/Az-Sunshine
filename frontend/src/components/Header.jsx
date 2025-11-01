import React from "react";
import { Bell, Search } from "lucide-react";

export default function Header({ title, subtitle }) {
  return (
    <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title || "Arizona Sunshine"}</h1>
        <p className="text-sm text-gray-500">{subtitle || "Dashboard"}</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search"
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-80 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <button className="p-2 rounded-lg bg-purple-600 hover:bg-purple-700 transition">
          <Bell className="w-5 h-5 text-white" />
        </button>
      </div>
    </header>
  );
}

