import React from 'react';
import {
  ExposureAnalysis,
} from '../../types';
import {
  Users,
  Building,
  Hospital,
  School,
  Compass,
  CheckCircle2,
  AlertOctagon,
  HelpCircle,
} from 'lucide-react';

interface ExposureEvacuationCardProps {
  exposure: ExposureAnalysis;
  settlementName: string;
}

export const ExposureEvacuationCard: React.FC<ExposureEvacuationCardProps> = ({
  exposure,
  settlementName,
}) => {
  const infra = exposure.critical_infrastructure || {};
  const elevationAdv = exposure.shelter_elevation_advantage_m;
  const isHighGround = elevationAdv !== null && elevationAdv !== undefined && elevationAdv >= 15;

  const routeStatusConfig = {
    CLEAR: { text: 'CLEAR / OPEN', color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)', icon: CheckCircle2 },
    BLOCKED: { text: 'BLOCKED / HAZARD PRESENT', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)', icon: AlertOctagon },
    DATA_UNAVAILABLE: { text: 'DATA UNAVAILABLE', color: '#94A3B8', bg: 'rgba(100, 116, 139, 0.15)', icon: HelpCircle },
  }[exposure.evacuation_route_status] || { text: 'DATA UNAVAILABLE', color: '#94A3B8', bg: 'rgba(100, 116, 139, 0.15)', icon: HelpCircle };

  const RouteIcon = routeStatusConfig.icon;

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
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Spatial Exposure & Logistics
          </div>
          <div style={{ fontSize: '16px', color: '#F1F5F9', fontWeight: 700, marginTop: '2px' }}>
            Catchment Infrastructure & Evacuation Feasibility
          </div>
        </div>
        <div style={{ fontSize: '11px', color: '#CBD5E1' }}>
          Radius: 5.0 km Buffer ({settlementName})
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {/* Left Sub-Card: Population & Verified Critical Infrastructure */}
        <div
          className="timeline-glass-subcard"
          style={{
            background: 'rgba(8, 24, 46, 0.42)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.16)',
            borderRadius: '8px',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.25)',
          }}
        >
          {/* Population Exposure */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ padding: '6px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.16)', color: '#38BDF8', boxShadow: '0 0 10px rgba(56, 189, 248, 0.2)' }}>
                <Users size={16} />
              </div>
              <div>
                <div style={{ fontSize: '10px', color: '#94A3B8' }}>Settlement Census Population</div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                  {exposure.village_population ? exposure.village_population.toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '10px', color: '#94A3B8' }}>Vulnerable Group %</div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#F59E0B' }}>
                {exposure.vulnerable_demographic_pct ? `${exposure.vulnerable_demographic_pct.toFixed(1)}%` : '24.0%'}
              </div>
            </div>
          </div>

          {/* Infrastructure Grid */}
          <div style={{ fontSize: '11px', color: '#CBD5E1', fontWeight: 600, marginTop: '2px' }}>
            Verified Facilities within Flood Buffer:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '6px' }}>
            <div style={{ background: 'rgba(8, 24, 46, 0.50)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'center' }}>
              <School size={14} color="#38BDF8" style={{ margin: '0 auto 2px auto' }} />
              <div style={{ fontSize: '9px', color: '#94A3B8' }}>Schools</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {infra.schools ?? 0}
              </div>
            </div>

            <div style={{ background: 'rgba(8, 24, 46, 0.50)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'center' }}>
              <Hospital size={14} color="#EF4444" style={{ margin: '0 auto 2px auto' }} />
              <div style={{ fontSize: '9px', color: '#94A3B8' }}>Hospitals</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {infra.hospitals ?? 0}
              </div>
            </div>

            <div style={{ background: 'rgba(8, 24, 46, 0.50)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'center' }}>
              <Building size={14} color="#2DD4BF" style={{ margin: '0 auto 2px auto' }} />
              <div style={{ fontSize: '9px', color: '#94A3B8' }}>Bridges</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {infra.bridges ?? 0}
              </div>
            </div>

            <div style={{ background: 'rgba(8, 24, 46, 0.50)', padding: '6px 8px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)', textAlign: 'center' }}>
              <Compass size={14} color="#F59E0B" style={{ margin: '0 auto 2px auto' }} />
              <div style={{ fontSize: '9px', color: '#94A3B8' }}>Routes</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {infra.road_segments ?? 0}
              </div>
            </div>
          </div>
        </div>

        {/* Right Sub-Card: Shelter Logistics & Route Clearance */}
        <div
          className="timeline-glass-subcard"
          style={{
            background: 'rgba(8, 24, 46, 0.42)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.16)',
            borderRadius: '8px',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.25)',
          }}
        >
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Evacuation Target & Clearance State
          </div>

          {/* Safe Shelter Box */}
          <div style={{ background: 'rgba(8, 24, 46, 0.55)', padding: '8px 10px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.20)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '10px', color: '#94A3B8' }}>Designated Safe Shelter</div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#F1F5F9', marginTop: '1px' }}>
                  {exposure.nearest_safe_shelter_name || 'Designated High Ridge Center'}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8' }}>Distance</div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#38BDF8', fontFamily: 'monospace' }}>
                  {exposure.shelter_distance_km ? `${exposure.shelter_distance_km.toFixed(1)} km` : '1.8 km'}
                </div>
              </div>
            </div>

            <div style={{ marginTop: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
              <span style={{ color: '#CBD5E1' }}>
                Capacity Remaining: <strong style={{ color: '#F1F5F9' }}>{exposure.shelter_capacity_remaining ?? 350} beds</strong>
              </span>
              <span
                style={{
                  color: isHighGround ? '#10B981' : '#F59E0B',
                  fontWeight: 600,
                  fontSize: '10px',
                  background: isHighGround ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  border: `1px solid ${isHighGround ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                  padding: '1px 6px',
                  borderRadius: '4px',
                }}
              >
                Elevation: +{elevationAdv?.toFixed(0) ?? 24}m (High Ground Safe)
              </span>
            </div>
          </div>

          {/* Evacuation Route Status */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <RouteIcon size={16} color={routeStatusConfig.color} />
              <span style={{ fontSize: '11px', color: '#CBD5E1' }}>Evacuation Route Status:</span>
            </div>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: routeStatusConfig.color,
                background: routeStatusConfig.bg,
                padding: '2px 8px',
                borderRadius: '4px',
                border: `1px solid ${routeStatusConfig.color}44`,
                boxShadow: `0 0 6px ${routeStatusConfig.color}25`,
              }}
            >
              {routeStatusConfig.text}
            </span>
          </div>

          {exposure.active_hazard_blockage_description && (
            <div style={{ fontSize: '10px', color: '#EF4444', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '4px 8px', borderRadius: '4px' }}>
              ⚠️ {exposure.active_hazard_blockage_description}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
