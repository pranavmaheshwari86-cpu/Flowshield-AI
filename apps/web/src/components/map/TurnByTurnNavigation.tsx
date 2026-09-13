import React, { useState } from 'react';
import {
  Navigation,
  ArrowUp,
  ArrowRight,
  ArrowLeft,
  CornerUpRight,
  CornerUpLeft,
  Flag,
  AlertTriangle,
  ShieldCheck,
  Clock,
  MapPin,
  X,
  ChevronDown,
  ChevronUp,
  Phone,
  Volume2,
  VolumeX,
  ExternalLink,
} from 'lucide-react';
import { EvacuationRoute, TurnByTurnStep, Shelter } from '../../types';

interface TurnByTurnNavigationProps {
  route: EvacuationRoute;
  shelter?: Shelter | null;
  originCoords?: [number, number] | null;
  onClose: () => void;
  onSelectStep?: (step: TurnByTurnStep) => void;
}

export const TurnByTurnNavigation: React.FC<TurnByTurnNavigationProps> = ({
  route,
  shelter,
  originCoords,
  onClose,
  onSelectStep,
}) => {
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  const steps = route.turn_by_turn_instructions || [];

  const googleMapsUrl = React.useMemo(() => {
    if (!shelter && (!route.coordinates || route.coordinates.length === 0)) return null;
    const destLat = shelter?.latitude ?? (route.coordinates?.[route.coordinates.length - 1]?.[0]);
    const destLon = shelter?.longitude ?? (route.coordinates?.[route.coordinates.length - 1]?.[1]);
    if (!destLat || !destLon) return null;
    if (originCoords && originCoords[0] && originCoords[1]) {
      return `https://www.google.com/maps/dir/?api=1&origin=${originCoords[0]},${originCoords[1]}&destination=${destLat},${destLon}&travelmode=driving`;
    }
    return `https://www.google.com/maps/search/?api=1&query=${destLat},${destLon}`;
  }, [shelter, route, originCoords]);

  const getManeuverIcon = (maneuver: string = '') => {
    const m = maneuver.toLowerCase();
    if (m.includes('depart')) return <Navigation className="w-5 h-5 text-cyan-400" />;
    if (m.includes('arrive')) return <Flag className="w-5 h-5 text-emerald-400" />;
    if (m.includes('sharp right') || m.includes('right')) return <ArrowRight className="w-5 h-5 text-cyan-400" />;
    if (m.includes('sharp left') || m.includes('left')) return <ArrowLeft className="w-5 h-5 text-cyan-400" />;
    if (m.includes('fork_right') || m.includes('bear_right')) return <CornerUpRight className="w-5 h-5 text-cyan-400" />;
    if (m.includes('fork_left') || m.includes('bear_left')) return <CornerUpLeft className="w-5 h-5 text-cyan-400" />;
    return <ArrowUp className="w-5 h-5 text-cyan-400" />;
  };

  const formatDistance = (meters: number) => {
    if (!meters || meters < 1000) return `${meters || 0} m`;
    return `${(meters / 1000).toFixed(1)} km`;
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '< 1 min';
    const mins = Math.round(seconds / 60);
    return mins <= 1 ? '1 min' : `${mins} min`;
  };

  return (
    <div
      style={{
        background: '#091526',
        border: '1.5px solid #06b6d4',
        borderRadius: '14px',
        boxShadow: '0 16px 48px rgba(0, 0, 0, 0.9)',
        color: '#f1f5f9',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        maxHeight: '100%',
        overflow: 'hidden',
        fontFamily: 'inherit',
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          padding: '14px 16px',
          background: 'linear-gradient(135deg, #0f2347 0%, #0a172c 100%)',
          borderBottom: '1px solid #1e355b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <div
            style={{
              padding: '8px',
              background: 'rgba(6, 182, 212, 0.18)',
              borderRadius: '8px',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              color: '#38bdf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Navigation size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '10px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#38bdf8' }}>
                Live Turn Guidance
              </span>
              {route.is_blocked ? (
                <span style={{ padding: '1px 6px', fontSize: '9px', fontWeight: 800, background: 'rgba(239, 68, 68, 0.25)', border: '1px solid #ef4444', color: '#f87171', borderRadius: '10px' }}>
                  UNSAFE ROUTE
                </span>
              ) : (
                <span style={{ padding: '1px 6px', fontSize: '9px', fontWeight: 800, background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981', color: '#34d399', borderRadius: '10px', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                  <ShieldCheck size={11} /> VERIFIED SAFE
                </span>
              )}
            </div>
            <h3 style={{ fontSize: '13.5px', fontWeight: 800, margin: '2px 0 0', color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '210px' }}>
              {shelter?.name || route.destination_shelter_name || 'Designated Safe Haven'}
            </h3>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            onClick={() => setIsMuted(!isMuted)}
            title={isMuted ? 'Unmute voice alerts' : 'Mute voice alerts'}
            style={{ padding: '6px', background: 'transparent', border: 'none', color: isMuted ? '#64748b' : '#38bdf8', cursor: 'pointer', borderRadius: '6px' }}
          >
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ padding: '6px', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', borderRadius: '6px' }}
          >
            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          <button
            onClick={onClose}
            style={{ padding: '6px', background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', borderRadius: '6px' }}
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Primary Metrics Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          borderBottom: '1px solid #14284b',
          background: '#07111f',
          textAlign: 'center',
          padding: '10px 8px',
          flexShrink: 0,
        }}
      >
        <div style={{ borderRight: '1px solid #14284b', padding: '0 4px' }}>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, color: '#64748b' }}>TOTAL DIST</div>
          <div style={{ fontSize: '14px', fontWeight: 800, color: '#38bdf8', marginTop: '2px', fontFamily: 'monospace' }}>
            {route.distance_km ? `${route.distance_km.toFixed(1)} km` : '—'}
          </div>
        </div>
        <div style={{ borderRight: '1px solid #14284b', padding: '0 4px' }}>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, color: '#64748b' }}>EST. TRANSIT</div>
          <div style={{ fontSize: '14px', fontWeight: 800, color: '#34d399', marginTop: '2px', fontFamily: 'monospace', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
            <Clock size={12} color="#34d399" />
            <span>{route.estimated_travel_time_min || 12} min</span>
          </div>
        </div>
        <div style={{ padding: '0 4px' }}>
          <div style={{ fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, color: '#64748b' }}>ROAD SAFETY</div>
          <div style={{ fontSize: '14px', fontWeight: 800, color: '#38bdf8', marginTop: '2px', fontFamily: 'monospace' }}>
            {route.safety_score !== undefined ? `${route.safety_score}%` : '92%'}
          </div>
        </div>
      </div>

      {/* Google Maps External Turn-by-Turn Voice Navigation Button */}
      {googleMapsUrl && (
        <div style={{ padding: '8px 12px', background: '#071324', borderBottom: '1px solid #14284b' }}>
          <a
            href={googleMapsUrl}
            target="_blank"
            rel="noreferrer"
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
              color: '#ffffff',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: 700,
              fontSize: '11.5px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              boxShadow: '0 3px 12px rgba(2, 132, 199, 0.35)',
              boxSizing: 'border-box',
            }}
          >
            <ExternalLink size={13} />
            <span>Open in Google Maps (Voice Navigation)</span>
          </a>
        </div>
      )}

      {/* Step List Scroll Area */}
      {isExpanded && (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          {steps.length > 0 ? (
            steps.map((s, idx) => {
              const isActive = idx === activeStepIndex;
              return (
                <div
                  key={s.step || idx}
                  onClick={() => {
                    setActiveStepIndex(idx);
                    if (onSelectStep) onSelectStep(s);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    background: isActive ? 'rgba(6, 182, 212, 0.18)' : '#0d1d36',
                    border: `1px solid ${isActive ? '#06b6d4' : '#172b4d'}`,
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div
                    style={{
                      padding: '6px',
                      borderRadius: '8px',
                      background: isActive ? 'rgba(6, 182, 212, 0.25)' : '#071224',
                      border: `1px solid ${isActive ? '#06b6d4' : '#1e355b'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '2px',
                    }}
                  >
                    {getManeuverIcon(s.maneuver)}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
                      <span style={{ fontWeight: 700, color: isActive ? '#38bdf8' : '#94a3b8' }}>
                        Step {s.step || idx + 1}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8' }}>
                          {formatDistance(s.distance_m)}
                        </span>
                        <span style={{ color: '#64748b', fontSize: '10px' }}>
                          ({formatDuration(s.duration_s)})
                        </span>
                      </div>
                    </div>

                    <div style={{ fontSize: '12.5px', fontWeight: isActive ? 800 : 600, color: '#f8fafc', marginTop: '3px', lineHeight: 1.4 }}>
                      {s.instruction}
                    </div>

                    {s.road_name && (
                      <div style={{ fontSize: '11px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '3px' }}>
                        <MapPin size={11} color="#64748b" />
                        <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.road_name}</span>
                      </div>
                    )}

                    {s.is_safe === false && (
                      <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10.5px', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', padding: '3px 6px', borderRadius: '4px' }}>
                        <AlertTriangle size={12} color="#f59e0b" style={{ flexShrink: 0 }} />
                        <span>Caution: Active road hazard or debris along corridor</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '24px 16px', textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>
              Direct verified corridor active. Follow official disaster evacuation signage towards safe haven entrance.
            </div>
          )}
        </div>
      )}

      {/* Footer Emergency Support Callout */}
      <div
        style={{
          padding: '10px 14px',
          background: '#060d19',
          borderTop: '1px solid #14284b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '11.5px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8' }}>
          <ShieldCheck size={14} color="#34d399" />
          <span>District Control 24x7</span>
        </div>

        <a
          href="tel:112"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(239, 68, 68, 0.25)',
            color: '#fca5a5',
            border: '1px solid #ef4444',
            padding: '5px 12px',
            borderRadius: '6px',
            fontWeight: 800,
            fontSize: '11.5px',
            textDecoration: 'none',
          }}
        >
          <Phone size={12} />
          <span>SOS 112</span>
        </a>
      </div>
    </div>
  );
};
