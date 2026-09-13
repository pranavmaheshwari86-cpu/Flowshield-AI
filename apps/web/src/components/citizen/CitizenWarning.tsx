import React, { useState, useEffect, useMemo } from 'react';
import { Village, Shelter, EvacuationRoute } from '../../types';
import { api } from '../../services/api';
import { EvacuationTacticalMap } from '../map/EvacuationTacticalMap';
import { TurnByTurnNavigation } from '../map/TurnByTurnNavigation';
import {
  PhoneCall,
  MapPin,
  Hospital,
  AlertTriangle,
  ShieldCheck,
  CheckSquare,
  Navigation,
  ExternalLink,
} from 'lucide-react';

interface CitizenWarningProps {
  villages: Village[];
  selectedVillageId: any;
  onSelectVillage: (villageId: any) => void;
  shelters: Shelter[];
}

export const CitizenWarning: React.FC<CitizenWarningProps> = ({
  villages,
  selectedVillageId,
  onSelectVillage,
  shelters,
}) => {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [activeRoute, setActiveRoute] = useState<EvacuationRoute | null>(null);
  const [isNavDrawerOpen, setIsNavDrawerOpen] = useState<boolean>(false);
  const [loadingRoute, setLoadingRoute] = useState<boolean>(false);

  const village = villages.find(v => String(v.id) === String(selectedVillageId)) || villages[0];
  const isCritical = village?.current_risk_tier === 'CRITICAL' || village?.current_risk_tier === 'SEVERE';
  const isHigh = village?.current_risk_tier === 'HIGH';
  const isModerate = village?.current_risk_tier === 'MODERATE';

  // Find nearest shelter geographically to the selected village
  const nearestShelter = useMemo(() => {
    if (!shelters || shelters.length === 0) return null;
    if (!village) return shelters[0];
    const sorted = [...shelters].sort((a, b) => {
      const distA = Math.hypot(a.latitude - village.latitude, a.longitude - village.longitude);
      const distB = Math.hypot(b.latitude - village.latitude, b.longitude - village.longitude);
      return distA - distB;
    });
    return sorted[0];
  }, [shelters, village]);

  // State-specific official disaster numbers
  const stateHelpline = React.useMemo(() => {
    const s = (village?.state || '').toLowerCase();
    if (s.includes('bihar')) {
      return {
        stateName: 'Bihar (BSDMA)',
        primary: { number: '1070', label: 'BSDMA State Control Room' },
        district: { number: '06122217350', display: '0612-2217350', label: 'Patna/Bhagalpur Flood HQ' },
        ndrf: { number: '1078', label: 'NDRF 9th Bn (Bihta, Patna)' }
      };
    }
    if (s.includes('uttar')) {
      return {
        stateName: 'Uttar Pradesh (Rahat)',
        primary: { number: '1070', label: 'UP State Disaster Control' },
        district: { number: '05122550100', display: '0512-2550100', label: 'Kanpur Pandu Control Cell' },
        ndrf: { number: '1078', label: 'NDRF 11th Bn (Varanasi/Lucknow)' }
      };
    }
    if (s.includes('assam')) {
      return {
        stateName: 'Assam (ASDMA)',
        primary: { number: '1070', label: 'ASDMA State Flood Control' },
        district: { number: '1079', display: '1079', label: 'Brahmaputra Flood Helpline' },
        ndrf: { number: '1078', label: 'NDRF 1st Bn (Guwahati)' }
      };
    }
    if (s.includes('madhya')) {
      return {
        stateName: 'Madhya Pradesh',
        primary: { number: '1070', label: 'MP State Emergency Ops' },
        district: { number: '1077', display: '1077', label: 'Sheopur/Gwalior District HQ' },
        ndrf: { number: '1078', label: 'NDRF Emergency Ops' }
      };
    }
    return {
      stateName: 'Uttarakhand (USDMA)',
      primary: { number: '1070', label: 'USDMA State Disaster Control' },
      district: { number: '1077', display: '1077', label: 'Rudraprayag / Chamoli DEOC' },
      ndrf: { number: '1078', label: 'NDRF / SDRF Alpine Rescue' }
    };
  }, [village?.state]);

  const toggleCheck = (key: string) => {
    setCheckedItems(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Automatically compute safe road corridor from citizen village to nearest shelter
  useEffect(() => {
    if (!village || !nearestShelter) return;
    let isMounted = true;
    setLoadingRoute(true);

    api.evaluateDisasterAwareRoute({
      origin_latitude: village.latitude,
      origin_longitude: village.longitude,
      destination_shelter_id: nearestShelter.id,
      state: village.state,
      district: village.district,
      avoid_hazards: true,
      radius_km: 30,
    })
      .then((res) => {
        if (isMounted && res && res.selected_route) {
          setActiveRoute(res.selected_route);
        }
      })
      .catch((e) => console.error('Failed to compute citizen evacuation corridor:', e))
      .finally(() => {
        if (isMounted) setLoadingRoute(false);
      });

    return () => { isMounted = false; };
  }, [village?.id, nearestShelter?.id]);

  // Plain-Language Status Styling
  const getBannerInfo = () => {
    if (isCritical) {
      return {
        title: 'EVACUATE IMMEDIATELY',
        subtext: 'Flash flood danger is imminent in your village catchment area. Move to designated high ground right now.',
        bg: 'linear-gradient(135deg, #dc2626, #991b1b)',
        color: '#ffffff',
        icon: <AlertTriangle size={28} color="#ffffff" />
      };
    }
    if (isHigh) {
      return {
        title: 'HIGH FLOOD WARNING',
        subtext: 'River levels and rainfall have reached critical warning marks. Be ready to evacuate immediately upon signal.',
        bg: 'linear-gradient(135deg, #ea580c, #c2410c)',
        color: '#ffffff',
        icon: <AlertTriangle size={28} color="#ffffff" />
      };
    }
    if (isModerate) {
      return {
        title: 'FLOOD WATCH ACTIVE',
        subtext: 'Persistent mountain rainfall detected. Avoid rivers, streams, and low-lying roads.',
        bg: 'linear-gradient(135deg, #d97706, #b45309)',
        color: '#ffffff',
        icon: <AlertTriangle size={28} color="#ffffff" />
      };
    }
    return {
      title: 'NORMAL CONDITIONS',
      subtext: 'Hydrological and weather sensors report safe water levels in your area. Routine monitoring active.',
      bg: 'linear-gradient(135deg, #059669, #047857)',
      color: '#ffffff',
      icon: <ShieldCheck size={28} color="#ffffff" />
    };
  };

  const banner = getBannerInfo();

  return (
    <div className="citizen-page">
      {/* Village Selector */}
      <div style={{
        padding: '14px 18px',
        background: 'rgba(6, 20, 38, 0.15)',
        backdropFilter: 'blur(28px) saturate(180%)',
        WebkitBackdropFilter: 'blur(28px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '14px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.20), inset 0 1px 1px rgba(255, 255, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column' as const,
        gap: '8px',
      }}>
        <label style={{ fontSize: '11px', color: 'rgba(148, 163, 184, 0.9)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', letterSpacing: '0.05em' }}>
          <MapPin size={13} color="#06b6d4" />
          SELECT YOUR LOCATION / VILLAGE:
        </label>
        <select
          value={String(village?.id || selectedVillageId)}
          onChange={(e) => onSelectVillage(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            background: 'rgba(22, 42, 77, 0.4)',
            backdropFilter: 'blur(12px)',
            color: '#f1f5f9',
            border: '1px solid rgba(255, 255, 255, 0.10)',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 600,
            outline: 'none',
          }}
        >
          {villages.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name} ({v.district || v.tehsil || 'Zone'}, {v.state || 'India'}) — Risk: {v.current_risk_tier}
            </option>
          ))}
        </select>
      </div>

      {/* Main High-Contrast Alert Banner — Glassmorphic */}
      <div
        style={{
          background: banner.bg,
          color: banner.color,
          padding: '22px',
          borderRadius: '14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 1px rgba(255,255,255,0.20)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {banner.icon}
          <div>
            <div style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '0.02em' }}>
              {banner.title}
            </div>
            <div style={{ fontSize: '13px', opacity: 0.95, marginTop: '2px' }}>
              Location: <strong>{village?.name}</strong> • Basin: {village?.basin}
            </div>
          </div>
        </div>

        <p style={{ fontSize: '13px', lineHeight: 1.5, margin: 0, opacity: 0.9 }}>
          {banner.subtext}
        </p>

        {isCritical && (
          <div style={{ background: 'rgba(0,0,0,0.30)', backdropFilter: 'blur(8px)', padding: '10px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 600, border: '1px solid rgba(255,255,255,0.15)' }}>
            ⚠️ Siren Sounding in Village • Do not attempt to drive through flowing water.
          </div>
        )}
      </div>

      {/* Designated Safe Shelter Card — Glassmorphic */}
      {nearestShelter && (
        <div style={{
          background: 'rgba(6, 20, 38, 0.15)',
          backdropFilter: 'blur(28px) saturate(180%)',
          WebkitBackdropFilter: 'blur(28px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderLeft: '4px solid #10b981',
          borderRadius: '14px',
          padding: '16px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.20), inset 0 1px 1px rgba(255, 255, 255, 0.15)',
          display: 'flex',
          flexDirection: 'column' as const,
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '10px' }}>
            <Hospital size={16} color="#10b981" />
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9' }}>Your Designated Safe Evacuation Shelter</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#f1f5f9' }}>
              🏥 {nearestShelter.name}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
              <div style={{ background: 'rgba(22, 42, 77, 0.35)', backdropFilter: 'blur(12px)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ color: '#94a3b8' }}>Distance: </span>
                <strong>~1.8 km (15 min walk)</strong>
              </div>
              <div style={{ background: 'rgba(22, 42, 77, 0.35)', backdropFilter: 'blur(12px)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span style={{ color: '#94a3b8' }}>Elevation Advantage: </span>
                <strong style={{ color: '#10b981' }}>+{nearestShelter.elevation_m}m Safe Contours</strong>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Navigation size={14} color="#38bdf8" />
              <span>Route: Proceed via higher ridge road. Avoid riverside bridge.</span>
            </div>

            <a
              href={`https://maps.google.com/?q=${nearestShelter.latitude},${nearestShelter.longitude}`}
              target="_blank"
              rel="noreferrer"
              style={{
                marginTop: '4px',
                width: '100%',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '10px 16px',
                fontSize: '13px',
                fontWeight: 600,
                borderRadius: '10px',
                background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.8), rgba(37, 99, 235, 0.8))',
                backdropFilter: 'blur(12px)',
                color: '#ffffff',
                border: '1px solid rgba(255,255,255,0.15)',
                boxShadow: '0 4px 16px rgba(2, 132, 199, 0.3)',
                transition: 'all 0.2s ease',
              }}
            >
              <ExternalLink size={14} />
              Open GPS Navigation to Safe Shelter
            </a>
          </div>
        </div>
      )}

      {/* Interactive Real-Life Evacuation Map & Road Guidance for Citizen */}
      {nearestShelter && (
        <div
          style={{
            background: 'rgba(6, 20, 38, 0.18)',
            backdropFilter: 'blur(28px) saturate(180%)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '16px',
            padding: '18px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            position: 'relative',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Navigation size={18} color="#06b6d4" />
                <span>Live Safe Evacuation Route & Real-Life Map</span>
                {loadingRoute && (
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 500 }}>
                    • Calculating safe road path...
                  </span>
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                From <strong>{village?.name}</strong> to <strong>{nearestShelter.name}</strong> • Toggle Streets or Satellite for real visual landmarks.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              {activeRoute && (
                <button
                  onClick={() => setIsNavDrawerOpen(!isNavDrawerOpen)}
                  style={{
                    padding: '7px 12px',
                    background: isNavDrawerOpen ? '#0284c7' : 'rgba(6, 182, 212, 0.15)',
                    border: '1px solid #06b6d4',
                    color: '#ffffff',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Navigation size={13} />
                  <span>{isNavDrawerOpen ? 'Close Navigation Steps' : '🧭 Show Turn-by-Turn Guidance'}</span>
                </button>
              )}

              <a
                href={`https://www.google.com/maps/dir/?api=1&origin=${village?.latitude},${village?.longitude}&destination=${nearestShelter.latitude},${nearestShelter.longitude}&travelmode=driving`}
                target="_blank"
                rel="noreferrer"
                style={{
                  padding: '7px 12px',
                  background: 'linear-gradient(135deg, #0284c7, #2563eb)',
                  color: '#ffffff',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
                }}
              >
                <ExternalLink size={13} />
                <span>Open in Google Maps (Voice GPS)</span>
              </a>
            </div>
          </div>

          <EvacuationTacticalMap
            center={[village?.latitude || 30.5, village?.longitude || 79.03]}
            zoom={13}
            originCoords={village ? [village.latitude, village.longitude] : null}
            originName={`${village?.name} (Your Village)`}
            shelters={shelters}
            routes={activeRoute ? [activeRoute] : []}
            selectedShelterId={nearestShelter.id}
            selectedSafeHaven={nearestShelter}
            primaryRouteId={activeRoute?.id}
            primaryRoute={activeRoute}
            onOpenNavDrawer={() => setIsNavDrawerOpen(true)}
            height="460px"
          />

          {/* Floating Turn-by-Turn Drawer for Citizen */}
          {isNavDrawerOpen && activeRoute && (
            <div
              style={{
                position: 'absolute',
                top: '74px',
                right: '28px',
                bottom: '28px',
                width: '380px',
                maxWidth: 'calc(100% - 56px)',
                zIndex: 1050,
                boxShadow: '-8px 8px 32px rgba(0, 0, 0, 0.85)',
                borderRadius: '14px',
                overflow: 'hidden',
              }}
            >
              <TurnByTurnNavigation
                route={activeRoute}
                shelter={nearestShelter}
                originCoords={village ? [village.latitude, village.longitude] : null}
                onClose={() => setIsNavDrawerOpen(false)}
              />
            </div>
          )}
        </div>
      )}

      {/* Emergency Action Checklist — Glassmorphic */}
      <div style={{
        background: 'rgba(6, 20, 38, 0.15)',
        backdropFilter: 'blur(28px) saturate(180%)',
        WebkitBackdropFilter: 'blur(28px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '14px',
        padding: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.20), inset 0 1px 1px rgba(255, 255, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column' as const,
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '10px' }}>
          <CheckSquare size={16} color="#38bdf8" />
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9' }}>Citizen Emergency Preparedness Checklist</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { id: 'c1', text: 'Pack emergency bag: Drinking water, dry food, torch, and medicines' },
            { id: 'c2', text: 'Keep original IDs (Aadhaar, ration card) in a waterproof plastic pouch' },
            { id: 'c3', text: 'Keep mobile phone charged and conserve battery in low-power mode' },
            { id: 'c4', text: 'Disconnect electricity main switch and cooking gas cylinder if flooding starts' },
            { id: 'c5', text: 'Check on elderly family members, children, and assist livestock to higher ground' },
            { id: 'c6', text: 'NEVER walk or drive across flowing water or submerged culverts' },
          ].map((item) => (
            <label
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                fontSize: '12px',
                color: checkedItems[item.id] ? '#6ee7b7' : '#f1f5f9',
                textDecoration: checkedItems[item.id] ? 'line-through' : 'none',
                cursor: 'pointer',
                background: checkedItems[item.id] ? 'rgba(16, 185, 129, 0.08)' : 'rgba(22, 42, 77, 0.25)',
                backdropFilter: 'blur(8px)',
                padding: '10px 12px',
                borderRadius: '8px',
                border: checkedItems[item.id] ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(255, 255, 255, 0.08)',
                transition: 'all 0.2s ease',
              }}
              onClick={() => toggleCheck(item.id)}
            >
              <input
                type="checkbox"
                checked={!!checkedItems[item.id]}
                onChange={() => {}}
                style={{ marginTop: '2px', cursor: 'pointer', accentColor: '#10b981' }}
              />
              <span>{item.text}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 1-Tap Emergency SOS Phone Callers — Glassmorphic */}
      <div style={{
        background: 'rgba(6, 20, 38, 0.15)',
        backdropFilter: 'blur(28px) saturate(180%)',
        WebkitBackdropFilter: 'blur(28px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderLeft: '4px solid #ef4444',
        borderRadius: '14px',
        padding: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.20), inset 0 1px 1px rgba(255, 255, 255, 0.15)',
        display: 'flex',
        flexDirection: 'column' as const,
        gap: '12px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PhoneCall size={16} color="#ef4444" />
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#f1f5f9' }}>Official Emergency Helpline Numbers (1-Tap Dial)</span>
          </div>
          <span style={{ fontSize: '11px', background: 'rgba(239,68,68,0.12)', backdropFilter: 'blur(8px)', color: '#f87171', padding: '3px 10px', borderRadius: '6px', fontWeight: 600, border: '1px solid rgba(239,68,68,0.15)' }}>
            {stateHelpline.stateName}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <a
            href={`tel:${stateHelpline.primary.number}`}
            style={{
              textDecoration: 'none',
              padding: '14px 10px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.15)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              color: '#ffffff',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.15)',
            }}
          >
            <div style={{ fontSize: '16px', fontWeight: 800 }}>📞 {stateHelpline.primary.number}</div>
            <div style={{ fontSize: '10px', opacity: 0.85 }}>{stateHelpline.primary.label}</div>
          </a>

          <a
            href={`tel:${stateHelpline.district.number}`}
            style={{
              textDecoration: 'none',
              padding: '14px 10px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.15)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              color: '#ffffff',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.15)',
            }}
          >
            <div style={{ fontSize: '16px', fontWeight: 800 }}>📞 {stateHelpline.district.display || stateHelpline.district.number}</div>
            <div style={{ fontSize: '10px', opacity: 0.85 }}>{stateHelpline.district.label}</div>
          </a>

          <a
            href="tel:1078"
            style={{
              textDecoration: 'none',
              padding: '12px 10px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              borderRadius: '10px',
              background: 'rgba(30, 53, 91, 0.3)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#f1f5f9',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ fontSize: '15px', fontWeight: 700 }}>🚨 1078</div>
            <div style={{ fontSize: '10px', color: '#94a3b8' }}>{stateHelpline.ndrf.label}</div>
          </a>

          <a
            href="tel:112"
            style={{
              textDecoration: 'none',
              padding: '12px 10px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              borderRadius: '10px',
              background: 'rgba(30, 53, 91, 0.3)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#f1f5f9',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ fontSize: '15px', fontWeight: 700 }}>🚓 112 / 108</div>
            <div style={{ fontSize: '10px', color: '#94a3b8' }}>Police & Medical Emergency</div>
          </a>
        </div>
      </div>

      {/* Statutory Emergency Advisory Disclaimer — Glassmorphic */}
      <div style={{
        marginTop: '8px',
        padding: '14px 18px',
        background: 'rgba(6, 20, 38, 0.12)',
        backdropFilter: 'blur(24px) saturate(160%)',
        WebkitBackdropFilter: 'blur(24px) saturate(160%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '12px',
        fontSize: '11px',
        color: 'rgba(148, 163, 184, 0.9)',
        lineHeight: 1.5,
        textAlign: 'center' as const,
      }}>
        <strong>Statutory Disaster Advisory:</strong> Flowshield public advisories are issued in accordance with National Disaster Management Authority (NDMA) flash flood response protocols. These notices supplement ground announcements by District Magistrates and State Disaster Management Authorities. During active cloudburst or breach events, strictly comply with direct instructions from SDRF/NDRF rescue personnel and local village administration.
      </div>
    </div>
  );
};
