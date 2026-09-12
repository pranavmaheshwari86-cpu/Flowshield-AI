import React from 'react';
import {
  MapPin,
  RefreshCw,
  Activity,
  Clock,
} from 'lucide-react';
import { TimelineLocationHierarchy } from '../../types';

interface TimelineHeaderProps {
  locations: TimelineLocationHierarchy | null;
  selectedState: string;
  selectedDistrict: string;
  selectedVillageId: string;
  onSelectLocation: (state: string, district: string, villageId: string) => void;
  activeMode: 'LIVE' | 'DEMO';
  overallHealth: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED' | 'COMPROMISED';
  isRefreshing: boolean;
  onRefresh: () => void;
  lastUpdated: string;
  settlementName: string;
  elevationMeters: number;
  riverBasin: string;
}

export const TimelineHeader: React.FC<TimelineHeaderProps> = ({
  locations,
  selectedState,
  selectedDistrict,
  selectedVillageId,
  onSelectLocation,
  // activeMode intentionally removed (DATA_MODE badge removed)
  overallHealth,
  isRefreshing,
  onRefresh,
  lastUpdated,
  settlementName,
  elevationMeters,
  riverBasin,
}) => {
  // Current state object
  const currentState = locations?.states.find((s) => s.name === selectedState) || locations?.states[0];
  const currentDistrict =
    currentState?.districts.find((d) => d.name === selectedDistrict) || currentState?.districts[0];

  const handleStateChange = (newState: string) => {
    const st = locations?.states.find((s) => s.name === newState);
    if (!st || st.districts.length === 0) return;
    const dist = st.districts[0];
    const vill = dist.settlements[0];
    onSelectLocation(st.name, dist.name, vill ? vill.id : '');
  };

  const handleDistrictChange = (newDistrict: string) => {
    if (!currentState) return;
    const dist = currentState.districts.find((d) => d.name === newDistrict);
    if (!dist || dist.settlements.length === 0) return;
    const vill = dist.settlements[0];
    onSelectLocation(currentState.name, dist.name, vill ? vill.id : '');
  };

  const handleVillageChange = (newVillageId: string) => {
    if (!currentState || !currentDistrict) return;
    onSelectLocation(currentState.name, currentDistrict.name, newVillageId);
  };

  const healthBadgeConfig = {
    OPTIMAL: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981', border: 'rgba(16, 185, 129, 0.3)' },
    ACCEPTABLE: { bg: 'rgba(56, 189, 248, 0.15)', text: '#38BDF8', border: 'rgba(56, 189, 248, 0.3)' },
    DEGRADED: { bg: 'rgba(245, 158, 11, 0.15)', text: '#F59E0B', border: 'rgba(245, 158, 11, 0.3)' },
    COMPROMISED: { bg: 'rgba(239, 68, 68, 0.15)', text: '#EF4444', border: 'rgba(239, 68, 68, 0.3)' },
  }[overallHealth] || { bg: 'rgba(100, 116, 139, 0.15)', text: '#94A3B8', border: 'rgba(100, 116, 139, 0.3)' };

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
        padding: '12px 18px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px rgba(34, 211, 238, 0.04)',
      }}
    >
      {/* Left: Location Selection Cascades */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.16)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38BDF8',
              boxShadow: '0 0 10px rgba(56, 189, 248, 0.2)',
            }}
          >
            <MapPin size={18} />
          </div>
          <div>
            <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
              Spatial Horizon Target
            </div>
            <div style={{ fontSize: '15px', color: '#F1F5F9', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>{settlementName}</span>
              <span style={{ fontSize: '11px', color: '#38BDF8', background: 'rgba(14, 165, 233, 0.16)', padding: '1px 6px', borderRadius: '4px', border: '1px solid rgba(14, 165, 233, 0.35)' }}>
                {riverBasin}
              </span>
              <span style={{ fontSize: '11px', color: '#CBD5E1' }}>
                Alt: {elevationMeters}m
              </span>
            </div>
          </div>
        </div>

        {/* Dynamic Cascading Selectors */}
        {locations && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* State Select */}
            <select
              value={selectedState}
              onChange={(e) => handleStateChange(e.target.value)}
              aria-label="Filter by State"
              style={{
                background: 'rgba(8, 24, 48, 0.70)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                color: '#F1F5F9',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderTop: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.25)',
              }}
            >
              {locations.states.map((st) => (
                <option key={st.name} value={st.name} style={{ background: '#0b172a', color: '#F1F5F9' }}>
                  {st.name}
                </option>
              ))}
            </select>

            {/* District Select */}
            <select
              value={selectedDistrict}
              onChange={(e) => handleDistrictChange(e.target.value)}
              aria-label="Filter by District"
              style={{
                background: 'rgba(8, 24, 48, 0.70)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                color: '#F1F5F9',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderTop: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                outline: 'none',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.25)',
              }}
            >
              {currentState?.districts.map((dist) => (
                <option key={dist.name} value={dist.name} style={{ background: '#0b172a', color: '#F1F5F9' }}>
                  {dist.name}
                </option>
              ))}
            </select>

            {/* Settlement Select */}
            <select
              value={selectedVillageId}
              onChange={(e) => handleVillageChange(e.target.value)}
              aria-label="Filter by Settlement or Watershed"
              style={{
                background: 'rgba(8, 28, 56, 0.75)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                color: '#38BDF8',
                border: '1px solid rgba(56, 189, 248, 0.45)',
                borderTop: '1px solid rgba(255, 255, 255, 0.25)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer',
                boxShadow: '0 0 10px rgba(56, 189, 248, 0.15)',
              }}
            >
              {currentDistrict?.settlements.map((vill) => (
                <option key={vill.id} value={vill.id} style={{ background: '#0b172a', color: '#38BDF8' }}>
                  {vill.name} ({vill.elevation_m}m)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right: Mode, Quality & Refresh Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>


        {/* SLA Telemetry Quality Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            background: healthBadgeConfig.bg,
            color: healthBadgeConfig.text,
            border: `1px solid ${healthBadgeConfig.border}`,
          }}
          title="Telemetry freshness SLA rating across IMD, ECMWF, CWC & ERA5 streams"
        >
          <Activity size={12} />
          <span>SLA: {overallHealth}</span>
        </div>

        {/* Last Updated Timestamp */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            fontSize: '11px',
            color: '#94A3B8',
            padding: '4px 8px',
          }}
        >
          <Clock size={12} />
          <span>{lastUpdated ? new Date(lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Syncing...'}</span>
        </div>

        {/* Force Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: isRefreshing ? '#1e293b' : 'rgba(14, 165, 233, 0.15)',
            border: '1px solid rgba(14, 165, 233, 0.4)',
            color: '#38BDF8',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: isRefreshing ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease',
          }}
          title="Force immediate upstream telemetry re-query"
        >
          <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
          <span>{isRefreshing ? 'Syncing...' : 'Sync Telemetry'}</span>
        </button>
      </div>
    </div>
  );
};
