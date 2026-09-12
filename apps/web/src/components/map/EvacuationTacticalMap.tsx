import React, { useState, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  CircleMarker,
  Circle,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Shelter, EvacuationRoute, DisasterEvent, EmergencyFacility } from '../../types';
import {
  Zap,
  HeartPulse,
  Navigation,
  MapPin,
  Flame,
  Waves,
  CloudRain,
  Shield,
  PhoneCall,
} from 'lucide-react';

interface EvacuationTacticalMapProps {
  center: [number, number];
  zoom: number;
  originCoords?: [number, number] | null;
  originName?: string;
  shelters: Shelter[];
  routes: EvacuationRoute[];
  selectedShelterId?: string | null;
  onSelectShelter?: (shelter: Shelter) => void;
  onMapClick?: (coords: [number, number]) => void;
  activeCorridorId?: string | null;
  disasterEvents?: DisasterEvent[];
  emergencyFacilities?: EmergencyFacility[];
  primaryRouteId?: string | null;
  height?: string;
}

// Controller to smoothly pan/zoom map when center/zoom changes
const MapViewController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true, duration: 0.8 });
  }, [center, zoom, map]);
  return null;
};

// Map click event listener for dynamic coordinate picking
const MapClickHandler: React.FC<{ onMapClick?: (coords: [number, number]) => void }> = ({ onMapClick }) => {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick([e.latlng.lat, e.latlng.lng]);
      }
    },
  });
  return null;
};

export const EvacuationTacticalMap: React.FC<EvacuationTacticalMapProps> = ({
  center,
  zoom,
  originCoords,
  originName,
  shelters,
  routes,
  selectedShelterId,
  onSelectShelter,
  onMapClick,
  activeCorridorId,
  disasterEvents = [],
  emergencyFacilities = [],
  primaryRouteId,
  height = '520px',
}) => {
  // Layer visibility toggles
  const [showHazards, setShowHazards] = useState<boolean>(true);
  const [showRoutes, setShowRoutes] = useState<boolean>(true);
  const [showShelters, setShowShelters] = useState<boolean>(true);
  const [showFacilities, setShowFacilities] = useState<boolean>(true);

  // Origin Pin Icon
  const originIcon = L.divIcon({
    className: 'evac-origin-pin',
    html: `
      <div style="
        width: 26px;
        height: 26px;
        background: #ef4444;
        border: 3px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 16px #ef4444;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 13px;
      ">📍</div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });

  // Create custom facility icon generator
  const createFacilityIcon = (type: string) => {
    let bg = '#0284c7';
    let icon = '🏛️';
    if (type === 'HOSPITAL') {
      bg = '#10b981';
      icon = '🏥';
    } else if (type === 'SDRF' || type === 'NDRF') {
      bg = '#f59e0b';
      icon = '🛡️';
    } else if (type === 'POLICE') {
      bg = '#6366f1';
      icon = '🚔';
    }
    return L.divIcon({
      className: 'facility-icon',
      html: `
        <div style="
          width: 28px;
          height: 28px;
          background: ${bg};
          border: 2px solid #ffffff;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
        ">${icon}</div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
  };

  // Routes to display
  const visibleRoutes = routes;

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: '14px',
        overflow: 'hidden',
        border: '1px solid #1e355b',
        boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
      }}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%', background: '#0a1628' }}
        zoomControl={true}
      >
        <MapViewController center={center} zoom={zoom} />
        <MapClickHandler onMapClick={onMapClick} />

        {/* Tactical Dark Base Tile (Clean Esri Dark Gray GIS) */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Flowshield Tactical GIS'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        {/* 1. Real-Time Disaster Event Perimeters & Hazard Zones */}
        {showHazards &&
          disasterEvents.map((event) => {
            const isLandslide = event.disaster_type === 'LANDSLIDE';
            const isFlood = event.disaster_type === 'FLASH_FLOOD' || event.disaster_type === 'RIVER_SURGE';
            const isRain = event.disaster_type === 'HEAVY_RAINFALL';

            const strokeColor = isLandslide ? '#ef4444' : isFlood ? '#0284c7' : isRain ? '#8b5cf6' : '#ec4899';
            const fillColor = isLandslide ? '#dc2626' : isFlood ? '#0369a1' : isRain ? '#7c3aed' : '#db2777';
            const radiusMeters = Math.max(800, (event.affected_radius_km || 2.5) * 1000);

            return (
              <React.Fragment key={event.id || event.event_id}>
                <Circle
                  center={[event.latitude, event.longitude]}
                  radius={radiusMeters}
                  pathOptions={{
                    color: strokeColor,
                    fillColor: fillColor,
                    fillOpacity: 0.22,
                    weight: 2,
                    dashArray: isLandslide ? '6, 6' : undefined,
                  }}
                >
                  <Popup className="tactical-popup">
                    <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '240px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: strokeColor, fontWeight: 800, fontSize: '13px' }}>
                        {isLandslide ? <Flame size={16} /> : isFlood ? <Waves size={16} /> : isRain ? <CloudRain size={16} /> : <Flame size={16} />}
                        <span>{event.disaster_type} HAZARD PERIMETER</span>
                      </div>
                      <div style={{ fontSize: '12px', fontWeight: 700, marginTop: '4px', color: '#f8fafc' }}>
                        {event.location_name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '6px' }}>
                        <div>Severity: <strong style={{ color: strokeColor }}>{event.severity}</strong> ({event.status})</div>
                        <div>Affected Radius: <strong>{event.affected_radius_km} km</strong></div>
                        <div>Estimated Population At Risk: <strong>{event.affected_population?.toLocaleString()}</strong></div>
                        <div>Confidence: <strong>{event.confidence_score}%</strong></div>
                      </div>
                      {event.description && (
                        <div style={{ fontSize: '10.5px', color: '#94a3b8', marginTop: '6px', borderTop: '1px solid #1e355b', paddingTop: '4px' }}>
                          {event.description}
                        </div>
                      )}
                    </div>
                  </Popup>
                </Circle>

                {/* Event Center Pulse Marker */}
                <CircleMarker
                  center={[event.latitude, event.longitude]}
                  radius={8}
                  pathOptions={{
                    color: '#ffffff',
                    fillColor: strokeColor,
                    fillOpacity: 0.95,
                    weight: 2,
                  }}
                />
              </React.Fragment>
            );
          })}

        {/* 2. Origin / Citizen Location Marker */}
        {originCoords && (
          <Marker position={originCoords} icon={originIcon}>
            <Popup className="tactical-popup">
              <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '220px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontWeight: 800, fontSize: '13px' }}>
                  <MapPin size={16} />
                  <span>EVACUATION ORIGIN</span>
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px', fontWeight: 700 }}>
                  {originName || 'Designated Coordinates'}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                  GPS: {originCoords[0].toFixed(4)}°N, {originCoords[1].toFixed(4)}°E
                </div>
                <div style={{ fontSize: '10px', color: '#38bdf8', marginTop: '6px', background: 'rgba(56, 189, 248, 0.1)', padding: '4px', borderRadius: '4px' }}>
                  Disaster-aware routing calculated from this origin
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* 3. Evacuation Corridors & Road Polylines */}
        {showRoutes &&
          visibleRoutes.map((route) => {
            if (!route.coordinates || route.coordinates.length < 2) return null;
            const isBlocked = route.is_blocked || route.status === 'BLOCKED';
            const isPrimary = primaryRouteId ? route.id === primaryRouteId : activeCorridorId === route.id;
            const isSelectedCorridor = activeCorridorId === route.id;

            // Route styling rules
            let color = '#10b981'; // Primary Safe Emerald
            let weight = isSelectedCorridor || isPrimary ? 6 : 4;
            let opacity = 0.85;

            if (isBlocked) {
              color = '#ef4444'; // Blocked Crimson
              weight = 4;
              opacity = 0.7;
            } else if (isPrimary) {
              color = '#06b6d4'; // Active Primary Cyan-Blue
              weight = 6;
              opacity = 1.0;
            } else if ((route.assessed_risk_score || 0) > 50) {
              color = '#f59e0b'; // Amber Caution
              weight = 4;
              opacity = 0.8;
            }

            return (
              <Polyline
                key={route.id}
                positions={route.coordinates}
                pathOptions={{
                  color,
                  weight,
                  opacity,
                  dashArray: isBlocked ? '8, 8' : undefined,
                }}
              >
                <Popup className="tactical-popup">
                  <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '230px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color, fontWeight: 700, fontSize: '13px' }}>
                      <Navigation size={14} />
                      <span>{route.name}</span>
                    </div>
                    {isPrimary && !isBlocked && (
                      <div style={{ fontSize: '10px', background: 'rgba(6, 182, 212, 0.2)', color: '#38bdf8', padding: '2px 6px', borderRadius: '4px', marginTop: '4px', display: 'inline-block' }}>
                        ★ PRIMARY SAFE EVACUATION PATH
                      </div>
                    )}
                    <div style={{ fontSize: '11px', marginTop: '6px', color: '#cbd5e1' }}>
                      <div>Distance: <strong>{route.distance_km?.toFixed(1)} km</strong></div>
                      <div>Travel Time: <strong>{route.estimated_time_min || Math.round(route.distance_km * 2.2)} min</strong></div>
                      <div>Safety Score: <strong>{route.safety_score ?? (100 - (route.assessed_risk_score || 15))}/100</strong></div>
                      <div>Status: <strong style={{ color }}>{isBlocked ? 'SEVERED / BLOCKED' : 'OPEN & PASSABLE'}</strong></div>
                      {route.is_river_crossing && (
                        <div style={{ color: '#38bdf8', fontSize: '10.5px', marginTop: '2px' }}>
                          🌊 Includes River Causeway Crossing
                        </div>
                      )}
                      {route.blockage_reason && (
                        <div style={{ color: '#f87171', marginTop: '4px', fontWeight: 600 }}>
                          Obstruction: {route.blockage_reason}
                        </div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Polyline>
            );
          })}

        {/* 4. Verified DDMP Shelters */}
        {showShelters &&
          shelters.map((shelter) => {
            const isSelected = selectedShelterId === shelter.id;
            const isVerified = shelter.verification_status === 'VERIFIED';
            const isBlockedRoute = shelter.corridor_blocked;
            const isSafeHaven = shelter.is_safe_haven !== false && !isBlockedRoute;

            let markerColor = '#10b981'; // Green Safe Haven
            if (!isSafeHaven) {
              markerColor = '#ef4444'; // Red unsafe / in hazard zone
            } else if (shelter.suitability_score && shelter.suitability_score < 70) {
              markerColor = '#f59e0b'; // Amber caution
            }

            return (
              <CircleMarker
                key={shelter.id}
                center={[shelter.latitude, shelter.longitude]}
                radius={isSelected ? 11 : 8}
                pathOptions={{
                  color: isSelected ? '#ffffff' : markerColor,
                  fillColor: markerColor,
                  fillOpacity: 0.9,
                  weight: isSelected ? 3 : 1.5,
                }}
                eventHandlers={{
                  click: () => {
                    if (onSelectShelter) onSelectShelter(shelter);
                  },
                }}
              >
                <Popup className="tactical-popup">
                  <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '260px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{ fontWeight: 800, fontSize: '13px', color: '#f1f5f9' }}>
                        🏥 {shelter.name}
                      </div>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: isSafeHaven ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: isSafeHaven ? '#34d399' : '#f87171',
                          border: isSafeHaven ? '1px solid #10b981' : '1px solid #ef4444',
                        }}
                      >
                        {isSafeHaven ? (isVerified ? 'VERIFIED SAFE HAVEN' : 'SAFE HAVEN') : 'IN HAZARD ZONE'}
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 6px' }}>
                      {shelter.type} • {shelter.village_town || shelter.district}
                    </div>

                    <div style={{ fontSize: '11px', background: '#162a4d', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
                      <div>Remaining Capacity: <strong>{shelter.available_capacity ?? shelter.capacity ?? 200} slots</strong></div>
                      <div>Total Capacity: <strong>{shelter.capacity ?? 300} persons</strong></div>
                      {shelter.distance_km && (
                        <div>Distance: <strong>{shelter.distance_km.toFixed(1)} km (~{shelter.estimated_travel_time_min || Math.round(shelter.distance_km * 2.2)} min)</strong></div>
                      )}
                      {shelter.suitability_score && (
                        <div>Suitability Score: <strong style={{ color: markerColor }}>{shelter.suitability_score}/100</strong></div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '10px', fontSize: '11px', color: '#cbd5e1', marginBottom: '8px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <HeartPulse size={12} color={shelter.has_medical ? '#10b981' : '#64748b'} />
                        {shelter.has_medical ? 'Medical Ready' : 'Basic Aid'}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={12} color={shelter.has_power_backup ? '#f59e0b' : '#64748b'} />
                        {shelter.has_power_backup ? 'Backup Gen Live' : 'Standard'}
                      </span>
                    </div>

                    {shelter.contact_phone && (
                      <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '6px' }}>
                        📞 In-Charge: {shelter.contact_person || 'DEOC Unit'} ({shelter.contact_phone})
                      </div>
                    )}

                    <button
                      onClick={() => onSelectShelter && onSelectShelter(shelter)}
                      className="btn btn-xs btn-primary"
                      style={{ width: '100%', marginTop: '4px', fontSize: '11px', padding: '4px' }}
                    >
                      Select as Evacuation Target
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

        {/* 5. Official Emergency Facilities & Response Bases */}
        {showFacilities &&
          emergencyFacilities.map((fac, idx) => {
            // Rough coordinates placed near district center with offset if explicit coords not attached
            const latOffset = (idx % 3) * 0.02 - 0.02;
            const lonOffset = Math.floor(idx / 3) * 0.02 - 0.02;
            const facCoords: [number, number] = [center[0] + latOffset, center[1] + lonOffset];

            return (
              <Marker key={`${fac.name}-${idx}`} position={facCoords} icon={createFacilityIcon(fac.type)}>
                <Popup className="tactical-popup">
                  <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '220px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontWeight: 800, fontSize: '12.5px' }}>
                      <Shield size={14} />
                      <span>{fac.name}</span>
                    </div>
                    <div style={{ fontSize: '11px', marginTop: '6px', color: '#cbd5e1' }}>
                      <div>Type: <strong>{fac.type}</strong></div>
                      <div>Status: <strong style={{ color: '#10b981' }}>{fac.status}</strong></div>
                      <div style={{ marginTop: '6px' }}>
                        <a
                          href={`tel:${fac.phone}`}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            background: '#0284c7',
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            textDecoration: 'none',
                            fontWeight: 700,
                            fontSize: '11px',
                          }}
                        >
                          <PhoneCall size={12} /> Call {fac.phone}
                        </a>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* Floating Tactical Layer Toggles Bar (Top Right) */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: 1000,
          background: 'rgba(15, 33, 62, 0.9)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '8px',
          padding: '6px 10px',
          display: 'flex',
          gap: '8px',
          fontSize: '11px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        <button
          onClick={() => setShowHazards(!showHazards)}
          style={{
            background: showHazards ? 'rgba(239, 68, 68, 0.25)' : 'transparent',
            border: `1px solid ${showHazards ? '#ef4444' : '#334155'}`,
            color: showHazards ? '#f87171' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 7px',
            cursor: 'pointer',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Flame size={12} /> Hazards ({disasterEvents.length})
        </button>

        <button
          onClick={() => setShowRoutes(!showRoutes)}
          style={{
            background: showRoutes ? 'rgba(6, 182, 212, 0.25)' : 'transparent',
            border: `1px solid ${showRoutes ? '#06b6d4' : '#334155'}`,
            color: showRoutes ? '#38bdf8' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 7px',
            cursor: 'pointer',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Navigation size={12} /> Routes ({routes.length})
        </button>

        <button
          onClick={() => setShowShelters(!showShelters)}
          style={{
            background: showShelters ? 'rgba(16, 185, 129, 0.25)' : 'transparent',
            border: `1px solid ${showShelters ? '#10b981' : '#334155'}`,
            color: showShelters ? '#34d399' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 7px',
            cursor: 'pointer',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <HeartPulse size={12} /> Shelters ({shelters.length})
        </button>

        <button
          onClick={() => setShowFacilities(!showFacilities)}
          style={{
            background: showFacilities ? 'rgba(59, 130, 246, 0.25)' : 'transparent',
            border: `1px solid ${showFacilities ? '#3b82f6' : '#334155'}`,
            color: showFacilities ? '#60a5fa' : '#94a3b8',
            borderRadius: '4px',
            padding: '3px 7px',
            cursor: 'pointer',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Shield size={12} /> Emergency ({emergencyFacilities.length})
        </button>
      </div>

      {/* Interactive Map Overlay Instructions (Top Left) */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '50px',
          zIndex: 1000,
          background: 'rgba(15, 33, 62, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #2a4778',
          borderRadius: '6px',
          padding: '4px 10px',
          fontSize: '11px',
          color: '#cbd5e1',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <MapPin size={12} color="#38bdf8" />
        <span>Click anywhere on map to pin custom GPS location</span>
      </div>

      {/* Semantic Legend (Bottom Right) */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          zIndex: 1000,
          background: 'rgba(15, 33, 62, 0.92)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #2a4778',
          borderRadius: '8px',
          padding: '8px 12px',
          fontSize: '10.5px',
          color: '#f1f5f9',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: '4px', fontSize: '10.5px', color: '#94a3b8', textTransform: 'uppercase' }}>
          GIS Evacuation Legend
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px 10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
            <span>Safe Haven</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
            <span>Hazard / Blocked</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: '#06b6d4' }}></span>
            <span>Primary Route</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '2px', borderTop: '2px dashed #ef4444' }}></span>
            <span>Severed Road</span>
          </div>
        </div>
      </div>
    </div>
  );
};
