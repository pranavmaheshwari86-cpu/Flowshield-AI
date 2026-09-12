import React from 'react';
import {
  CloudRain,
  Droplets,
  Wind,
  Thermometer,
} from 'lucide-react';
import { ObservationSnapshot, HydrologicalAnalysis, ForecastHorizonPoint } from '../../types';

interface CurrentSituationBarProps {
  observation: ObservationSnapshot;
  hydrology?: HydrologicalAnalysis;
  currentHorizon?: ForecastHorizonPoint | undefined;
  baselineRiskScore?: number;
  trendRatePointsPerHr?: number;
}

export const CurrentSituationBar: React.FC<CurrentSituationBarProps> = ({
  observation,
}) => {
  const isAtmosphericLive = observation.atmospheric_freshness_status === 'LIVE';
  const atmosphericSource = observation.atmospheric_telemetry_source || 'Open-Meteo Synoptic Grid';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%' }}>
      {/* Real-time Atmospheric Telemetry Ribbon: Precipitation · Wind Speed · Humidity · Soil Moisture */}
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.72) 0%, rgba(4, 12, 26, 0.82) 100%)',
          backdropFilter: 'blur(20px) saturate(140%)',
          WebkitBackdropFilter: 'blur(20px) saturate(140%)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderTop: '1px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '12px',
          padding: '16px 20px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.12)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: isAtmosphericLive ? '#10B981' : '#F59E0B',
                boxShadow: isAtmosphericLive ? '0 0 8px #10B981' : '0 0 8px #F59E0B',
                animation: 'pulse 1.5s infinite',
              }}
            />
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Current Atmospheric & Hydrological Telemetry
            </span>
            <span
              style={{
                fontSize: '9px',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                background: isAtmosphericLive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: isAtmosphericLive ? '#34D399' : '#FBBF24',
                border: `1px solid ${isAtmosphericLive ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
              }}
            >
              {observation.atmospheric_freshness_status || 'LIVE'}
            </span>
          </div>
          <span style={{ fontSize: '9.5px', color: '#94A3B8' }}>
            Telemetry: {atmosphericSource} • {observation.soil_telemetry_source || 'Copernicus ERA5-Land'}
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '14px',
          }}
        >
          {/* 1. Current Precipitation */}
          <div
            style={{
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.28)',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Current Precipitation Rate
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '3px' }}>
                <span style={{ fontSize: '26px', fontWeight: 800, color: '#38BDF8', fontFamily: 'monospace' }}>
                  {observation.rainfall_rate_mm_hr != null ? observation.rainfall_rate_mm_hr.toFixed(1) : '—'}
                </span>
                <span style={{ fontSize: '11px', color: '#94A3B8' }}>mm/h</span>
              </div>
              <div style={{ fontSize: '10px', color: '#64748B', marginTop: '3px' }}>
                24h Total: <strong style={{ color: '#CBD5E1' }}>{observation.rainfall_24h_mm != null ? `${observation.rainfall_24h_mm.toFixed(1)} mm` : '—'}</strong>
              </div>
            </div>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(56, 189, 248, 0.16)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CloudRain size={22} color="#38BDF8" />
            </div>
          </div>

          {/* 2. Wind Speed */}
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.28)',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Wind Speed
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '3px' }}>
                <span style={{ fontSize: '26px', fontWeight: 800, color: '#10B981', fontFamily: 'monospace' }}>
                  {observation.wind_speed_kmh != null ? observation.wind_speed_kmh.toFixed(1) : '—'}
                </span>
                <span style={{ fontSize: '11px', color: '#94A3B8' }}>km/h</span>
              </div>
              <div style={{ fontSize: '10px', color: '#64748B', marginTop: '3px' }}>
                Condition: <strong style={{ color: '#CBD5E1' }}>{observation.wind_speed_kmh != null ? (observation.wind_speed_kmh > 25 ? 'High Wind' : observation.wind_speed_kmh > 12 ? 'Moderate' : 'Calm') : '—'}</strong>
              </div>
            </div>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(16, 185, 129, 0.16)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Wind size={22} color="#10B981" />
            </div>
          </div>

          {/* 3. Humidity */}
          <div
            style={{
              background: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.28)',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Relative Humidity
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '3px' }}>
                <span style={{ fontSize: '26px', fontWeight: 800, color: '#818CF8', fontFamily: 'monospace' }}>
                  {observation.humidity_pct != null ? `${observation.humidity_pct.toFixed(0)}%` : '—'}
                </span>
              </div>
              <div style={{ fontSize: '10px', color: '#64748B', marginTop: '3px' }}>
                Air Temp: <strong style={{ color: '#CBD5E1' }}>{observation.temperature_c != null ? `${observation.temperature_c.toFixed(1)}°C` : '—'}</strong>
              </div>
            </div>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(99, 102, 241, 0.16)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Droplets size={22} color="#818CF8" />
            </div>
          </div>

          {/* 4. Soil Moisture */}
          <div
            style={{
              background: 'rgba(168, 85, 247, 0.08)',
              border: '1px solid rgba(168, 85, 247, 0.28)',
              borderRadius: '10px',
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Soil Moisture (VWC)
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '3px' }}>
                <span style={{ fontSize: '26px', fontWeight: 800, color: '#C084FC', fontFamily: 'monospace' }}>
                  {observation.soil_moisture_m3_m3 != null ? `${observation.soil_moisture_m3_m3.toFixed(3)}` : '—'}
                </span>
                <span style={{ fontSize: '11px', color: '#94A3B8' }}>m³/m³</span>
              </div>
              <div style={{ fontSize: '10px', color: '#64748B', marginTop: '3px' }}>
                {observation.soil_moisture_vwc_pct != null
                  ? `${observation.soil_moisture_vwc_pct.toFixed(1)}% VWC`
                  : observation.soil_saturation_pct != null
                  ? `${observation.soil_saturation_pct.toFixed(1)}% Sat`
                  : '—'} • {observation.soil_effective_saturation_pct != null
                  ? `${observation.soil_effective_saturation_pct.toFixed(1)}% Se`
                  : observation.soil_saturation_pct != null
                  ? `${observation.soil_saturation_pct.toFixed(1)}% Sat`
                  : '—'}
              </div>
              <div style={{ fontSize: '9px', color: '#A855F7', marginTop: '2px', fontWeight: 600 }}>
                {observation.soil_telemetry_source || 'AgroMonitoring Sentinel-1'}
              </div>
            </div>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(168, 85, 247, 0.16)',
                border: '1px solid rgba(168, 85, 247, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Thermometer size={22} color="#C084FC" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
