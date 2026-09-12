import React from 'react';
import {
  HydrologicalAnalysis,
} from '../../types';
import {
  Waves,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Droplet,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
} from 'lucide-react';

interface HydrologicalAnalysisCardProps {
  hydrology: HydrologicalAnalysis;
}

export const HydrologicalAnalysisCard: React.FC<HydrologicalAnalysisCardProps> = ({
  hydrology,
}) => {
  const isGaugeAvailable =
    hydrology.current_stage_meters !== null && hydrology.current_stage_meters !== undefined;

  const currentStage = hydrology.current_stage_meters || 0;
  const warningMark = hydrology.warning_mark_meters || (currentStage * 1.1);
  const dangerMark = hydrology.danger_mark_meters || (currentStage * 1.25);
  const marginToDanger = hydrology.margin_to_danger_meters;
  const isOverDanger = marginToDanger !== null && marginToDanger !== undefined && marginToDanger > 0;

  // Derive authoritative freshness badge
  const getHydrologyFreshnessBadge = () => {
    if (!isGaugeAvailable) {
      return {
        label: 'UNGAUGED BASIN',
        color: '#94A3B8',
        bg: 'rgba(100, 116, 139, 0.18)',
        border: 'rgba(100, 116, 139, 0.35)',
        icon: <Waves size={13} />,
      };
    }
    const state = (hydrology.data_state || '').toUpperCase();
    if (state.includes('BULLETIN')) {
      return {
        label: 'VERIFIED CWC BULLETIN',
        color: '#F59E0B',
        bg: 'rgba(245, 158, 11, 0.15)',
        border: 'rgba(245, 158, 11, 0.4)',
        icon: <FileText size={13} />,
      };
    }
    if (state === 'LIVE') {
      return {
        label: 'LIVE SENSOR TELEMETRY',
        color: '#10B981',
        bg: 'rgba(16, 185, 129, 0.15)',
        border: 'rgba(16, 185, 129, 0.4)',
        icon: <CheckCircle2 size={13} />,
      };
    }
    return {
      label: 'AUTHENTICATED GAUGE',
      color: '#2DD4BF',
      bg: 'rgba(45, 212, 191, 0.15)',
      border: 'rgba(45, 212, 191, 0.35)',
      icon: <CheckCircle2 size={13} />,
    };
  };

  const badge = getHydrologyFreshnessBadge();

  // Format bulletin timestamp in IST
  const formattedBulletinTime = hydrology.bulletin_timestamp
    ? `${new Date(hydrology.bulletin_timestamp).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        timeZone: 'Asia/Kolkata',
      })}, ${new Date(hydrology.bulletin_timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'Asia/Kolkata',
      })} IST`
    : null;

  // Adaptive gauge scale (handles MSL datum rivers like Ganga 50-65m and mountain streams 0-10m)
  const isMslDatum = warningMark > 25;
  const minScale = isMslDatum ? Math.max(0, Math.floor(Math.min(currentStage, warningMark) - 6)) : 0;
  const maxScale = isMslDatum
    ? Math.ceil(Math.max(dangerMark, currentStage) + 4)
    : Math.max(dangerMark * 1.15, currentStage * 1.1, 10);
  const scaleRange = Math.max(1, maxScale - minScale);

  const stagePct = Math.min(100, Math.max(0, ((currentStage - minScale) / scaleRange) * 100));
  const warningPct = Math.min(100, Math.max(0, ((warningMark - minScale) / scaleRange) * 100));
  const dangerPct = Math.min(100, Math.max(0, ((dangerMark - minScale) / scaleRange) * 100));

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
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px rgba(34, 211, 238, 0.04)',
      }}
    >
      {/* Header: Basin & Station */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {hydrology.telemetry_source || 'Central Water Commission (CWC) Gauge Network'}
          </div>
          <div style={{ fontSize: '16px', color: '#F1F5F9', fontWeight: 700, marginTop: '2px' }}>
            Hydrological River Dynamics & Gauge Analytics
          </div>
          {formattedBulletinTime && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#38BDF8', marginTop: '3px' }}>
              <Clock size={12} />
              <span>CWC Official Bulletin Date: {formattedBulletinTime}</span>
            </div>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '6px',
            background: badge.bg,
            color: badge.color,
            fontSize: '11px',
            fontWeight: 700,
            border: `1px solid ${badge.border}`,
            boxShadow: `0 0 10px ${badge.bg}`,
          }}
        >
          {badge.icon}
          <span>{badge.label}</span>
        </div>
      </div>

      {/* Official CWC Bulletin Provenance Notice */}
      {hydrology.data_state === 'VERIFIED_BULLETIN_CACHE' && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            borderRadius: '6px',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            fontSize: '11px',
            color: '#FCD34D',
          }}
        >
          <AlertCircle size={14} style={{ flexShrink: 0, color: '#F59E0B' }} />
          <span>
            <strong>Authentic CWC Bulletin:</strong> River stage figures represent verified CWC gauge observations for this basin. Bulletins are officially gazetted at standard diurnal intervals (typically 08:00 &amp; 19:00 IST), not automated per-second telemetry.
          </span>
        </div>
      )}

      {!isGaugeAvailable ? (
        <div
          className="timeline-glass-subcard"
          style={{
            background: 'rgba(8, 24, 46, 0.45)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '8px',
            padding: '24px 16px',
            textAlign: 'center',
            color: '#CBD5E1',
            fontSize: '13px',
          }}
        >
          <p style={{ margin: 0, fontWeight: 600, color: '#F1F5F9' }}>
            No active river gauge station registered in this mountain watershed buffer.
          </p>
          <p style={{ margin: '6px 0 0 0', fontSize: '11px', color: '#94A3B8' }}>
            River weight is dynamically normalized out of composite risk; pluvial and antecedent saturation drive threat projections.
          </p>
        </div>
      ) : (
        <>
          {/* Main Gauge Summary Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
            {/* River Name & Station */}
            <div
              className="timeline-glass-subcard"
              style={{
                background: 'rgba(8, 24, 46, 0.42)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(56, 189, 248, 0.18)',
                borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{ fontSize: '10px', color: '#94A3B8' }}>River & Station</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#F1F5F9', marginTop: '2px' }}>
                {hydrology.river_name}
              </div>
              <div style={{ fontSize: '11px', color: '#CBD5E1' }}>
                {hydrology.gauge_station_name}
              </div>
            </div>

            {/* Current Stage */}
            <div
              className="timeline-glass-subcard"
              style={{
                background: 'rgba(8, 24, 46, 0.42)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(56, 189, 248, 0.18)',
                borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{ fontSize: '10px', color: '#94A3B8' }}>Observed Water Level</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#2DD4BF', fontFamily: 'monospace', marginTop: '2px' }}>
                {currentStage.toFixed(2)} m
              </div>
              <div style={{ fontSize: '10px', color: '#CBD5E1' }}>
                Warning: {warningMark.toFixed(2)}m | Danger: {dangerMark.toFixed(2)}m
              </div>
            </div>

            {/* Margin to Danger Mark */}
            <div
              className="timeline-glass-subcard"
              style={{
                background: 'rgba(8, 24, 46, 0.42)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                padding: '10px 12px',
                borderRadius: '6px',
                border: `1px solid ${isOverDanger ? 'rgba(239, 68, 68, 0.45)' : 'rgba(56, 189, 248, 0.18)'}`,
                borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{ fontSize: '10px', color: '#94A3B8' }}>Margin to Danger Mark</div>
              <div
                style={{
                  fontSize: '15px',
                  fontWeight: 800,
                  color: isOverDanger ? '#EF4444' : '#2DD4BF',
                  fontFamily: 'monospace',
                  marginTop: '2px',
                }}
              >
                {marginToDanger !== null && marginToDanger !== undefined
                  ? isOverDanger
                    ? `+${marginToDanger.toFixed(2)}m OVER DANGER`
                    : `${Math.abs(marginToDanger).toFixed(2)}m below danger mark`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '10px', color: isOverDanger ? '#FCA5A5' : '#CBD5E1' }}>
                {isOverDanger ? 'Active Channel Inundation' : 'Within Channel Banks'}
              </div>
            </div>

            {/* Surge Rate & Hydraulic Trend */}
            <div
              className="timeline-glass-subcard"
              style={{
                background: 'rgba(8, 24, 46, 0.42)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                padding: '10px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(56, 189, 248, 0.18)',
                borderTop: '1px solid rgba(255, 255, 255, 0.15)',
              }}
            >
              <div style={{ fontSize: '10px', color: '#94A3B8' }}>Rate of Rise / Hydraulic Trend</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#F1F5F9', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {hydrology.hydraulic_trend === 'RISING' ? (
                  <ArrowUpRight size={16} color="#F59E0B" />
                ) : hydrology.hydraulic_trend === 'FALLING' ? (
                  <ArrowDownRight size={16} color="#10B981" />
                ) : (
                  <Minus size={16} color="#CBD5E1" />
                )}
                <span>
                  {hydrology.rate_of_rise_m_per_hr !== null && hydrology.rate_of_rise_m_per_hr !== undefined
                    ? `${hydrology.rate_of_rise_m_per_hr > 0 ? '+' : ''}${hydrology.rate_of_rise_m_per_hr.toFixed(2)} m/h`
                    : 'Steady'}
                </span>
              </div>
              <div style={{ fontSize: '10px', color: '#CBD5E1' }}>
                Trend: {hydrology.hydraulic_trend}
              </div>
            </div>
          </div>

          {/* Visual Hydraulic Meter Bar */}
          <div
            className="timeline-glass-subcard"
            style={{
              background: 'rgba(8, 24, 46, 0.40)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              padding: '12px 14px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.18)',
              borderTop: '1px solid rgba(255, 255, 255, 0.15)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '6px' }}>
              <span style={{ color: '#CBD5E1' }}>Water Level Progression vs Official CWC Marks:</span>
              <span style={{ color: '#F1F5F9', fontWeight: 600 }}>
                {isMslDatum ? `Scale: ${minScale}m – ${maxScale}m MSL` : `Scale Max: ${maxScale.toFixed(1)}m`}
              </span>
            </div>

            {/* Multi-Marker Progress Bar */}
            <div style={{ position: 'relative', width: '100%', height: '18px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden' }}>
              {/* Warning Level Marker Line */}
              <div
                style={{
                  position: 'absolute',
                  left: `${warningPct}%`,
                  top: 0,
                  bottom: 0,
                  width: '2px',
                  background: '#EAB308',
                  zIndex: 2,
                }}
                title={`Warning Mark: ${warningMark.toFixed(2)}m`}
              />

              {/* Danger Level Marker Line */}
              <div
                style={{
                  position: 'absolute',
                  left: `${dangerPct}%`,
                  top: 0,
                  bottom: 0,
                  width: '2px',
                  background: '#EF4444',
                  zIndex: 2,
                }}
                title={`Danger Mark: ${dangerMark.toFixed(2)}m`}
              />

              {/* Current Water Stage Fill */}
              <div
                style={{
                  height: '100%',
                  width: `${stagePct}%`,
                  background: isOverDanger
                    ? 'linear-gradient(90deg, #2DD4BF 0%, #EAB308 60%, #EF4444 100%)'
                    : 'linear-gradient(90deg, #0EA5E9 0%, #2DD4BF 100%)',
                  transition: 'width 0.5s ease',
                  position: 'relative',
                  zIndex: 1,
                }}
              />
            </div>

            {/* Markers Label Row */}
            <div style={{ position: 'relative', width: '100%', height: '16px', marginTop: '4px', fontSize: '9px' }}>
              <span style={{ position: 'absolute', left: '0%', color: '#64748B' }}>{minScale}m</span>
              <span style={{ position: 'absolute', left: `${warningPct}%`, transform: 'translateX(-50%)', color: '#EAB308', fontWeight: 700 }}>
                Warning ({warningMark.toFixed(1)}m)
              </span>
              <span style={{ position: 'absolute', left: `${dangerPct}%`, transform: 'translateX(-50%)', color: '#EF4444', fontWeight: 700 }}>
                Danger ({dangerMark.toFixed(1)}m)
              </span>
              <span style={{ position: 'absolute', right: '0%', color: '#64748B' }}>{maxScale}m</span>
            </div>
          </div>

          {/* Upstream Dam Discharge Info (if available) */}
          {hydrology.upstream_dam_discharge_cumec !== null && hydrology.upstream_dam_discharge_cumec !== undefined && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(15, 23, 42, 0.5)',
                padding: '8px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#CBD5E1',
                border: '1px solid rgba(51, 65, 85, 0.4)',
              }}
            >
              <Droplet size={14} color="#38BDF8" />
              <span>
                <strong>Upstream Reservoir Discharge:</strong> {hydrology.dam_name || 'Upstream Dam'}:{' '}
                <strong style={{ color: '#38BDF8', fontFamily: 'monospace' }}>{hydrology.upstream_dam_discharge_cumec.toLocaleString()} cumec</strong> outflow reported.
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
};
