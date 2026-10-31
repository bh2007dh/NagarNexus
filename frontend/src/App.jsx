import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import AuthPage from './pages/AuthPage';
import OverviewDashboard from './pages/OverviewDashboard';
import LocationIntelligence from './pages/LocationIntelligence';
import DatasetExplorer from './pages/DatasetExplorer';
import DataCleaning from './pages/DataCleaning';
import ExploratoryDataAnalysis from './pages/ExploratoryDataAnalysis';
import StatisticalAnalysis from './pages/StatisticalAnalysis';
import MachineLearningLab from './pages/MachineLearningLab';
import PredictiveAnalytics from './pages/PredictiveAnalytics';
import RiskDetection from './pages/RiskDetection';
import LocationComparison from './pages/LocationComparison';
import AIInsights from './pages/AIInsights';
import ReportCenter from './pages/ReportCenter';
import UserProfile from './pages/UserProfile';
import SettingsPage from './pages/SettingsPage';
import { LoadingSkeleton } from './components/LoadingSkeleton';

export const ProtectedRoute = ({ children }) => {
  const { user, token, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-[#060b19] p-10">
        <LoadingSkeleton rows={4} label="Verifying session token..." />
      </div>
    );
  }
  if (!token || !user) {
    return <Navigate to="/auth" replace />;
  }
  return <DashboardLayout>{children}</DashboardLayout>;
};

export const AppRoutes = () => (
  <Routes>
    <Route path="/auth" element={<AuthPage />} />
    <Route path="/" element={<ProtectedRoute><OverviewDashboard /></ProtectedRoute>} />
    <Route path="/locations" element={<ProtectedRoute><LocationIntelligence /></ProtectedRoute>} />
    <Route path="/datasets" element={<ProtectedRoute><DatasetExplorer /></ProtectedRoute>} />
    <Route path="/cleaning" element={<ProtectedRoute><DataCleaning /></ProtectedRoute>} />
    <Route path="/eda" element={<ProtectedRoute><ExploratoryDataAnalysis /></ProtectedRoute>} />
    <Route path="/statistics" element={<ProtectedRoute><StatisticalAnalysis /></ProtectedRoute>} />
    <Route path="/ml-lab" element={<ProtectedRoute><MachineLearningLab /></ProtectedRoute>} />
    <Route path="/predictions" element={<ProtectedRoute><PredictiveAnalytics /></ProtectedRoute>} />
    <Route path="/risk" element={<ProtectedRoute><RiskDetection /></ProtectedRoute>} />
    <Route path="/comparison" element={<ProtectedRoute><LocationComparison /></ProtectedRoute>} />
    <Route path="/insights" element={<ProtectedRoute><AIInsights /></ProtectedRoute>} />
    <Route path="/reports" element={<ProtectedRoute><ReportCenter /></ProtectedRoute>} />
    <Route path="/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
    <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

const App = () => (
  <AuthProvider>
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  </AuthProvider>
);

export default App;

