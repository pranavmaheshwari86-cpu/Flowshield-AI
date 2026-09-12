import React from 'react';
import {
  ForecastHorizonPoint,
} from '../../types';
import {
  CloudRain,
  Waves,
} from 'lucide-react';

interface MultiHorizonForecastGridProps {
  horizons: ForecastHorizonPoint[];
  selectedHorizonHours: number | null;
  onSelectHorizon: (horizonHours: number) => void;
}

const HORIZON_TITLES: Record<number, { title: string; subtitle: string }> = {
  1: { title: '+1h Immediate Horizon', subtitle: 'Flash-flood & pluvial drainage' },
  3: { title: '+3h Catchment Horizon', subtitle: 'Small-stream concentration' },
  6: { title: '+6h Tributary Peak', subtitle: 'Micro-basin surge window' },
  12: { title: '+12h Mainstem Horizon', subtitle: 'Hydraulic wave propagation' },
  24: { title: '+24h Basin Crest', subtitle: 'Regional river crest peak' },
  48: { title: '+48h Storm Passage', subtitle: 'Extended runoff & recession' },
};

export const MultiHorizonForecastGrid: React.FC<MultiHorizonForecastGridProps> = ({
  horizons,
  selectedHorizonHours,
  onSelectHorizon,
}) => {
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return { text: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' };
      case 'HIGH':
        return { text: '#F97316', bg: 'rgba(249, 115, 22, 0.15)', border: 'rgba(249, 115, 22, 0.3)' };
      case 'WATCH':
        return { text: '#EAB308', bg: 'rgba(234, 179, 8, 0.15)', border: 'rgba(234, 179, 8, 0.3)' };
      case 'UNSUPPORTED':
        return { text: '#94A3B8', bg: 'rgba(100, 116, 139, 0.15)', border: 'rgba(100, 116, 139, 0.3)' };
      default:
        return { text: '#10B981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' };
    }
  };

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Multi-Horizon Planning Projections
          </div>
          <div style={{ fontSize: '15px', color: '#F1F5F9', fontWeight: 700 }}>
            Calibrated Machine Learning Projections (+1h to +48h)
          </div>
        </div>
        <div style={{ fontSize: '11px', color: '#94A3B8' }}>
          Click card to inspect horizon details
        </div>
      </div>

      {/* Grid of 6 Horizon Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '10px',
        }}
      >
        {horizons.map((h) => {
          const isSelected = selectedHorizonHours === h.horizon_hours;
          const tierStyle = getTierColor(h.risk_tier);
          const meta = HORIZON_TITLES[h.horizon_hours] || {
            title: `+${h.horizon_hours}h Projection`,
            subtitle: 'Calibrated forecast point',
          };

          const timeFormatted = h.forecast_timestamp
            ? new Date(h.forecast_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : `+${h.horizon_hours}h`;

          return (
            <div
              key={h.horizon_hours}
              onClick={() => onSelectHorizon(h.horizon_hours)}
              className="timeline-glass-card"
              style={{
                background: isSelected
                  ? 'linear-gradient(135deg, rgba(14, 45, 85, 0.65) 0%, rgba(8, 25, 52, 0.75) 100%)'
                  : 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
                backdropFilter: 'blur(18px) saturate(140%)',
                WebkitBackdropFilter: 'blur(18px) saturate(140%)',
                border: isSelected
                  ? '2px solid #38BDF8'
                  : '1px solid rgba(56, 189, 248, 0.20)',
                borderTop: '1px solid rgba(255, 255, 255, 0.24)',
                borderRadius: '8px',
                padding: '12px 14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: isSelected
                  ? '0 0 20px rgba(56, 189, 248, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2)'
                  : '0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.10)',
              }}
            >
              {/* Header: Horizon Label & Risk Tier Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 800, color: isSelected ? '#38BDF8' : '#F1F5F9' }}>
                      +{h.horizon_hours}h
                    </span>
                    <span style={{ fontSize: '11px', color: '#CBD5E1' }}>({timeFormatted})</span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '1px' }}>
                    {meta.subtitle}
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '10px',
                    fontWeight: 800,
                    padding: '2px 7px',
                    borderRadius: '4px',
                    background: tierStyle.bg,
                    color: tierStyle.text,
                    border: `1px solid ${tierStyle.border}`,
                    letterSpacing: '0.04em',
                    boxShadow: `0 0 6px ${tierStyle.border}`,
                  }}
                >
                  {h.risk_tier}
                </div>
              </div>

              {/* Main Score & Uncertainty Interval */}
              <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <div>
                  <span style={{ fontSize: '24px', fontWeight: 900, color: tierStyle.text, fontFamily: 'monospace' }}>
                    {h.operational_risk_score !== null && h.operational_risk_score !== undefined
                      ? h.operational_risk_score.toFixed(1)
                      : 'N/A'}
                  </span>
                  {h.operational_risk_score !== null && h.operational_risk_score !== undefined && (
                    <span style={{ fontSize: '11px', color: '#94A3B8', marginLeft: '4px' }}>/ 100</span>
                  )}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '9px', color: '#94A3B8' }}>Uncertainty [P10–P90]</div>
                  <div style={{ fontSize: '11px', color: '#FDBA74', fontFamily: 'monospace', fontWeight: 600 }}>
                    {h.uncertainty_band && h.uncertainty_band.p10 != null && h.uncertainty_band.p90 != null
                      ? `[${h.uncertainty_band.p10.toFixed(0)} – ${h.uncertainty_band.p90.toFixed(0)}]`
                      : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Metrics: Precipitation & River Stage */}
              <div
                className="timeline-glass-subcard"
                style={{
                  marginTop: '10px',
                  background: 'rgba(8, 24, 46, 0.45)',
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                  padding: '6px 8px',
                  borderRadius: '6px',
                  border: '1px solid rgba(56, 189, 248, 0.18)',
                  borderTop: '1px solid rgba(255, 255, 255, 0.15)',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '6px',
                  fontSize: '11px',
                }}
              >
                <div>
                  <div style={{ fontSize: '9px', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '3px' }}>
                    <CloudRain size={10} color="#38BDF8" /> Rain Rate
                  </div>
                  <div style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                    {h.projected_rainfall_rate_mm_hr != null
                      ? `${h.projected_rainfall_rate_mm_hr.toFixed(1)} mm/h`
                      : 'N/A'}
                  </div>
                  <div style={{ fontSize: '9px', color: '#CBD5E1' }}>
                    Cum: {h.cumulative_precipitation_mm != null ? `${h.cumulative_precipitation_mm.toFixed(1)} mm` : 'N/A'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '9px', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '3px' }}>
                    <Waves size={10} color="#2DD4BF" /> River Stage
                  </div>
                  <div style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                    {h.projected_river_stage_meters !== null && h.projected_river_stage_meters !== undefined
                      ? `${h.projected_river_stage_meters.toFixed(2)} m`
                      : 'N/A'}
                  </div>
                  <div style={{ fontSize: '9px', color: '#CBD5E1' }}>
                    Soil: {h.projected_soil_saturation_pct != null ? `${h.projected_soil_saturation_pct.toFixed(0)}%` : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Bottom: Calibrated Flood Probability & Primary Driver */}
              <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px' }}>
                <span style={{ color: '#94A3B8' }}>
                  P<sub>cal</sub>:{' '}
                  <strong style={{ color: '#F1F5F9' }}>
                    {h.calibrated_flood_probability !== null && h.calibrated_flood_probability !== undefined
                      ? `${(h.calibrated_flood_probability * 100).toFixed(1)}%`
                      : 'N/A'}
                  </strong>
                </span>
                <span style={{ color: '#38BDF8', fontWeight: 600, maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={h.primary_risk_driver}>
                  {h.primary_risk_driver}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
