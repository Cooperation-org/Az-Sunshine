import React from "react";
import { Routes, Route } from "react-router-dom";
import { DarkModeProvider } from "./context/DarkModeContext";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { useSecurityProtection } from "./hooks/useSecurityProtection";

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
// PrimaryRaceView removed - consolidated into RaceAnalysis
import EmailCampaign from "./pages/EmailCampaign";
import DataValidation from "./pages/DataValidation";
import WorkflowAutomation from "./pages/WorkflowAutomation";
import Visualizations from "./pages/Visualizations";
import DataVerification from "./pages/DataVerification";
import DataImport from "./pages/DataImport";
import ScraperControl from "./pages/ScraperControl";
import SOSAutomation from "./pages/SOSAutomation";
import SeeTheMoney from "./pages/SeeTheMoney";
import ReportAdBuy from "./pages/ReportAdBuy";
import AdBuyReview from "./pages/AdBuyReview";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

export default function App() {
  // Apply security protection (right-click, DevTools, etc.)
  useSecurityProtection();

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
          <Route path="/donors" element={<Donors />} />
          <Route path="/expenditures" element={<Expenditures />} />
          <Route path="/visualizations" element={<Visualizations />} />
          <Route path="/verification" element={<DataVerification />} />
          <Route path="/report-ad" element={<ReportAdBuy />} />

          {/* Admin-Only Routes - Require Login */}
          <Route path="/soi" element={<ProtectedRoute><SOIManagement /></ProtectedRoute>} />
          <Route path="/email-campaign" element={<ProtectedRoute><EmailCampaign /></ProtectedRoute>} />
          <Route path="/data-validation" element={<ProtectedRoute><DataValidation /></ProtectedRoute>} />
          <Route path="/workflow" element={<ProtectedRoute><WorkflowAutomation /></ProtectedRoute>} />
          <Route path="/staff/import" element={<ProtectedRoute><DataImport /></ProtectedRoute>} />
          <Route path="/staff/scrapers" element={<ProtectedRoute><ScraperControl /></ProtectedRoute>} />
          <Route path="/staff/sos" element={<ProtectedRoute><SOSAutomation /></ProtectedRoute>} />
          <Route path="/staff/seethemoney" element={<ProtectedRoute><SeeTheMoney /></ProtectedRoute>} />
          <Route path="/staff/ad-review" element={<ProtectedRoute><AdBuyReview /></ProtectedRoute>} />
          <Route path="/staff/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </DarkModeProvider>
  );
}