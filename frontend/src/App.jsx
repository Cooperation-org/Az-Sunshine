import React from "react";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import Donors from "./pages/Donors";
import Candidates from "./pages/Candidates";
import Expenditures from "./pages/Expenditures";
import SOIManagement from "./pages/SOIManagement";
import RaceAnalysis from "./pages/RaceAnalysis";
import EmailCampaign from "./pages/EmailCampaign";
import DataValidation from "./pages/DataValidation";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/soi" element={<SOIManagement />} />
      <Route path="/candidates" element={<Candidates />} />
      <Route path="/candidate/:id" element={<CandidateDetail />} />
      <Route path="/races" element={<RaceAnalysis />} />
      <Route path="/donors" element={<Donors />} />
      <Route path="/expenditures" element={<Expenditures />} />
      <Route path="/email-campaign" element={<EmailCampaign />} />
      <Route path="/data-validation" element={<DataValidation />} />
    </Routes>
  );
}