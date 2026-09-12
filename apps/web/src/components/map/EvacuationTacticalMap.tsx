import React, { useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  CircleMarker,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Shelter, EvacuationRoute } from '../../types';
import { Zap, HeartPulse, Navigation, MapPin } from 'lucide-react';

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
}) => {
  // Origin Pin Icon
  const originIcon = L.divIcon({
    className: 'evac-origin-pin',
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background: #ef4444;
        border: 3px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 15px #ef4444;
        animation: pulse 1.5s infinite;
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

  return (
    <div style={{ position: 'relative', width: '100%', height: '480px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #1e355b' }}>
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
          attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Tactical Evacuation Map'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        {/* Origin / Stranded Location Marker */}
        {originCoords && (
          <Marker position={originCoords} icon={originIcon}>
            <Popup className="tactical-popup">
              <div style={{ padding: '6px', color: '#f1f5f9', background: '#0f213e' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444', fontWeight: 800, fontSize: '13px' }}>
                  <MapPin size={16} />
                  <span>AFFECTED EVACUATION ORIGIN</span>
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  <strong>{originName || 'Designated Coordinates'}</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                  GPS: {originCoords[0].toFixed(4)}°N, {originCoords[1].toFixed(4)}°E
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Evacuation Corridors & Road Polylines */}
        {routes.map((route) => {
          if (!route.coordinates || route.coordinates.length < 2) return null;
          const isBlocked = route.is_blocked || route.status === 'BLOCKED';
          const isActive = activeCorridorId === route.id;
          const color = isBlocked ? '#ef4444' : (route.assessed_risk_score || 0) > 50 ? '#f59e0b' : '#10b981';

          return (
            <Polyline
              key={route.id}
              positions={route.coordinates}
              pathOptions={{
                color: color,
                weight: isActive ? 6 : 4,
                opacity: isBlocked ? 0.6 : 0.9,
                dashArray: isBlocked ? '8, 8' : undefined,
              }}
            >
              <Popup className="tactical-popup">
                <div style={{ padding: '8px', color: '#f1f5f9', background: '#0f213e', minWidth: '220px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: color, fontWeight: 700, fontSize: '13px' }}>
                    <Navigation size={14} />
                    <span>{route.name}</span>
                  </div>
                  <div style={{ fontSize: '11px', marginTop: '6px', color: '#cbd5e1' }}>
                    <div>Distance: <strong>{route.distance_km?.toFixed(1)} km</strong></div>
                    <div>Est. Travel Time: <strong>{route.estimated_time_min || Math.round(route.distance_km * 2.2)} min</strong></div>
                    <div>Assessed Risk: <strong>{route.assessed_risk_score}/100</strong></div>
                    <div>Status: <strong style={{ color }}>{isBlocked ? 'BLOCKED' : 'CLEAR'}</strong></div>
                    {route.blockage_reason && (
                      <div style={{ color: '#f87171', marginTop: '4px' }}>
                        Obstruction: {route.blockage_reason}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* Shelters Markers with Semantic Colors */}
        {shelters.map((shelter) => {
          const isSelected = selectedShelterId === shelter.id;
          const isVerified = shelter.verification_status === 'VERIFIED';
          const isBlockedRoute = shelter.corridor_blocked;
          
          // Semantic Colors:
          // GREEN: Safe & verified
          // YELLOW: Caution / moderate risk
          // RED: Route blocked / unsafe hazard zone / closed
          // GREY: Unverified / stale
          let markerColor = '#10b981';
          if (isBlockedRoute || shelter.status === 'CLOSED') {
            markerColor = '#ef4444';
          } else if (shelter.verification_status === 'STALE' || shelter.verification_status === 'UNVERIFIED') {
            markerColor = '#94a3b8';
          } else if (shelter.recommendation_label?.includes('CAUTION') || (shelter.suitability_score && shelter.suitability_score < 70)) {
            markerColor = '#f59e0b';
          }

          return (
            <CircleMarker
              key={shelter.id}
              center={[shelter.latitude, shelter.longitude]}
              radius={isSelected ? 10 : 7}
              pathOptions={{
                color: markerColor,
                fillColor: markerColor,
                fillOpacity: 0.85,
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
                        background: isVerified ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: isVerified ? '#34d399' : '#fbbf24',
                        border: isVerified ? '1px solid #10b981' : '1px solid #f59e0b',
                      }}
                    >
                      {isVerified ? 'VERIFIED SHELTER' : 'DATA UNCONFIRMED'}
                    </span>
                  </div>

                  <div style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 8px' }}>
                    {shelter.type} • {shelter.village_town || shelter.district}
                  </div>

                  <div style={{ fontSize: '11px', background: '#162a4d', padding: '6px 8px', borderRadius: '6px', marginBottom: '8px' }}>
                    <div>Capacity: <strong>{shelter.capacity_display || (shelter.capacity ? `${shelter.capacity} slots` : 'Not officially published')}</strong></div>
                    <div>Occupancy: <strong>{shelter.occupancy_display || 'Not currently available'}</strong></div>
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
                      {shelter.has_medical ? 'Medical Ready' : 'First Aid'}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Zap size={12} color={shelter.has_power_backup ? '#f59e0b' : '#64748b'} />
                      {shelter.has_power_backup ? 'Generator Live' : 'Grid'}
                    </span>
                  </div>

                  {shelter.source_name && (
                    <div style={{ fontSize: '10px', color: '#64748b', borderTop: '1px solid #1e355b', paddingTop: '6px' }}>
                      Source: {shelter.source_name} ({shelter.source_last_verified || 'Recent'})
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Interactive Map Overlay Instructions */}
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
        <span>Click anywhere on map to set evacuation origin coordinates</span>
      </div>

      {/* Semantic Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          zIndex: 1000,
          background: 'rgba(15, 33, 62, 0.9)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #2a4778',
          borderRadius: '8px',
          padding: '8px 12px',
          fontSize: '11px',
          color: '#f1f5f9',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: '4px', fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>
          Tactical Map Legend
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
            <span>Verified Safe</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>
            <span>Caution / Secondary</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
            <span>Unsafe / Blocked</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#94a3b8' }}></span>
            <span>Unconfirmed / Stale</span>
          </div>
        </div>
      </div>
    </div>
  );
};
