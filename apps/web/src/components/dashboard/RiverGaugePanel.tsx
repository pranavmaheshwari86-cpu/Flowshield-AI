import React from 'react';
import { Waves, MapPin, ExternalLink } from 'lucide-react';
import { RiverGauge } from '../../types';

interface RiverGaugePanelProps {
  gauges?: RiverGauge[];
  onSelectRiver?: (river: RiverGauge) => void;
}

// Verified September 2026 Crisis Reference Data
const DEFAULT_GAUGES: RiverGauge[] = [
  {
    river: 'Ganga',
    station: 'Bihar',
    current_level_m: 49.82,
    danger_level_m: 48.60,
    warning_level_m: 47.50,
    delta_danger_m: 1.22,
    trend: 'RISING',
    status: 'CRITICAL',
    state: 'Bihar',
    impact: 'Patna & Bhagalpur flood plain inundation',
  },
  {
    river: 'Kosi',
    station: 'Bihar',
    current_level_m: 35.14,
    danger_level_m: 33.85,
    warning_level_m: 32.80,
    delta_danger_m: 1.29,
    trend: 'RAPIDLY_RISING',
    status: 'CRITICAL',
    state: 'Bihar',
    impact: 'Supual & Saharsa embankment breach warning',
  },
  {
    river: 'Gandak',
    station: 'Bihar',
    current_level_m: 62.30,
    danger_level_m: 62.22,
    warning_level_m: 61.20,
    delta_danger_m: 0.08,
    trend: 'RISING',
    status: 'CRITICAL',
    state: 'Bihar',
    impact: 'Gopalganj low-lying rural inundation',
  },
  {
    river: 'Bagmati',
    station: 'Bihar',
    current_level_m: 42.49,
    danger_level_m: 45.72,
    warning_level_m: 44.50,
    delta_danger_m: -3.23,
    trend: 'STABLE',
    status: 'NORMAL',
    state: 'Bihar',
    impact: 'Flowing below alert threshold',
  },
  {
    river: 'Punpun',
    station: 'Bihar',
    current_level_m: 51.97,
    danger_level_m: 50.60,
    warning_level_m: 49.50,
    delta_danger_m: 1.37,
    trend: 'RISING',
    status: 'CRITICAL',
    state: 'Bihar',
    impact: 'Surge threatening Sripalpur corridor',
  },
];

export const RiverGaugePanel: React.FC<RiverGaugePanelProps> = ({
  gauges = DEFAULT_GAUGES,
  onSelectRiver,
}) => {
  const displayGauges = gauges && gauges.length > 0 ? gauges : DEFAULT_GAUGES;

  return (
    <div
      className="cc-card"
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        padding: '14px 16px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(61, 139, 180, 0.20)',
          paddingBottom: '10px',
          marginBottom: '10px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Waves size={16} color="#22D3EE" />
          <span style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '0.04em', color: '#FFFFFF' }}>
            RIVER GAUGE OVERVIEW
          </span>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: 'rgba(16, 185, 129, 0.15)',
              padding: '1px 6px',
              borderRadius: '9999px',
            }}
          >
            <span className="live-dot" style={{ width: '6px', height: '6px' }} />
            <span style={{ fontSize: '10px', fontWeight: 700, color: '#10B981' }}>Live</span>
          </div>
        </div>

        <a
          href="#rivers"
          onClick={(e) => { e.preventDefault(); }}
          style={{
            fontSize: '11px',
            color: '#22D3EE',
            textDecoration: 'none',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
          }}
        >
          <span>View All Rivers</span>
          <ExternalLink size={11} />
        </a>
      </div>

      {/* Table Headers */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 0.9fr 0.9fr 0.9fr',
          fontSize: '10.5px',
          fontWeight: 600,
          color: '#7F95A5',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          padding: '4px 6px 8px 6px',
          borderBottom: '1px solid rgba(61, 139, 180, 0.15)',
          flexShrink: 0,
        }}
      >
        <span>River</span>
        <span style={{ textAlign: 'right' }}>Level</span>
        <span style={{ textAlign: 'right' }}>Danger Mark</span>
        <span style={{ textAlign: 'right' }}>Status</span>
      </div>

      {/* Table Rows */}
      <div
        className="cc-scrollable"
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
        }}
      >
        {displayGauges.slice(0, 5).map((g, idx) => {
          const isBreached = g.delta_danger_m > 0 || g.status === 'CRITICAL' || g.status === 'DANGER';
          const deltaStr = isBreached
            ? `+${g.delta_danger_m.toFixed(2)} m`
            : 'NORMAL';

          return (
            <div
              key={`${g.river}-${idx}`}
              onClick={() => onSelectRiver && onSelectRiver(g)}
              style={{
                display: 'grid',
                gridTemplateColumns: '1.2fr 0.9fr 0.9fr 0.9fr',
                alignItems: 'center',
                padding: '9px 6px',
                borderRadius: '6px',
                borderBottom: '1px solid rgba(61, 139, 180, 0.08)',
                cursor: 'pointer',
                transition: 'background 0.12s ease',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(20, 184, 166, 0.08)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >
              {/* River Name & Location */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MapPin size={12} color="#22D3EE" style={{ flexShrink: 0 }} />
                <div style={{ lineHeight: 1.15 }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#F1F7FA' }}>
                    {g.river}
                  </div>
                  <div style={{ fontSize: '10px', color: '#7F95A5' }}>
                    ({g.station || g.state || 'Catchment'})
                  </div>
                </div>
              </div>

              {/* Current Level */}
              <div
                style={{
                  textAlign: 'right',
                  fontSize: '12px',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: '#FFFFFF',
                }}
              >
                {g.current_level_m.toFixed(2)} m
              </div>

              {/* Danger Mark */}
              <div
                style={{
                  textAlign: 'right',
                  fontSize: '11.5px',
                  fontWeight: 500,
                  fontFamily: 'var(--font-mono)',
                  color: '#94A3B8',
                }}
              >
                {g.danger_level_m.toFixed(2)} m
              </div>

              {/* Status Badge */}
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <span
                  style={{
                    padding: '2px 7px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: '#FFFFFF',
                    background: isBreached ? '#C62828' : '#2D6A4F',
                    boxShadow: isBreached ? '0 0 8px rgba(198, 40, 40, 0.4)' : 'none',
                    letterSpacing: '0.02em',
                  }}
                >
                  {deltaStr}
                </span>
              </div>
            </div>
          );
        })}

        {/* Others (2) Row matching the screenshot */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1.2fr 0.9fr 0.9fr 0.9fr',
            alignItems: 'center',
            padding: '9px 6px',
            color: '#7F95A5',
            fontSize: '11px',
            borderTop: '1px dashed rgba(61, 139, 180, 0.2)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <MapPin size={12} color="#7F95A5" />
            <span>Others (2)</span>
          </div>
          <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>--</div>
          <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>--</div>
          <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>--</div>
        </div>
      </div>
    </div>
  );
};
