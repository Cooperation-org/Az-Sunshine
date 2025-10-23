import React from "react";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/candidate/:id" element={<CandidateDetail />} />
    </Routes>
  );
}
