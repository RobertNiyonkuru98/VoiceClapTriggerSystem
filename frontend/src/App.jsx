import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import axios from 'axios';

import Login from './pages/Login';
import Signup from './pages/Signup';
import HouseholdSignup from './pages/HouseholdSignup';

// Admin Imports
import AdminLayout from './pages/admin/AdminLayout';
import Overview from './pages/admin/Overview';
import AlertLogs from './pages/admin/AlertLogs';
import Households from './pages/admin/Households';
import Settings from './pages/admin/Settings';
import SystemLogs from './pages/admin/SystemLogs';

// Responder Imports
import ResponderLayout from './pages/responder/ResponderLayout';
import LiveFeed from './pages/responder/LiveFeed';
import IncidentHistory from './pages/responder/IncidentHistory';
import ResponderProfile from './pages/responder/ResponderProfile';

// Configure Axios — VITE_API_URL is set per-environment (.env / Vercel dashboard)
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get('/api/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return <div className="flex-center" style={{ height: '100vh', fontFamily: 'Outfit' }}>Loading Security Context...</div>;

  // Role-based route guard
  const ProtectedRoute = ({ children, allowedRoles }) => {
    if (!user) return <Navigate to="/login" replace />;
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      return <Navigate to="/" replace />;
    }
    return children;
  };

  const getDashboardRoute = () => {
    if (!user) return '/login';
    if (user.role === 'admin') return '/admin';
    return '/responder';
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Navigate to={getDashboardRoute()} replace />} />
        <Route path="/login" element={user ? <Navigate to={getDashboardRoute()} replace /> : <Login setUser={setUser} />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/signup/household" element={<HouseholdSignup />} />

        {/* Administrator Portal */}
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminLayout user={user} setUser={setUser} />
            </ProtectedRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="logs" element={<AlertLogs />} />
          <Route path="households" element={<Households />} />
          <Route path="settings" element={<Settings />} />
          <Route path="system-logs" element={<SystemLogs />} />
        </Route>

        {/* Responder Portal */}
        <Route 
          path="/responder" 
          element={
            <ProtectedRoute allowedRoles={['health_responder', 'fire_responder', 'police_responder']}>
              <ResponderLayout user={user} setUser={setUser} />
            </ProtectedRoute>
          }
        >
          <Route index element={<LiveFeed user={user} />} />
          <Route path="history" element={<IncidentHistory user={user} />} />
          <Route path="profile" element={<ResponderProfile user={user} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
