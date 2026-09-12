import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Shield, Smartphone, UserCheck, LogOut } from 'lucide-react';
import { SystemStatus, User } from '../../types';

interface NavbarProps {
  systemStatus?: SystemStatus | null;
  user?: User | null;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ systemStatus: _systemStatus, user, onLogout }) => {
  const location = useLocation();

  return (
    <header
      className="cc-header-zone"
      style={{
        height: '68px',
        background: 'rgba(2, 12, 28, 0.28)',
        backdropFilter: 'blur(20px) saturate(1.5)',
        WebkitBackdropFilter: 'blur(20px) saturate(1.5)',
        borderBottom: '1px solid rgba(56, 189, 248, 0.18)',
        boxShadow: '0 4px 30px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        boxSizing: 'border-box',
        position: 'relative',
        zIndex: 100,
      }}
    >
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexShrink: 0 }}>
        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none', whiteSpace: 'nowrap' }}>
          {/* Hexagonal Shield Logo */}
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.25), rgba(34, 211, 238, 0.15))',
              border: '1px solid rgba(34, 211, 238, 0.45)',
              boxShadow: '0 0 16px rgba(20, 184, 166, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>

          <div style={{ whiteSpace: 'nowrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '18px',
                  fontWeight: 800,
                  letterSpacing: '0.04em',
                  color: '#FFFFFF',
                  fontFamily: 'var(--font-sans)',
                  whiteSpace: 'nowrap',
                }}
              >
                FLOWSHIELD
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: '#22D3EE',
                  background: 'rgba(34, 211, 238, 0.12)',
                  border: '1px solid rgba(34, 211, 238, 0.35)',
                  padding: '1px 7px',
                  borderRadius: '4px',
                  letterSpacing: '0.05em',
                  whiteSpace: 'nowrap',
                }}
              >
                PS-26192
              </span>
            </div>
            <div
              style={{
                fontSize: '10.5px',
                fontWeight: 500,
                color: '#7F95A5',
                letterSpacing: '0.04em',
                lineHeight: 1.1,
                marginTop: '1px',
                whiteSpace: 'nowrap',
              }}
            >
              Himalayan Emergency Intelligence
            </div>
          </div>
        </Link>
      </div>

      {/* Centered Navigation Pills with 3D Tactile Effect and Ambient Background Light */}
      <nav className="nav-3d-rail" aria-label="Primary Navigation">
        <Link
          to="/dashboard"
          className={`nav-3d-pill ${location.pathname === '/dashboard' ? 'active' : ''}`}
        >
          <Home size={17} className="nav-3d-icon" />
          <span>Command Center</span>
        </Link>

        <Link
          to="/responder"
          className={`nav-3d-pill ${location.pathname === '/responder' ? 'active' : ''}`}
        >
          <Shield size={17} className="nav-3d-icon" />
          <span>Tactical Responder</span>
        </Link>

        <Link
          to="/citizen"
          className={`nav-3d-pill ${location.pathname === '/citizen' ? 'active' : ''}`}
        >
          <Smartphone size={17} className="nav-3d-icon" />
          <span>Citizen Mode</span>
        </Link>
      </nav>

      {/* Right Controls: Telemetry Capsule, India Flag, Auth */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexShrink: 0, whiteSpace: 'nowrap' }}>


        {/* Flag of India */}
        <div
          title="Republic of India — NDMA & State EOC Feed"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '20px',
            borderRadius: '3px',
            overflow: 'hidden',
            boxShadow: '0 1px 4px rgba(0,0,0,0.4)',
            border: '1px solid rgba(255,255,255,0.15)',
            fontSize: '16px',
            lineHeight: 1,
            cursor: 'default',
          }}
        >
          🇮🇳
        </div>

        {/* Auth / Profile Trigger */}
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '12px',
                color: '#C5D4DF',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: 'rgba(20, 184, 166, 0.12)',
                border: '1px solid rgba(20, 184, 166, 0.3)',
                padding: '4px 10px',
                borderRadius: '6px',
              }}
            >
              <UserCheck size={13} color="#22D3EE" />
              {user.username} ({user.role})
            </span>
            <button
              onClick={onLogout}
              style={{
                background: 'transparent',
                border: '1px solid rgba(61, 139, 180, 0.3)',
                borderRadius: '6px',
                color: '#7F95A5',
                padding: '5px 8px',
                cursor: 'pointer',
              }}
              title="Logout"
            >
              <LogOut size={13} />
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(17, 38, 58, 0.50)',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
              border: '1px solid rgba(56, 189, 248, 0.30)',
              boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 2px 10px rgba(0, 0, 0, 0.2)',
              color: '#F1F7FA',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '12.5px',
              fontWeight: 600,
              textDecoration: 'none',
              transition: 'all 0.15s ease',
            }}
          >
            Authority Login
          </Link>
        )}
      </div>
    </header>
  );
};
