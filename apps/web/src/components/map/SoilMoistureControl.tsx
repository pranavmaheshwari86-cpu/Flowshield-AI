import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Satellite,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Database,
  Thermometer,
  Droplets,
  X,
} from 'lucide-react';
import { api } from '../../services/api';
import { AgroStatus, SoilGeoJSONFeature } from '../../types';

interface SoilMoistureControlProps {
  showLayer: boolean;
  onToggleLayer: (enabled: boolean) => void;
  selectedFeature: SoilGeoJSONFeature | null;
  onCloseFeatureCard: () => void;
  onGridUpdated: () => void;
}

export const SoilMoistureControl: React.FC<SoilMoistureControlProps> = ({
  showLayer,
  onToggleLayer,
  selectedFeature,
  onCloseFeatureCard,
  onGridUpdated,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [status, setStatus] = useState<AgroStatus | null>(null);
  const [hierarchy, setHierarchy] = useState<Record<string, string[]>>({});
  const [selectedState, setSelectedState] = useState<string>('Himachal Pradesh');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Mandi');
  const [batchLimit, setBatchLimit] = useState<number>(5);
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Load status and hierarchy on mount
  useEffect(() => {
    fetchStatus();
    loadHierarchy();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await api.getAgroStatus();
      setStatus(res);
    } catch (err) {
      console.error('Failed to fetch AgroMonitoring status', err);
    }
  };

  const loadHierarchy = async () => {
    try {
      const res = await api.getAgroHierarchy();
      setHierarchy(res);
      if (res['Himachal Pradesh'] && res['Himachal Pradesh'].length > 0) {
        setSelectedState('Himachal Pradesh');
        if (res['Himachal Pradesh'].includes('Mandi')) {
          setSelectedDistrict('Mandi');
        } else {
          setSelectedDistrict(res['Himachal Pradesh'][0]);
        }
      }
    } catch (err) {
      console.error('Failed to load administrative hierarchy', err);
    }
  };

  const handleStateChange = (state: string) => {
    setSelectedState(state);
    const districts = hierarchy[state] || [];
    setSelectedDistrict(districts.length > 0 ? districts[0] : '');
  };

  const handleInitializeGrid = async () => {
    try {
      setIsInitializing(true);
      setNotification({ type: 'info', message: `Dividing ${selectedDistrict} into valid 1-3,000 ha polygons...` });
      
      const res = await api.initAgroGrid({
        scope: 'district',
        state_name: selectedState,
        district_name: selectedDistrict,
        register_with_agro: true,
        batch_limit: batchLimit,
      });

      if (res.status === 'success') {
        const r = res.result;
        setNotification({
          type: 'success',
          message: `Grid Ready! ${r.total_cells_generated} cells created, ${r.newly_registered_with_agro} registered with AgroMonitoring.`,
        });
        await fetchStatus();
        onGridUpdated();
      }
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err?.detail || 'Failed to initialize grid. Check API key and network.',
      });
    } finally {
      setIsInitializing(false);
    }
  };

  const handleSyncTelemetry = async () => {
    try {
      setIsSyncing(true);
      setNotification({ type: 'info', message: 'Retrieving live satellite soil telemetry...' });
      const res = await api.syncAgroSoilData();
      setNotification({
        type: 'success',
        message: `Updated soil telemetry for ${res.updated_polygons} registered monitoring polygons.`,
      });
      await fetchStatus();
      onGridUpdated();
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err?.detail || 'Telemetry sync failed.',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const districts = hierarchy[selectedState] || [];

  return (
    <div
      style={{
        position: 'absolute',
        top: '80px',
        right: '16px',
        zIndex: 1000,
        width: '320px',
        maxHeight: 'calc(100vh - 120px)',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        pointerEvents: 'auto',
      }}
    >
      {/* Main Control Panel */}
      <div
        style={{
          background: 'rgba(2, 10, 24, 0.88)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.55)',
          padding: '12px',
          color: '#E2E8F0',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                background: showLayer ? 'rgba(56, 189, 248, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                border: `1px solid ${showLayer ? '#38BDF8' : '#64748B'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Satellite size={16} color={showLayer ? '#38BDF8' : '#94A3B8'} />
            </div>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '0.02em' }}>
                AgroMonitoring Soil GIS
              </div>
              <div style={{ fontSize: '9.5px', color: '#94A3B8' }}>
                Satellite Sentinel Telemetry (1–3,000 ha)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => onToggleLayer(!showLayer)}
              style={{
                background: showLayer ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                border: `1px solid ${showLayer ? '#10B981' : '#64748B'}`,
                color: showLayer ? '#10B981' : '#94A3B8',
                borderRadius: '6px',
                padding: '3px 8px',
                fontSize: '10px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {showLayer ? 'ACTIVE' : 'OFF'}
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '2px',
              }}
            >
              {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
            </button>
          </div>
        </div>

        {/* Expanded Panel */}
        {isExpanded && (
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Status overview badges */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '6px',
                background: 'rgba(15, 23, 42, 0.65)',
                padding: '8px',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#38BDF8' }}>
                  {status?.total_cells_generated ?? 0}
                </div>
                <div style={{ fontSize: '8.5px', color: '#94A3B8' }}>Grid Cells</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#10B981' }}>
                  {status?.registered_polygons ?? 0}
                </div>
                <div style={{ fontSize: '8.5px', color: '#94A3B8' }}>Agro Active</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '13px', fontWeight: 800, color: status?.limit_exceeded_polygons ? '#F59E0B' : '#94A3B8' }}>
                  {status?.limit_exceeded_polygons ?? 0}
                </div>
                <div style={{ fontSize: '8.5px', color: '#94A3B8' }}>Quota Capped</div>
              </div>
            </div>

            {/* Notification alert */}
            {notification && (
              <div
                style={{
                  fontSize: '10px',
                  padding: '6px 8px',
                  borderRadius: '6px',
                  background:
                    notification.type === 'error'
                      ? 'rgba(239, 68, 68, 0.18)'
                      : notification.type === 'success'
                      ? 'rgba(16, 185, 129, 0.18)'
                      : 'rgba(56, 189, 248, 0.18)',
                  border: `1px solid ${
                    notification.type === 'error'
                      ? 'rgba(239, 68, 68, 0.4)'
                      : notification.type === 'success'
                      ? 'rgba(16, 185, 129, 0.4)'
                      : 'rgba(56, 189, 248, 0.4)'
                  }`,
                  color:
                    notification.type === 'error'
                      ? '#FECACA'
                      : notification.type === 'success'
                      ? '#A7F3D0'
                      : '#BAE6FD',
                }}
              >
                {notification.message}
              </div>
            )}

            {/* Plan limit notice */}
            {status?.plan_notice && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '6px',
                  background: 'rgba(245, 158, 11, 0.12)',
                  border: '1px solid rgba(245, 158, 11, 0.35)',
                  borderRadius: '6px',
                  padding: '6px 8px',
                  fontSize: '9.5px',
                  color: '#FDE68A',
                }}
              >
                <AlertTriangle size={13} color="#F59E0B" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>{status.plan_notice}</span>
              </div>
            )}

            {/* State & District Selector */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', gap: '6px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '9px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>
                    State
                  </label>
                  <select
                    value={selectedState}
                    onChange={(e) => handleStateChange(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      color: '#F1F5F9',
                      fontSize: '10.5px',
                      borderRadius: '6px',
                      padding: '4px 6px',
                      outline: 'none',
                    }}
                  >
                    {Object.keys(hierarchy).map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '9px', fontWeight: 700, color: '#94A3B8', textTransform: 'uppercase' }}>
                    District
                  </label>
                  <select
                    value={selectedDistrict}
                    onChange={(e) => setSelectedDistrict(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      color: '#F1F5F9',
                      fontSize: '10.5px',
                      borderRadius: '6px',
                      padding: '4px 6px',
                      outline: 'none',
                    }}
                  >
                    {districts.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Batch Limit Setting */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '9.5px', color: '#94A3B8' }}>
                <span>Agro Register Quota:</span>
                <select
                  value={batchLimit}
                  onChange={(e) => setBatchLimit(Number(e.target.value))}
                  style={{
                    background: 'rgba(15, 23, 42, 0.9)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    color: '#38BDF8',
                    fontSize: '10px',
                    borderRadius: '4px',
                    padding: '2px 4px',
                  }}
                >
                  <option value={2}>2 Polygons (Safe)</option>
                  <option value={5}>5 Polygons</option>
                  <option value={10}>10 Polygons</option>
                  <option value={25}>25 Polygons</option>
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                onClick={handleInitializeGrid}
                disabled={isInitializing}
                style={{
                  flex: 1,
                  background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  borderRadius: '6px',
                  color: '#FFFFFF',
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  cursor: isInitializing ? 'not-allowed' : 'pointer',
                  opacity: isInitializing ? 0.7 : 1,
                }}
              >
                <Database size={12} className={isInitializing ? 'animate-spin' : ''} />
                <span>{isInitializing ? 'Tiling...' : 'Tile & Register'}</span>
              </button>

              <button
                onClick={handleSyncTelemetry}
                disabled={isSyncing || (status?.registered_polygons ?? 0) === 0}
                style={{
                  flex: 1,
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  borderRadius: '6px',
                  color: '#10B981',
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '6px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  cursor: isSyncing ? 'not-allowed' : 'pointer',
                }}
              >
                <RefreshCw size={12} className={isSyncing ? 'animate-spin' : ''} />
                <span>{isSyncing ? 'Syncing...' : 'Sync Soil'}</span>
              </button>
            </div>

            {/* Hydrologic Moisture Legend */}
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.55)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '8px',
                padding: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <div style={{ fontSize: '9px', fontWeight: 800, color: '#94A3B8', textTransform: 'uppercase' }}>
                Hydrologic Soil Moisture Scale (m³/m³)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px', fontSize: '9px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#F59E0B' }} />
                  <span style={{ color: '#FDE68A' }}>Low (&lt; 0.15)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#10B981' }} />
                  <span style={{ color: '#A7F3D0' }}>Moderate (0.15-0.30)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#3B82F6' }} />
                  <span style={{ color: '#BAE6FD' }}>High (0.30-0.45)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#EF4444' }} />
                  <span style={{ color: '#FECACA' }}>Very High (&gt; 0.45)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Selected Polygon Telemetry Inspection Card */}
      {selectedFeature && (
        <div
          style={{
            background: 'rgba(2, 10, 24, 0.94)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(56, 189, 248, 0.5)',
            borderRadius: '12px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.7)',
            padding: '12px',
            color: '#E2E8F0',
            fontFamily: 'Inter, system-ui, sans-serif',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Satellite size={15} color="#38BDF8" />
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#FFFFFF' }}>
                {selectedFeature.properties.name}
              </span>
            </div>
            <button
              onClick={onCloseFeatureCard}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '2px',
              }}
            >
              <X size={14} />
            </button>
          </div>

          {/* Location & Metadata */}
          <div style={{ fontSize: '9.5px', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <div>
              <strong>District:</strong> {selectedFeature.properties.district}, {selectedFeature.properties.state}
            </div>
            <div>
              <strong>Area:</strong> {selectedFeature.properties.area_ha?.toFixed(2)} hectares (Complies with 1-3,000 ha)
            </div>
            <div>
              <strong>AgroMonitoring ID:</strong> {selectedFeature.properties.agro_polygon_id || 'Pending Registration'}
            </div>
          </div>

          {/* Telemetry Metrics */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '6px',
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: '8px',
              padding: '8px',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '9px', color: '#94A3B8', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                <Droplets size={10} color="#38BDF8" />
                <span>Moisture</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#38BDF8' }}>
                {selectedFeature.properties.soil_moisture !== undefined && selectedFeature.properties.soil_moisture !== null
                  ? `${selectedFeature.properties.soil_moisture.toFixed(3)}`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '8px', color: '#64748B' }}>m³/m³</div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '9px', color: '#94A3B8', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                <Thermometer size={10} color="#F59E0B" />
                <span>Soil Temp</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#F59E0B' }}>
                {selectedFeature.properties.soil_temp_c !== undefined && selectedFeature.properties.soil_temp_c !== null
                  ? `${selectedFeature.properties.soil_temp_c.toFixed(1)}°`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '8px', color: '#64748B' }}>10cm Depth</div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '9px', color: '#94A3B8', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                <Thermometer size={10} color="#EF4444" />
                <span>Surface</span>
              </div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#EF4444' }}>
                {selectedFeature.properties.surface_temp_c !== undefined && selectedFeature.properties.surface_temp_c !== null
                  ? `${selectedFeature.properties.surface_temp_c.toFixed(1)}°`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '8px', color: '#64748B' }}>Skin Temp</div>
            </div>
          </div>

          {/* Hydrologic Interpretation */}
          <div
            style={{
              fontSize: '9px',
              padding: '6px 8px',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              color: '#CBD5E1',
            }}
          >
            <strong>Hydrologic Status: </strong>
            {selectedFeature.properties.moisture_tier === 'VERY_HIGH'
              ? 'Near-saturation. High flash-flood runoff hazard on steep slopes.'
              : selectedFeature.properties.moisture_tier === 'HIGH'
              ? 'Elevated moisture. Reduced infiltration buffer during torrential rain.'
              : selectedFeature.properties.moisture_tier === 'MODERATE'
              ? 'Standard baseline. Normal soil absorption profile.'
              : selectedFeature.properties.moisture_tier === 'LOW'
              ? 'Low moisture / dry topsoil conditions.'
              : 'Awaiting satellite telemetry pass.'}
          </div>
        </div>
      )}
    </div>
  );
};
