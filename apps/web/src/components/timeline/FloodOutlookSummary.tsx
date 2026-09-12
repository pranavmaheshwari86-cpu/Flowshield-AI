import { ShieldAlert, AlertTriangle, ShieldCheck, Gauge, CloudRain, Clock } from 'lucide-react';
import { TimelineDetailedResponse } from '../../types';

interface FloodOutlookSummaryProps {
  data: TimelineDetailedResponse;
}

export const FloodOutlookSummary: React.FC<FloodOutlookSummaryProps> = ({ data }) => {
  const outlook = data.flood_outlook;
  const horizons = outlook?.horizons || {};
  const peakRisk = outlook?.peak_risk;
  const horizonKeys = ['1h', '3h', '6h', '12h', '24h', '48h'];

  const getTierBadgeStyle = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
        return {
          bg: 'rgba(239, 68, 68, 0.15)',
          border: 'rgba(239, 68, 68, 0.5)',
          color: '#EF4444',
          icon: <ShieldAlert size={12} className="inline mr-1" />
        };
      case 'HIGH':
        return {
          bg: 'rgba(249, 115, 22, 0.15)',
          border: 'rgba(249, 115, 22, 0.5)',
          color: '#F97316',
          icon: <AlertTriangle size={12} className="inline mr-1" />
        };
      case 'WATCH':
        return {
          bg: 'rgba(234, 179, 8, 0.15)',
          border: 'rgba(234, 179, 8, 0.5)',
          color: '#EAB308',
          icon: <AlertTriangle size={12} className="inline mr-1" />
        };
      default:
        return {
          bg: 'rgba(16, 185, 129, 0.15)',
          border: 'rgba(16, 185, 129, 0.5)',
          color: '#10B981',
          icon: <ShieldCheck size={12} className="inline mr-1" />
        };
    }
  };

  return (
    <div
      className="timeline-glass-card"
      style={{
        background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
        backdropFilter: 'blur(20px) saturate(140%)',
        WebkitBackdropFilter: 'blur(20px) saturate(140%)',
        border: '1px solid rgba(56, 189, 248, 0.22)',
        borderTop: '1px solid rgba(255, 255, 255, 0.28)',
        borderRadius: '10px',
        padding: '16px',
        marginTop: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px rgba(34, 211, 238, 0.04)',
      }}
    >
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid rgba(56, 189, 248, 0.15)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '8px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.16)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              color: '#38BDF8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(56, 189, 248, 0.25)',
            }}
          >
            <Gauge size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#F1F5F9', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Multi-Horizon Flood Risk Outlook
              </h3>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(56, 189, 248, 0.18)',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.35)',
                }}
              >
                ERA5 ML Calibrated
              </span>
            </div>
            <p style={{ fontSize: '11px', color: '#CBD5E1', margin: '3px 0 0 0' }}>
              Isotonically calibrated risk assessment across standard hydrometeorological forecast windows.
            </p>
          </div>
        </div>

        {/* Peak Forecast Callout */}
        {peakRisk && (
          <div
            className="timeline-glass-subcard"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              background: 'rgba(8, 24, 46, 0.50)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderTop: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={14} color="#38BDF8" />
              <span style={{ fontSize: '11px', color: '#CBD5E1' }}>Peak Threat Window:</span>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#F8FAFC', fontFamily: 'monospace' }}>
                +{peakRisk.lead_hours}h ({peakRisk.horizon})
              </span>
            </div>
            <div style={{ height: '14px', width: '1px', background: 'rgba(56, 189, 248, 0.3)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: '#CBD5E1' }}>Peak Score:</span>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 800,
                  fontFamily: 'monospace',
                  color: getTierBadgeStyle(peakRisk.risk_tier).color,
                }}
              >
                {peakRisk.risk_score.toFixed(1)}/100
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 6 Horizon Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '10px',
          marginTop: '14px',
        }}
      >
        {horizonKeys.map((key) => {
          const hData = horizons[key];
          // Fallback to forecast_horizons if outlook horizon not populated
          const fallbackH = data.forecast_horizons.find(f => f.horizon_hours === parseInt(key.replace('h', '')));
          
          const leadHours = hData?.lead_hours ?? parseInt(key.replace('h', ''));
          const tier = hData?.risk_tier || fallbackH?.risk_tier || 'LOW';
          const badge = getTierBadgeStyle(tier);
          const prob = hData ? (hData.calibrated_probability * 100) : ((fallbackH?.calibrated_flood_probability ?? 0.15) * 100);
          const score = hData?.risk_score ?? (fallbackH?.operational_risk_score ?? 20.0);
          const rain = hData?.projected_accumulated_rain_mm ?? (fallbackH?.cumulative_precipitation_mm ?? 0.0);
          const rainDisplay = typeof rain === 'number' ? `${rain.toFixed(1)} mm` : String(rain);
          const isExceeded = hData?.threshold_exceeded ?? (score >= 50.0);

          return (
            <div
              key={key}
              className="timeline-glass-subcard"
              style={{
                background: 'rgba(8, 24, 46, 0.42)',
                backdropFilter: 'blur(12px) saturate(130%)',
                WebkitBackdropFilter: 'blur(12px) saturate(130%)',
                border: isExceeded ? `1px solid ${badge.border}` : '1px solid rgba(56, 189, 248, 0.18)',
                borderTop: '1px solid rgba(255, 255, 255, 0.18)',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.25)',
              }}
            >
              {/* Card Top: Horizon + Badge */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                    +{leadHours}h
                  </span>
                  <span style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 500 }}>
                    lead
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: badge.bg,
                    border: `1px solid ${badge.border}`,
                    color: badge.color,
                    display: 'flex',
                    alignItems: 'center',
                    boxShadow: `0 0 6px ${badge.border}`,
                  }}
                >
                  {badge.icon}
                  {tier}
                </div>
              </div>

              {/* Metrics Middle */}
              <div style={{ margin: '10px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '10px', color: '#94A3B8' }}>Probability:</span>
                  <span style={{ fontSize: '15px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                    {prob.toFixed(1)}%
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '4px' }}>
                  <span style={{ fontSize: '10px', color: '#94A3B8' }}>Risk Score:</span>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: badge.color, fontFamily: 'monospace' }}>
                    {score.toFixed(1)}/100
                  </span>
                </div>
              </div>

              {/* Card Bottom: Cumulative Rain & Status */}
              <div
                style={{
                  borderTop: '1px solid rgba(56, 189, 248, 0.15)',
                  paddingTop: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '10px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#CBD5E1' }}>
                  <CloudRain size={11} color="#38BDF8" />
                  <span>{rainDisplay}</span>
                </div>
                <span
                  style={{
                    fontWeight: 600,
                    color: isExceeded ? '#EF4444' : '#10B981',
                  }}
                >
                  {isExceeded ? 'Exceeds Tau' : 'Safe'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
