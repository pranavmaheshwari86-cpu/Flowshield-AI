import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { ShieldAlert, Lock, User as UserIcon, LogIn, Key } from 'lucide-react';
import { User } from '../types';

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState<string>('demo');
  const [password, setPassword] = useState<string>('flowshield2026');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tokenData = await api.login(username, password);
      onLoginSuccess(tokenData.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoAccess = async () => {
    setUsername('demo');
    setPassword('flowshield2026');
    setLoading(true);
    try {
      const tokenData = await api.login('demo', 'flowshield2026');
      onLoginSuccess(tokenData.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
      <div className="card" style={{ maxWidth: '420px', width: '100%', padding: '32px 28px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              margin: '0 auto 12px auto',
              boxShadow: '0 0 16px rgba(6,182,212,0.4)'
            }}
          >
            <ShieldAlert size={26} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff' }}>
            Authority Command Portal
          </h2>
          <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
            Restricted access for District EOC & Disaster Management Officers
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: '10px 12px',
              background: 'rgba(239,68,68,0.15)',
              border: '1px solid #ef4444',
              borderRadius: '6px',
              color: '#f87171',
              fontSize: '12px',
              marginBottom: '16px'
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              OFFICER USERNAME
            </label>
            <div style={{ position: 'relative' }}>
              <UserIcon size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '12px' }} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px 10px 10px 32px',
                  background: '#162a4d',
                  color: '#f1f5f9',
                  border: '1px solid #2a4778',
                  borderRadius: '6px',
                  fontSize: '13px'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              SECRET ACCESS KEY
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '12px' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '10px 10px 10px 32px',
                  background: '#162a4d',
                  color: '#f1f5f9',
                  border: '1px solid #2a4778',
                  borderRadius: '6px',
                  fontSize: '13px'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '6px', padding: '10px' }}
          >
            <LogIn size={15} />
            {loading ? 'Authenticating...' : 'Sign In as Officer'}
          </button>
        </form>

        <div style={{ margin: '20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ flex: 1, height: '1px', background: '#1e355b' }} />
          <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase' }}>Hackathon Evaluator</span>
          <div style={{ flex: 1, height: '1px', background: '#1e355b' }} />
        </div>

        <button
          onClick={handleQuickDemoAccess}
          disabled={loading}
          className="btn btn-secondary"
          style={{ width: '100%', padding: '10px', border: '1px solid #06b6d4', color: '#38bdf8' }}
        >
          <Key size={15} color="#06b6d4" />
          1-Click Quick Demo Login (Incident Commander)
        </button>
      </div>
    </div>
  );
};
