import React from "react";
import { Routes, Route } from "react-router-dom";
import { DarkModeProvider } from "./context/DarkModeContext";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import Donors from "./pages/Donors";
import Candidates from "./pages/Candidates";
import Expenditures from "./pages/Expenditures";
import SOIManagement from "./pages/SOIManagement";
import RaceAnalysis from "./pages/RaceAnalysis";
import EmailCampaign from "./pages/EmailCampaign";
import DataValidation from "./pages/DataValidation";
import WorkflowAutomation from "./pages/WorkflowAutomation";
import Visualizations from "./pages/Visualizations";

export default function App() {
  return (
    <DarkModeProvider>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/soi" element={<SOIManagement />} />
        <Route path="/candidates" element={<Candidates />} />
        <Route path="/candidate/:id" element={<CandidateDetail />} />
        <Route path="/race-analysis" element={<RaceAnalysis />} />
        <Route path="/donors" element={<Donors />} />
        <Route path="/expenditures" element={<Expenditures />} />
        <Route path="/email-campaign" element={<EmailCampaign />} />
        <Route path="/data-validation" element={<DataValidation />} />
        <Route path="/workflow" element={<WorkflowAutomation />} />
        <Route path="/visualizations" element={<Visualizations />} />
      </Routes>
    </DarkModeProvider>
  );
}