import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SystemStatus, User } from './types';
import { api } from './services/api';
import { Navbar } from './components/common/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';

import { ResponderPage } from './pages/ResponderPage';
import { CitizenPage } from './pages/CitizenPage';
const AboutPage = lazy(() => import('./pages/AboutPage').then(m => ({ default: m.AboutPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));

import './styles/tokens.css';
import './styles/reset.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/command-center.css';

export const App: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [user, setUser] = useState<User | null>(null);

  // Fetch system status & current authenticated user
  useEffect(() => {
    const fetchStatus = () => {
      api.getSystemStatus()
        .then(setSystemStatus)
        .catch((err) => console.warn('System status poll:', err));
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);

    if (api.getToken()) {
      api.getMe()
        .then(setUser)
        .catch(() => {
          api.logout();
          setUser(null);
        });
    }

    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <BrowserRouter>
      <div className="app-container">
        {/* Full-Viewport Photorealistic Himalayan 3D Mountain Backdrop */}
        <div className="himalayan-viewport-backdrop" />

        {/* Global Navigation Bar */}
        <Navbar
          systemStatus={systemStatus}
          user={user}
          onLogout={handleLogout}
        />

        {/* Dynamic Route View */}
        <main className="main-content">
          <Suspense
            fallback={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#38BDF8' }}>
                <div style={{ width: '32px', height: '32px', border: '3px solid rgba(56, 189, 248, 0.2)', borderTopColor: '#38BDF8', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/timeline" element={<DashboardPage initialTab="Timeline" />} />
              <Route path="/responder" element={<ResponderPage />} />
              <Route path="/citizen" element={<CitizenPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/login" element={<LoginPage onLoginSuccess={setUser} />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
