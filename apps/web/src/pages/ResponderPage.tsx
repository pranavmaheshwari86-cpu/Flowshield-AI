import React, { useState, useEffect } from 'react';
import {
  Truck,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Navigation,
  RotateCcw,
  Hospital,
  Radio,
  Zap,
  HeartPulse,
  Ban,
  Check,
  Compass,
  AlertCircle
} from 'lucide-react';
import { EvacuationRoute, Shelter, Alert } from '../types';
import { api } from '../services/api';

export const ResponderPage: React.FC = () => {
  const [routes, setRoutes] = useState<EvacuationRoute[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [updatingRouteId, setUpdatingRouteId] = useState<any>(null);
  const [blockageReasonInput, setBlockageReasonInput] = useState<string>('Debris and boulder obstruction on carriage way');
  const [selectedRouteForModal, setSelectedRouteForModal] = useState<EvacuationRoute | null>(null);

  // Dynamic Route Evaluation Form state
  const [evalLat, setEvalLat] = useState<string>('31.708');
  const [evalLon, setEvalLon] = useState<string>('76.932');
  const [evalResult, setEvalResult] = useState<any>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [actionNotice, setActionNotice] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rData, sData, aData] = await Promise.all([
        api.getRoutes(),
        api.getShelters(),
        api.getAlerts({ status: 'ACTIVE' }),
      ]);
      setRoutes(rData);
      setShelters(sData);
      setAlerts(aData);
    } catch (err: any) {
      console.error('Failed to load responder tactical data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleBlockage = async (route: EvacuationRoute, shouldBlock: boolean, reason?: string) => {
    try {
      setUpdatingRouteId(route.id);
      await api.setRouteBlockage(
        route.id,
        shouldBlock,
        shouldBlock ? (reason || blockageReasonInput) : undefined,
        shouldBlock ? 10.0 : 1.0
      );

      // Update local state
      setRoutes(prev =>
        prev.map(r => (r.id === route.id ? {
          ...r,
          is_blocked: shouldBlock,
          status: shouldBlock ? 'BLOCKED' : 'CLEAR',
          blockage_reason: shouldBlock ? (reason || blockageReasonInput) : undefined,
          assessed_risk_score: shouldBlock ? 95 : 15,
        } : r))
      );

      setSelectedRouteForModal(null);
      setActionNotice({
        message: `Corridor '${route.name}' successfully ${shouldBlock ? 'SEVERED (BLOCKED)' : 'RESTORED (OPEN)'}. Graph routing updated in real time.`,
        type: 'success',
      });
      setTimeout(() => setActionNotice(null), 6000);
    } catch (err: any) {
      console.error('Blockage update failed:', err);
      setActionNotice({
        message: `Permission / Network Error: ${err.message || 'Only authorized Responders/Authorities may alter corridor status. Ensure you are logged in.'}`,
        type: 'error',
      });
      setTimeout(() => setActionNotice(null), 8000);
    } finally {
      setUpdatingRouteId(null);
    }
  };

  const handleEvaluateRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(evalLat);
    const lon = parseFloat(evalLon);
    if (isNaN(lat) || isNaN(lon)) return;

    try {
      setEvaluating(true);
      setEvalResult(null);
      const result = await api.evaluateRoute({
        origin_latitude: lat,
        origin_longitude: lon,
      });
      setEvalResult(result);
    } catch (err: any) {
      console.error('Route evaluation error:', err);
      setEvalResult({
        error: true,
        message: err.message || 'Route evaluation failed',
      });
    } finally {
      setEvaluating(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: any) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      setActionNotice({
        message: `Alert #${alertId} acknowledged by field responder unit.`,
        type: 'success',
      });
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err: any) {
      setActionNotice({
        message: `Acknowledgment error: ${err.message}`,
        type: 'error',
      });
      setTimeout(() => setActionNotice(null), 4000);
    }
  };

  if (loading && routes.length === 0) {
    return (
      <div style={{ padding: '80px 20px', textAlign: 'center', color: '#94a3b8' }}>
        <Radio className="animate-spin" size={32} color="#06b6d4" style={{ margin: '0 auto 16px' }} />
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Connecting to Tactical Responder Network...</div>
        <div style={{ fontSize: '12px', marginTop: '6px' }}>Synchronizing corridor blockages, shelter occupancy, and active field alerts.</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', color: '#f1f5f9' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', padding: '6px', borderRadius: '8px', color: '#ef4444' }}>
              <Truck size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
                TACTICAL FIELD RESPONDER CONSOLE
                <span style={{ fontSize: '11px', background: '#1e355b', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', border: '1px solid #2a4778' }}>
                  SDRF / NDRF OPS
                </span>
              </h1>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0' }}>
                Live Evacuation Corridor Status • Road Blockage Severing • Shelter Resource Logistics
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ background: '#0f213e', border: '1px solid #1e355b', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
            <span>Corridors Monitored: <strong>{routes.length}</strong></span>
            <span style={{ color: '#475569' }}>|</span>
            <span style={{ color: routes.some(r => r.is_blocked || r.status === 'BLOCKED') ? '#ef4444' : '#10b981' }}>
              Blocked: <strong>{routes.filter(r => r.is_blocked || r.status === 'BLOCKED').length}</strong>
            </span>
          </div>
          <button
            onClick={loadData}
            className="btn btn-sm btn-secondary"
            title="Refresh Field Telemetry"
          >
            <RotateCcw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div
          style={{
            padding: '12px 16px',
            marginBottom: '20px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: actionNotice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: actionNotice.type === 'success' ? '1px solid #10b981' : '1px solid #ef4444',
            color: actionNotice.type === 'success' ? '#34d399' : '#f87171',
          }}
        >
          {actionNotice.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {actionNotice.message}
        </div>
      )}

      {/* Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '24px' }}>
        {/* Left Column: Corridor Management & Dynamic Evaluation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

          {/* 1. Evacuation Corridor Management Table */}
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Navigation size={18} color="#06b6d4" />
                  Evacuation Corridors & Road Obstruction Control
                </h2>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                  Toggle road blockage upon field confirmation of debris, landslides, or bridge collapse.
                </div>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1e355b', color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '10px 12px' }}>Corridor Route</th>
                    <th style={{ padding: '10px 12px' }}>Distance</th>
                    <th style={{ padding: '10px 12px' }}>Risk Score</th>
                    <th style={{ padding: '10px 12px' }}>Current Status</th>
                    <th style={{ padding: '10px 12px' }}>Blockage Reason</th>
                    <th style={{ padding: '10px 12px', textAlign: 'right' }}>Field Action</th>
                  </tr>
                </thead>
                <tbody>
                  {routes.map((route) => {
                    const isBlocked = route.is_blocked || route.status === 'BLOCKED';
                    return (
                      <tr
                        key={route.id}
                        style={{
                          borderBottom: '1px solid #14284b',
                          background: isBlocked ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                        }}
                      >
                        <td style={{ padding: '12px' }}>
                          <div style={{ fontWeight: 700, color: '#f1f5f9' }}>{route.name}</div>
                          <div style={{ fontSize: '11px', color: '#64748b' }}>
                            ID: {route.id} • {route.origin_village_name ? `From: ${route.origin_village_name}` : ''}
                          </div>
                        </td>
                        <td style={{ padding: '12px', color: '#cbd5e1' }}>
                          {route.distance_km ? `${route.distance_km.toFixed(1)} km` : '—'}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span
                            style={{
                              fontFamily: 'var(--font-mono, monospace)',
                              fontWeight: 700,
                              color: isBlocked ? '#ef4444' : (route.assessed_risk_score || 0) > 50 ? '#f59e0b' : '#10b981',
                          }}
                        >
                          {route.assessed_risk_score !== undefined ? Math.round(route.assessed_risk_score) : 15}/100
                        </span>
                        </td>
                        <td style={{ padding: '12px' }}>
                          {isBlocked ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#f87171', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 }}>
                              <Ban size={12} /> BLOCKED
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#34d399', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 }}>
                              <Check size={12} /> CLEAR
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '12px', color: '#94a3b8', fontSize: '12px', maxWidth: '200px' }}>
                          {isBlocked ? (route.blockage_reason || 'Field obstruction reported') : '—'}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {isBlocked ? (
                            <button
                              onClick={() => handleToggleBlockage(route, false)}
                              disabled={updatingRouteId === route.id}
                              className="btn btn-sm btn-outline"
                              style={{ color: '#10b981', borderColor: '#10b981' }}
                            >
                              <CheckCircle2 size={13} /> Clear Road
                            </button>
                          ) : (
                            <button
                              onClick={() => setSelectedRouteForModal(route)}
                              disabled={updatingRouteId === route.id}
                              className="btn btn-sm btn-outline"
                              style={{ color: '#ef4444', borderColor: '#ef4444' }}
                            >
                              <Ban size={13} /> Report Blockage
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 2. Tactical Route Safety Evaluator (Snap Limits & Cost Multipliers) */}
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ marginBottom: '16px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Compass size={18} color="#38bdf8" />
                Dynamic Field Evacuation Evaluation (1.5 km Snap Guard)
              </h2>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Test evacuation viability from stranded field party GPS coordinates. Checks 1.5 km network proximity and penalizes hazard zones.
              </div>
            </div>

            <form onSubmit={handleEvaluateRoute} style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'flex-end' }}>
              <div style={{ flex: '1 1 140px' }}>
                <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  LATITUDE (°N)
                </label>
                <input
                  type="text"
                  value={evalLat}
                  onChange={(e) => setEvalLat(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div style={{ flex: '1 1 140px' }}>
                <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  LONGITUDE (°E)
                </label>
                <input
                  type="text"
                  value={evalLon}
                  onChange={(e) => setEvalLon(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="submit"
                  disabled={evaluating}
                  className="btn btn-primary"
                  style={{ padding: '8px 16px', fontSize: '13px' }}
                >
                  {evaluating ? 'Computing Viability...' : 'Evaluate Route Viability'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEvalLat('31.708');
                    setEvalLon('76.932');
                  }}
                  className="btn btn-secondary"
                  style={{ padding: '8px 12px', fontSize: '12px' }}
                  title="Preset: Mandi Catchment"
                >
                  Mandi Preset
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEvalLat('32.500');
                    setEvalLon('78.500');
                  }}
                  className="btn btn-secondary"
                  style={{ padding: '8px 12px', fontSize: '12px' }}
                  title="Preset: Remote Glacial Off-Grid"
                >
                  Off-Grid Preset (&gt;1.5km)
                </button>
              </div>
            </form>

            {/* Evaluation Results Card */}
            {evalResult && (
              <div style={{ marginTop: '16px', padding: '16px', borderRadius: '8px', background: evalResult.error || evalResult.status === 'ROUTING_UNAVAILABLE_OFF_GRID' || evalResult.status === 'NO_SAFE_ROUTE_FOUND' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', border: evalResult.error || evalResult.status === 'ROUTING_UNAVAILABLE_OFF_GRID' || evalResult.status === 'NO_SAFE_ROUTE_FOUND' ? '1px solid #ef4444' : '1px solid #10b981' }}>
                {evalResult.error ? (
                  <div style={{ color: '#f87171', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertTriangle size={16} />
                    <span>Evaluation Error: {evalResult.message}</span>
                  </div>
                ) : (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '14px', fontWeight: 800, color: evalResult.status === 'RECOMMENDED_LOWER_RISK_ROUTE' ? '#34d399' : '#f87171' }}>
                        STATUS: {evalResult.status}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        Off-network snap distance: {evalResult.snap_distance_km ? `${evalResult.snap_distance_km.toFixed(2)} km` : '—'}
                      </span>
                    </div>

                    <p style={{ fontSize: '12px', color: '#cbd5e1', margin: '0 0 10px' }}>
                      {evalResult.disclaimer || evalResult.message || 'Evacuation corridor evaluation complete.'}
                    </p>

                    {evalResult.requires_authority_coordination && (
                      <div style={{ background: 'rgba(239, 68, 68, 0.2)', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', color: '#fca5a5', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                        <AlertCircle size={14} />
                        Mandatory Emergency Authority Coordination Required: Ground traversal dangerous or inaccessible.
                      </div>
                    )}

                    {evalResult.selected_route && (
                      <div style={{ fontSize: '12px', background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div><strong>Recommended Corridor:</strong> {evalResult.selected_route.name}</div>
                        <div><strong>Distance:</strong> {evalResult.selected_route.distance_km?.toFixed(1)} km</div>
                        <div><strong>Assessed Risk:</strong> {evalResult.selected_route.assessed_risk_score}/100</div>
                        <div><strong>Destination Shelter:</strong> {evalResult.selected_route.destination_shelter_name || 'Designated Base Shelter'}</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Shelter Logistics & Priority Alerts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

          {/* 3. Shelter Logistics */}
          <div className="card" style={{ padding: '20px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Hospital size={18} color="#10b981" />
              Shelter Haven Logistics
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {shelters.map((shelter) => {
                const available = shelter.capacity - shelter.current_occupancy;
                const pct = Math.min(100, Math.round((shelter.current_occupancy / shelter.capacity) * 100));
                const isFull = available <= 0;

                return (
                  <div
                    key={shelter.id}
                    style={{
                      background: '#162a4d',
                      border: '1px solid #1e355b',
                      borderRadius: '8px',
                      padding: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ fontWeight: 700, fontSize: '13px' }}>🏥 {shelter.name}</div>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: isFull ? '#ef4444' : '#10b981',
                        }}
                      >
                        {isFull ? 'FULL' : `${available} SLOTS OPEN`}
                      </span>
                    </div>

                    <div style={{ margin: '8px 0 6px', background: '#0a1628', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: pct > 85 ? '#ef4444' : pct > 60 ? '#f59e0b' : '#10b981',
                        }}
                      />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8' }}>
                      <span>Occupancy: {shelter.current_occupancy} / {shelter.capacity}</span>
                      <span>Elev: +{shelter.elevation_m}m</span>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', marginTop: '8px', fontSize: '11px', color: '#cbd5e1' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <HeartPulse size={12} color={shelter.has_medical ? '#10b981' : '#64748b'} />
                        {shelter.has_medical ? 'Medical Ready' : 'First Aid Only'}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Zap size={12} color={shelter.has_power_backup ? '#f59e0b' : '#64748b'} />
                        {shelter.has_power_backup ? 'Generator Live' : 'Grid Tied'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 4. Active Field Alerts */}
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="#ef4444" />
                Active Tactical Alerts
              </h2>
              <span style={{ fontSize: '11px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                {alerts.length} PENDING
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {alerts.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#64748b', fontSize: '12px' }}>
                  No active tactical alerts requiring field acknowledgment.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    style={{
                      background: 'rgba(239, 68, 68, 0.08)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '8px',
                      padding: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '11px', fontWeight: 800, color: '#ef4444' }}>
                        {alert.severity} • {alert.village_name || `Settlement #${alert.village_id}`}
                      </span>
                      <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                        Lead Time: ~{alert.lead_time_hours}h
                      </span>
                    </div>

                    <div style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', marginTop: '4px' }}>
                      {alert.headline || 'Urgent Evacuation Advisory'}
                    </div>

                    <div style={{ fontSize: '11px', color: '#94a3b8', margin: '4px 0 8px' }}>
                      Trigger: {alert.trigger_reason || 'Catchment rainfall surge'}
                    </div>

                    <button
                      onClick={() => handleAcknowledgeAlert(alert.id)}
                      className="btn btn-sm btn-outline"
                      style={{ width: '100%', fontSize: '11px', color: '#38bdf8', borderColor: '#2a4778' }}
                    >
                      Acknowledge Field Directive
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Blockage Confirmation Modal */}
      {selectedRouteForModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(6, 13, 23, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px',
          }}
        >
          <div
            style={{
              background: '#0f213e',
              border: '1px solid #2a4778',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '480px',
              width: '100%',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ef4444', marginBottom: '12px' }}>
              <Ban size={22} />
              <h3 style={{ fontSize: '18px', fontWeight: 800, margin: 0 }}>Report Corridor Blockage</h3>
            </div>

            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5, margin: '0 0 16px' }}>
              You are about to sever evacuation corridor <strong>{selectedRouteForModal.name}</strong>.
              Graph routing will immediately penalize this corridor (hazard cost multiplier: 10×) and re-route affected settlements.
            </p>

            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              BLOCKAGE REASON / INCIDENT DETAILS:
            </label>
            <textarea
              rows={3}
              value={blockageReasonInput}
              onChange={(e) => setBlockageReasonInput(e.target.value)}
              placeholder="e.g., Debris slide at KM 4, culvert collapse, active river overflow..."
              style={{
                width: '100%',
                padding: '10px',
                background: '#162a4d',
                color: '#f1f5f9',
                border: '1px solid #2a4778',
                borderRadius: '6px',
                fontSize: '13px',
                marginBottom: '16px',
                fontFamily: 'inherit',
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setSelectedRouteForModal(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleToggleBlockage(selectedRouteForModal, true, blockageReasonInput)}
                className="btn btn-danger"
              >
                Confirm Corridor Blocked
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
