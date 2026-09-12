import React from 'react';
import {
  CloudRain,
  Waves,
  Droplets,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { ObservationSnapshot, HydrologicalAnalysis, ForecastHorizonPoint } from '../../types';

interface CurrentSituationBarProps {
  observation: ObservationSnapshot;
  hydrology: HydrologicalAnalysis;
  currentHorizon: ForecastHorizonPoint | undefined;
  baselineRiskScore: number;
  trendRatePointsPerHr: number;
}

export const CurrentSituationBar: React.FC<CurrentSituationBarProps> = ({
  observation,
  hydrology,
  currentHorizon,
  baselineRiskScore,
  trendRatePointsPerHr,
}) => {
  const riskTier = currentHorizon?.risk_tier || 'LOW';

  const riskTierColor: Record<string, string> = {
    LOW: '#10B981',
    WATCH: '#EAB308',
    HIGH: '#F97316',
    CRITICAL: '#EF4444',
    UNSUPPORTED: '#94A3B8',
  };
  const activeColor = riskTierColor[riskTier] || '#10B981';

  const renderTrendIcon = () => {
    if (trendRatePointsPerHr > 1.5) {
      return <TrendingUp size={16} color="#EF4444" />;
    } else if (trendRatePointsPerHr < -1.5) {
      return <TrendingDown size={16} color="#10B981" />;
    }
    return <Minus size={16} color="#94A3B8" />;
  };

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '12px',
        width: '100%',
      }}
    >
      {/* KPI 1: Observed Rainfall Rate & Accumulation */}
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
          backdropFilter: 'blur(20px) saturate(140%)',
          WebkitBackdropFilter: 'blur(20px) saturate(140%)',
          border: '1px solid rgba(56, 189, 248, 0.22)',
          borderTop: '1px solid rgba(255, 255, 255, 0.28)',
          borderRadius: '10px',
          padding: '14px 16px',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 16px rgba(34, 211, 238, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Observed Station Telemetry
            </div>
            <div style={{ fontSize: '13px', color: '#F1F5F9', fontWeight: 600, marginTop: '2px' }}>
              Precipitation Loading
            </div>
          </div>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.16)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#38BDF8',
              boxShadow: '0 0 10px rgba(56, 189, 248, 0.2)',
            }}
          >
            <CloudRain size={18} />
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '24px', fontWeight: 800, color: '#38BDF8', fontFamily: 'monospace' }}>
            {observation.rainfall_rate_mm_hr.toFixed(1)}
          </span>
          <span style={{ fontSize: '12px', color: '#CBD5E1', fontWeight: 500 }}>mm/hr rate</span>
        </div>

        <div
          className="timeline-glass-subcard"
          style={{
            marginTop: '10px',
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '4px',
            background: 'rgba(8, 24, 46, 0.45)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            padding: '6px 8px',
            borderRadius: '6px',
            textAlign: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>1h</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>{observation.rainfall_1h_mm.toFixed(1)}</div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>3h</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>{observation.rainfall_3h_mm.toFixed(1)}</div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>6h</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>{observation.rainfall_6h_mm.toFixed(1)}</div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>12h</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>{(observation.rainfall_12h_mm ?? 0).toFixed(1)}</div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>24h</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8' }}>{observation.rainfall_24h_mm.toFixed(1)}</div>
          </div>
        </div>

        <div style={{ marginTop: '8px', fontSize: '10px', color: '#94A3B8', display: 'flex', justifyContent: 'space-between' }}>
          <span>Source: {observation.provenance.source_name}</span>
          <span style={{ color: observation.provenance.quality_status === 'GOOD' ? '#10B981' : '#F59E0B', fontWeight: 600 }}>
            {observation.provenance.quality_status}
          </span>
        </div>
      </div>

      {/* KPI 2: CWC River Stage & Surge */}
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
          backdropFilter: 'blur(20px) saturate(140%)',
          WebkitBackdropFilter: 'blur(20px) saturate(140%)',
          border: '1px solid rgba(56, 189, 248, 0.22)',
          borderTop: '1px solid rgba(255, 255, 255, 0.28)',
          borderRadius: '10px',
          padding: '14px 16px',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 16px rgba(45, 212, 191, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              CWC Hydrological Gauge
            </div>
            <div style={{ fontSize: '13px', color: '#F1F5F9', fontWeight: 600, marginTop: '2px' }}>
              {hydrology.river_name || 'Catchment River'} Stage
            </div>
          </div>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'rgba(45, 212, 191, 0.16)',
              border: '1px solid rgba(45, 212, 191, 0.35)',
              color: '#2DD4BF',
              boxShadow: '0 0 10px rgba(45, 212, 191, 0.2)',
            }}
          >
            <Waves size={18} />
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          {hydrology.current_stage_meters !== null && hydrology.current_stage_meters !== undefined ? (
            <>
              <span style={{ fontSize: '24px', fontWeight: 800, color: '#2DD4BF', fontFamily: 'monospace' }}>
                {hydrology.current_stage_meters.toFixed(2)}
              </span>
              <span style={{ fontSize: '12px', color: '#CBD5E1', fontWeight: 500 }}>
                meters (Danger: {hydrology.danger_mark_meters?.toFixed(2) || 'N/A'}m)
              </span>
            </>
          ) : (
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#94A3B8' }}>
              GAUGE TELEMETRY UNAVAILABLE
            </span>
          )}
        </div>

        <div
          className="timeline-glass-subcard"
          style={{
            marginTop: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(8, 24, 46, 0.45)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            padding: '6px 8px',
            borderRadius: '6px',
          }}
        >
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>Margin to Danger</div>
            <div
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color:
                  hydrology.margin_to_danger_meters !== null && hydrology.margin_to_danger_meters !== undefined && hydrology.margin_to_danger_meters > 0
                    ? '#EF4444'
                    : '#2DD4BF',
              }}
            >
              {hydrology.margin_to_danger_meters !== null && hydrology.margin_to_danger_meters !== undefined
                ? hydrology.margin_to_danger_meters > 0
                  ? `+${hydrology.margin_to_danger_meters.toFixed(2)}m OVER DANGER`
                  : `${Math.abs(hydrology.margin_to_danger_meters).toFixed(2)}m below danger`
                : 'N/A'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>Surge Rate</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>
              {hydrology.rate_of_rise_m_per_hr !== null && hydrology.rate_of_rise_m_per_hr !== undefined
                ? `${hydrology.rate_of_rise_m_per_hr > 0 ? '+' : ''}${hydrology.rate_of_rise_m_per_hr.toFixed(2)} m/h`
                : 'Steady'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '9px', color: '#94A3B8' }}>Hydraulic Trend</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: hydrology.hydraulic_trend === 'RISING' ? '#F59E0B' : '#CBD5E1' }}>
              {hydrology.hydraulic_trend}
            </div>
          </div>
        </div>

        <div style={{ marginTop: '8px', fontSize: '10px', color: '#94A3B8', display: 'flex', justifyContent: 'space-between' }}>
          <span>Station: {hydrology.gauge_station_name || 'Watershed Sensor Node'}</span>
          <span style={{ color: '#2DD4BF', fontWeight: 600 }}>CWC Realtime Grid</span>
        </div>
      </div>

      {/* KPI 3: Land Surface Topsoil Saturation */}
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
          backdropFilter: 'blur(20px) saturate(140%)',
          WebkitBackdropFilter: 'blur(20px) saturate(140%)',
          border: '1px solid rgba(56, 189, 248, 0.22)',
          borderTop: '1px solid rgba(255, 255, 255, 0.28)',
          borderRadius: '10px',
          padding: '14px 16px',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 16px rgba(168, 85, 247, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Copernicus ERA5-Land
            </div>
            <div style={{ fontSize: '13px', color: '#F1F5F9', fontWeight: 600, marginTop: '2px' }}>
              Topsoil Saturation
            </div>
          </div>
          <div
            style={{
              padding: '6px',
              borderRadius: '8px',
              background: 'rgba(168, 85, 247, 0.16)',
              border: '1px solid rgba(168, 85, 247, 0.35)',
              color: '#C084FC',
              boxShadow: '0 0 10px rgba(168, 85, 247, 0.2)',
            }}
          >
            <Droplets size={18} />
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '24px', fontWeight: 800, color: '#C084FC', fontFamily: 'monospace' }}>
            {observation.soil_saturation_pct.toFixed(1)}%
          </span>
          <span style={{ fontSize: '12px', color: '#CBD5E1', fontWeight: 500 }}>
            ({observation.soil_moisture_m3_m3.toFixed(3)} m³/m³)
          </span>
        </div>

        {/* Progress Bar for Saturation */}
        <div style={{ marginTop: '10px', width: '100%', height: '6px', background: 'rgba(30, 41, 59, 0.7)', borderRadius: '3px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, Math.max(0, observation.soil_saturation_pct))}%`,
              background:
                observation.soil_saturation_pct > 80
                  ? '#EF4444'
                  : observation.soil_saturation_pct > 60
                  ? '#F59E0B'
                  : '#10B981',
              transition: 'width 0.5s ease',
              boxShadow: '0 0 8px currentColor',
            }}
          />
        </div>

        <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
          <span style={{ color: '#94A3B8' }}>Infiltration Capacity:</span>
          <span style={{ color: observation.soil_saturation_pct > 75 ? '#EF4444' : '#10B981', fontWeight: 600 }}>
            {observation.soil_saturation_pct > 75 ? 'Critically Reduced' : 'Normal Absorption'}
          </span>
        </div>

        <div style={{ marginTop: '6px', fontSize: '10px', color: '#94A3B8', display: 'flex', justifyContent: 'space-between' }}>
          <span>Depth: 0–7cm Layer</span>
          <span style={{ color: '#C084FC', fontWeight: 600 }}>ECMWF Land Surface</span>
        </div>
      </div>

      {/* KPI 4: Current Composite Operational Risk Score */}
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
          backdropFilter: 'blur(20px) saturate(140%)',
          WebkitBackdropFilter: 'blur(20px) saturate(140%)',
          border: `1px solid ${riskTierColor}55`,
          borderTop: '1px solid rgba(255, 255, 255, 0.28)',
          borderRadius: '10px',
          padding: '14px 16px',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: `0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px ${riskTierColor}25`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Operational Risk Index
            </div>
            <div style={{ fontSize: '13px', color: '#F1F5F9', fontWeight: 600, marginTop: '2px' }}>
              Multi-Factor Score (Now)
            </div>
          </div>
          <div
            style={{
              padding: '4px 8px',
              borderRadius: '6px',
              background: `${activeColor}28`,
              color: activeColor,
              border: `1px solid ${activeColor}66`,
              fontSize: '11px',
              fontWeight: 800,
              letterSpacing: '0.05em',
              boxShadow: `0 0 10px ${activeColor}33`,
            }}
          >
            {riskTier}
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '28px', fontWeight: 900, color: activeColor, fontFamily: 'monospace' }}>
            {riskTier === 'UNSUPPORTED' ? 'N/A' : baselineRiskScore.toFixed(1)}
          </span>
          {riskTier !== 'UNSUPPORTED' && (
            <span style={{ fontSize: '14px', color: '#94A3B8', fontWeight: 600 }}>/ 100</span>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: '3px', marginLeft: 'auto', fontSize: '12px', fontWeight: 600, color: '#F1F5F9' }}>
            {renderTrendIcon()}
            <span>
              {trendRatePointsPerHr > 0 ? '+' : ''}
              {trendRatePointsPerHr.toFixed(1)} pts/h
            </span>
          </div>
        </div>

        <div
          className="timeline-glass-subcard"
          style={{
            marginTop: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(8, 24, 46, 0.45)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            padding: '5px 8px',
            borderRadius: '6px',
          }}
        >
          <span style={{ fontSize: '10px', color: '#94A3B8' }}>Calibrated Likelihood (P<sub>cal</sub>):</span>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#F1F5F9' }}>
            {currentHorizon?.calibrated_flood_probability !== null && currentHorizon?.calibrated_flood_probability !== undefined
              ? `${(currentHorizon.calibrated_flood_probability * 100).toFixed(1)}%`
              : 'N/A'}
          </span>
        </div>

        <div style={{ marginTop: '6px', fontSize: '10px', color: '#94A3B8', display: 'flex', justifyContent: 'space-between' }}>
          <span>Primary Driver: <strong style={{ color: '#CBD5E1' }}>{currentHorizon?.primary_risk_driver || 'Hydrological Loading'}</strong></span>
        </div>
      </div>
    </div>
  );
};
