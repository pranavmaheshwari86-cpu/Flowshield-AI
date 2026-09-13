import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { CloudRain, AlertCircle, Info, ZoomIn, Maximize2, ShieldAlert, Waves, BarChart2 } from 'lucide-react';
import {
  PrecipitationForecastResponse,
  HistoricalSeriesPoint,
  ForecastHorizonPoint,
  ThresholdCrossingAnalysis,
  ObservationSnapshot,
  LocationCapability,
} from '../../types';

interface PrecipitationChartProps {
  precipitationForecast?: PrecipitationForecastResponse | null;
  currentRainfallRate?: number | null;
  historicalSeries?: HistoricalSeriesPoint[];
  forecastHorizons?: ForecastHorizonPoint[];
  settlementName?: string;
  thresholdAnalysis?: ThresholdCrossingAnalysis | null;
  peakAnalysis?: { rainfall_peak_hours?: number | null; river_crest_peak_hours?: number | null; risk_peak_hours?: number | null; [key: string]: number | null | undefined } | null;
  currentSituation?: ObservationSnapshot | null;
  capability?: LocationCapability | null;
}

interface PrecipDataPoint {
  relativeHour: number;
  label: string;
  timeIst: string;
  timestamp: string;
  observedRate?: number | null;
  forecastRate?: number | null;
  floodProbPct?: number | null;
  riskScore?: number | null;
  riskTier?: string;
  primaryDriver?: string;
  p10?: number | null;
  p90?: number | null;
  isForecast: boolean;
  status: string;
  source: string;
}

export const PrecipitationChart: React.FC<PrecipitationChartProps> = ({
  precipitationForecast,
  currentRainfallRate,
  historicalSeries = [],
  forecastHorizons = [],
  settlementName,
  thresholdAnalysis,
  peakAnalysis,
  currentSituation,
  capability,
}) => {
  const [scaleMode, setScaleMode] = useState<'auto' | 'full'>('auto');
  const [viewMode, setViewMode] = useState<'combined' | 'flood' | 'rainfall'>('combined');

  const isModelSupported = capability ? capability.flood_risk_model === 'SUPPORTED' : true;

  // Build continuous timeline: strictly 1 point per relativeHour to prevent duplicate X-axis labels
  const hourMap = new Map<number, PrecipDataPoint>();

  // Map of forecast horizons for quick lookup
  const horizonByHour = new Map<number, ForecastHorizonPoint>();
  forecastHorizons.forEach((h) => {
    horizonByHour.set(h.horizon_hours, h);
  });

  // Calculate baseline risk at NOW
  const lastHistRisk = historicalSeries.length > 0
    ? historicalSeries[historicalSeries.length - 1].operational_risk_score
    : 15.0;

  // 1. Historical Observed Points
  if (precipitationForecast?.observed_points && precipitationForecast.observed_points.length > 0) {
    precipitationForecast.observed_points.forEach((pt) => {
      const histMatch = historicalSeries.find((h) => h.relative_hour === pt.relative_hour);
      const observedRisk = histMatch?.operational_risk_score ?? lastHistRisk;

      hourMap.set(pt.relative_hour, {
        relativeHour: pt.relative_hour,
        label: pt.relative_hour === 0 ? 'NOW' : `${pt.relative_hour}hr`,
        timeIst: pt.timestamp_ist,
        timestamp: pt.timestamp_utc,
        observedRate: pt.value_mm_hr,
        floodProbPct: isModelSupported ? Math.round(observedRisk) : null,
        riskScore: isModelSupported ? observedRisk : null,
        riskTier: isModelSupported ? (observedRisk >= 75 ? 'CRITICAL' : observedRisk >= 50 ? 'HIGH' : observedRisk >= 25 ? 'WATCH' : 'LOW') : 'UNSUPPORTED',
        isForecast: false,
        status: pt.status,
        source: pt.source,
      });
    });
  }

  // Also merge all historical series points to ensure no observed interval is dropped
  historicalSeries.forEach((pt) => {
    if (!hourMap.has(pt.relative_hour)) {
      hourMap.set(pt.relative_hour, {
        relativeHour: pt.relative_hour,
        label: pt.relative_hour === 0 ? 'NOW' : `${pt.relative_hour}hr`,
        timeIst: pt.timestamp,
        timestamp: pt.timestamp,
        observedRate: pt.observed_rainfall_rate ?? null,
        floodProbPct: isModelSupported ? Math.round(pt.operational_risk_score) : null,
        riskScore: isModelSupported ? pt.operational_risk_score : null,
        riskTier: isModelSupported ? (pt.operational_risk_score >= 75 ? 'CRITICAL' : pt.operational_risk_score >= 50 ? 'HIGH' : pt.operational_risk_score >= 25 ? 'WATCH' : 'LOW') : 'UNSUPPORTED',
        isForecast: false,
        status: 'OBSERVED',
        source: pt.source_attribution || 'Synoptic Weather Station',
      });
    } else {
      const existing = hourMap.get(pt.relative_hour)!;
      if (existing.observedRate == null && pt.observed_rainfall_rate != null) {
        existing.observedRate = pt.observed_rainfall_rate;
      }
    }
  });

  // Anchor at NOW (0h)
  const nowHist = historicalSeries.find((h) => h.relative_hour === 0);
  const nowRate = currentRainfallRate ?? (hourMap.has(0) ? hourMap.get(0)!.observedRate : null) ?? nowHist?.observed_rainfall_rate ?? 0.0;
  const nowHorizon = horizonByHour.get(1);
  const nowProbPct = isModelSupported
    ? (nowHorizon?.calibrated_flood_probability != null
        ? Math.round(nowHorizon.calibrated_flood_probability * 100)
        : Math.round(lastHistRisk))
    : null;

  hourMap.set(0, {
    relativeHour: 0,
    label: 'NOW',
    timeIst: precipitationForecast?.model_run_ist || 'NOW (IST)',
    timestamp: new Date().toISOString(),
    observedRate: nowRate,
    forecastRate: nowRate, // Anchor to connect seamlessly
    floodProbPct: nowProbPct,
    riskScore: isModelSupported ? lastHistRisk : null,
    riskTier: isModelSupported ? (lastHistRisk >= 75 ? 'CRITICAL' : lastHistRisk >= 50 ? 'HIGH' : lastHistRisk >= 25 ? 'WATCH' : 'LOW') : 'UNSUPPORTED',
    primaryDriver: nowHorizon?.primary_risk_driver || (isModelSupported ? 'Environmental Telemetry Baseline' : 'ML Model Inactive for Catchment'),
    isForecast: false,
    status: 'LIVE_OBSERVED',
    source: 'Automated Weather Telemetry',
  });

  // Ensure requested past milestones (-24hr, -12hr, -6hr, -1hr) exist in hourMap with real observed data
  const hist24 = historicalSeries.find((h) => h.relative_hour === -24);
  const rate24 = hist24?.observed_rainfall_rate ?? (currentSituation?.rainfall_24h_mm != null ? Math.round((currentSituation.rainfall_24h_mm / 24) * 10) / 10 : null);
  if (!hourMap.has(-24)) {
    hourMap.set(-24, {
      relativeHour: -24,
      label: '-24hr',
      timeIst: '-24h Past',
      timestamp: new Date(Date.now() - 24 * 3600000).toISOString(),
      observedRate: rate24,
      floodProbPct: isModelSupported ? Math.round(hist24?.operational_risk_score ?? historicalSeries[0]?.operational_risk_score ?? lastHistRisk) : null,
      riskScore: isModelSupported ? (hist24?.operational_risk_score ?? historicalSeries[0]?.operational_risk_score ?? lastHistRisk) : null,
      riskTier: isModelSupported ? 'LOW' : 'UNSUPPORTED',
      isForecast: false,
      status: 'OBSERVED',
      source: 'Synoptic 24h Telemetry',
    });
  } else {
    const pt24 = hourMap.get(-24)!;
    pt24.label = '-24hr';
    if (pt24.observedRate == null && rate24 != null) {
      pt24.observedRate = rate24;
    }
  }

  const hist12 = historicalSeries.find((h) => h.relative_hour === -12);
  const rate12 = hist12?.observed_rainfall_rate ?? (currentSituation?.rainfall_12h_mm != null ? Math.round((currentSituation.rainfall_12h_mm / 12) * 10) / 10 : null);
  if (!hourMap.has(-12)) {
    hourMap.set(-12, {
      relativeHour: -12,
      label: '-12hr',
      timeIst: '-12h Past',
      timestamp: new Date(Date.now() - 12 * 3600000).toISOString(),
      observedRate: rate12,
      floodProbPct: isModelSupported ? Math.round(hist12?.operational_risk_score ?? historicalSeries[0]?.operational_risk_score ?? lastHistRisk) : null,
      riskScore: isModelSupported ? (hist12?.operational_risk_score ?? historicalSeries[0]?.operational_risk_score ?? lastHistRisk) : null,
      riskTier: isModelSupported ? 'LOW' : 'UNSUPPORTED',
      isForecast: false,
      status: 'OBSERVED',
      source: 'Synoptic 12h Telemetry',
    });
  } else {
    const pt12 = hourMap.get(-12)!;
    pt12.label = '-12hr';
    if (pt12.observedRate == null && rate12 != null) {
      pt12.observedRate = rate12;
    }
  }

  const hist6 = historicalSeries.find((h) => h.relative_hour === -6);
  const rate6 = hist6?.observed_rainfall_rate ?? (currentSituation?.rainfall_6h_mm != null ? Math.round((currentSituation.rainfall_6h_mm / 6) * 10) / 10 : null);
  if (!hourMap.has(-6)) {
    hourMap.set(-6, {
      relativeHour: -6,
      label: '-6hr',
      timeIst: '-6h Past',
      timestamp: new Date(Date.now() - 6 * 3600000).toISOString(),
      observedRate: rate6,
      floodProbPct: isModelSupported ? Math.round(hist6?.operational_risk_score ?? lastHistRisk) : null,
      riskScore: isModelSupported ? (hist6?.operational_risk_score ?? lastHistRisk) : null,
      riskTier: isModelSupported ? 'LOW' : 'UNSUPPORTED',
      isForecast: false,
      status: 'OBSERVED',
      source: 'Synoptic 6h Telemetry',
    });
  } else {
    const pt6 = hourMap.get(-6)!;
    pt6.label = '-6hr';
    if (pt6.observedRate == null && rate6 != null) {
      pt6.observedRate = rate6;
    }
  }

  const hist1 = historicalSeries.find((h) => h.relative_hour === -1);
  const rate1 = hist1?.observed_rainfall_rate ?? currentSituation?.rainfall_1h_mm ?? null;
  if (!hourMap.has(-1)) {
    hourMap.set(-1, {
      relativeHour: -1,
      label: '-1hr',
      timeIst: '-1h Past',
      timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
      observedRate: rate1,
      floodProbPct: isModelSupported ? Math.round(hist1?.operational_risk_score ?? lastHistRisk) : null,
      riskScore: isModelSupported ? (hist1?.operational_risk_score ?? lastHistRisk) : null,
      riskTier: isModelSupported ? 'LOW' : 'UNSUPPORTED',
      isForecast: false,
      status: 'OBSERVED',
      source: 'Synoptic 1h Rain Gauge',
    });
  } else {
    const pt1 = hourMap.get(-1)!;
    pt1.label = '-1hr';
    if (pt1.observedRate == null && rate1 != null) {
      pt1.observedRate = rate1;
    }
  }

  // 2. Future Forecast Points (+1h to +48h): filter strictly to 1hr, 6hr, 12hr, 24hr, 48hr
  const targetFutureHorizons = [1, 6, 12, 24, 48];

  // Helper function to interpolate flood probability for intermediate hours
  const interpolateFloodProbability = (hour: number): { prob: number | null; score: number | null; tier: string; driver: string; p10: number | null; p90: number | null } => {
    if (!isModelSupported) {
      return {
        prob: null,
        score: null,
        tier: 'UNSUPPORTED',
        driver: 'Validated ML flood model inactive for location',
        p10: null,
        p90: null,
      };
    }

    // If exact horizon exists
    if (horizonByHour.has(hour)) {
      const h = horizonByHour.get(hour)!;
      if (h.risk_tier === 'UNSUPPORTED' || (h.calibrated_flood_probability == null && h.operational_risk_score == null)) {
        return {
          prob: null,
          score: null,
          tier: 'UNSUPPORTED',
          driver: h.primary_risk_driver || 'ML model inactive for location',
          p10: null,
          p90: null,
        };
      }
      const prob = h.calibrated_flood_probability != null
        ? Math.round(h.calibrated_flood_probability * 100)
        : (h.operational_risk_score != null ? Math.round(h.operational_risk_score) : null);
      const score = h.operational_risk_score ?? prob;
      const tier = h.risk_tier || (score !== null ? (score >= 75 ? 'CRITICAL' : score >= 50 ? 'HIGH' : score >= 25 ? 'WATCH' : 'LOW') : 'LOW');
      return {
        prob,
        score,
        tier,
        driver: h.primary_risk_driver || 'Precipitation Loading',
        p10: h.uncertainty_band?.p10 ?? (prob !== null ? Math.max(0, prob - 5) : null),
        p90: h.uncertainty_band?.p90 ?? (prob !== null ? Math.min(100, prob + 7) : null),
      };
    }

    // Find bounding horizons for interpolation
    const knownHours = Array.from(horizonByHour.keys()).sort((a, b) => a - b);
    const validKnown = knownHours.filter((kh) => {
      const hz = horizonByHour.get(kh);
      return hz && hz.risk_tier !== 'UNSUPPORTED' && (hz.calibrated_flood_probability != null || hz.operational_risk_score != null);
    });

    if (validKnown.length === 0) {
      return {
        prob: null,
        score: null,
        tier: 'UNSUPPORTED',
        driver: 'Empirical Hydrology Active',
        p10: null,
        p90: null,
      };
    }

    let prevH = 0;
    let nextH = validKnown[0];
    let prevProb: number | null = nowProbPct;
    let nextProb: number | null = null;

    for (let i = 0; i < validKnown.length; i++) {
      if (validKnown[i] <= hour) {
        prevH = validKnown[i];
        const ph = horizonByHour.get(prevH)!;
        prevProb = ph.calibrated_flood_probability != null ? Math.round(ph.calibrated_flood_probability * 100) : (ph.operational_risk_score ?? prevProb);
      }
      if (validKnown[i] > hour) {
        nextH = validKnown[i];
        const nh = horizonByHour.get(nextH)!;
        nextProb = nh.calibrated_flood_probability != null ? Math.round(nh.calibrated_flood_probability * 100) : (nh.operational_risk_score ?? prevProb);
        break;
      }
    }

    if (prevProb === null || nextProb === null || nextH === prevH || nextH === 0) {
      return {
        prob: prevProb,
        score: prevProb,
        tier: prevProb !== null ? (prevProb >= 75 ? 'CRITICAL' : prevProb >= 50 ? 'HIGH' : prevProb >= 25 ? 'WATCH' : 'LOW') : 'LOW',
        driver: 'Model Projection',
        p10: prevProb !== null ? Math.max(0, prevProb - 5) : null,
        p90: prevProb !== null ? Math.min(100, prevProb + 8) : null,
      };
    }

    const ratio = (hour - prevH) / (nextH - prevH);
    const interpolatedProb = Math.round(prevProb + ratio * (nextProb - prevProb));
    const tier = interpolatedProb >= 75 ? 'CRITICAL' : interpolatedProb >= 50 ? 'HIGH' : interpolatedProb >= 25 ? 'WATCH' : 'LOW';

    return {
      prob: interpolatedProb,
      score: interpolatedProb,
      tier,
      driver: horizonByHour.get(nextH)?.primary_risk_driver || 'Precipitation Loading',
      p10: Math.max(0, interpolatedProb - 6),
      p90: Math.min(100, interpolatedProb + 8),
    };
  };

  targetFutureHorizons.forEach((h) => {
    const pt = precipitationForecast?.forecast_points?.find((p) => p.relative_hour === h);
    const floodInfo = interpolateFloodProbability(h);
    const fcHorizon = horizonByHour.get(h);
    const rateVal = pt?.value_mm_hr ?? fcHorizon?.projected_rainfall_rate_mm_hr ?? null;

    hourMap.set(h, {
      relativeHour: h,
      label: `${h}hr`,
      timeIst: pt?.timestamp_ist || `+${h}h Future`,
      timestamp: pt?.timestamp_utc || new Date(Date.now() + h * 3600000).toISOString(),
      forecastRate: rateVal,
      floodProbPct: floodInfo.prob,
      riskScore: floodInfo.score,
      riskTier: floodInfo.tier,
      primaryDriver: floodInfo.driver,
      p10: floodInfo.p10,
      p90: floodInfo.p90,
      isForecast: true,
      status: pt?.status || 'PROJECTED',
      source: pt?.source || 'ECMWF IFS NWP & FlowShield Model',
    });
  });

  // User-mandated milestone timeline on X-axis:
  // -24hr, -12hr, -6hr, -1hr, NOW, 1hr, 6hr, 12hr, 24hr, 48hr
  const requestedHorizons = [-24, -12, -6, -1, 0, 1, 6, 12, 24, 48];
  const chartData = requestedHorizons
    .map((h) => hourMap.get(h))
    .filter((pt): pt is PrecipDataPoint => pt !== undefined);

  // Check if forecast data is actually available with valid data points
  const hasForecast = chartData.some(
    (p) => p.isForecast && (
      (p.forecastRate !== null && p.forecastRate !== undefined) ||
      (p.floodProbPct !== null && p.floodProbPct !== undefined && isModelSupported)
    )
  );

  // Calculate actual peak rate across observed and forecast series
  const allRates = chartData.map((d) => Math.max(d.observedRate ?? 0, d.forecastRate ?? 0));
  const peakVal = Math.max(
    currentRainfallRate || 0,
    precipitationForecast?.peak_forecast_mm_hr || 0,
    ...allRates
  );

  // Calculate peak future flood chance across forecast horizons
  const futureForecastPoints = chartData.filter((d) => d.isForecast && d.floodProbPct !== null && d.floodProbPct !== undefined);
  const peakFutureFloodProb = (isModelSupported && futureForecastPoints.length > 0)
    ? Math.max(...futureForecastPoints.map((d) => d.floodProbPct || 0))
    : (isModelSupported ? nowProbPct : null);
  const peakFloodPoint = futureForecastPoints.find((d) => d.floodProbPct === peakFutureFloodProb) || (isModelSupported ? chartData.find((d) => d.relativeHour === 0) : null);

  // Dynamic Adaptive Scaling (Auto-Zoom) for precipitation
  let yDomainMax: number;
  if (scaleMode === 'full') {
    yDomainMax = Math.max(20, Math.ceil(peakVal * 1.25));
  } else {
    if (peakVal <= 0.25) {
      yDomainMax = 0.5;
    } else if (peakVal <= 0.6) {
      yDomainMax = 1.0;
    } else if (peakVal <= 1.5) {
      yDomainMax = 2.0;
    } else if (peakVal <= 3.5) {
      yDomainMax = 5.0;
    } else if (peakVal <= 7.0) {
      yDomainMax = 10.0;
    } else if (peakVal <= 12.0) {
      yDomainMax = 15.0;
    } else {
      yDomainMax = Math.ceil(peakVal * 1.25);
    }
  }

  const modelName = precipitationForecast?.model_name || 'ECMWF IFS (0.1° High-Res Grid)';
  const modelRunIst = precipitationForecast?.model_run_ist || 'Recent Ingestion';
  const peakForecast = precipitationForecast?.peak_forecast_mm_hr;
  const peakTimeIst = precipitationForecast?.peak_forecast_time_ist;
  const calcAccum24h = () => {
    if (precipitationForecast?.accumulated_24h_forecast_mm != null) {
      return precipitationForecast.accumulated_24h_forecast_mm;
    }
    if (precipitationForecast?.forecast_points && precipitationForecast.forecast_points.length > 0) {
      const pts24 = precipitationForecast.forecast_points.slice(0, 24).filter((p) => p.value_mm_hr != null);
      if (pts24.length > 0) {
        return Math.round(pts24.reduce((sum, p) => sum + (p.value_mm_hr || 0), 0) * 10) / 10;
      }
    }
    const fcPoints = chartData.filter((d) => d.isForecast && d.forecastRate != null && d.relativeHour <= 24);
    if (fcPoints.length > 0) {
      return Math.round(fcPoints.reduce((sum, d) => sum + (d.forecastRate || 0), 0) * 10) / 10;
    }
    return null;
  };
  const accum24h = calcAccum24h();

  // Disaggregate observed historical peak vs forecast NWP peak
  const observedPeakRate = currentSituation?.observed_peak_rate_mm_hr ??
    Math.max(currentRainfallRate || 0, ...chartData.filter((d) => !d.isForecast).map((d) => d.observedRate ?? 0));
  const forecastPeakRate = currentSituation?.forecast_peak_rate_mm_hr ?? peakForecast ??
    (chartData.some((d) => d.isForecast) ? Math.max(...chartData.filter((d) => d.isForecast).map((d) => d.forecastRate ?? 0)) : null);

  // Helper for risk tier colors
  const getRiskColor = (prob: number) => {
    if (prob >= 75) return '#EF4444';
    if (prob >= 50) return '#F97316';
    if (prob >= 25) return '#F59E0B';
    return '#10B981';
  };

  const peakRiskColor = peakFutureFloodProb !== null ? getRiskColor(peakFutureFloodProb) : '#94A3B8';

  return (
    <div
      className="timeline-glass-card"
      style={{
        background: 'linear-gradient(135deg, rgba(7, 18, 38, 0.78) 0%, rgba(5, 12, 26, 0.88) 100%)',
        backdropFilter: 'blur(24px) saturate(140%)',
        WebkitBackdropFilter: 'blur(24px) saturate(140%)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '12px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.38)',
      }}
    >
      {/* 1. Header Strip: Title, View Switcher, Dynamic Metric Badges */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          paddingBottom: '12px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: viewMode === 'flood' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(56, 189, 248, 0.15)',
              border: viewMode === 'flood' ? '1px solid rgba(168, 85, 247, 0.35)' : '1px solid rgba(56, 189, 248, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {viewMode === 'flood' ? (
              <Waves size={19} color="#C084FC" />
            ) : viewMode === 'combined' ? (
              <ShieldAlert size={19} color="#38BDF8" />
            ) : (
              <CloudRain size={19} color="#38BDF8" />
            )}
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#F1F5F9', letterSpacing: '-0.01em', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>
                {viewMode === 'flood'
                  ? 'Predictive Flood Probability Horizon'
                  : viewMode === 'combined'
                  ? 'Dual-Axis Flood Chance & Precipitation Forecast'
                  : 'Numerical Precipitation Forecast'}
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                +48h Predictive ML
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
              <span>{settlementName ? `${settlementName} Catchment` : modelName}</span>
              <span>•</span>
              <span style={{ color: '#94A3B8' }}>{modelName}</span>
              <span>•</span>
              <span style={{ color: '#94A3B8' }}>Run: {modelRunIst}</span>
            </div>
          </div>
        </div>

        {/* View Mode Switcher: Flood Probability vs Dual Combined vs Raw Precipitation */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(15, 23, 42, 0.75)',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            gap: '2px',
          }}
        >
          <button
            onClick={() => setViewMode('flood')}
            style={{
              background: viewMode === 'flood' ? 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)' : 'transparent',
              color: viewMode === 'flood' ? '#FFFFFF' : '#94A3B8',
              border: 'none',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.18s ease',
              boxShadow: viewMode === 'flood' ? '0 2px 8px rgba(124, 58, 237, 0.4)' : 'none',
            }}
          >
            <Waves size={13} />
            <span>Flood Chance (%)</span>
          </button>

          <button
            onClick={() => setViewMode('combined')}
            style={{
              background: viewMode === 'combined' ? 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)' : 'transparent',
              color: viewMode === 'combined' ? '#FFFFFF' : '#94A3B8',
              border: 'none',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.18s ease',
              boxShadow: viewMode === 'combined' ? '0 2px 8px rgba(2, 132, 199, 0.4)' : 'none',
            }}
          >
            <BarChart2 size={13} />
            <span>Dual Combined</span>
          </button>

          <button
            onClick={() => setViewMode('rainfall')}
            style={{
              background: viewMode === 'rainfall' ? 'linear-gradient(135deg, #0D9488 0%, #0F766E 100%)' : 'transparent',
              color: viewMode === 'rainfall' ? '#FFFFFF' : '#94A3B8',
              border: 'none',
              borderRadius: '6px',
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.18s ease',
              boxShadow: viewMode === 'rainfall' ? '0 2px 8px rgba(13, 148, 136, 0.4)' : 'none',
            }}
          >
            <CloudRain size={13} />
            <span>Precipitation (mm/h)</span>
          </button>
        </div>

        {/* Real Metrics Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Peak Future Flood Chance Badge (Always Prominent!) */}
          <div
            style={{
              background: `${peakRiskColor}15`,
              border: `1px solid ${peakRiskColor}45`,
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '125px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: peakRiskColor, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={11} />
              <span>Future Flood Chance</span>
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {peakFutureFloodProb !== null ? (
                <>
                  {peakFutureFloodProb}%{' '}
                  <span style={{ fontSize: '10px', fontWeight: 600, color: peakRiskColor, textTransform: 'uppercase' }}>
                    ({peakFloodPoint?.riskTier || 'LOW'})
                  </span>
                </>
              ) : (
                <>
                  <span style={{ color: '#CBD5E1' }}>UNSUPPORTED</span>{' '}
                  <span style={{ fontSize: '10px', fontWeight: 600, color: '#F59E0B', textTransform: 'uppercase' }}>
                    (ML Inactive)
                  </span>
                </>
              )}
            </div>
            <div style={{ fontSize: '9.5px', color: '#94A3B8', marginTop: '1px' }}>
              {peakFutureFloodProb !== null
                ? `Peak Horizon: ${peakFloodPoint?.label || 'NOW'}`
                : 'Empirical Hydrology Active'}
            </div>
          </div>

          {/* Current Observed Rate */}
          <div
            style={{
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '115px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#38BDF8', textTransform: 'uppercase' }}>
              Current Rate
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {currentRainfallRate != null ? currentRainfallRate.toFixed(1) : '—'} <span style={{ fontSize: '11px', fontWeight: 500, color: '#64748B' }}>mm/h</span>
            </div>
            <div style={{ fontSize: '9.5px', color: '#94A3B8', marginTop: '1px' }}>
              Obs Peak: {observedPeakRate != null && observedPeakRate > 0 ? `${observedPeakRate.toFixed(1)} mm/h` : '0.0 mm/h'}
            </div>
          </div>

          {/* Forecast Peak Rain Rate */}
          <div
            style={{
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '120px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#F59E0B', textTransform: 'uppercase' }}>
              Forecast Peak Rate
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {forecastPeakRate !== undefined && forecastPeakRate !== null ? `${forecastPeakRate.toFixed(1)} mm/h` : 'N/A'}
            </div>
            {peakTimeIst ? (
              <div style={{ fontSize: '9.5px', color: '#94A3B8', marginTop: '1px' }}>
                {peakTimeIst.split(' ')[1]} IST
              </div>
            ) : (
              <div style={{ fontSize: '9.5px', color: '#94A3B8', marginTop: '1px' }}>
                Numerical Model
              </div>
            )}
          </div>

          {/* 24h Projected Accumulation */}
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '110px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#10B981', textTransform: 'uppercase' }}>
              24h Projected
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {accum24h !== undefined && accum24h !== null ? `${accum24h.toFixed(1)} mm` : 'N/A'}
            </div>
          </div>

          {/* Scale Mode Toggle (for rainfall axis) */}
          {viewMode !== 'flood' && (
            <button
              onClick={() => setScaleMode(scaleMode === 'auto' ? 'full' : 'auto')}
              style={{
                background: scaleMode === 'auto' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                border: scaleMode === 'auto' ? '1px solid rgba(56, 189, 248, 0.35)' : '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '8px',
                padding: '6px 12px',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                minWidth: '115px',
                textAlign: 'left',
                transition: 'all 0.2s ease',
              }}
              title={scaleMode === 'auto' ? 'Click to view Full IMD Scale (0-20 mm/h)' : 'Click to enable Auto Zoom'}
            >
              <div style={{ fontSize: '10px', fontWeight: 600, color: '#38BDF8', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {scaleMode === 'auto' ? <ZoomIn size={12} /> : <Maximize2 size={12} />}
                <span>{scaleMode === 'auto' ? 'Adaptive Zoom' : 'Full Scale'}</span>
              </div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC', marginTop: '1px' }}>
                0 – {yDomainMax} <span style={{ fontSize: '11px', fontWeight: 500, color: '#64748B' }}>mm/h</span>
              </div>
            </button>
          )}
        </div>
      </div>

      {/* 1.5 Flood Prediction Alert Banner — powered by rainfall model threshold_analysis */}
      {(() => {
        const crossingHour = thresholdAnalysis?.most_likely_crossing_hour ?? peakAnalysis?.risk_peak_hours ?? null;
        const tier = thresholdAnalysis?.threshold_name || 'WATCH';
        const isCrossed = thresholdAnalysis?.is_crossed ?? false;
        const leadTime = thresholdAnalysis?.lead_time_hours ?? null;

        // Compute absolute predicted time from now + crossing hours
        let predictedTimeStr = '';
        if (crossingHour !== null && crossingHour !== undefined) {
          const predictedDate = new Date(Date.now() + crossingHour * 60 * 60 * 1000);
          predictedTimeStr = predictedDate.toLocaleTimeString('en-IN', {
            timeZone: 'Asia/Kolkata',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
          }) + ' IST, ' + predictedDate.toLocaleDateString('en-IN', {
            timeZone: 'Asia/Kolkata',
            day: 'numeric',
            month: 'short',
          });
        }

        const bannerColor = tier === 'CRITICAL' ? '#EF4444' : tier === 'HIGH' ? '#F97316' : '#F59E0B';
        const bannerBg = tier === 'CRITICAL' ? 'rgba(239,68,68,0.10)' : tier === 'HIGH' ? 'rgba(249,115,22,0.10)' : 'rgba(245,158,11,0.10)';
        const bannerBorder = tier === 'CRITICAL' ? 'rgba(239,68,68,0.38)' : tier === 'HIGH' ? 'rgba(249,115,22,0.38)' : 'rgba(245,158,11,0.38)';

        if (!crossingHour && !isCrossed) return null;

        return (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px',
              background: bannerBg,
              border: `1px solid ${bannerBorder}`,
              borderRadius: '8px',
              padding: '10px 14px',
              animation: tier === 'CRITICAL' ? 'floodPulse 2.2s ease-in-out infinite' : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* Animated dot */}
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: bannerColor,
                  boxShadow: `0 0 8px ${bannerColor}`,
                  flexShrink: 0,
                  animation: 'ping 1.5s cubic-bezier(0,0,0.2,1) infinite',
                }}
              />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: bannerColor, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {isCrossed ? '⚠ Threshold Already Breached' : `Rainfall Model Prediction — ${tier} Tier`}
                </div>
                <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#F1F5F9', marginTop: '2px' }}>
                  {isCrossed
                    ? `Flood threshold breached · Risk Score ≥ ${thresholdAnalysis?.threshold_value ?? '–'}`
                    : predictedTimeStr
                    ? <>Expected flood conditions predicted at <span style={{ color: bannerColor }}>{predictedTimeStr}</span> <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 500 }}>(T+{crossingHour}h horizon)</span></>
                    : 'Flood threshold crossing forecast window active'}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '18px', flexWrap: 'wrap' }}>
              {leadTime !== null && leadTime !== undefined && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase' }}>Model Lead-Time</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: bannerColor }}>{leadTime.toFixed(1)}h</div>
                </div>
              )}
              {thresholdAnalysis?.earliest_crossing_hour != null && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase' }}>Earliest (P90)</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#F1F5F9' }}>T+{thresholdAnalysis.earliest_crossing_hour.toFixed(1)}h</div>
                </div>
              )}
              <div
                style={{
                  padding: '4px 12px',
                  borderRadius: '20px',
                  background: `${bannerColor}20`,
                  border: `1px solid ${bannerColor}55`,
                  fontSize: '11px',
                  fontWeight: 700,
                  color: bannerColor,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {tier} ALERT
              </div>
            </div>
          </div>
        );
      })()}

      {/* 2. Main Predictive Chart Container */}
      {!hasForecast ? (
        <div
          style={{
            padding: '36px 20px',
            textAlign: 'center',
            background: 'rgba(15, 23, 42, 0.4)',
            borderRadius: '8px',
            border: '1px dashed rgba(100, 116, 139, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          <AlertCircle size={24} color="#F59E0B" />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#E2E8F0' }}>
            Forecast Telemetry Currently Synchronizing
          </div>
          <div style={{ fontSize: '11.5px', color: '#64748B', maxWidth: '540px', lineHeight: 1.5 }}>
            Synthesizing latest numerical NWP and multi-horizon machine learning predictions for {settlementName || 'this settlement'}.
          </div>
        </div>
      ) : (
        <div style={{ width: '100%', height: '310px', position: 'relative' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 12, right: viewMode === 'combined' ? 24 : 16, left: -10, bottom: 4 }}>
              <defs>
                {/* Cyan Gradient for Observed Rainfall */}
                <linearGradient id="observedRainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity={0.55} />
                  <stop offset="100%" stopColor="#00f0ff" stopOpacity={0.03} />
                </linearGradient>

                {/* Sky Blue Gradient for Forecast Rainfall */}
                <linearGradient id="forecastRainGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.03} />
                </linearGradient>

                {/* Purple/Violet Gradient for Flood Probability (%) */}
                <linearGradient id="floodProbGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#A855F7" stopOpacity={0.65} />
                  <stop offset="40%" stopColor="#8B5CF6" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.04} />
                </linearGradient>
              </defs>

              <CartesianGrid stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="3 3" vertical={false} />

              <XAxis
                dataKey="label"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                stroke="rgba(255, 255, 255, 0.12)"
                tickLine={false}
              />

              {/* Primary Left Y-Axis */}
              {viewMode === 'flood' ? (
                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  tick={{ fill: '#C084FC', fontSize: 11 }}
                  stroke="rgba(168, 85, 247, 0.25)"
                  tickLine={false}
                  tickFormatter={(val: number) => `${val}%`}
                  label={{
                    value: 'Future Flood Probability (%)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#C084FC',
                    fontSize: 10,
                    dy: 60,
                  }}
                />
              ) : (
                <YAxis
                  yAxisId={viewMode === 'combined' ? 'rain' : undefined}
                  domain={[0, yDomainMax]}
                  tick={{ fill: '#38BDF8', fontSize: 11 }}
                  stroke="rgba(56, 189, 248, 0.25)"
                  tickLine={false}
                  tickFormatter={(val: number) => {
                    if (yDomainMax <= 2.0) {
                      return val.toFixed(1);
                    }
                    return Number.isInteger(val) ? val.toString() : val.toFixed(1);
                  }}
                  label={{
                    value: 'Rainfall Rate (mm/h)',
                    angle: -90,
                    position: 'insideLeft',
                    fill: '#38BDF8',
                    fontSize: 10,
                    dy: 50,
                  }}
                />
              )}

              {/* Secondary Right Y-Axis for Combined View */}
              {viewMode === 'combined' && (
                <YAxis
                  yAxisId="flood"
                  orientation="right"
                  domain={[0, 100]}
                  ticks={[0, 25, 50, 75, 100]}
                  tick={{ fill: '#C084FC', fontSize: 11 }}
                  stroke="rgba(168, 85, 247, 0.25)"
                  tickLine={false}
                  tickFormatter={(val: number) => `${val}%`}
                  label={{
                    value: 'Flood Chance (%)',
                    angle: 90,
                    position: 'insideRight',
                    fill: '#C084FC',
                    fontSize: 10,
                    dy: 40,
                  }}
                />
              )}

              {/* Vertical Reference Line at NOW (Observed vs Forecast boundary) */}
              <ReferenceLine
                x="NOW"
                yAxisId={viewMode === 'combined' ? 'rain' : undefined}
                stroke="#F59E0B"
                strokeWidth={2}
                strokeDasharray="4 4"
                label={{
                  value: 'NOW (LIVE)',
                  position: 'top',
                  fill: '#F59E0B',
                  fontSize: 10,
                  fontWeight: 700,
                }}
              />

              {/* Threshold Lines for Flood Risk in Flood / Combined Modes */}
              {viewMode !== 'rainfall' && (
                <>
                  <ReferenceLine
                    yAxisId={viewMode === 'combined' ? 'flood' : undefined}
                    y={25}
                    stroke="#EAB308"
                    strokeDasharray="2 3"
                    strokeWidth={1}
                    label={{
                      value: 'Watch: 25%',
                      position: 'insideBottomRight',
                      fill: '#EAB308',
                      fontSize: 9,
                    }}
                  />
                  <ReferenceLine
                    yAxisId={viewMode === 'combined' ? 'flood' : undefined}
                    y={50}
                    stroke="#F97316"
                    strokeDasharray="2 3"
                    strokeWidth={1}
                    label={{
                      value: 'High Risk: 50%',
                      position: 'insideBottomRight',
                      fill: '#F97316',
                      fontSize: 9,
                    }}
                  />
                  <ReferenceLine
                    yAxisId={viewMode === 'combined' ? 'flood' : undefined}
                    y={75}
                    stroke="#EF4444"
                    strokeDasharray="3 3"
                    strokeWidth={1.5}
                    label={{
                      value: 'Critical Inundation: 75%',
                      position: 'insideTopRight',
                      fill: '#EF4444',
                      fontSize: 9,
                    }}
                  />
                </>
              )}

              {/* Heavy Rainfall Advisory Threshold (15 mm/h IMD standard) */}
              {viewMode === 'rainfall' && yDomainMax >= 15 && (
                <ReferenceLine
                  y={15}
                  stroke="#EF4444"
                  strokeDasharray="3 3"
                  strokeWidth={1.5}
                  label={{
                    value: 'Heavy Rain Threshold (15 mm/h)',
                    position: 'right',
                    fill: '#EF4444',
                    fontSize: 9.5,
                  }}
                />
              )}

              {/* 1. Rainfall Series (in Combined or Rainfall Mode) */}
              {viewMode !== 'flood' && (
                <>
                  {/* Observed Telemetry: Solid Vibrant Cyan Area */}
                  <Area
                    yAxisId={viewMode === 'combined' ? 'rain' : undefined}
                    type="linear"
                    dataKey="observedRate"
                    name="Observed Rainfall Rate"
                    stroke="#00f0ff"
                    strokeWidth={2.4}
                    fill="url(#observedRainGrad)"
                    dot={{ r: 3, fill: '#00f0ff', stroke: '#0891b2', strokeWidth: 1 }}
                    connectNulls={true}
                  />

                  {/* Numerical Forecast: Shaded Area with Glowing Sky Blue Boundary */}
                  <Area
                    yAxisId={viewMode === 'combined' ? 'rain' : undefined}
                    type="linear"
                    dataKey="forecastRate"
                    name="Forecast Rainfall Rate"
                    stroke="#38bdf8"
                    strokeWidth={2.4}
                    strokeDasharray="5 4"
                    fill="url(#forecastRainGrad)"
                    dot={{ r: 3.5, fill: '#38bdf8', stroke: '#0369a1', strokeWidth: 1.5 }}
                    activeDot={{ r: 6, fill: '#38bdf8', stroke: '#ffffff', strokeWidth: 2 }}
                    connectNulls={true}
                  />
                </>
              )}

              {/* 2. Flood Probability Series (in Flood or Combined Mode) */}
              {viewMode === 'flood' && (
                <Area
                  type="linear"
                  dataKey="floodProbPct"
                  name="Future Flood Chance (%)"
                  stroke="#C084FC"
                  strokeWidth={3}
                  fill="url(#floodProbGrad)"
                  dot={(props: any) => {
                    const { cx, cy, payload } = props;
                    if (!cx || !cy) return <g key={`dot-${props.index}`} />;
                    const color = getRiskColor(payload.floodProbPct || 0);
                    return (
                      <circle
                        key={`dot-${payload.relativeHour}`}
                        cx={cx}
                        cy={cy}
                        r={payload.relativeHour === 0 ? 5 : 4}
                        fill={color}
                        stroke="#FFFFFF"
                        strokeWidth={1.5}
                      />
                    );
                  }}
                  activeDot={{ r: 7, fill: '#C084FC', stroke: '#FFFFFF', strokeWidth: 2 }}
                  connectNulls={true}
                />
              )}

              {viewMode === 'combined' && (
                <Line
                  yAxisId="flood"
                  type="linear"
                  dataKey="floodProbPct"
                  name="Future Flood Probability (%)"
                  stroke="#C084FC"
                  strokeWidth={3}
                  dot={(props: any) => {
                    const { cx, cy, payload } = props;
                    if (!cx || !cy) return <g key={`dot-${props.index}`} />;
                    const color = getRiskColor(payload.floodProbPct || 0);
                    return (
                      <circle
                        key={`dot-${payload.relativeHour}`}
                        cx={cx}
                        cy={cy}
                        r={payload.relativeHour === 0 ? 5 : 4}
                        fill={color}
                        stroke="#FFFFFF"
                        strokeWidth={1.5}
                      />
                    );
                  }}
                  activeDot={{ r: 7, fill: '#C084FC', stroke: '#FFFFFF', strokeWidth: 2 }}
                  connectNulls={true}
                />
              )}

              {/* Interactive Tooltip */}
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null;
                  const data: PrecipDataPoint = payload[0].payload;
                  const rainVal = data.isForecast ? data.forecastRate : data.observedRate;
                  const floodProb = data.floodProbPct;
                  const riskColor = getRiskColor(floodProb ?? 0);

                  return (
                    <div
                      style={{
                        background: 'rgba(6, 15, 30, 0.96)',
                        backdropFilter: 'blur(16px)',
                        border: '1px solid rgba(168, 85, 247, 0.35)',
                        boxShadow: '0 8px 28px rgba(0,0,0,0.65)',
                        borderRadius: '8px',
                        padding: '12px 15px',
                        minWidth: '220px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11.5px', fontWeight: 700, color: data.isForecast ? '#C084FC' : '#00F0FF' }}>
                          {data.isForecast ? `Forecast Horizon (${data.label})` : `Observed Telemetry (${data.label})`}
                        </span>
                        <span
                          style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: `${riskColor}22`,
                            color: riskColor,
                            border: `1px solid ${riskColor}55`,
                            textTransform: 'uppercase',
                          }}
                        >
                          {data.riskTier || 'LOW'}
                        </span>
                      </div>

                      <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: '6px' }}>
                        IST Time: <strong style={{ color: '#F1F5F9' }}>{data.timeIst}</strong>
                      </div>

                      {/* Future Flood Probability Callout */}
                      <div
                        style={{
                          background: 'rgba(168, 85, 247, 0.1)',
                          border: '1px solid rgba(168, 85, 247, 0.25)',
                          borderRadius: '6px',
                          padding: '6px 10px',
                          marginBottom: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span style={{ fontSize: '11px', color: '#E2E8F0', fontWeight: 600 }}>Flood Chance:</span>
                        <span style={{ fontSize: '15px', fontWeight: 800, color: riskColor }}>
                          {floodProb !== null && floodProb !== undefined ? `${floodProb}%` : 'Evaluating'}
                        </span>
                      </div>

                      {/* Rainfall Rate */}
                      <div style={{ fontSize: '11.5px', color: '#CBD5E1', display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ color: '#94A3B8' }}>Rainfall Rate:</span>
                        <strong>{rainVal !== null && rainVal !== undefined ? `${rainVal.toFixed(2)} mm/h` : '0.00 mm/h'}</strong>
                      </div>

                      {/* Primary Risk Driver */}
                      {data.primaryDriver && (
                        <div style={{ fontSize: '10px', color: '#94A3B8', marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '5px' }}>
                          Primary Driver: <span style={{ color: '#E2E8F0' }}>{data.primaryDriver}</span>
                        </div>
                      )}

                      <div style={{ fontSize: '9px', color: '#64748B', marginTop: '4px' }}>
                        Source: {data.source}
                      </div>
                    </div>
                  );
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 3. Interactive Legend & Scientific Calibration Notice */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '10px',
          fontSize: '11px',
          color: '#64748B',
          paddingTop: '8px',
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          {/* Flood Probability Indicator */}
          {viewMode !== 'rainfall' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#C084FC', border: '2px solid #FFFFFF' }} />
              <span style={{ color: '#E2E8F0', fontWeight: 600 }}>Predictive Flood Chance (0-100%)</span>
            </div>
          )}

          {/* Observed Rain Indicator */}
          {viewMode !== 'flood' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '14px', height: '3px', background: '#00f0ff', borderRadius: '2px' }} />
              <span style={{ color: '#CBD5E1' }}>Observed Rainfall (-6h to NOW)</span>
            </div>
          )}

          {/* Forecast Rain Indicator */}
          {viewMode !== 'flood' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '14px', height: '2px', borderTop: '2px dashed #38bdf8' }} />
              <span style={{ color: '#CBD5E1' }}>ECMWF Forecast (+1h to +48h)</span>
            </div>
          )}

          {/* Threshold Badges in Legend */}
          {viewMode !== 'rainfall' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px' }}>
              <span style={{ color: '#10B981' }}>● Low (&lt;25%)</span>
              <span style={{ color: '#EAB308' }}>● Watch (25-50%)</span>
              <span style={{ color: '#F97316' }}>● High (50-75%)</span>
              <span style={{ color: '#EF4444' }}>● Critical (&ge;75%)</span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '10.5px', color: '#94A3B8' }}>
          <Info size={13} color="#38BDF8" />
          <span>Calibrated Machine Learning Inference • Cross-Horizon Physical Runoff Integration</span>
        </div>
      </div>

      {/* 4. Rainfall Accumulation Summary Strip */}
      {(() => {
        // --- Observed windows (from pre-computed ObservationSnapshot) ---
        const obs1h  = currentSituation?.rainfall_1h_mm  ?? null;
        const obs6h  = currentSituation?.rainfall_6h_mm  ?? null;
        const obs12h = currentSituation?.rainfall_12h_mm ?? null;
        const obs24h = currentSituation?.rainfall_24h_mm ?? null;

        // --- Forecast windows (cumulative_precipitation_mm from forecast horizons) ---
        const getFC = (h: number) => {
          const pt = forecastHorizons.find((f) => f.horizon_hours === h);
          return pt?.cumulative_precipitation_mm ?? null;
        };
        const fc1h  = getFC(1);
        const fc6h  = getFC(6);
        const fc12h = getFC(12);
        const fc24h = getFC(24) ?? precipitationForecast?.accumulated_24h_forecast_mm ?? null;
        const fc48h = getFC(48);

        const fmt = (v: number | null) => v !== null ? `${v.toFixed(1)}` : '—';

        // IMD rainfall intensity classification (mm/h)
        const classifyObs = (v: number | null, hours: number): { label: string; color: string } => {
          if (v === null) return { label: '', color: '#94A3B8' };
          const rate = v / hours;
          if (rate >= 8.0)  return { label: 'Heavy', color: '#EF4444' };
          if (rate >= 2.5)  return { label: 'Mod', color: '#F97316' };
          if (rate >= 0.5)  return { label: 'Light', color: '#EAB308' };
          return { label: 'Trace', color: '#10B981' };
        };

        const obsWindows = [
          { label: 'Prev 1h',  value: obs1h,  hours: 1 },
          { label: 'Prev 6h',  value: obs6h,  hours: 6 },
          { label: 'Prev 12h', value: obs12h, hours: 12 },
          { label: 'Prev 24h', value: obs24h, hours: 24 },
        ];
        const fcWindows = [
          { label: 'Next 1h',  value: fc1h  },
          { label: 'Next 6h',  value: fc6h  },
          { label: 'Next 12h', value: fc12h },
          { label: 'Next 24h', value: fc24h },
          { label: 'Next 48h', value: fc48h },
        ];

        return (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              gap: '0',
              alignItems: 'stretch',
              background: 'rgba(10, 20, 40, 0.55)',
              border: '1px solid rgba(56, 189, 248, 0.15)',
              borderRadius: '10px',
              overflow: 'hidden',
            }}
          >
            {/* LEFT — Observed */}
            <div style={{ padding: '12px 14px' }}>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#00F0FF', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00F0FF', display: 'inline-block' }} />
                Observed Accumulation
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {obsWindows.map(({ label, value, hours }) => {
                  const cls = classifyObs(value, hours);
                  return (
                    <div key={label} style={{ flex: '1 1 70px', background: 'rgba(0, 240, 255, 0.06)', border: '1px solid rgba(0, 240, 255, 0.18)', borderRadius: '7px', padding: '8px 10px', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, marginBottom: '4px' }}>{label}</div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: value !== null ? '#E2E8F0' : '#475569', lineHeight: 1 }}>{fmt(value)}</div>
                      <div style={{ fontSize: '9.5px', color: '#64748B', marginTop: '2px' }}>mm</div>
                      {cls.label && <div style={{ fontSize: '9px', fontWeight: 700, color: cls.color, marginTop: '3px', textTransform: 'uppercase' }}>{cls.label}</div>}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* DIVIDER */}
            <div style={{ width: '1px', background: 'rgba(255,255,255,0.08)', margin: '12px 0' }} />

            {/* RIGHT — Forecast */}
            <div style={{ padding: '12px 14px' }}>
              <div style={{ fontSize: '10px', fontWeight: 700, color: '#C084FC', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#C084FC', display: 'inline-block' }} />
                Predicted Accumulation
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {fcWindows.map(({ label, value }) => (
                  <div key={label} style={{ flex: '1 1 70px', background: 'rgba(192, 132, 252, 0.06)', border: '1px solid rgba(192, 132, 252, 0.18)', borderRadius: '7px', padding: '8px 10px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 600, marginBottom: '4px' }}>{label}</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: value !== null ? '#E2E8F0' : '#475569', lineHeight: 1 }}>{fmt(value)}</div>
                    <div style={{ fontSize: '9.5px', color: '#64748B', marginTop: '2px' }}>mm</div>
                    {value !== null && (
                      <div style={{ fontSize: '9px', fontWeight: 600, color: '#8B5CF6', marginTop: '3px' }}>cumul.</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
