import React from "react";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import Donors from "./pages/Donors";
import Candidates from "./pages/Candidates";
import Expenditures from "./pages/Expenditures";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/donors" element={<Donors />} />
      <Route path="/candidates" element={<Candidates />} />
      <Route path="/expenditures" element={<Expenditures />} />
      <Route path="/candidate/:id" element={<CandidateDetail />} />
    </Routes>
  );
}
