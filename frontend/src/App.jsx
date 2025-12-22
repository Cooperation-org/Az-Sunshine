import React from "react";
import { Routes, Route } from "react-router-dom";
import { DarkModeProvider } from "./context/DarkModeContext";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

// Auth Pages
import Login from "./pages/Login";
import Register from "./pages/Register";

// Protected Pages
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";
import Donors from "./pages/Donors";
import Candidates from "./pages/Candidates";
import Expenditures from "./pages/Expenditures";
import SOIManagement from "./pages/SOIManagement";
import RaceAnalysis from "./pages/RaceAnalysis";
import PrimaryRaceView from "./pages/PrimaryRaceView";
import EmailCampaign from "./pages/EmailCampaign";
import DataValidation from "./pages/DataValidation";
import WorkflowAutomation from "./pages/WorkflowAutomation";
import Visualizations from "./pages/Visualizations";
import DataImport from "./pages/DataImport";
import ScraperControl from "./pages/ScraperControl";
import SOSAutomation from "./pages/SOSAutomation";
import SeeTheMoney from "./pages/SeeTheMoney";
import ReportAdBuy from "./pages/ReportAdBuy";
import AdBuyReview from "./pages/AdBuyReview";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <DarkModeProvider>
      <AuthProvider>
        <Routes>
          {/* Public Routes - No Login Required */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Dashboard />} />
          <Route path="/candidates" element={<Candidates />} />
          <Route path="/candidate/:id" element={<CandidateDetail />} />
          <Route path="/race-analysis" element={<RaceAnalysis />} />
          <Route path="/primary-race" element={<PrimaryRaceView />} />
          <Route path="/donors" element={<Donors />} />
          <Route path="/expenditures" element={<Expenditures />} />
          <Route path="/visualizations" element={<Visualizations />} />
          <Route path="/report-ad" element={<ReportAdBuy />} />

          {/* Admin-Only Routes - Require Login */}
          <Route path="/soi" element={<ProtectedRoute><SOIManagement /></ProtectedRoute>} />
          <Route path="/email-campaign" element={<ProtectedRoute><EmailCampaign /></ProtectedRoute>} />
          <Route path="/data-validation" element={<ProtectedRoute><DataValidation /></ProtectedRoute>} />
          <Route path="/workflow" element={<ProtectedRoute><WorkflowAutomation /></ProtectedRoute>} />
          <Route path="/admin/import" element={<ProtectedRoute><DataImport /></ProtectedRoute>} />
          <Route path="/admin/scrapers" element={<ProtectedRoute><ScraperControl /></ProtectedRoute>} />
          <Route path="/admin/sos" element={<ProtectedRoute><SOSAutomation /></ProtectedRoute>} />
          <Route path="/admin/seethemoney" element={<ProtectedRoute><SeeTheMoney /></ProtectedRoute>} />
          <Route path="/admin/ad-review" element={<ProtectedRoute><AdBuyReview /></ProtectedRoute>} />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </DarkModeProvider>
  );
}