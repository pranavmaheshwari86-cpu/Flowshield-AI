import React from 'react';
import { ShieldAlert, AlertTriangle, CloudRain } from 'lucide-react';

interface IncidentForecastBarProps {
  crisisTitle?: string;
  crisisLocations?: string;
  forecastHeadline?: string;
  forecastRegion?: string;
  forecastRainfall?: string;
}

export const IncidentForecastBar: React.FC<IncidentForecastBarProps> = ({
  crisisTitle = 'NATIONAL FLOOD CRISIS MONITOR',
  crisisLocations = 'North & Eastern India  |  14 Districts  |  UP (Kanpur Pandu Surge) + 24 Districts',
  forecastHeadline = 'Heavy to Very Heavy Rainfall',
  forecastRegion = 'Gangetic Plains & Foothills',
  forecastRainfall = '200–300 mm',
}) => {
  return (
    <section className="incident-forecast-bar" aria-label="Active Incident and Forecast">
      {/* 1. Left Card: Active Incident Monitor */}
      <div
        className="cc-card cc-card-critical"
        style={{
          padding: '12px 18px',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderRadius: 'var(--radius-card)',
          gap: '14px',
        }}
      >
        {/* Left Icon & Text Details */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.22)',
              border: '1px solid rgba(239, 68, 68, 0.65)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 0 12px rgba(239, 68, 68, 0.35)',
            }}
          >
            <ShieldAlert size={22} color="#EF4444" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 800,
                  color: '#EF4444',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                }}
              >
                ACTIVE INCIDENT
              </span>
            </div>
            <div
              style={{
                fontSize: '15px',
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
                lineHeight: 1.2,
                marginTop: '1px',
              }}
            >
              {crisisTitle}
            </div>
            <div
              style={{
                fontSize: '11px',
                color: '#C5D4DF',
                marginTop: '2px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {crisisLocations}
            </div>
          </div>
        </div>

        {/* Right Live Badge & Telemetry Waveform */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
          {/* ECG/Telemetry Pulse Waveform */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="48" height="20" viewBox="0 0 48 20" fill="none">
              <path
                d="M0 10 H12 L15 2 L19 18 L23 7 L27 13 L30 10 H48"
                stroke="#EF4444"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ filter: 'drop-shadow(0 0 4px rgba(239,68,68,0.7))' }}
              />
            </svg>
            <span style={{ fontSize: '11px', color: '#C5D4DF', fontWeight: 500 }}>
              Real-time Telemetry
            </span>
          </div>

          {/* LIVE Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: '#DC2626',
              padding: '3px 9px',
              borderRadius: '9999px',
              boxShadow: '0 0 12px rgba(220, 38, 38, 0.6)',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: '#FFFFFF',
                animation: 'livePulse 1.5s infinite ease-in-out',
              }}
            />
            <span
              style={{
                color: '#FFFFFF',
                fontSize: '10px',
                fontWeight: 800,
                letterSpacing: '0.06em',
              }}
            >
              LIVE
            </span>
          </div>
        </div>
      </div>

      {/* 2. Right Card: IMD Forecast */}
      <div
        className="cc-card cc-card-warning"
        style={{
          padding: '12px 18px',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderRadius: 'var(--radius-card)',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.22)',
              border: '1px solid rgba(245, 158, 11, 0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 0 12px rgba(245, 158, 11, 0.25)',
            }}
          >
            <AlertTriangle size={20} color="#F59E0B" />
          </div>

          <div>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 800,
                color: '#F59E0B',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              IMD FORECAST
            </span>
            <div
              style={{
                fontSize: '14px',
                fontWeight: 700,
                color: '#FFFFFF',
                marginTop: '1px',
                lineHeight: 1.2,
              }}
            >
              {forecastHeadline}
            </div>
            <div style={{ fontSize: '11px', color: '#C5D4DF', marginTop: '2px' }}>
              {forecastRegion}
            </div>
          </div>
        </div>

        {/* Forecast Metric Capsule */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(15, 33, 62, 0.65)',
              border: '1px solid rgba(61, 139, 180, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CloudRain size={18} color="#38BDF8" />
          </div>

          <div>
            <div style={{ fontSize: '10px', color: '#7F95A5', fontWeight: 500 }}>
              Next 24 Hours
            </div>
            <div
              style={{
                fontSize: '14.5px',
                fontWeight: 700,
                color: '#FFFFFF',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {forecastRainfall}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
