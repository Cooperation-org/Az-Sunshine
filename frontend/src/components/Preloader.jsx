/**
 * ============================================================================
 * PRELOADER COMPONENT
 * ============================================================================
 * 
 * Full-screen pre-loader component extracted from SOI Management page.
 * This component displays a loading spinner with a message while page data is being fetched.
 * 
 * Usage:
 *   <Preloader message="Loading data..." />
 * 
 * Props:
 *   - message (string): Optional loading message. Default: "Loading..."
 */

import React from "react";
import { Loader } from "lucide-react";

export default function Preloader({ message = "Loading..." }) {
  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        {/* Spinning loader icon - matches SOI page exactly */}
        <Loader className="w-12 h-12 animate-spin text-purple-600 mx-auto mb-4" />
        {/* Loading message */}
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
}

