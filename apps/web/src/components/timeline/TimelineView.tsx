import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../../services/api';
import {
  TimelineDetailedResponse,
  TimelineLocationHierarchy,
} from '../../types';
import { TimelineHeader } from './TimelineHeader';
import { CurrentSituationBar } from './CurrentSituationBar';
import { PrecipitationChart } from './PrecipitationChart';
import { FloodRiskChart } from './FloodRiskChart';
import { MultiHorizonForecastGrid } from './MultiHorizonForecastGrid';
import { SituationAnalysisCard } from './SituationAnalysisCard';
import { HydrologicalAnalysisCard } from './HydrologicalAnalysisCard';
import { ExposureEvacuationCard } from './ExposureEvacuationCard';
import { DataQualityTransparencyCard } from './DataQualityTransparencyCard';
import { FloodOutlookSummary } from './FloodOutlookSummary';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface TimelineViewProps {
  initialVillageId?: string;
  onVillageChange?: (villageId: string) => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  initialVillageId,
  onVillageChange,
}) => {
  // Geographic Location Hierarchy State
  const [locations, setLocations] = useState<TimelineLocationHierarchy | null>(null);
  const [selectedState, setSelectedState] = useState<string>('Bihar');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('Buxar');
  const [selectedVillageId, setSelectedVillageId] = useState<string>(initialVillageId || 'bh-07-buxar');

  // Detailed Timeline Intelligence State
  const [timelineData, setTimelineData] = useState<TimelineDetailedResponse | null>(null);
  const [selectedHorizonHours, setSelectedHorizonHours] = useState<number | null>(null);

  // Status & Concurrency State
  const [status, setStatus] = useState<'INITIALIZING' | 'LOADING' | 'LIVE' | 'UPDATING' | 'DEGRADED' | 'ERROR'>('INITIALIZING');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // Active in-flight request abort controller
  const abortControllerRef = useRef<AbortController | null>(null);

  // 1. Fetch Location Hierarchy on Mount
  useEffect(() => {
    let isMounted = true;
    api.getTimelineLocations()
      .then((hierarchy) => {
        if (!isMounted) return;
        setLocations(hierarchy);

        if (hierarchy.states.length > 0) {
          const targetId = selectedVillageId || initialVillageId || 'bh-07-buxar';
          let foundState = '';
          let foundDistrict = '';
          let foundVillageId = '';

          for (const st of hierarchy.states) {
            for (const dist of st.districts) {
              const match = dist.settlements.find((v) => v.id === targetId);
              if (match) {
                foundState = st.name;
                foundDistrict = dist.name;
                foundVillageId = match.id;
                break;
              }
            }
            if (foundVillageId) break;
          }

          if (!foundVillageId && hierarchy.states[0].districts[0]?.settlements[0]) {
            foundState = hierarchy.states[0].name;
            foundDistrict = hierarchy.states[0].districts[0].name;
            foundVillageId = hierarchy.states[0].districts[0].settlements[0].id;
          }

          if (foundVillageId) {
            setSelectedState(foundState);
            setSelectedDistrict(foundDistrict);
            setSelectedVillageId(foundVillageId);
            if (onVillageChange) onVillageChange(foundVillageId);
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load timeline location hierarchy:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch Detailed Timeline Data for Selected Settlement
  const fetchTimelineData = useCallback(
    async (villageId: string, forceRefresh: boolean = false) => {
      if (!villageId) return;

      // Cancel any prior in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      if (forceRefresh) {
        setIsRefreshing(true);
        setStatus('UPDATING');
      } else if (!timelineData) {
        setStatus('LOADING');
      }

      setErrorMessage(null);

      try {
        const response = await api.getTimelineDetailed(villageId, forceRefresh);
        setTimelineData(response);

        // Evaluate status based on response data quality
        if (response.data_quality.overall_health === 'COMPROMISED' || response.data_quality.overall_health === 'DEGRADED') {
          setStatus('DEGRADED');
        } else {
          setStatus('LIVE');
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          return; // Silently handle cancellation
        }
        console.error('Error fetching timeline intelligence:', err);
        setErrorMessage(err.message || 'Telemetry synthesis error. Please retry.');
        setStatus('ERROR');
      } finally {
        setIsRefreshing(false);
      }
    },
    [timelineData]
  );

  // Trigger fetch when selectedVillageId changes
  useEffect(() => {
    if (selectedVillageId) {
      fetchTimelineData(selectedVillageId, false);
    }
  }, [selectedVillageId]);

  // 3. Adaptive HTTP Polling based on Risk Tier
  useEffect(() => {
    if (!selectedVillageId) return;

    // Determine poll interval: 30s for CRITICAL, 60s for HIGH/WATCH, 300s (5m) for LOW/normal
    const currentTier = timelineData?.forecast_horizons[0]?.risk_tier || 'LOW';
    const pollIntervalMs =
      currentTier === 'CRITICAL' ? 30000 : currentTier === 'HIGH' || currentTier === 'WATCH' ? 60000 : 300000;

    const timer = setInterval(() => {
      fetchTimelineData(selectedVillageId, false);
    }, pollIntervalMs);

    return () => clearInterval(timer);
  }, [selectedVillageId, timelineData?.forecast_horizons, fetchTimelineData]);

  // Location selector change handler
  const handleSelectLocation = (state: string, district: string, villageId: string) => {
    setSelectedState(state);
    setSelectedDistrict(district);
    setSelectedVillageId(villageId);
    if (onVillageChange) onVillageChange(villageId);
  };

  // Manual force refresh handler
  const handleRefresh = () => {
    if (selectedVillageId) {
      fetchTimelineData(selectedVillageId, true);
    }
  };

  // Compute 3h rate of change (pts/hr)
  const computeTrendRate = (): number => {
    if (!timelineData || timelineData.forecast_horizons.length < 2) return 0.0;
    const nowScore = timelineData.historical_series[timelineData.historical_series.length - 1]?.operational_risk_score || 20.0;
    const h3Point = timelineData.forecast_horizons.find((h) => h.horizon_hours === 3);
    if (!h3Point || h3Point.operational_risk_score == null) return 0.0;
    return (h3Point.operational_risk_score - nowScore) / 3.0;
  };

  const trendRate = computeTrendRate();
  const baselineRiskScore = timelineData?.historical_series[timelineData.historical_series.length - 1]?.operational_risk_score || 20.0;
  const currentHorizon = timelineData?.forecast_horizons[0];

  return (
    <div
      style={{
        flex: 1,
        width: '100%',
        minHeight: 0,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '0 14px 14px 14px',
        boxSizing: 'border-box',
      }}
    >
      {/* 1. Master Header: Location Selector, Data Quality, Sync Button */}
      <TimelineHeader
        locations={locations}
        selectedState={selectedState}
        selectedDistrict={selectedDistrict}
        selectedVillageId={selectedVillageId}
        onSelectLocation={handleSelectLocation}
        activeMode={timelineData?.data_quality.active_mode || 'LIVE'}
        overallHealth={timelineData?.data_quality.overall_health || 'OPTIMAL'}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
        lastUpdated={timelineData?.generated_at || ''}
        settlementName={timelineData?.settlement.name || 'Selecting Location...'}
        elevationMeters={timelineData?.settlement.elevation_meters || 500}
        riverBasin={timelineData?.settlement.river_basin || 'Catchment Basin'}
      />

      {/* Loading Skeleton */}
      {status === 'LOADING' && !timelineData && (
        <div
          className="timeline-glass-card"
          style={{
            borderRadius: '10px',
            padding: '48px 24px',
            textAlign: 'center',
            color: '#38BDF8',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <RefreshCw size={28} className="animate-spin" />
          <div style={{ fontSize: '15px', fontWeight: 600, color: '#F1F5F9' }}>
            Synthesizing Calibrated Multi-Horizon Hydrometeorological Intelligence...
          </div>
          <div style={{ fontSize: '12px', color: '#64748B' }}>
            Querying OpenWeather observations, CWC gauge telemetry, ERA5 soil layers, and ECMWF IFS 0.1° grid
          </div>
        </div>
      )}

      {/* Error Fallback Box */}
      {status === 'ERROR' && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: '#FCA5A5',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={20} color="#EF4444" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '13px', color: '#EF4444' }}>Telemetry Synthesis Failure</div>
              <div style={{ fontSize: '12px', color: '#CBD5E1' }}>{errorMessage}</div>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            style={{
              background: '#EF4444',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Retry Sync
          </button>
        </div>
      )}

      {/* Main Operational Dashboard Content */}
      {timelineData && (
        <>
          {/* 2. Current Situation Bar (4 Real-Time Observed KPI Cards) */}
          <CurrentSituationBar
            observation={timelineData.current_situation}
            hydrology={timelineData.hydrology}
            currentHorizon={currentHorizon}
            baselineRiskScore={baselineRiskScore}
            trendRatePointsPerHr={trendRate}
          />

          {/* 2.5 Multi-Horizon Flood Risk Outlook (Calibrated 6-Horizon Badges) */}
          <FloodOutlookSummary data={timelineData} />

          {/* 3. Dedicated Precipitation Forecast Visualizer (NWP ECMWF mm/h) */}
          <PrecipitationChart
            precipitationForecast={timelineData.precipitation_forecast}
            currentRainfallRate={timelineData.current_situation.rainfall_rate_mm_hr}
            historicalSeries={timelineData.historical_series}
            settlementName={timelineData.settlement.name}
          />

          {/* 3.5 Dedicated Flood Risk Probability Visualizer (Calibrated ML Model 0-100) */}
          <FloodRiskChart
            historicalSeries={timelineData.historical_series}
            forecastHorizons={timelineData.forecast_horizons}
            capability={timelineData.location_capabilities}
            settlementName={timelineData.settlement.name}
          />

          {/* 4. Multi-Horizon Forecast Projection Grid (+1h to +48h) */}
          <MultiHorizonForecastGrid
            horizons={timelineData.forecast_horizons}
            selectedHorizonHours={selectedHorizonHours}
            onSelectHorizon={setSelectedHorizonHours}
          />

          {/* 5. Commander Situation Brief & Explainable Risk Drivers */}
          <SituationAnalysisCard
            situationSummary={timelineData.situation_summary}
            thresholdAnalysis={timelineData.threshold_analysis}
            peaks={timelineData.peak_analysis}
            riskDrivers={timelineData.risk_drivers}
            trendRatePointsPerHr={trendRate}
          />

          {/* 6. Dual Card: Hydrological River Dynamics & Spatial Exposure */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '14px' }}>
            <HydrologicalAnalysisCard hydrology={timelineData.hydrology} />
            <ExposureEvacuationCard exposure={timelineData.exposure} settlementName={timelineData.settlement.name} />
          </div>

          {/* 7. Auditable Data Quality & Telemetry Provenance Matrix */}
          <DataQualityTransparencyCard
            dataQuality={timelineData.data_quality}
            modelMetadata={timelineData.model_metadata}
            locationCapabilities={timelineData.location_capabilities}
            currentSituation={timelineData.current_situation}
          />
        </>
      )}
    </div>
  );
};
