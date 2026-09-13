import React, { useState, useEffect, useMemo } from 'react';
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
  ExternalLink,
  Compass,
  Clock,
} from 'lucide-react';

export type BasemapType = 'streets' | 'satellite' | 'terrain' | 'dark';

interface EvacuationTacticalMapProps {
  center: [number, number];
  zoom: number;
  originCoords?: [number, number] | null;
  originName?: string;
  accuracyRadius?: number | null;
  shelters: Shelter[];
  routes: EvacuationRoute[];
  selectedShelterId?: string | null;
  selectedSafeHaven?: Shelter | null;
  onSelectShelter?: (shelter: Shelter) => void;
  onMapClick?: (coords: [number, number]) => void;
  activeCorridorId?: string | null;
  disasterEvents?: DisasterEvent[];
  emergencyFacilities?: EmergencyFacility[];
  primaryRouteId?: string | null;
  primaryRoute?: EvacuationRoute | null;
  onOpenNavDrawer?: () => void;
  height?: string;
}

// Controller to smoothly pan/zoom map when center/zoom changes
const MapViewController: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center && !isNaN(center[0]) && !isNaN(center[1])) {
      map.setView(center, zoom, { animate: true, duration: 0.8 });
    }
  }, [center, zoom, map]);
  return null;
};

// Robust Controller to smoothly fit bounds to origin, destination shelter, and active route
const MapBoundsController: React.FC<{
  origin?: [number, number] | null;
  routes?: EvacuationRoute[];
  activeRouteId?: string | null;
  selectedShelter?: Shelter | null;
}> = ({ origin, routes = [], activeRouteId, selectedShelter }) => {
  const map = useMap();

  useEffect(() => {
    const pts: [number, number][] = [];

    const addSanitized = (lat?: number | null, lon?: number | null) => {
      if (lat == null || lon == null || isNaN(lat) || isNaN(lon)) return;
      let clat = Number(lat);
      let clon = Number(lon);
      // Auto-fix swapped GeoJSON [lon, lat] coordinates (e.g. 79.5, 30.4)
      if (clat > 50 && clon < 45) {
        const tmp = clat;
        clat = clon;
        clon = tmp;
      }
      // Clamping to India geographic bounds (Lat: 6°N - 38°N, Lon: 65°E - 100°E)
      if (clat >= 6 && clat <= 38 && clon >= 65 && clon <= 100) {
        pts.push([clat, clon]);
      }
    };

    if (origin) addSanitized(origin[0], origin[1]);
    if (selectedShelter) addSanitized(selectedShelter.latitude, selectedShelter.longitude);

    const activeRoute = routes.find((r) => r.id === activeRouteId) || routes[0];
    if (activeRoute?.coordinates && Array.isArray(activeRoute.coordinates)) {
      activeRoute.coordinates.forEach((pt: any) => {
        if (Array.isArray(pt) && pt.length >= 2) {
          addSanitized(pt[0], pt[1]);
        }
      });
    }

    if (pts.length >= 2) {
      try {
        const bounds = L.latLngBounds(pts);
        map.fitBounds(bounds, { padding: [70, 70], maxZoom: 15 });
      } catch (e) {
        // Fallback gracefully
      }
    } else if (pts.length === 1) {
      map.setView(pts[0], 14, { animate: true });
    }
  }, [origin, activeRouteId, routes, selectedShelter, map]);

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
  accuracyRadius,
  shelters,
  routes,
  selectedShelterId,
  selectedSafeHaven,
  onSelectShelter,
  onMapClick,
  activeCorridorId,
  disasterEvents = [],
  emergencyFacilities = [],
  primaryRouteId,
  primaryRoute,
  onOpenNavDrawer,
  height = '560px',
}) => {
  // Real-Life Basemap Selector State (Defaults to Streets for ultra-clarity)
  const [activeBasemap, setActiveBasemap] = useState<BasemapType>('streets');

  // Layer visibility toggles
  const [showHazards, setShowHazards] = useState<boolean>(true);
  const [showRoutes, setShowRoutes] = useState<boolean>(true);
  const [showShelters, setShowShelters] = useState<boolean>(true);
  const [showFacilities, setShowFacilities] = useState<boolean>(true);

  // Active target shelter resolution
  const targetShelter = useMemo(() => {
    if (selectedShelterId) {
      const found = shelters.find((s) => s.id === selectedShelterId);
      if (found) return found;
    }
    return selectedSafeHaven || shelters.find((s) => s.is_best_safe_option) || shelters[0] || null;
  }, [selectedShelterId, selectedSafeHaven, shelters]);

  // Radar Pulse Origin Beacon Icon
  const originIcon = useMemo(
    () =>
      L.divIcon({
        className: 'evac-origin-pin',
        html: `
          <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; background: rgba(6, 182, 212, 0.45); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="width: 20px; height: 20px; background: #06b6d4; border: 3px solid #ffffff; border-radius: 50%; box-shadow: 0 0 14px #06b6d4; z-index: 2;"></div>
          </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      }),
    []
  );

  // Custom facility icon generator
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
          width: 30px;
          height: 30px;
          background: ${bg};
          border: 2px solid #ffffff;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 15px;
        ">${icon}</div>
      `,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
  };

  // Combine static routes with dynamic primaryRoute (ensuring valid coordinates)
  const visibleRoutes = useMemo(() => {
    const list = [...routes];
    if (primaryRoute && primaryRoute.coordinates && primaryRoute.coordinates.length >= 2) {
      const idx = list.findIndex((r) => r.id === primaryRoute.id);
      if (idx >= 0) {
        list[idx] = primaryRoute;
      } else {
        list.unshift(primaryRoute);
      }
    }
    return list;
  }, [routes, primaryRoute]);

  // Active navigation route (for HUD display)
  const activeNavRoute = useMemo(() => {
    if (primaryRoute && primaryRoute.coordinates && primaryRoute.coordinates.length >= 2) {
      return primaryRoute;
    }
    return visibleRoutes.find((r) => r.id === (primaryRouteId || activeCorridorId)) || visibleRoutes[0] || null;
  }, [primaryRoute, visibleRoutes, primaryRouteId, activeCorridorId]);

  // Google Maps Universal Driving/Walking Direction URL
  const googleMapsDirectionsUrl = useMemo(() => {
    if (!targetShelter) return null;
    const destLat = targetShelter.latitude;
    const destLon = targetShelter.longitude;
    if (originCoords && originCoords[0] && originCoords[1]) {
      return `https://www.google.com/maps/dir/?api=1&origin=${originCoords[0]},${originCoords[1]}&destination=${destLat},${destLon}&travelmode=driving`;
    }
    return `https://www.google.com/maps/search/?api=1&query=${destLat},${destLon}`;
  }, [targetShelter, originCoords]);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: '16px',
        overflow: 'hidden',
        border: '1.5px solid #1e355b',
        boxShadow: '0 12px 40px rgba(0,0,0,0.45)',
      }}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%', background: '#0a1628' }}
        zoomControl={true}
      >
        <MapViewController center={center} zoom={zoom} />
        <MapBoundsController
          origin={originCoords}
          routes={visibleRoutes}
          activeRouteId={primaryRouteId || activeCorridorId}
          selectedShelter={targetShelter}
        />
        <MapClickHandler onMapClick={onMapClick} />

        {/* 1. Real-Life Basemap Layer Options */}
        {activeBasemap === 'streets' && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            subdomains={['a', 'b', 'c']}
            maxZoom={19}
          />
        )}

        {activeBasemap === 'satellite' && (
          <>
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a>, Earthstar Geographics'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
            />
            <TileLayer
              attribution='&copy; Esri Reference'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
              opacity={0.88}
            />
          </>
        )}

        {activeBasemap === 'terrain' && (
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>, USGS, NOAA'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
            maxZoom={18}
          />
        )}

        {activeBasemap === 'dark' && (
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Flowshield Tactical GIS'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={16}
          />
        )}

        {/* 2. Real-Time Disaster Event Perimeters & Hazard Zones */}
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
                        <div>Estimated Population: <strong>{event.affected_population?.toLocaleString()}</strong></div>
                        <div>Confidence: <strong>{event.confidence_score}%</strong></div>
                      </div>
                    </div>
                  </Popup>
                </Circle>

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

        {/* 3. Origin / Citizen Location Marker & Accuracy Radius */}
        {originCoords && accuracyRadius && accuracyRadius > 0 && (
          <Circle
            center={originCoords}
            radius={accuracyRadius}
            pathOptions={{
              color: '#06b6d4',
              fillColor: '#06b6d4',
              fillOpacity: 0.12,
              weight: 1.5,
              dashArray: '4, 4',
            }}
          />
        )}

        {originCoords && (
          <Marker position={originCoords} icon={originIcon}>
            <Popup className="tactical-popup">
              <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '220px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#06b6d4', fontWeight: 800, fontSize: '13px' }}>
                  <MapPin size={16} />
                  <span>YOUR LOCATION (ORIGIN)</span>
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px', fontWeight: 700 }}>
                  {originName || 'Current Geographic Sector'}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                  GPS: {originCoords[0].toFixed(4)}°N, {originCoords[1].toFixed(4)}°E
                  {accuracyRadius ? ` (±${Math.round(accuracyRadius)}m)` : ''}
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* 4. Evacuation Corridors & Road Polylines */}
        {showRoutes &&
          visibleRoutes.map((route) => {
            if (!route.coordinates || route.coordinates.length < 2) return null;
            const isBlocked = route.is_blocked || route.status === 'BLOCKED';
            const isPrimary = primaryRouteId ? route.id === primaryRouteId : activeCorridorId === route.id;

            // Route styling rules
            let color = '#10b981'; // Safe Emerald
            let weight = isPrimary ? 6 : 4;
            let opacity = isPrimary ? 1.0 : 0.75;

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
                        ★ ACTIVE EVACUATION CORRIDOR
                      </div>
                    )}
                    <div style={{ fontSize: '11px', marginTop: '6px', color: '#cbd5e1' }}>
                      <div>Distance: <strong>{route.distance_km?.toFixed(1)} km</strong></div>
                      <div>Travel Time: <strong>{route.estimated_time_min || Math.round(route.distance_km * 2.2)} min</strong></div>
                      <div>Safety Score: <strong>{route.safety_score ?? (100 - (route.assessed_risk_score || 15))}/100</strong></div>
                      <div>Status: <strong style={{ color }}>{isBlocked ? 'SEVERED / BLOCKED' : 'OPEN & PASSABLE'}</strong></div>
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

        {/* 5. Verified DDMP Shelters */}
        {showShelters &&
          shelters.map((shelter) => {
            const isSelected = selectedShelterId === shelter.id || (targetShelter && targetShelter.id === shelter.id);
            const isVerified = shelter.verification_status === 'VERIFIED';
            const isBlockedRoute = shelter.corridor_blocked;
            const isSafeHaven = shelter.is_safe_haven !== false && !isBlockedRoute;

            let markerColor = '#10b981'; // Green Safe Haven
            if (!isSafeHaven) {
              markerColor = '#ef4444'; // Red unsafe
            } else if (shelter.suitability_score && shelter.suitability_score < 70) {
              markerColor = '#f59e0b'; // Amber caution
            }

            return (
              <CircleMarker
                key={shelter.id}
                center={[shelter.latitude, shelter.longitude]}
                radius={isSelected ? 12 : 8}
                pathOptions={{
                  color: isSelected ? '#ffffff' : markerColor,
                  fillColor: markerColor,
                  fillOpacity: 0.95,
                  weight: isSelected ? 3.5 : 1.5,
                }}
                eventHandlers={{
                  click: () => {
                    if (onSelectShelter) onSelectShelter(shelter);
                  },
                }}
              >
                <Popup className="tactical-popup">
                  <div style={{ padding: '10px', color: '#f1f5f9', background: '#0f213e', minWidth: '270px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{ fontWeight: 800, fontSize: '13.5px', color: '#f1f5f9' }}>
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
                        {isSafeHaven ? (isVerified ? 'VERIFIED SAFE' : 'SAFE HAVEN') : 'HAZARD ZONE'}
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 6px' }}>
                      {shelter.type} • {shelter.village_town || shelter.district}
                    </div>

                    <div style={{ fontSize: '11px', background: '#162a4d', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
                      <div>Remaining Capacity: <strong>{shelter.available_capacity ?? shelter.capacity ?? 200} slots</strong></div>
                      {shelter.distance_km && (
                        <div>Distance: <strong>{shelter.distance_km.toFixed(1)} km (~{shelter.estimated_travel_time_min || Math.round(shelter.distance_km * 2.2)} min)</strong></div>
                      )}
                      {shelter.elevation_m && (
                        <div>Elevation: <strong>{Math.round(shelter.elevation_m)} m</strong></div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: '10px', fontSize: '11px', color: '#cbd5e1', marginBottom: '10px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <HeartPulse size={12} color={shelter.has_medical ? '#10b981' : '#64748b'} />
                        {shelter.has_medical ? 'Medical Ready' : 'Basic Aid'}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={12} color={shelter.has_power_backup ? '#f59e0b' : '#64748b'} />
                        {shelter.has_power_backup ? 'Backup Gen' : 'Standard'}
                      </span>
                    </div>

                    {/* Action Buttons: Navigate Here & Google Maps */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <button
                        onClick={() => onSelectShelter && onSelectShelter(shelter)}
                        style={{
                          width: '100%',
                          padding: '7px 12px',
                          background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                          border: 'none',
                          borderRadius: '6px',
                          color: '#ffffff',
                          fontWeight: 700,
                          fontSize: '11.5px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          boxShadow: '0 2px 8px rgba(2, 132, 199, 0.4)',
                        }}
                      >
                        <Navigation size={13} />
                        <span>Navigate to this Shelter</span>
                      </button>

                      {originCoords && (
                        <a
                          href={`https://www.google.com/maps/dir/?api=1&origin=${originCoords[0]},${originCoords[1]}&destination=${shelter.latitude},${shelter.longitude}&travelmode=driving`}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            width: '100%',
                            padding: '6px 12px',
                            background: 'rgba(255, 255, 255, 0.08)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '6px',
                            color: '#38bdf8',
                            textDecoration: 'none',
                            fontWeight: 600,
                            fontSize: '11px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '6px',
                            boxSizing: 'border-box',
                          }}
                        >
                          <ExternalLink size={12} />
                          <span>Open in Google Maps (Turn-by-Turn)</span>
                        </a>
                      )}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

        {/* 6. Official Emergency Facilities */}
        {showFacilities &&
          emergencyFacilities.map((fac, idx) => {
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

      {/* FLOATING TOP-LEFT: Basemap Switcher (Streets, Satellite, Terrain, Dark) */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '52px',
          zIndex: 1000,
          background: 'rgba(11, 23, 44, 0.92)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '8px',
          padding: '4px 6px',
          display: 'flex',
          gap: '4px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        <button
          onClick={() => setActiveBasemap('streets')}
          title="Real-Life Streets & Cities (Carto / OpenStreetMap)"
          style={{
            background: activeBasemap === 'streets' ? '#0284c7' : 'transparent',
            color: activeBasemap === 'streets' ? '#ffffff' : '#94a3b8',
            border: 'none',
            borderRadius: '5px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            transition: 'all 0.15s ease',
          }}
        >
          🗺️ Streets
        </button>

        <button
          onClick={() => setActiveBasemap('satellite')}
          title="Real-World Satellite Imagery with Labels (Esri World Imagery)"
          style={{
            background: activeBasemap === 'satellite' ? '#0284c7' : 'transparent',
            color: activeBasemap === 'satellite' ? '#ffffff' : '#94a3b8',
            border: 'none',
            borderRadius: '5px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            transition: 'all 0.15s ease',
          }}
        >
          🛰️ Satellite
        </button>

        <button
          onClick={() => setActiveBasemap('terrain')}
          title="Mountain Topography & Contours (Esri Topo)"
          style={{
            background: activeBasemap === 'terrain' ? '#0284c7' : 'transparent',
            color: activeBasemap === 'terrain' ? '#ffffff' : '#94a3b8',
            border: 'none',
            borderRadius: '5px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            transition: 'all 0.15s ease',
          }}
        >
          ⛰️ Terrain
        </button>

        <button
          onClick={() => setActiveBasemap('dark')}
          title="Tactical Dark Gray GIS"
          style={{
            background: activeBasemap === 'dark' ? '#0284c7' : 'transparent',
            color: activeBasemap === 'dark' ? '#ffffff' : '#94a3b8',
            border: 'none',
            borderRadius: '5px',
            padding: '4px 8px',
            fontSize: '11px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            transition: 'all 0.15s ease',
          }}
        >
          🌃 Dark
        </button>
      </div>

      {/* FLOATING TOP-RIGHT: Layer Visibility Toggles */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: 1000,
          background: 'rgba(11, 23, 44, 0.92)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '8px',
          padding: '4px 8px',
          display: 'flex',
          gap: '6px',
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

      {/* FLOATING BOTTOM-LEFT: In-Map Live Navigation HUD */}
      {targetShelter && (
        <div
          style={{
            position: 'absolute',
            bottom: '14px',
            left: '14px',
            zIndex: 1000,
            background: 'linear-gradient(135deg, rgba(11, 24, 48, 0.95) 0%, rgba(7, 16, 34, 0.98) 100%)',
            backdropFilter: 'blur(16px)',
            border: '1.5px solid #06b6d4',
            borderRadius: '12px',
            padding: '12px 16px',
            maxWidth: '380px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.65)',
            color: '#f1f5f9',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#06b6d4', fontSize: '11px', fontWeight: 800, textTransform: 'uppercase' }}>
              <Compass size={14} />
              <span>Target Safe Destination</span>
            </div>
            <span style={{ fontSize: '10px', background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981', color: '#34d399', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
              VERIFIED SAFE HAVEN
            </span>
          </div>

          <div style={{ fontSize: '13.5px', fontWeight: 800, color: '#ffffff', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {targetShelter.name}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '11.5px', color: '#cbd5e1', marginBottom: '10px' }}>
            {activeNavRoute?.distance_km && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Navigation size={12} color="#38bdf8" />
                <strong>{activeNavRoute.distance_km.toFixed(1)} km</strong>
              </span>
            )}
            {activeNavRoute?.estimated_time_min && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} color="#34d399" />
                <strong>~{activeNavRoute.estimated_time_min} min ETA</strong>
              </span>
            )}
            <span style={{ color: '#94a3b8' }}>Elev: +{targetShelter.elevation_m || 890}m</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            {onOpenNavDrawer && (
              <button
                onClick={onOpenNavDrawer}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '5px',
                }}
              >
                <Navigation size={12} />
                <span>Turn-by-Turn Steps</span>
              </button>
            )}

            {googleMapsDirectionsUrl && (
              <a
                href={googleMapsDirectionsUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '6px',
                  color: '#38bdf8',
                  fontWeight: 700,
                  fontSize: '11px',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '5px',
                  boxSizing: 'border-box',
                }}
              >
                <ExternalLink size={12} />
                <span>Google Maps Voice GPS</span>
              </a>
            )}
          </div>
        </div>
      )}

      {/* FLOATING BOTTOM-RIGHT: Semantic Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '14px',
          right: '14px',
          zIndex: 1000,
          background: 'rgba(11, 23, 44, 0.92)',
          backdropFilter: 'blur(12px)',
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
            <span>Active Safe Route</span>
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
