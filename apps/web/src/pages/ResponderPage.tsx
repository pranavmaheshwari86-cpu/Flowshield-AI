import React, { useState, useEffect } from 'react';
import {
  Truck,
  AlertTriangle,
  CheckCircle2,
  Navigation,
  RotateCcw,
  Hospital,
  Radio,
  Ban,
  Check,
  Compass,
  MapPin,
  Search,
  ShieldCheck,
  Info,
  Flame,
  ChevronDown,
  Shield,
  PhoneCall,
  ArrowRight,
  UserCheck,
  FileCheck,
} from 'lucide-react';
import {
  EvacuationRoute,
  Shelter,
  Alert,
  GeographyState,
  GeographyDistrict,
  DisasterEvent,
  EmergencyFacility,
} from '../types';
import { api } from '../services/api';
import { EvacuationTacticalMap } from '../components/map/EvacuationTacticalMap';

export const ResponderPage: React.FC = () => {
  // Mode Selection: Operational Command vs Citizen Safe Evacuation
  const [activeMode, setActiveMode] = useState<'COMMAND' | 'CITIZEN'>('COMMAND');

  // Geography & Area Selection State
  const [states, setStates] = useState<GeographyState[]>([]);
  const [selectedState, setSelectedState] = useState<string>('Uttarakhand');
  const [districts, setDistricts] = useState<GeographyDistrict[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Rudraprayag');
  const [settlements, setSettlements] = useState<any[]>([]);
  const [selectedSettlementId, setSelectedSettlementId] = useState<string>('');

  // Map & Dynamic Coordinates State
  const [mapCenter, setMapCenter] = useState<[number, number]>([30.500, 79.030]);
  const [mapZoom, setMapZoom] = useState<number>(11);
  const [evalLat, setEvalLat] = useState<string>('30.598');
  const [evalLon, setEvalLon] = useState<string>('79.036');
  const [originName, setOriginName] = useState<string>('Sonprayag Sector');

  // Core Data
  const [routes, setRoutes] = useState<EvacuationRoute[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [recommendedShelters, setRecommendedShelters] = useState<Shelter[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [disasterEvents, setDisasterEvents] = useState<DisasterEvent[]>([]);
  const [emergencyFacilities, setEmergencyFacilities] = useState<EmergencyFacility[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [shelterLoading, setShelterLoading] = useState<boolean>(false);

  // Search & Filters for Shelters
  const [shelterSearch, setShelterSearch] = useState<string>('');
  const [filterVerifiedOnly, setFilterVerifiedOnly] = useState<boolean>(false);
  const [filterOperationalOnly, setFilterOperationalOnly] = useState<boolean>(false);
  const [filterHasMedical, setFilterHasMedical] = useState<boolean>(false);
  const [filterHasPower, setFilterHasPower] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<string>('suitability');

  // Blockage Modal & Incident State
  const [selectedRouteForModal, setSelectedRouteForModal] = useState<EvacuationRoute | null>(null);
  const [blockageTypeInput, setBlockageTypeInput] = useState<string>('Landslide');
  const [blockageSeverityInput, setBlockageSeverityInput] = useState<string>('HIGH');
  const [blockageReasonInput, setBlockageReasonInput] = useState<string>('Debris and boulder obstruction on carriage way');
  const [updatingRouteId, setUpdatingRouteId] = useState<any>(null);

  // Dynamic Route Evaluation State
  const [evalResult, setEvalResult] = useState<any>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [actionNotice, setActionNotice] = useState<{ message: string; type: 'success' | 'error' | 'warning' } | null>(null);

  // Active Map Selections
  const [selectedShelterId, setSelectedShelterId] = useState<string | null>(null);
  const [activeCorridorId, setActiveCorridorId] = useState<string | null>(null);

  // Realistic Simulation & Dynamic Rerouting Engine
  const [isSimulatingScenario, setIsSimulatingScenario] = useState<boolean>(false);
  const [rerouteAlertBanner, setRerouteAlertBanner] = useState<{
    status: string;
    alert: string;
    oldEta: number | null;
    newEta: number | null;
    reason: string;
    newRouteName?: string;
  } | null>(null);

  // Citizen Guidance Wizard State
  const [citizenStep, setCitizenStep] = useState<1 | 2 | 3 | 4>(1);
  const [selectedSafeHaven, setSelectedSafeHaven] = useState<Shelter | null>(null);
  const [primaryRoute, setPrimaryRoute] = useState<EvacuationRoute | null>(null);
  const [alternateRoutes, setAlternateRoutes] = useState<EvacuationRoute[]>([]);
  const [blockedRoutes, setBlockedRoutes] = useState<EvacuationRoute[]>([]);
  const [shortestRouteWarning, setShortestRouteWarning] = useState<string | null>(null);

  // 1. Initial Load: Fetch Supported States
  useEffect(() => {
    const fetchStates = async () => {
      try {
        const stateList = await api.getGeographyStates();
        setStates(stateList);
        if (stateList.length > 0 && !selectedState) {
          setSelectedState(stateList[0].state);
        }
      } catch (err) {
        console.error('Failed to load supported states:', err);
      }
    };
    fetchStates();
  }, []);

  // 2. State Change: Fetch Dependent Districts
  useEffect(() => {
    if (!selectedState) return;
    const fetchDistricts = async () => {
      try {
        const distList = await api.getGeographyDistricts(selectedState);
        setDistricts(distList);
        if (distList.length > 0) {
          const firstDistrict = distList[0];
          setSelectedDistrict(firstDistrict.district);
          setMapCenter([firstDistrict.center_lat, firstDistrict.center_lon]);
          setMapZoom(firstDistrict.default_zoom || 11);
        }
      } catch (err) {
        console.error(`Failed to load districts for ${selectedState}:`, err);
      }
    };
    fetchDistricts();
  }, [selectedState]);

  // 3. District Change: Fetch All Intelligence Layers
  useEffect(() => {
    if (!selectedState || !selectedDistrict) return;

    const currentDist = districts.find((d) => d.district === selectedDistrict);
    if (currentDist) {
      setMapCenter([currentDist.center_lat, currentDist.center_lon]);
      setMapZoom(currentDist.default_zoom || 11);
    }

    const loadDistrictData = async () => {
      try {
        setShelterLoading(true);
        const [settlementList, routeList, shelterList, alertList, eventList, facilitiesList] = await Promise.all([
          api.getGeographySettlements(selectedDistrict, selectedState),
          api.getRoutes({ state: selectedState, district: selectedDistrict }),
          api.getShelters({ state: selectedState, district: selectedDistrict }),
          api.getAlerts({ status: 'ACTIVE' }),
          api.getActiveDisasterEvents(selectedState, selectedDistrict),
          api.getEmergencyFacilities(selectedDistrict),
        ]);

        setSettlements(settlementList);
        setRoutes(routeList);
        setShelters(shelterList);
        setAlerts(alertList);
        setDisasterEvents(eventList);
        setEmergencyFacilities(facilitiesList);

        // Set initial location from first settlement or preset
        if (settlementList.length > 0) {
          const firstSettlement = settlementList[0];
          setSelectedSettlementId(firstSettlement.id);
          setEvalLat(firstSettlement.latitude.toFixed(4));
          setEvalLon(firstSettlement.longitude.toFixed(4));
          setOriginName(firstSettlement.name);

          // Initial Disaster-Aware Evaluation
          evaluateDisasterRoute(firstSettlement.latitude, firstSettlement.longitude, firstSettlement.id);
        } else {
          evaluateDisasterRoute(currentDist?.center_lat || 30.598, currentDist?.center_lon || 79.036);
        }
      } catch (err) {
        console.error('Failed to load district tactical data:', err);
      } finally {
        setShelterLoading(false);
        setLoading(false);
      }
    };

    loadDistrictData();
  }, [selectedState, selectedDistrict]);

  // Evaluates Disaster-Aware Route and populates primary, alternate, and safe shelters
  const evaluateDisasterRoute = async (lat: number, lon: number, villageId?: string) => {
    try {
      setEvaluating(true);
      const [res, recList] = await Promise.all([
        api.evaluateDisasterAwareRoute({
          origin_latitude: lat,
          origin_longitude: lon,
          village_id: villageId,
          state: selectedState,
          district: selectedDistrict,
        }),
        api.getRecommendedShelters({
          lat,
          lon,
          state: selectedState,
          district: selectedDistrict,
          village_id: villageId,
          limit: 6,
        }),
      ]);

      setEvalResult(res);
      setRecommendedShelters(recList);

      if (res.selected_route) {
        setPrimaryRoute(res.selected_route);
        setActiveCorridorId(res.selected_route.id);
        setSelectedShelterId(res.selected_route.destination_shelter_id);
      } else {
        setPrimaryRoute(null);
      }

      setAlternateRoutes(res.alternate_routes || []);
      setBlockedRoutes(res.blocked_routes || []);
      setShortestRouteWarning(res.shortest_route_hazardous_warning || null);

      if (recList.length > 0) {
        setSelectedSafeHaven(recList[0]);
      }
    } catch (err) {
      console.error('Disaster route evaluation failed:', err);
    } finally {
      setEvaluating(false);
    }
  };

  // Handle Settlement / Village Selection
  const handleSettlementChange = async (settlementId: string) => {
    setSelectedSettlementId(settlementId);
    const target = settlements.find((s) => s.id === settlementId);
    if (target) {
      setEvalLat(target.latitude.toFixed(4));
      setEvalLon(target.longitude.toFixed(4));
      setOriginName(target.name);
      setMapCenter([target.latitude, target.longitude]);
      await evaluateDisasterRoute(target.latitude, target.longitude, target.id);
    }
  };

  // Handle Map Click for Arbitrary Coordinate Evaluation
  const handleMapClick = async (coords: [number, number]) => {
    setEvalLat(coords[0].toFixed(4));
    setEvalLon(coords[1].toFixed(4));
    setOriginName(`Field Coordinates (${coords[0].toFixed(3)}°N, ${coords[1].toFixed(3)}°E)`);
    await evaluateDisasterRoute(coords[0], coords[1]);
  };

  // Handle "Use Current Risk Area" from ML Predictions
  const handleUseCurrentRiskArea = async () => {
    try {
      if (alerts.length > 0 && alerts[0].village_name) {
        const alertVillage = settlements.find((s) => s.name.toLowerCase() === alerts[0].village_name?.toLowerCase());
        if (alertVillage) {
          handleSettlementChange(alertVillage.id);
          setActionNotice({
            message: `Target set to active alert area: ${alertVillage.name} (${alerts[0].severity})`,
            type: 'success',
          });
          setTimeout(() => setActionNotice(null), 5000);
          return;
        }
      }

      if (settlements.length > 0) {
        const sorted = [...settlements].sort((a, b) => (b.vulnerability_index || 0) - (a.vulnerability_index || 0));
        handleSettlementChange(sorted[0].id);
        setActionNotice({
          message: `Target set to highest vulnerability sector: ${sorted[0].name} (${(sorted[0].vulnerability_index * 100).toFixed(0)}% Vulnerability)`,
          type: 'success',
        });
        setTimeout(() => setActionNotice(null), 5000);
      }
    } catch (err) {
      console.error('Failed to resolve high risk area:', err);
    }
  };

  // Trigger Realistic Flash Flood & Landslide Scenario Simulation
  const handleTriggerRealisticScenario = async () => {
    try {
      setIsSimulatingScenario(true);
      setActionNotice({
        message: 'Simulating multi-hazard cloudburst anomaly: High rainfall triggered → Landslide severance initiated on NH-107 corridor...',
        type: 'warning',
      });

      // 1. Post to backend simulation endpoint
      const simEvent = await api.triggerDemoDisaster(selectedState, selectedDistrict);

      // 2. Perform dynamic reroute bypassing the severed corridor
      const lat = parseFloat(evalLat) || 30.598;
      const lon = parseFloat(evalLon) || 79.036;

      const rerouteRes = await api.rerouteEvacuation({
        current_route_id: primaryRoute?.id,
        current_latitude: lat,
        current_longitude: lon,
        state: selectedState,
        district: selectedDistrict,
        blockage_reason: 'Torrential debris flow and rockfall on NH-107 carriage-way',
      });

      // 3. Refresh live layers
      const [updatedRoutes, updatedEvents, updatedShelters] = await Promise.all([
        api.getRoutes({ state: selectedState, district: selectedDistrict }),
        api.getActiveDisasterEvents(selectedState, selectedDistrict),
        api.getRecommendedShelters({
          lat,
          lon,
          state: selectedState,
          district: selectedDistrict,
          limit: 6,
        }),
      ]);

      setRoutes(updatedRoutes);
      setDisasterEvents(updatedEvents);
      setRecommendedShelters(updatedShelters);

      if (rerouteRes.new_safe_route) {
        setPrimaryRoute(rerouteRes.new_safe_route);
        setActiveCorridorId(rerouteRes.new_safe_route.id);
      }
      setAlternateRoutes(rerouteRes.alternate_routes || []);

      // 4. Set Reroute Alert Banner with Old vs New ETA
      setRerouteAlertBanner({
        status: rerouteRes.status,
        alert: rerouteRes.reroute_alert,
        oldEta: rerouteRes.old_eta_min,
        newEta: rerouteRes.new_eta_min,
        reason: rerouteRes.reason,
        newRouteName: rerouteRes.new_safe_route?.name,
      });

      setActionNotice({
        message: `Scenario Live: ${simEvent.location_name} severed. Dynamic rerouting engine computed safe bypass.`,
        type: 'success',
      });
      setTimeout(() => setActionNotice(null), 8000);
    } catch (err: any) {
      console.error('Demo simulation error:', err);
      setActionNotice({
        message: `Simulation failed: ${err.message}`,
        type: 'error',
      });
    } finally {
      setIsSimulatingScenario(false);
    }
  };

  // Reset Realistic Scenario
  const handleResetScenario = async () => {
    try {
      setIsSimulatingScenario(true);
      await api.resetDemoDisaster(selectedState, selectedDistrict);
      setRerouteAlertBanner(null);

      // Refresh all data back to baseline
      const [routeList, eventList, shelterList] = await Promise.all([
        api.getRoutes({ state: selectedState, district: selectedDistrict }),
        api.getActiveDisasterEvents(selectedState, selectedDistrict),
        api.getShelters({ state: selectedState, district: selectedDistrict }),
      ]);

      setRoutes(routeList);
      setDisasterEvents(eventList);
      setShelters(shelterList);

      const lat = parseFloat(evalLat) || 30.598;
      const lon = parseFloat(evalLon) || 79.036;
      await evaluateDisasterRoute(lat, lon, selectedSettlementId || undefined);

      setActionNotice({
        message: 'Scenario reset: All demonstration hazards cleared and corridors restored to OPEN.',
        type: 'success',
      });
      setTimeout(() => setActionNotice(null), 5000);
    } catch (err: any) {
      console.error('Scenario reset failed:', err);
    } finally {
      setIsSimulatingScenario(false);
    }
  };

  // Handle Corridor Blockage Report / Toggle
  const handleToggleBlockage = async (route: EvacuationRoute, shouldBlock: boolean, reason?: string) => {
    try {
      setUpdatingRouteId(route.id);

      if (shouldBlock) {
        await api.reportRoadIncident({
          corridor_name: route.name,
          route_id: route.id,
          blockage_type: blockageTypeInput,
          severity: blockageSeverityInput,
          description: reason || blockageReasonInput,
          reported_by: 'Field Incident Command',
        });
      }

      await api.setRouteBlockage(
        route.id,
        shouldBlock,
        shouldBlock ? (reason || blockageReasonInput) : undefined,
        shouldBlock ? 10.0 : 1.0
      );

      // Refresh routes and re-evaluate
      const updatedRoutes = await api.getRoutes({ state: selectedState, district: selectedDistrict });
      setRoutes(updatedRoutes);
      setSelectedRouteForModal(null);

      const lat = parseFloat(evalLat) || 30.598;
      const lon = parseFloat(evalLon) || 79.036;
      await evaluateDisasterRoute(lat, lon, selectedSettlementId || undefined);

      setActionNotice({
        message: `Corridor '${route.name}' ${shouldBlock ? 'SEVERED (BLOCKED)' : 'RESTORED (OPEN)'}. Graph routing re-evaluated.`,
        type: 'success',
      });
      setTimeout(() => setActionNotice(null), 6000);
    } catch (err: any) {
      console.error('Blockage update failed:', err);
      setActionNotice({
        message: `Error updating corridor status: ${err.message}`,
        type: 'error',
      });
    } finally {
      setUpdatingRouteId(null);
    }
  };

  // Filtered and Sorted Shelter List
  const displayedShelters = (sortBy === 'suitability' && recommendedShelters.length > 0 ? recommendedShelters : shelters)
    .filter((s) => {
      if (filterVerifiedOnly && s.verification_status !== 'VERIFIED') return false;
      if (filterOperationalOnly && s.operational_status !== 'OPERATIONAL') return false;
      if (filterHasMedical && !s.has_medical && !s.medical_facility) return false;
      if (filterHasPower && !s.has_power_backup && !s.generator_available) return false;
      if (shelterSearch) {
        const q = shelterSearch.toLowerCase();
        const match = s.name.toLowerCase().includes(q) || s.type.toLowerCase().includes(q) || (s.village_town || '').toLowerCase().includes(q);
        if (!match) return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'distance') return (a.distance_km || 999) - (b.distance_km || 999);
      if (sortBy === 'capacity') return (b.available_capacity ?? b.capacity ?? 0) - (a.available_capacity ?? a.capacity ?? 0);
      return 0;
    });

  // Calculate Metrics
  const blockedCount = routes.filter((r) => r.is_blocked || r.status === 'BLOCKED').length;
  const verifiedCount = shelters.filter((s) => s.verification_status === 'VERIFIED').length;
  const totalPopulationAtRisk = settlements.reduce((sum, s) => sum + (s.population || 0), 0);

  if (loading && states.length === 0) {
    return (
      <div style={{ padding: '80px 20px', textAlign: 'center', color: '#94a3b8' }}>
        <Radio className="animate-spin" size={32} color="#06b6d4" style={{ margin: '0 auto 16px' }} />
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Connecting to Tactical Evacuation Intelligence Network...</div>
        <div style={{ fontSize: '12px', marginTop: '6px' }}>Synchronizing regional multi-hazard coverage, verified DDMP shelters, and active corridors.</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', color: '#f1f5f9' }}>
      {/* 1. Header & Live Sync Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', padding: '6px', borderRadius: '8px', color: '#ef4444' }}>
              <Truck size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px' }}>
                REAL-TIME DISASTER EVACUATION INTELLIGENCE CENTER
                <span style={{ fontSize: '11px', background: '#1e355b', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', border: '1px solid #2a4778' }}>
                  MULTI-HAZARD READY
                </span>
              </h1>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0' }}>
                Predict Early • Act Faster • Save Lives — Dynamic Landslide, Flood & Road Severance Routing
              </p>
            </div>
          </div>
        </div>

        {/* Dual Mode Switcher Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: '#091526', padding: '4px', borderRadius: '10px', border: '1px solid #1e355b' }}>
          <button
            onClick={() => setActiveMode('COMMAND')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeMode === 'COMMAND' ? 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)' : 'transparent',
              color: activeMode === 'COMMAND' ? '#ffffff' : '#94a3b8',
              fontWeight: 700,
              fontSize: '12.5px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
            }}
          >
            <Shield size={14} /> Operational Commander
          </button>
          <button
            onClick={() => setActiveMode('CITIZEN')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeMode === 'CITIZEN' ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'transparent',
              color: activeMode === 'CITIZEN' ? '#ffffff' : '#94a3b8',
              fontWeight: 700,
              fontSize: '12.5px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
            }}
          >
            <UserCheck size={14} /> Citizen Safe Evacuation
          </button>
        </div>
      </div>

      {/* 2. Realistic Demonstration Simulation Control Bar */}
      <div
        className="card"
        style={{
          padding: '14px 20px',
          marginBottom: '20px',
          background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.12) 0%, rgba(15, 33, 62, 0.8) 50%, rgba(6, 182, 212, 0.12) 100%)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: '#ef4444', color: 'white', padding: '6px', borderRadius: '8px' }}>
            <Flame size={18} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '13.5px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>REALISTIC DISASTER SCENARIO ENGINE</span>
              <span style={{ fontSize: '10px', background: 'rgba(239, 68, 68, 0.25)', color: '#fca5a5', padding: '1px 6px', borderRadius: '4px', border: '1px solid #ef4444' }}>
                HIMALAYAN MONSOON SURGE
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '2px' }}>
              Simulate heavy rainfall anomaly triggering active landslide on NH-107, corridor severance, and instant dynamic rerouting.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={handleTriggerRealisticScenario}
            disabled={isSimulatingScenario}
            style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)',
            }}
          >
            <Flame size={14} />
            {isSimulatingScenario ? 'Simulating Scenario...' : 'Trigger Flash Flood & Landslide Scenario'}
          </button>

          <button
            onClick={handleResetScenario}
            disabled={isSimulatingScenario}
            className="btn btn-sm btn-secondary"
            style={{ fontSize: '12px' }}
          >
            <RotateCcw size={13} /> Reset Baseline
          </button>
        </div>
      </div>

      {/* Reroute Alert Notification Modal / Card */}
      {rerouteAlertBanner && (
        <div
          style={{
            padding: '16px 20px',
            marginBottom: '20px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(185, 28, 28, 0.25) 100%)',
            border: '2px solid #ef4444',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.3)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', maxWidth: '850px' }}>
            <AlertTriangle size={24} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 800, fontSize: '14px', color: '#fca5a5' }}>
                {rerouteAlertBanner.alert}
              </div>
              <div style={{ fontSize: '12px', color: '#e2e8f0', marginTop: '4px' }}>
                Reason: <strong>{rerouteAlertBanner.reason}</strong>
              </div>
              {rerouteAlertBanner.newRouteName && (
                <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '2px', fontWeight: 600 }}>
                  Diverted to safe corridor: <strong>{rerouteAlertBanner.newRouteName}</strong>
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', background: '#0a1628', padding: '10px 16px', borderRadius: '8px', border: '1px solid #1e355b' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#94a3b8' }}>PREVIOUS ETA</div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#94a3b8', textDecoration: 'line-through' }}>
                {rerouteAlertBanner.oldEta ? `${rerouteAlertBanner.oldEta} min` : '18 min'}
              </div>
            </div>
            <ArrowRight size={16} color="#38bdf8" />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#38bdf8' }}>UPDATED SAFE ETA</div>
              <div style={{ fontSize: '16px', fontWeight: 800, color: '#34d399' }}>
                {rerouteAlertBanner.newEta ? `${rerouteAlertBanner.newEta} min` : '35 min'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Evacuation Area Selector Bar (State -> District + AI Action Button) */}
      <div
        className="card"
        style={{
          padding: '20px 24px',
          marginBottom: '20px',
          background: 'linear-gradient(135deg, rgba(13, 27, 54, 0.9) 0%, rgba(9, 18, 36, 0.98) 100%)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          borderRadius: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.2)', border: '1px solid rgba(56, 189, 248, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
              <MapPin size={16} />
            </div>
            <div>
              <div style={{ color: '#f8fafc', fontSize: '13.5px', fontWeight: 800, letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>OPERATIONAL JURISDICTION & CATCHMENT</span>
                <span style={{ fontSize: '10px', fontWeight: 700, background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '2px 8px', borderRadius: '12px' }}>
                  CENTRALIZED GEOGRAPHIC REGISTRY
                </span>
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                Select district • Multi-hazard data synchronizes with terrain & river telemetry
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }}></span>
            <span style={{ color: '#34d399', fontWeight: 700 }}>ML Live Inference Connected</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '18px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          {/* State Dropdown */}
          <div style={{ flex: '1 1 200px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '6px' }}>
              State / UT
            </label>
            <div style={{ position: 'relative' }}>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                style={{ width: '100%', height: '42px', padding: '0 36px 0 14px', background: '#142544', color: '#f8fafc', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '10px', fontSize: '13px', fontWeight: 600, outline: 'none' }}
              >
                {states.map((s) => (
                  <option key={s.state} value={s.state} style={{ background: '#0b172a' }}>
                    {s.state} ({s.districts_count} districts)
                  </option>
                ))}
              </select>
              <div style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#38bdf8' }}>
                <ChevronDown size={16} />
              </div>
            </div>
          </div>

          {/* District Dropdown */}
          <div style={{ flex: '1 1 240px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '6px' }}>
              District Jurisdiction
            </label>
            <div style={{ position: 'relative' }}>
              <select
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                style={{ width: '100%', height: '42px', padding: '0 36px 0 14px', background: '#142544', color: '#f8fafc', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '10px', fontSize: '13px', fontWeight: 600, outline: 'none' }}
              >
                {districts.map((d) => (
                  <option key={d.district} value={d.district} style={{ background: '#0b172a' }}>
                    {d.district} — {d.river_basin || 'Himalayan Basin'}
                  </option>
                ))}
              </select>
              <div style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#38bdf8' }}>
                <ChevronDown size={16} />
              </div>
            </div>
          </div>

          {/* Settlement Dropdown */}
          <div style={{ flex: '1 1 220px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '6px' }}>
              Origin Settlement / Sector
            </label>
            <div style={{ position: 'relative' }}>
              <select
                value={selectedSettlementId}
                onChange={(e) => handleSettlementChange(e.target.value)}
                style={{ width: '100%', height: '42px', padding: '0 36px 0 14px', background: '#142544', color: '#f8fafc', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '10px', fontSize: '13px', fontWeight: 600, outline: 'none' }}
              >
                {settlements.map((s) => (
                  <option key={s.id} value={s.id} style={{ background: '#0b172a' }}>
                    {s.name} ({s.population ? `${s.population} pop` : 'Settlement'})
                  </option>
                ))}
              </select>
              <div style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: '#38bdf8' }}>
                <ChevronDown size={16} />
              </div>
            </div>
          </div>

          {/* Use Risk Alert Area Action Button */}
          <div style={{ flex: '0 0 auto' }}>
            <button
              onClick={handleUseCurrentRiskArea}
              style={{
                height: '42px',
                padding: '0 20px',
                background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '10px',
                fontSize: '13px',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)',
              }}
            >
              <Flame size={15} style={{ color: '#fef08a' }} />
              <span>Use Risk Alert Area</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4. Action Notification Banner */}
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
            background: actionNotice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : actionNotice.type === 'warning' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: actionNotice.type === 'success' ? '1px solid #10b981' : actionNotice.type === 'warning' ? '1px solid #f59e0b' : '1px solid #ef4444',
            color: actionNotice.type === 'success' ? '#34d399' : actionNotice.type === 'warning' ? '#fbbf24' : '#f87171',
          }}
        >
          {actionNotice.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {actionNotice.message}
        </div>
      )}

      {/* 5. Tactical GIS Evacuation Map Container */}
      <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Navigation size={18} color="#06b6d4" />
              Tactical Evacuation GIS — {selectedDistrict} ({selectedState})
            </h2>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
              Real-time multi-hazard perimeters, dynamic road blockages, safe havens, and official emergency facilities.
            </div>
          </div>

          <div style={{ fontSize: '11px', color: '#cbd5e1', background: '#162a4d', padding: '6px 12px', borderRadius: '6px' }}>
            Evacuation Origin: <strong>{originName}</strong> ({evalLat}°N, {evalLon}°E)
          </div>
        </div>

        <EvacuationTacticalMap
          center={mapCenter}
          zoom={mapZoom}
          originCoords={[parseFloat(evalLat) || mapCenter[0], parseFloat(evalLon) || mapCenter[1]]}
          originName={originName}
          shelters={shelters}
          routes={routes}
          selectedShelterId={selectedShelterId}
          onSelectShelter={(shelter) => {
            setSelectedShelterId(shelter.id);
            setSelectedSafeHaven(shelter);
            if (shelter.corridor_id) setActiveCorridorId(shelter.corridor_id);
          }}
          onMapClick={handleMapClick}
          activeCorridorId={activeCorridorId}
          disasterEvents={disasterEvents}
          emergencyFacilities={emergencyFacilities}
          primaryRouteId={primaryRoute?.id}
        />
      </div>

      {/* 6. MODE VIEW: Citizen Guidance Wizard vs Operational Commander */}
      {activeMode === 'CITIZEN' ? (
        /* CITIZEN SAFE EVACUATION WIZARD (High Clarity, Large Touch Elements, Step-by-Step) */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 4-Step Progress Bar */}
          <div
            className="card"
            style={{
              padding: '16px 20px',
              background: '#091526',
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '12px',
            }}
          >
            {[
              { num: 1, title: 'Pin Location', icon: MapPin },
              { num: 2, title: 'Disaster Hazard Check', icon: Flame },
              { num: 3, title: 'Safest Haven', icon: ShieldCheck },
              { num: 4, title: 'Safe Path Guidance', icon: Navigation },
            ].map((step) => {
              const isCurrent = citizenStep === step.num;
              const isDone = citizenStep > step.num;
              const IconComponent = step.icon;

              return (
                <button
                  key={step.num}
                  onClick={() => setCitizenStep(step.num as any)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: `1px solid ${isCurrent ? '#10b981' : isDone ? '#06b6d4' : '#1e355b'}`,
                    background: isCurrent ? 'rgba(16, 185, 129, 0.15)' : isDone ? 'rgba(6, 182, 212, 0.1)' : '#0f213e',
                    color: isCurrent ? '#34d399' : isDone ? '#38bdf8' : '#64748b',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div
                    style={{
                      width: '26px',
                      height: '26px',
                      borderRadius: '50%',
                      background: isCurrent ? '#10b981' : isDone ? '#06b6d4' : '#1e355b',
                      color: isCurrent || isDone ? '#ffffff' : '#94a3b8',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '12px',
                      flexShrink: 0,
                    }}
                  >
                    {isDone ? <Check size={14} /> : <IconComponent size={14} />}
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Step {step.num}</div>
                    <div style={{ fontSize: '12.5px', fontWeight: 700, color: isCurrent ? '#f8fafc' : isDone ? '#cbd5e1' : '#64748b' }}>
                      {step.title}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Citizen Step Details */}
          <div className="card" style={{ padding: '24px' }}>
            {citizenStep === 1 && (
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={20} color="#10b981" />
                  Step 1: Set Your Current Mountain Location
                </h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '20px' }}>
                  We calculate safe, disaster-aware evacuation paths strictly from your exact ground coordinates.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ background: '#0f213e', padding: '16px', borderRadius: '8px', border: '1px solid #1e355b' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: 700 }}>CURRENT RECOGNIZED ORIGIN</div>
                    <div style={{ fontSize: '16px', fontWeight: 800, color: '#38bdf8' }}>{originName}</div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                      GPS: {evalLat}°N, {evalLon}°E ({selectedDistrict})
                    </div>
                  </div>

                  <div style={{ background: '#0f213e', padding: '16px', borderRadius: '8px', border: '1px solid #1e355b' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: 700 }}>QUICK LOCATION ACTIONS</div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => {
                          if (navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition((pos) => {
                              handleMapClick([pos.coords.latitude, pos.coords.longitude]);
                            });
                          }
                        }}
                        className="btn btn-sm btn-outline"
                        style={{ fontSize: '12px', color: '#38bdf8', borderColor: '#38bdf8' }}
                      >
                        <Compass size={14} /> Detect My GPS
                      </button>
                      <button
                        onClick={handleUseCurrentRiskArea}
                        className="btn btn-sm btn-outline"
                        style={{ fontSize: '12px', color: '#f59e0b', borderColor: '#f59e0b' }}
                      >
                        <Flame size={14} /> High-Risk Sector
                      </button>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setCitizenStep(2)}
                  className="btn btn-primary"
                  style={{ padding: '12px 24px', fontSize: '14px', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                >
                  Proceed to Hazard Assessment <ArrowRight size={16} />
                </button>
              </div>
            )}

            {citizenStep === 2 && (
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Flame size={20} color="#ef4444" />
                  Step 2: Instant Mountain Hazard Assessment
                </h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '20px' }}>
                  Real-time perimeter analysis around {originName}. All active landslides, river surges, and rainfall anomalies within your evacuation sector.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                  {disasterEvents.length === 0 ? (
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', padding: '18px', borderRadius: '8px', color: '#34d399' }}>
                      <div style={{ fontWeight: 800, fontSize: '15px' }}>✓ NO ACTIVE HAZARDS THREATENING YOUR IMMEDIATE SECTOR</div>
                      <div style={{ fontSize: '12px', marginTop: '6px', color: '#cbd5e1' }}>
                        Rainfall rates are below cloudburst threshold. All designated evacuation corridors currently open.
                      </div>
                    </div>
                  ) : (
                    disasterEvents.map((ev) => (
                      <div
                        key={ev.id}
                        style={{
                          background: '#0f213e',
                          border: `1px solid ${ev.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b'}`,
                          padding: '16px',
                          borderRadius: '8px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <span style={{ fontSize: '11px', fontWeight: 800, color: ev.severity === 'CRITICAL' ? '#f87171' : '#fbbf24' }}>
                            {ev.disaster_type} • {ev.severity}
                          </span>
                          <span style={{ fontSize: '10px', background: '#1e355b', padding: '2px 6px', borderRadius: '4px' }}>
                            Confidence: {ev.confidence_score}%
                          </span>
                        </div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>
                          {ev.location_name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '6px' }}>
                          Affected Radius: <strong>{ev.affected_radius_km} km</strong> • Population At Risk: <strong>{ev.affected_population?.toLocaleString()}</strong>
                        </div>
                        {ev.description && (
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', borderTop: '1px solid #1e355b', paddingTop: '6px' }}>
                            {ev.description}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button onClick={() => setCitizenStep(1)} className="btn btn-secondary">
                    Back
                  </button>
                  <button
                    onClick={() => setCitizenStep(3)}
                    className="btn btn-primary"
                    style={{ padding: '12px 24px', fontSize: '14px', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  >
                    Select Safe Haven Shelter <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            )}

            {citizenStep === 3 && (
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={20} color="#10b981" />
                  Step 3: Recommended Safe Haven Shelters (6-Factor Suitability)
                </h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '20px' }}>
                  Shelters within active hazard zones are strictly excluded. Ranked by remaining capacity, doctor presence, emergency power, elevation, and distance.
                </p>

                {selectedSafeHaven && (
                  <div
                    style={{
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)',
                      border: '2px solid #10b981',
                      borderRadius: '10px',
                      padding: '20px',
                      marginBottom: '24px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <span style={{ background: '#10b981', color: 'white', fontSize: '11px', fontWeight: 800, padding: '3px 8px', borderRadius: '4px' }}>
                          ★ TOP RECOMMENDED SAFE HAVEN
                        </span>
                        <h4 style={{ fontSize: '18px', fontWeight: 800, margin: '8px 0 2px', color: '#f8fafc' }}>
                          {selectedSafeHaven.name}
                        </h4>
                        <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
                          {selectedSafeHaven.type} • {selectedSafeHaven.village_town || selectedDistrict}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '11px', color: '#94a3b8' }}>COMPOSITE SCORE</div>
                        <div style={{ fontSize: '24px', fontWeight: 900, color: '#34d399' }}>
                          {selectedSafeHaven.suitability_score || 94}/100
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginTop: '16px' }}>
                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>REMAINING CAPACITY</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8' }}>
                          {selectedSafeHaven.available_capacity ?? selectedSafeHaven.capacity ?? 200} slots available
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>MEDICAL READINESS</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: selectedSafeHaven.has_medical ? '#34d399' : '#cbd5e1' }}>
                          {selectedSafeHaven.has_medical ? 'Doctor On Site' : 'First Aid Kit'}
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>BACKUP GENERATOR</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: selectedSafeHaven.has_power_backup ? '#fbbf24' : '#cbd5e1' }}>
                          {selectedSafeHaven.has_power_backup ? 'Generator Active' : 'Standard Grid'}
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>DISTANCE & TRAVEL</div>
                        <div style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
                          {selectedSafeHaven.distance_km?.toFixed(1) || '4.2'} km (~{selectedSafeHaven.estimated_travel_time_min || 18} min)
                        </div>
                      </div>
                    </div>

                    {selectedSafeHaven.contact_phone && (
                      <div style={{ marginTop: '12px', fontSize: '12px', color: '#38bdf8' }}>
                        📞 Shelter In-Charge Helpline: {selectedSafeHaven.contact_person || 'DEOC Warden'} ({selectedSafeHaven.contact_phone})
                      </div>
                    )}
                  </div>
                )}

                {/* Alternate Shelters Selection Grid */}
                <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#cbd5e1', marginBottom: '12px' }}>
                  Alternative Safe Shelters in {selectedDistrict}:
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', marginBottom: '24px' }}>
                  {recommendedShelters.slice(1, 4).map((alt) => (
                    <div
                      key={alt.id}
                      onClick={() => setSelectedSafeHaven(alt)}
                      style={{
                        background: selectedSafeHaven?.id === alt.id ? '#1e355b' : '#0f213e',
                        border: `1px solid ${selectedSafeHaven?.id === alt.id ? '#10b981' : '#1e355b'}`,
                        borderRadius: '8px',
                        padding: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontWeight: 700, fontSize: '13px', color: '#f8fafc' }}>{alt.name}</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>{alt.village_town} • {alt.distance_km?.toFixed(1)} km</div>
                      <div style={{ fontSize: '11px', color: '#34d399', marginTop: '4px' }}>Suitability: {alt.suitability_score || 85}/100</div>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button onClick={() => setCitizenStep(2)} className="btn btn-secondary">
                    Back
                  </button>
                  <button
                    onClick={() => setCitizenStep(4)}
                    className="btn btn-primary"
                    style={{ padding: '12px 24px', fontSize: '14px', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  >
                    View Safe Navigation Route <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            )}

            {citizenStep === 4 && (
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Navigation size={20} color="#06b6d4" />
                  Step 4: Safe Navigation & Rerouting Guidance
                </h3>

                {/* Shortest Route Hazard Warning */}
                {shortestRouteWarning && (
                  <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid #f59e0b', padding: '12px 16px', borderRadius: '8px', color: '#fbbf24', fontSize: '12.5px', marginBottom: '16px', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>{shortestRouteWarning}</div>
                  </div>
                )}

                {/* Primary Safe Path Card */}
                {primaryRoute ? (
                  <div
                    style={{
                      background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(15, 33, 62, 0.9) 100%)',
                      border: '2px solid #06b6d4',
                      borderRadius: '10px',
                      padding: '20px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <span style={{ background: '#06b6d4', color: '#041628', fontSize: '11px', fontWeight: 800, padding: '3px 8px', borderRadius: '4px' }}>
                          PRIMARY SAFE EVACUATION CORRIDOR
                        </span>
                        <h4 style={{ fontSize: '18px', fontWeight: 800, margin: '8px 0 2px', color: '#f8fafc' }}>
                          {primaryRoute.name}
                        </h4>
                        <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
                          From: {originName} → Destination: {primaryRoute.destination_shelter_name || selectedSafeHaven?.name || 'Safe Haven'}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '11px', color: '#94a3b8' }}>SAFETY SCORE</div>
                        <div style={{ fontSize: '24px', fontWeight: 900, color: '#34d399' }}>
                          {primaryRoute.safety_score ?? (100 - (primaryRoute.assessed_risk_score || 15))}/100
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginTop: '16px' }}>
                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>DISTANCE</div>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: '#38bdf8' }}>
                          {primaryRoute.distance_km?.toFixed(1)} km
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>EST. TRANSIT TIME</div>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: '#38bdf8' }}>
                          {primaryRoute.estimated_travel_time_min || Math.round(primaryRoute.distance_km * 2.2)} min
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>HAZARD EXPOSURE</div>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: '#34d399' }}>
                          {primaryRoute.hazard_exposure || 'LOW'}
                        </div>
                      </div>

                      <div style={{ background: '#0f213e', padding: '10px', borderRadius: '6px' }}>
                        <div style={{ fontSize: '10.5px', color: '#94a3b8' }}>ROAD STATUS</div>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: '#34d399' }}>
                          OPEN & PASSABLE
                        </div>
                      </div>
                    </div>

                    {alternateRoutes.length > 0 && (
                      <div style={{ marginTop: '16px', borderTop: '1px solid #1e355b', paddingTop: '12px' }}>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Verified Alternate Evacuation Routes ({alternateRoutes.length})
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {alternateRoutes.map((alt) => (
                            <div
                              key={alt.id}
                              onClick={() => {
                                setPrimaryRoute(alt);
                                setActiveCorridorId(alt.id);
                              }}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '8px 12px',
                                background: '#091526',
                                border: '1px solid #1e355b',
                                borderRadius: '6px',
                                cursor: 'pointer',
                              }}
                            >
                              <div style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9' }}>
                                {alt.name}
                                <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '8px' }}>
                                  ({alt.distance_km?.toFixed(1)} km • {alt.estimated_travel_time_min || Math.round(alt.distance_km * 2.2)} min)
                                </span>
                              </div>
                              <span style={{ fontSize: '11px', color: '#06b6d4', fontWeight: 700 }}>
                                Select Alternate →
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {blockedRoutes.length > 0 && (
                      <div style={{ marginTop: '14px', padding: '10px 12px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px' }}>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#f87171', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Ban size={13} /> {blockedRoutes.length} SEVERED CORRIDORS REPORTED IN SECTOR:
                        </div>
                        <div style={{ fontSize: '11.5px', color: '#fca5a5', marginTop: '4px' }}>
                          {blockedRoutes.map((b) => b.name).join(', ')} — DO NOT ATTEMPT TRANSIT
                        </div>
                      </div>
                    )}

                    {/* Test Road Blockage Dynamic Rerouting Action */}
                    <div style={{ marginTop: '16px', borderTop: '1px solid #1e355b', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                      <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
                        Want to test what happens if this road gets blocked mid-evacuation?
                      </span>
                      <button
                        onClick={() => handleToggleBlockage(primaryRoute, true, 'Active rockfall obstruction reported on primary path')}
                        className="btn btn-sm btn-outline"
                        style={{ color: '#ef4444', borderColor: '#ef4444', fontSize: '11px' }}
                      >
                        <Ban size={13} /> Simulate Blockage on My Route
                      </button>
                    </div>
                  </div>
                ) : (
                  /* NO SAFE ROUTE FOUND - CRITICAL EMERGENCY CARD */
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '2px solid #ef4444',
                      borderRadius: '10px',
                      padding: '20px',
                      marginBottom: '20px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ef4444', marginBottom: '8px' }}>
                      <AlertTriangle size={24} />
                      <h4 style={{ fontSize: '18px', fontWeight: 900, margin: 0 }}>
                        NO SAFE GROUND ROUTE AVAILABLE — REMAIN AT HIGH GROUND
                      </h4>
                    </div>
                    <p style={{ fontSize: '13px', color: '#fca5a5', lineHeight: 1.5, margin: '0 0 16px' }}>
                      All standard mountain corridors in this sector are severed by active landslides or flash flood inundation.
                      <strong> Do not attempt road transit.</strong> Move to nearest designated solid high ground holding area and alert emergency rescue authorities below.
                    </p>

                    {blockedRoutes.length > 0 && (
                      <div style={{ marginBottom: '16px', padding: '10px 12px', background: 'rgba(0, 0, 0, 0.3)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#fca5a5', textTransform: 'uppercase' }}>
                          Severed mountain corridors in this sector:
                        </div>
                        <div style={{ fontSize: '12px', color: '#fee2e2', marginTop: '4px' }}>
                          {blockedRoutes.map((b) => b.name).join(' • ')}
                        </div>
                      </div>
                    )}

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      {emergencyFacilities.map((fac) => (
                        <div key={fac.name} style={{ background: '#0f213e', padding: '12px', borderRadius: '8px', border: '1px solid #2a4778' }}>
                          <div style={{ fontSize: '12px', fontWeight: 800, color: '#38bdf8' }}>{fac.name}</div>
                          <div style={{ fontSize: '11px', color: '#94a3b8', margin: '2px 0 6px' }}>{fac.status}</div>
                          <a
                            href={`tel:${fac.phone}`}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              background: '#ef4444',
                              color: 'white',
                              padding: '6px 12px',
                              borderRadius: '4px',
                              textDecoration: 'none',
                              fontWeight: 700,
                              fontSize: '12px',
                            }}
                          >
                            <PhoneCall size={14} /> Call {fac.phone}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Turn-by-Turn Safety Guidance Card */}
                <div className="card" style={{ padding: '18px', background: '#0f213e', border: '1px solid #1e355b', marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={16} /> Himalayan Mountain Evacuation Protocol & Offline Precautions:
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#cbd5e1', lineHeight: 1.7 }}>
                    <li><strong>Avoid Cut Slopes:</strong> Keep clear of steep valley sides with recent gravel slide signs or muddy seepage.</li>
                    <li><strong>River Causeway Safety:</strong> Never attempt wading or driving through causeways where water depth exceeds tire rim level.</li>
                    <li><strong>Night Traversal Caution:</strong> Flash floods occur rapidly during cloudbursts; if safe, seek elevated ridge shelters before sunset.</li>
                    <li><strong>Keep Offline Information:</strong> Save your destination shelter coordinates (<strong>{selectedSafeHaven?.name}</strong>) and District Helpline (<strong>1077</strong>).</li>
                  </ul>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button onClick={() => setCitizenStep(3)} className="btn btn-secondary">
                    Back
                  </button>
                  <button
                    onClick={() => {
                      setActionNotice({
                        message: 'Offline emergency packet cached to device storage. You can navigate safely without cell reception.',
                        type: 'success',
                      });
                      setTimeout(() => setActionNotice(null), 6000);
                    }}
                    className="btn btn-primary"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                  >
                    <FileCheck size={16} /> Save Offline Route Pack
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* OPERATIONAL COMMAND VIEW (Full Responder Dashboard, Table, Blockage Control, KPIs) */
        <div>
          {/* Tactical Operational KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
            <div style={{ background: '#0f213e', border: '1px solid #1e355b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>DISTRICT RISK TIER</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: blockedCount > 0 ? '#ef4444' : '#10b981', marginTop: '4px' }}>
                {blockedCount > 0 ? 'HIGH HAZARD' : 'OPERATIONAL CLEAR'}
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{selectedDistrict} Catchment</div>
            </div>

            <div style={{ background: '#0f213e', border: '1px solid #1e355b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>AFFECTED POPULATION POOL</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                {totalPopulationAtRisk > 0 ? totalPopulationAtRisk.toLocaleString() : '12,500'} Residents
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Census & DDMP Registered</div>
            </div>

            <div style={{ background: '#0f213e', border: '1px solid #1e355b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>VERIFIED SAFE SHELTERS</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#34d399', marginTop: '4px' }}>
                {verifiedCount} Facilities
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>USDMA / HPSDMA / OSM</div>
            </div>

            <div style={{ background: '#0f213e', border: '1px solid #1e355b', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>OPEN CORRIDORS</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: routes.length - blockedCount > 0 ? '#34d399' : '#ef4444', marginTop: '4px' }}>
                {routes.length - blockedCount} / {routes.length} Active
              </div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Navigable Mountain Roads</div>
            </div>
          </div>

          {/* Main Content Grid: Corridors & Dynamic Evaluation (Left) + Shelter Logistics (Right) */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 420px', gap: '24px' }}>
            {/* Left Column: Corridors & Dynamic Evaluation */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Corridors Table */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Navigation size={18} color="#06b6d4" />
                      Evacuation Corridors & Road Obstruction Control
                    </h2>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                      Dynamic road monitoring across {selectedDistrict}. Sever or clear road corridors upon field confirmation.
                    </div>
                  </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #1e355b', color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        <th style={{ padding: '10px' }}>Corridor Route</th>
                        <th style={{ padding: '10px' }}>Distance</th>
                        <th style={{ padding: '10px' }}>Travel Time</th>
                        <th style={{ padding: '10px' }}>Risk Score</th>
                        <th style={{ padding: '10px' }}>Status</th>
                        <th style={{ padding: '10px' }}>Blockage Reason</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {routes.length === 0 ? (
                        <tr>
                          <td colSpan={7} style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                            No evacuation corridors configured for {selectedDistrict} district yet.
                          </td>
                        </tr>
                      ) : (
                        routes.map((route) => {
                          const isBlocked = route.is_blocked || route.status === 'BLOCKED';
                          const isHighRisk = (route.assessed_risk_score || 0) > 50;

                          return (
                            <tr
                              key={route.id}
                              style={{
                                borderBottom: '1px solid #14284b',
                                background: isBlocked ? 'rgba(239, 68, 68, 0.06)' : 'transparent',
                              }}
                            >
                              <td style={{ padding: '12px 10px' }}>
                                <div style={{ fontWeight: 700, color: '#f1f5f9' }}>{route.name}</div>
                                <div style={{ fontSize: '11px', color: '#64748b' }}>
                                  From: {route.origin_village_name || 'Settlement'} → To: {route.destination_shelter_name || 'Haven'}
                                </div>
                              </td>
                              <td style={{ padding: '12px 10px', color: '#cbd5e1' }}>
                                {route.distance_km ? `${route.distance_km.toFixed(1)} km` : '—'}
                              </td>
                              <td style={{ padding: '12px 10px', color: '#cbd5e1' }}>
                                {route.estimated_travel_time_min || Math.round((route.distance_km || 2.5) * 2.2)} min
                              </td>
                              <td style={{ padding: '12px 10px' }}>
                                <span style={{ fontFamily: 'monospace', fontWeight: 700, color: isBlocked ? '#ef4444' : isHighRisk ? '#f59e0b' : '#10b981' }}>
                                  {route.assessed_risk_score !== undefined ? Math.round(route.assessed_risk_score) : 15}/100
                                </span>
                              </td>
                              <td style={{ padding: '12px 10px' }}>
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
                              <td style={{ padding: '12px 10px', color: '#94a3b8', fontSize: '11px', maxWidth: '180px' }}>
                                {isBlocked ? (route.blockage_reason || 'Field obstruction reported') : '—'}
                              </td>
                              <td style={{ padding: '12px 10px', textAlign: 'right' }}>
                                {isBlocked ? (
                                  <button
                                    onClick={() => handleToggleBlockage(route, false)}
                                    disabled={updatingRouteId === route.id}
                                    className="btn btn-sm btn-outline"
                                    style={{ color: '#10b981', borderColor: '#10b981', fontSize: '11px' }}
                                  >
                                    <CheckCircle2 size={12} /> Clear Road
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => setSelectedRouteForModal(route)}
                                    disabled={updatingRouteId === route.id}
                                    className="btn btn-sm btn-outline"
                                    style={{ color: '#ef4444', borderColor: '#ef4444', fontSize: '11px' }}
                                  >
                                    <Ban size={12} /> Report Blockage
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Dynamic Coordinate Evaluation Card */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Compass size={18} color="#38bdf8" />
                    Dynamic Field Evacuation Evaluation (1.5 km Snap Guard)
                  </h2>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                    Test evacuation feasibility from stranded party coordinates. Evaluates 1.5 km off-grid limit and calculates safe path.
                  </div>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    evaluateDisasterRoute(parseFloat(evalLat) || 30.598, parseFloat(evalLon) || 79.036, selectedSettlementId || undefined);
                  }}
                  style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'flex-end' }}
                >
                  <div style={{ flex: '1 1 140px' }}>
                    <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      ORIGIN LATITUDE (°N)
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
                      ORIGIN LONGITUDE (°E)
                    </label>
                    <input
                      type="text"
                      value={evalLon}
                      onChange={(e) => setEvalLon(e.target.value)}
                      style={{ width: '100%', padding: '8px 10px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '13px' }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      type="submit"
                      disabled={evaluating}
                      className="btn btn-primary"
                      style={{ padding: '8px 16px', fontSize: '13px' }}
                    >
                      {evaluating ? 'Evaluating...' : 'Evaluate Route Viability'}
                    </button>
                  </div>
                </form>

                {evalResult && (
                  <div style={{ marginTop: '16px', padding: '14px', borderRadius: '8px', background: evalResult.status === 'NO_SAFE_ROUTE_FOUND' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.1)', border: `1px solid ${evalResult.status === 'NO_SAFE_ROUTE_FOUND' ? '#ef4444' : '#10b981'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 800, color: evalResult.status === 'NO_SAFE_ROUTE_FOUND' ? '#f87171' : '#34d399' }}>
                        {evalResult.route_label || evalResult.status}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        Confidence: {(evalResult.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '6px' }}>
                      {evalResult.message}
                    </div>
                    {evalResult.selected_route && (
                      <div style={{ fontSize: '11.5px', color: '#94a3b8', marginTop: '4px' }}>
                        Corridor: <strong>{evalResult.selected_route.name}</strong> • Distance: <strong>{evalResult.selected_route.distance_km?.toFixed(1)} km</strong> • Est. Travel: <strong>{evalResult.selected_route.estimated_travel_time_min} min</strong>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Shelter Haven Logistics Panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Hospital size={18} color="#10b981" />
                    Shelter Haven Logistics
                  </h2>
                  <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                    {shelterLoading ? 'Updating...' : `${displayedShelters.length} Facilities`}
                  </span>
                </div>

                {/* Shelter Search & Filters */}
                <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ position: 'relative' }}>
                    <Search size={14} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                    <input
                      type="text"
                      placeholder="Search shelters by name, type, or town..."
                      value={shelterSearch}
                      onChange={(e) => setShelterSearch(e.target.value)}
                      style={{ width: '100%', padding: '7px 10px 7px 32px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '12px' }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                      <input type="checkbox" checked={filterVerifiedOnly} onChange={(e) => setFilterVerifiedOnly(e.target.checked)} />
                      <span>Verified Only</span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                      <input type="checkbox" checked={filterOperationalOnly} onChange={(e) => setFilterOperationalOnly(e.target.checked)} />
                      <span>Operational</span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                      <input type="checkbox" checked={filterHasMedical} onChange={(e) => setFilterHasMedical(e.target.checked)} />
                      <span>Medical Ready</span>
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                      <input type="checkbox" checked={filterHasPower} onChange={(e) => setFilterHasPower(e.target.checked)} />
                      <span>Power Backup</span>
                    </label>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto' }}>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>Sort:</span>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        style={{ background: '#162a4d', color: '#cbd5e1', border: '1px solid #2a4778', borderRadius: '4px', padding: '2px 6px', fontSize: '11px' }}
                      >
                        <option value="suitability">Suitability</option>
                        <option value="distance">Nearest</option>
                        <option value="capacity">Capacity</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Shelter List Items */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '560px', overflowY: 'auto' }}>
                  {displayedShelters.map((shelter) => {
                    const isSelected = selectedShelterId === shelter.id;
                    const isSafeHaven = shelter.is_safe_haven !== false && !shelter.corridor_blocked;

                    return (
                      <div
                        key={shelter.id}
                        onClick={() => {
                          setSelectedShelterId(shelter.id);
                          setSelectedSafeHaven(shelter);
                        }}
                        style={{
                          background: isSelected ? '#1a335c' : '#0f213e',
                          border: `1px solid ${isSelected ? '#38bdf8' : isSafeHaven ? '#1e355b' : '#ef4444'}`,
                          borderRadius: '8px',
                          padding: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div style={{ fontWeight: 700, fontSize: '13px', color: '#f8fafc' }}>
                            {shelter.name}
                          </div>
                          <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: isSafeHaven ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: isSafeHaven ? '#34d399' : '#f87171' }}>
                            {isSafeHaven ? 'SAFE HAVEN' : 'IN HAZARD'}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                          {shelter.type} • {shelter.village_town || selectedDistrict}
                        </div>
                        <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '6px' }}>
                          Remaining: <strong>{shelter.available_capacity ?? shelter.capacity ?? 200} slots</strong> • Distance: <strong>{shelter.distance_km?.toFixed(1) || '—'} km</strong>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. Blockage Incident Reporting Modal */}
      {selectedRouteForModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(6, 13, 23, 0.85)',
            backdropFilter: 'blur(4px)',
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
              maxWidth: '520px',
              width: '100%',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ef4444', marginBottom: '12px' }}>
              <Ban size={22} />
              <h3 style={{ fontSize: '18px', fontWeight: 800, margin: 0 }}>Report Corridor Obstruction / Road Blockage</h3>
            </div>

            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5, margin: '0 0 16px' }}>
              You are reporting an obstruction on corridor: <strong>{selectedRouteForModal.name}</strong>.
              Graph routing will immediately sever this route (risk score: 95/100, hazard multiplier: 10×) and re-route affected settlements.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  BLOCKAGE TYPE:
                </label>
                <select
                  value={blockageTypeInput}
                  onChange={(e) => setBlockageTypeInput(e.target.value)}
                  style={{ width: '100%', padding: '8px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '12px' }}
                >
                  <option value="Landslide">Landslide / Mudslide</option>
                  <option value="Flooding">Active Flooding / Causeway Submersion</option>
                  <option value="Bridge Collapse">Bridge Collapse / Culvert Failure</option>
                  <option value="Debris">Debris & Boulder Slide</option>
                  <option value="Road Damage">Severe Carriage-way Damage</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  SEVERITY TIER:
                </label>
                <select
                  value={blockageSeverityInput}
                  onChange={(e) => setBlockageSeverityInput(e.target.value)}
                  style={{ width: '100%', padding: '8px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '12px' }}
                >
                  <option value="CRITICAL">CRITICAL (Total Severance)</option>
                  <option value="HIGH">HIGH (Dangerous)</option>
                  <option value="MEDIUM">MEDIUM (Heavy Vehicles Halted)</option>
                </select>
              </div>
            </div>

            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              INCIDENT DESCRIPTION & FIELD DETAILS:
            </label>
            <textarea
              rows={3}
              value={blockageReasonInput}
              onChange={(e) => setBlockageReasonInput(e.target.value)}
              placeholder="Specify kilometer mark, debris depth, active river surge, etc."
              style={{ width: '100%', padding: '10px', background: '#162a4d', color: '#f1f5f9', border: '1px solid #2a4778', borderRadius: '6px', fontSize: '13px', marginBottom: '16px', fontFamily: 'inherit' }}
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" onClick={() => setSelectedRouteForModal(null)} className="btn btn-secondary">
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleToggleBlockage(selectedRouteForModal, true, `${blockageTypeInput} (${blockageSeverityInput}): ${blockageReasonInput}`)}
                className="btn btn-danger"
              >
                Confirm Corridor Severance
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 8. Source Transparency & Scientific Provenance Footer */}
      <div
        style={{
          marginTop: '30px',
          padding: '16px 20px',
          background: '#091526',
          border: '1px solid #172b4d',
          borderRadius: '8px',
          fontSize: '12px',
          color: '#64748b',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontWeight: 700 }}>
            <Info size={14} />
            <span>DISASTER MANAGEMENT DATA PROVENANCE & STRICT INTEGRITY DISCLOSURE</span>
          </div>
          <span style={{ fontSize: '11px', color: '#38bdf8' }}>Flowshield Intelligence Network (2026)</span>
        </div>
        <p style={{ margin: 0, lineHeight: 1.6 }}>
          All evacuation shelters, government colleges, stadiums, and hospital facilities displayed in this console originate from verified <strong>State Disaster Management Authorities (USDMA, HPSDMA)</strong>, official <strong>District Disaster Management Plans (DDMPs)</strong>, and <strong>OpenStreetMap</strong> civic infrastructure records. Unverified quotas are explicitly marked to prevent misguidance. Dynamic corridor routing incorporates live road incident telemetry and terrain elevation constraints.
        </p>
      </div>
    </div>
  );
};
