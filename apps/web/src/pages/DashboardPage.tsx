import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Village,
  Alert,
  Shelter,
  EvacuationRoute,
  SimulationStatus,
  NationalFloodSummary,
  RiverGauge,
} from '../types';
import { api } from '../services/api';
import { CommandSidebar } from '../components/common/CommandSidebar';
import { SystemStatusBar } from '../components/common/SystemStatusBar';
import { IncidentForecastBar } from '../components/dashboard/IncidentForecastBar';
import { ExecutiveKpiGrid } from '../components/dashboard/ExecutiveKpiGrid';
import { RiverGaugePanel } from '../components/dashboard/RiverGaugePanel';
import { TerrainMapContainer } from '../components/map/TerrainMapContainer';
import { AlertCenter } from '../components/dashboard/AlertCenter';
import { QuickActions } from '../components/dashboard/QuickActions';

import { AIRiskExplanationCard } from '../components/dashboard/AIRiskExplanationCard';
import { WebIntelligencePanel } from '../components/dashboard/WebIntelligencePanel';
import { TimelineView } from '../components/timeline/TimelineView';

interface DashboardPageProps {
  initialTab?: string;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ initialTab = 'Map' }) => {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const tabParam = searchParams.get('tab');
  const isTimelineRoute = location.pathname.includes('/timeline') || tabParam?.toLowerCase() === 'timeline';

  // Core Data State
  const [villages, setVillages] = useState<Village[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [routes, setRoutes] = useState<EvacuationRoute[]>([]);
  const [simStatus, setSimStatus] = useState<SimulationStatus | null>(null);
  const [nationalSummary, setNationalSummary] = useState<NationalFloodSummary | null>(null);
  const [riverGauges, setRiverGauges] = useState<RiverGauge[]>([]);

  // Selection & Telemetry State
  const [selectedVillageId, setSelectedVillageId] = useState<string | number | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [lastSyncedTime, setLastSyncedTime] = useState<string>('Just now');
  const [activeSidebarItem, setActiveSidebarItem] = useState<string>(
    isTimelineRoute ? 'Timeline' : initialTab
  );

  // Fetch all core dashboard telemetry
  const fetchData = useCallback(async () => {
    try {
      const [vData, aData, sData, rData, simData, natSummary, gaugesData] = await Promise.all([
        api.getVillages().catch(() => []),
        api.getAlerts({ status: 'ACTIVE' }).catch(() => []),
        api.getShelters().catch(() => []),
        api.getRoutes().catch(() => []),
        api.getSimulationStatus().catch(() => null),
        api.getNationalFloodSummary().catch(() => null),
        api.getLiveRiverGauges().catch(() => ({ gauges: [] })),
      ]);

      if (vData) setVillages(vData);
      if (aData) setAlerts(aData);
      if (sData) setShelters(sData);
      if (rData) setRoutes(rData);
      if (simData) setSimStatus(simData);
      if (natSummary) setNationalSummary(natSummary);
      if (gaugesData?.gauges && gaugesData.gauges.length > 0) {
        setRiverGauges(gaugesData.gauges);
      }
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    }
  }, []);

  // Initial load and live telemetry synchronization
  useEffect(() => {
    // If on the dedicated Timeline route or active on Timeline tab, skip the heavy 7-endpoint dashboard polling
    // and skip global multi-settlement live telemetry synchronization
    if (isTimelineRoute || activeSidebarItem === 'Timeline') {
      return;
    }

    fetchData();
    api.syncLiveTelemetry()
      .then(() => {
        const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        setLastSyncedTime(nowStr);
      })
      .catch((err) => console.warn('Live telemetry initial sync:', err));

    // Poll status every 15 seconds (only when on Map or Overview dashboards)
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData, isTimelineRoute, activeSidebarItem]);

  // Connect to Real-Time SSE Event Stream
  useEffect(() => {
    if (isTimelineRoute || activeSidebarItem === 'Timeline') return;

    const unsub = api.subscribeRealtimeStream(
      selectedVillageId ? String(selectedVillageId) : undefined,
      (evt) => {
        console.log('⚡ SSE Event Received:', evt);
        const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        setLastSyncedTime(`${nowStr} (Live Push)`);
        fetchData();
      }
    );
    return () => {
      unsub();
    };
  }, [selectedVillageId, fetchData, isTimelineRoute, activeSidebarItem]);



  // Simulation Step Action
  const handleStepSimulation = async () => {
    setIsLoading(true);
    try {
      const stepRes = await api.simulationStep();
      if (stepRes?.status) {
        setSimStatus(stepRes.status);
      }
      await fetchData();
    } catch (err) {
      console.error('Simulation step error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Generate Report Action
  const handleGenerateReport = () => {
    const title = 'Flowshield National Incident Situation Report - September 2026';
    const textContent = `${title}\nGenerated: ${new Date().toISOString()}\n\nCrisis: National Flood Crisis Monitor (North & Eastern India)\nAffected Population: 47.74 Lakh\nDistricts Impacted: 42 (13 Critical, 21 Warning, 8 Watch)\nMajor Rivers Breached: 7 of 9 (Ganga, Kosi, Gandak, Punpun)\nSubmerged Schools: 4,120+ (68% flooded or converted)\n\nSTATUS: ACTIVE EMERGENCY PROTOCOL PS-26192 (Sim Substep: ${simStatus?.current_substep || 0})`;
    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Flowshield_Crisis_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Selected Village Object for Map Centering
  const selectedVillageObj = villages.find(v => v.id === selectedVillageId) || null;

  // Dynamic values derived from nationalSummary if available
  const affectedPopStr = nationalSummary?.national_overview?.total_affected_population
    ? `${(nationalSummary.national_overview.total_affected_population / 100000).toFixed(2)} Lakh`
    : '47.74 Lakh';
  const districtsTotal = nationalSummary?.national_overview?.total_districts_impacted || 42;
  const schoolsTotal = nationalSummary?.national_overview?.schools_submerged_national
    ? `${nationalSummary.national_overview.schools_submerged_national.toLocaleString()}+`
    : '4,120+';

  return (
    <div
      className="command-center-root"
      style={{
        height: 'calc(100vh - 68px)',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Atmospheric Mountain Light Particles Overlay */}
      <div className="mountain-ambient-particles" />

      {/* Middle Body Zone: Sidebar + Operations Workspace */}
      <div className="cc-body-zone" style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {/* Left 122px Operations Navigation Rail */}
        <CommandSidebar
          activeItem={activeSidebarItem}
          onSelectItem={setActiveSidebarItem}
        />

        {/* Main Central Dashboard Workspace */}
        <div className="cc-main-zone" style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, minHeight: 0, overflow: 'hidden' }}>
          {activeSidebarItem === 'Map' ? (
            /* Full-Page Complete India Map View with zero clutter */
            <div
              style={{
                flex: 1,
                width: '100%',
                height: '100%',
                minHeight: 0,
                position: 'relative',
                padding: '6px 14px 10px 6px',
                boxSizing: 'border-box',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <TerrainMapContainer
                villages={villages}
                shelters={shelters}
                routes={routes}
                selectedVillage={null}
                onSelectVillage={(v) => setSelectedVillageId(v.id)}
                isFullPage={true}
                onBackToOverview={() => setActiveSidebarItem('Overview')}
              />
            </div>
          ) : activeSidebarItem === 'Timeline' ? (
            /* Dedicated Multi-Horizon Predictive Risk & Hydro-Meteorological Timeline */
            <div
              style={{
                flex: 1,
                width: '100%',
                minHeight: 0,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                paddingTop: '6px',
              }}
            >
              <TimelineView
                initialVillageId={selectedVillageId ? String(selectedVillageId) : 'vil-hp-mnd-01'}
                onVillageChange={(id) => setSelectedVillageId(id)}
              />
            </div>
          ) : (
            <>
              {/* Sub-Zone 1: Active Incident & IMD Forecast Header */}
              <IncidentForecastBar
                crisisTitle={nationalSummary?.report_title || 'NATIONAL FLOOD CRISIS MONITOR'}
                crisisLocations="North & Eastern India  |  14 Districts  |  UP (Kanpur Pandu Surge) + 24 Districts"
                forecastHeadline={nationalSummary?.national_overview?.imd_forecast ? 'Heavy to Very Heavy Rainfall (IMD Orange Alert)' : 'Heavy to Very Heavy Rainfall'}
                forecastRegion="Gangetic Plains & Foothills"
                forecastRainfall="200–300 mm"
              />

              {/* Sub-Zone 2: Executive KPI Grid (4 Cards) */}
              <ExecutiveKpiGrid
                affectedPopFormatted={affectedPopStr}
                affectedPopDelta="↑ 12.4% (6h)"
                biharPop="43.64 L"
                othersPop="4.10 L"
                districtsCount={districtsTotal}
                criticalDists={13}
                warningDists={21}
                watchDists={8}
                highRiskPct={67}
                riversAboveDanger={nationalSummary?.national_overview?.major_rivers_above_danger?.length ? `${nationalSummary.national_overview.major_rivers_above_danger.length} / 9` : '7 / 9'}
                keyRiversList="Ganga • Kosi • Gandak • Punpun • ..."
                schoolsCount={schoolsTotal}
                schoolsFloodedPct={68}
              />

              {/* Sub-Zone 3: Operations Workspace (Conditional on Sidebar Selection) */}
              {activeSidebarItem === 'AI Intel' ? (
                <div style={{ flex: 1, margin: '0 14px 10px 14px', overflowY: 'auto', display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '14px' }}>
                  <WebIntelligencePanel region="Himachal Pradesh / Mandi Basin" />
                  <AIRiskExplanationCard
                    villageId={String(selectedVillageId || (villages[0]?.id || 'mandi_sadar'))}
                    villageName={selectedVillageObj?.name || 'Mandi Sadar Basin'}
                    riskScore={selectedVillageObj?.current_risk_score || 64.0}
                    riskLevel={selectedVillageObj?.current_risk_tier || 'HIGH'}
                    floodProbability={0.68}
                    keyFactors={['Saturated topsoil layers (ERA5)', 'Intensifying 3-hour precipitation cell', 'Steep Beas gorge slope runoff']}
                    telemetrySummary={{
                      rainfall_1h_mm: selectedVillageObj?.latest_rainfall_1h || 12.4,
                      rainfall_24h_mm: 58.0,
                      soil_saturation_pct: selectedVillageObj?.latest_soil_moisture || 74.0,
                      elevation_m: selectedVillageObj?.elevation_m || 850,
                      dist_to_river_m: selectedVillageObj?.distance_to_river_m || 110,
                    }}
                  />
                </div>
              ) : (
                <div className="operations-workspace" style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                  {/* Column 1 (25%): River Gauge Overview */}
                  <RiverGaugePanel
                    gauges={riverGauges}
                    onSelectRiver={(r) => {
                      const match = villages.find(v => v.name.toLowerCase().includes(r.river.toLowerCase()) || v.tehsil.toLowerCase().includes(r.river.toLowerCase()));
                      if (match) setSelectedVillageId(match.id);
                    }}
                  />

                  {/* Column 2 (48%): Center GIS Terrain Digital Twin Map Hero */}
                  <TerrainMapContainer
                    villages={villages}
                    shelters={shelters}
                    routes={routes}
                    selectedVillage={selectedVillageObj}
                    onSelectVillage={(v) => setSelectedVillageId(v.id)}
                  />

                  {/* Column 3 (27%): Alert Center & Quick Actions */}
                  <div
                    style={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                      minHeight: 0,
                      overflow: 'hidden',
                    }}
                  >
                    {/* Alert Center (Upper Section) */}
                    <AlertCenter
                      alerts={alerts}
                      onSelectAlert={(alt) => {
                        const match = villages.find(v => v.name.toLowerCase().includes(alt.title.toLowerCase()));
                        if (match) setSelectedVillageId(match.id);
                      }}
                    />

                    {/* Quick Actions (Lower Section) */}
                    <QuickActions
                      onRunSimulation={handleStepSimulation}
                      onGenerateReport={handleGenerateReport}
                      onToggleRoutes={() => {
                        if (routes.length > 0) {
                          const firstRouteVillage = villages.find(v => v.id === routes[0].from_village_id);
                          if (firstRouteVillage) setSelectedVillageId(firstRouteVillage.id);
                        }
                      }}
                      onOpenAssistant={() => {
                        if (villages.length > 0) setSelectedVillageId(villages[0].id);
                      }}
                      isSimulating={isLoading}
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Persistent Bottom System Status Bar — Hidden on Map page so map gets 100% full vertical height */}
      {activeSidebarItem !== 'Map' && (() => {
        const validRains = villages.map(v => v.latest_rainfall_1h).filter((r): r is number => r != null);
        const liveMaxRain = validRains.length > 0 ? Math.max(...validRains) : undefined;

        const breachedRiversCount = riverGauges.filter(g => g.status === 'CRITICAL' || g.status === 'WARNING').length;
        const totalRiversCount = Math.max(riverGauges.length, 6);
        const highRiskCount = villages.filter(v => (v.current_risk_score || 0) >= 50).length;
        const clearRoutesCount = routes.filter(r => !r.is_blocked).length;
        const totalRoutesCount = Math.max(routes.length, 5);
        const computedHealth = Math.round(Math.max(88, Math.min(100, 100 - (alerts.length * 2) - (breachedRiversCount * 1.5))));

        return (
          <SystemStatusBar
            systemHealth={computedHealth}
            rainfall1h={liveMaxRain !== undefined ? Number(liveMaxRain.toFixed(1)) : undefined}
            rainfallTrend={lastSyncedTime ? `Live • ${lastSyncedTime}` : 'Telemetry Live'}
            riversBreachedCount={breachedRiversCount}
            totalRivers={totalRiversCount}
            landslideRiskTier={highRiskCount > 2 ? 'High' : highRiskCount > 0 ? 'Watch' : 'Low'}
            landslideDistrictsCount={Math.max(1, highRiskCount)}
            evacuationClearCount={clearRoutesCount}
            totalEvacuationRoutes={totalRoutesCount}
          />
        );
      })()}


    </div>
  );
};
