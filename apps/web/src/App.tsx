import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SystemStatus, User } from './types';
import { api } from './services/api';
import { Navbar } from './components/common/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResponderPage } from './pages/ResponderPage';
import { CitizenPage } from './pages/CitizenPage';
import { AboutPage } from './pages/AboutPage';
import { LoginPage } from './pages/LoginPage';

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
    const interval = setInterval(fetchStatus, 8000);

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
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/responder" element={<ResponderPage />} />
            <Route path="/citizen" element={<CitizenPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/login" element={<LoginPage onLoginSuccess={setUser} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
