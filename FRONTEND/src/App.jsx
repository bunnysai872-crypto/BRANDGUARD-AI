import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import CreatorDashboard from './pages/CreatorDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import BrandManagement from './pages/BrandManagement';
import GuidelinesPage from './pages/GuidelinesPage';
import CreateContent from './pages/CreateContent';
import MySubmissions from './pages/MySubmissions';
import SubmissionDetails from './pages/SubmissionDetails';
import ApprovalQueue from './pages/ApprovalQueue';
import PublishedContent from './pages/PublishedContent';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import NotFound from './pages/NotFound';
import ProtectedRoute from './components/ProtectedRoute';

// Root redirector based on authenticated role
const RootRedirect = () => {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role === 'admin') return <Navigate to="/manager-dashboard" replace />;
  return <Navigate to="/creator-dashboard" replace />;
};

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Role-based root redirect */}
      <Route path="/" element={<RootRedirect />} />

      {/* Dashboards */}
      <Route
        path="/creator-dashboard"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <CreatorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager-dashboard"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <ManagerDashboard />
          </ProtectedRoute>
        }
      />

      {/* Brand Governance Routes (Manager) */}
      <Route
        path="/manager/brands"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <BrandManagement />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager/guidelines"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <GuidelinesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager/approvals"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <ApprovalQueue />
          </ProtectedRoute>
        }
      />

      {/* Content & Guidelines Routes (Creator & Manager) */}
      <Route
        path="/creator/guidelines"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <GuidelinesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/creator/submissions/new"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <CreateContent />
          </ProtectedRoute>
        }
      />
      <Route
        path="/creator/submissions"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <MySubmissions />
          </ProtectedRoute>
        }
      />
      <Route
        path="/submissions/:id"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <SubmissionDetails />
          </ProtectedRoute>
        }
      />
      <Route
        path="/published-content"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <PublishedContent />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute allowedRoles={['creator', 'admin']}>
            <AnalyticsDashboard />
          </ProtectedRoute>
        }
      />

      {/* Catch-all 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
