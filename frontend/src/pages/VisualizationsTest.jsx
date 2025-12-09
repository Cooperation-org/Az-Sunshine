// frontend/src/pages/VisualizationsTest.jsx
// MINIMAL TEST VERSION - No external dependencies
import React from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function VisualizationsTest() {
  return (
    <div className="flex h-screen bg-gradient-to-br from-[#1a1625] via-[#2d1b3d] to-[#1a1625] overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        
        
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-white mb-6">
              Visualizations Test
            </h1>
            
            <div className="bg-white rounded-lg p-6 shadow-lg">
              <h2 className="text-xl font-bold mb-4">Test Content</h2>
              <p className="text-gray-600">
                If you can see this, the basic page structure works.
              </p>
              <p className="text-gray-600 mt-2">
                Next step: Check browser console for errors (F12)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}