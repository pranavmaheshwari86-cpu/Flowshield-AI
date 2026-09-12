import React, { useState, useEffect } from 'react';
import { CloudRain, Waves, Mountain, Navigation, Clock } from 'lucide-react';

interface SystemStatusBarProps {
  systemHealth?: number;
  rainfall1h?: number;
  rainfallTrend?: string;
  riversBreachedCount?: number;
  totalRivers?: number;
  landslideRiskTier?: string;
  landslideDistrictsCount?: number;
  evacuationClearCount?: number;
  totalEvacuationRoutes?: number;
}

export const SystemStatusBar: React.FC<SystemStatusBarProps> = ({
  systemHealth = 98,
  rainfall1h = 47.3,
  rainfallTrend = '↑ 18%',
  riversBreachedCount = 7,
  totalRivers = 9,
  landslideRiskTier = 'High',
  landslideDistrictsCount = 3,
  evacuationClearCount = 5,
  totalEvacuationRoutes = 5,
}) => {
  // Live Clock (defaults to formatted IST time)
  const [timeStr, setTimeStr] = useState<string>('03:57:24 PM');
  const [dateStr, setDateStr] = useState<string>('15 Sep 2026');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Format time as HH:MM:SS AM/PM
      const timeFormatted = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
      // Format date as 15 Sep 2026 (or current date)
      const dateFormatted = now.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
      setTimeStr(timeFormatted);
      setDateStr(dateFormatted);
    };

    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // SVG Ring Calculation
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (systemHealth / 100) * circumference;

  return (
    <footer className="cc-status-glass-dock">
      {/* Subtle River/Glacier Shimmer Accent on Far Right */}
      <div
        style={{
          position: 'absolute',
          right: '0',
          bottom: '0',
          width: '300px',
          height: '66px',
          background: 'radial-gradient(ellipse at 85% 100%, rgba(34, 211, 238, 0.12) 0%, transparent 75%)',
          pointerEvents: 'none',
        }}
      />

      {/* 1. System Health Ring & Status */}
      <div className="cc-status-glass-card">
        <div style={{ position: 'relative', width: '42px', height: '42px', flexShrink: 0 }}>
          <svg width="42" height="42" viewBox="0 0 48 48">
            {/* Background Track */}
            <circle
              cx="24"
              cy="24"
              r={radius}
              fill="transparent"
              stroke="rgba(23, 49, 73, 0.6)"
              strokeWidth="4"
            />
            {/* Progress Arc */}
            <circle
              cx="24"
              cy="24"
              r={radius}
              fill="transparent"
              stroke="#14B8A6"
              strokeWidth="4"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform="rotate(-90 24 24)"
              style={{ filter: 'drop-shadow(0 0 6px rgba(20, 184, 166, 0.8))' }}
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
              color: '#FFFFFF',
            }}
          >
            {systemHealth}%
          </div>
        </div>

        <div>
          <div style={{ fontSize: '10px', fontWeight: 700, color: '#C5D4DF', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            SYSTEM HEALTH
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '1px' }}>
            <span className="live-dot" style={{ width: '5px', height: '5px' }} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#22D3EE' }}>
              All Systems Operational
            </span>
          </div>
          <div style={{ fontSize: '9px', color: '#94A3B8' }}>
            Data • Models • Comms
          </div>
        </div>
      </div>

      {/* Glass Divider */}
      <div className="cc-status-glass-divider" />

      {/* 2. Rainfall Telemetry */}
      <div className="cc-status-glass-card">
        <div
          className="cc-status-glass-icon-box"
          style={{
            background: 'rgba(34, 211, 238, 0.14)',
            border: '1px solid rgba(34, 211, 238, 0.35)',
          }}
        >
          <CloudRain size={16} color="#22D3EE" />
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 500 }}>
            Rainfall (1h)
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', fontFamily: 'var(--font-mono)' }}>
            {rainfall1h.toFixed(1)} <span style={{ fontSize: '10px', fontWeight: 500, color: '#94A3B8' }}>mm/h</span>
          </div>
          <div style={{ fontSize: '9.5px', color: '#10B981', fontWeight: 600 }}>
            {rainfallTrend}
          </div>
        </div>
      </div>

      {/* Glass Divider */}
      <div className="cc-status-glass-divider" />

      {/* 3. Rivers Above Danger */}
      <div className="cc-status-glass-card">
        <div
          className="cc-status-glass-icon-box"
          style={{
            background: 'rgba(56, 189, 248, 0.14)',
            border: '1px solid rgba(56, 189, 248, 0.35)',
          }}
        >
          <Waves size={16} color="#38BDF8" />
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 500 }}>
            Rivers (&gt;Danger)
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', fontFamily: 'var(--font-mono)' }}>
            {riversBreachedCount} / {totalRivers}
          </div>
          <div style={{ fontSize: '9.5px', color: '#F59E0B', fontWeight: 600 }}>
            ↑ 2 since last hour
          </div>
        </div>
      </div>

      {/* Glass Divider */}
      <div className="cc-status-glass-divider" />

      {/* 4. Landslide Risk */}
      <div className="cc-status-glass-card">
        <div
          className="cc-status-glass-icon-box"
          style={{
            background: 'rgba(245, 158, 11, 0.14)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
          }}
        >
          <Mountain size={16} color="#F59E0B" />
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 500 }}>
            Landslide Risk
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FB923C' }}>
            {landslideRiskTier}
          </div>
          <div style={{ fontSize: '9.5px', color: '#94A3B8' }}>
            {landslideDistrictsCount} districts
          </div>
        </div>
      </div>

      {/* Glass Divider */}
      <div className="cc-status-glass-divider" />

      {/* 5. Evacuation Routes */}
      <div className="cc-status-glass-card">
        <div
          className="cc-status-glass-icon-box"
          style={{
            background: 'rgba(16, 185, 129, 0.14)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
          }}
        >
          <Navigation size={16} color="#10B981" />
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 500 }}>
            Evacuation Routes
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', fontFamily: 'var(--font-mono)' }}>
            {evacuationClearCount} / {totalEvacuationRoutes}
          </div>
          <div style={{ fontSize: '9.5px', color: '#10B981', fontWeight: 600 }}>
            Clear
          </div>
        </div>
      </div>

      {/* Flexible Spacer */}
      <div style={{ flex: 1, minWidth: '4px' }} />

      {/* Glass Divider */}
      <div className="cc-status-glass-divider" />

      {/* 6. Date & Time Console */}
      <div className="cc-status-glass-card" style={{ position: 'relative', zIndex: 2 }}>
        <div
          className="cc-status-glass-icon-box"
          style={{
            background: 'rgba(34, 211, 238, 0.12)',
            border: '1px solid rgba(34, 211, 238, 0.30)',
          }}
        >
          <Clock size={16} color="#22D3EE" />
        </div>
        <div>
          <div style={{ fontSize: '10px', color: '#C5D4DF', fontWeight: 500 }}>
            {dateStr}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#FFFFFF', fontFamily: 'var(--font-mono)' }}>
            {timeStr}
          </div>
          <div style={{ fontSize: '9px', color: '#7F95A5', fontWeight: 600, letterSpacing: '0.05em' }}>
            IST (UTC+5:30)
          </div>
        </div>
      </div>
    </footer>
  );
};
