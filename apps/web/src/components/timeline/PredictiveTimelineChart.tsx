import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import {
  HistoricalSeriesPoint,
  ForecastHorizonPoint,
} from '../../types';
import { Eye, EyeOff, Layers } from 'lucide-react';

interface PredictiveTimelineChartProps {
  historicalSeries: HistoricalSeriesPoint[];
  forecastHorizons: ForecastHorizonPoint[];
  currentRainfallRate: number;
  currentRiverStage: number | null | undefined;
  currentSoilSaturation: number;
}

interface MergedChartPoint {
  relativeHour: number;
  label: string;
  timestamp: string;
  isForecast: boolean;
  // Observed series (only defined up to relativeHour 0)
  observedRisk?: number;
  observedRain?: number | null;
  observedRiver?: number | null;
  observedSoil?: number | null;
  // Forecast series (defined from relativeHour 0 onwards for continuity)
  forecastRisk?: number | null;
  forecastRain?: number | null;
  forecastRiver?: number | null;
  forecastSoil?: number | null;
  // Uncertainty band (for forecast)
  p10?: number | null;
  p90?: number | null;
  uncertaintySpan?: [number, number] | null;
  primaryDriver?: string;
}

export const PredictiveTimelineChart: React.FC<PredictiveTimelineChartProps> = ({
  historicalSeries,
  forecastHorizons,
  currentRainfallRate,
  currentRiverStage,
  currentSoilSaturation,
}) => {
  // Toggleable Layer States
  const [showRisk, setShowRisk] = useState<boolean>(true);
  const [showUncertainty, setShowUncertainty] = useState<boolean>(true);
  const [showRainfall, setShowRainfall] = useState<boolean>(true);
  const [showRiver, setShowRiver] = useState<boolean>(true);
  const [showSoil, setShowSoil] = useState<boolean>(false);

  // Merge historical and forecast points into a single continuous time continuum
  const chartData: MergedChartPoint[] = [];

  // 1. Add historical points
  historicalSeries.forEach((pt) => {
    chartData.push({
      relativeHour: pt.relative_hour,
      label: `${pt.relative_hour}h`,
      timestamp: pt.timestamp,
      isForecast: false,
      observedRisk: pt.operational_risk_score,
      observedRain: pt.observed_rainfall_rate,
      observedRiver: pt.observed_river_stage,
      observedSoil: pt.observed_soil_saturation,
    });
  });

  // Base anchor point at relativeHour 0 (NOW)
  const nowRisk = historicalSeries.length > 0 ? historicalSeries[historicalSeries.length - 1].operational_risk_score : 20.0;
  const nowPoint: MergedChartPoint = {
    relativeHour: 0,
    label: 'NOW',
    timestamp: new Date().toISOString(),
    isForecast: false,
    observedRisk: nowRisk,
    observedRain: currentRainfallRate,
    observedRiver: currentRiverStage,
    observedSoil: currentSoilSaturation,
    // Connect forecast line seamlessly from NOW
    forecastRisk: nowRisk,
    forecastRain: currentRainfallRate,
    forecastRiver: currentRiverStage,
    forecastSoil: currentSoilSaturation,
    p10: undefined,
    p90: undefined,
    uncertaintySpan: undefined,
  };

  // Replace or add NOW point
  const existingNowIdx = chartData.findIndex((p) => p.relativeHour === 0);
  if (existingNowIdx >= 0) {
    chartData[existingNowIdx] = nowPoint;
  } else {
    chartData.push(nowPoint);
  }

  // 2. Add forecast points
  forecastHorizons.forEach((h) => {
    chartData.push({
      relativeHour: h.horizon_hours,
      label: `+${h.horizon_hours}h`,
      timestamp: h.forecast_timestamp,
      isForecast: true,
      forecastRisk: h.operational_risk_score,
      forecastRain: h.projected_rainfall_rate_mm_hr,
      forecastRiver: h.projected_river_stage_meters,
      forecastSoil: h.projected_soil_saturation_pct,
      p10: h.uncertainty_band?.p10,
      p90: h.uncertainty_band?.p90,
      uncertaintySpan: (h.uncertainty_band && h.uncertainty_band.p10 != null && h.uncertainty_band.p90 != null)
        ? [h.uncertainty_band.p10, h.uncertainty_band.p90]
        : null,
      primaryDriver: h.primary_risk_driver,
    });
  });

  // Sort chronologically by relative hour
  chartData.sort((a, b) => a.relativeHour - b.relativeHour);

  // Custom Chart Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const data: MergedChartPoint = payload[0]?.payload;
    if (!data) return null;

    const isForecast = data.relativeHour > 0;
    const timeFormatted = data.timestamp
      ? `${new Date(data.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', timeZone: 'Asia/Kolkata' })}, ${new Date(data.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata' })} IST`
      : label;

    return (
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.88) 0%, rgba(4, 12, 26, 0.92) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderTop: '1px solid rgba(255, 255, 255, 0.25)',
          borderRadius: '8px',
          padding: '10px 14px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.12)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          minWidth: '220px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155', paddingBottom: '6px', marginBottom: '8px' }}>
          <span style={{ fontWeight: 700, color: '#F1F5F9', fontSize: '13px' }}>
            Horizon: {data.label}
          </span>
          <span
            style={{
              fontSize: '10px',
              padding: '1px 6px',
              borderRadius: '4px',
              background: isForecast ? 'rgba(56, 189, 248, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              color: isForecast ? '#38BDF8' : '#10B981',
              fontWeight: 700,
            }}
          >
            {isForecast ? 'NUMERICAL FORECAST' : 'GROUND TRUTH OBSERVED'}
          </span>
        </div>

        <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: '8px' }}>
          Time: {timeFormatted}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '12px' }}>
          {/* Risk Score */}
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#F97316', fontWeight: 600 }}>Operational Risk:</span>
            <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
              {(data.forecastRisk ?? data.observedRisk ?? 0).toFixed(1)} / 100
            </span>
          </div>

          {/* Uncertainty Range */}
          {isForecast && data.p10 != null && data.p90 != null && (
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94A3B8' }}>
              <span>Uncertainty Band [P10–P90]:</span>
              <span style={{ fontFamily: 'monospace', color: '#FDBA74' }}>
                [{data.p10.toFixed(1)} – {data.p90.toFixed(1)}]
              </span>
            </div>
          )}

          {/* Rainfall */}
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#38BDF8', fontWeight: 600 }}>Rainfall Rate:</span>
            <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
              {(data.forecastRain ?? data.observedRain ?? 0).toFixed(1)} mm/hr
            </span>
          </div>

          {/* River Stage */}
          {(data.forecastRiver !== null && data.forecastRiver !== undefined) ||
          (data.observedRiver !== null && data.observedRiver !== undefined) ? (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#2DD4BF', fontWeight: 600 }}>River Stage:</span>
              <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {(data.forecastRiver ?? data.observedRiver)?.toFixed(2)} m
              </span>
            </div>
          ) : null}

          {/* Soil Moisture */}
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#C084FC', fontWeight: 600 }}>Soil Saturation:</span>
            <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
              {(data.forecastSoil ?? data.observedSoil ?? 0).toFixed(1)}%
            </span>
          </div>

          {/* Primary Driver */}
          {data.primaryDriver && (
            <div style={{ marginTop: '4px', paddingTop: '4px', borderTop: '1px solid #1e293b', fontSize: '10px', color: '#CBD5E1' }}>
              Primary Driver: <strong style={{ color: '#38BDF8' }}>{data.primaryDriver}</strong>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div
      className="timeline-glass-card"
      style={{
        background: 'linear-gradient(135deg, rgba(6, 18, 38, 0.58) 0%, rgba(4, 12, 26, 0.68) 100%)',
        backdropFilter: 'blur(20px) saturate(140%)',
        WebkitBackdropFilter: 'blur(20px) saturate(140%)',
        border: '1px solid rgba(56, 189, 248, 0.22)',
        borderTop: '1px solid rgba(255, 255, 255, 0.28)',
        borderRadius: '10px',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px rgba(34, 211, 238, 0.04)',
      }}
    >
      {/* Top Controls: Title, Legend and Layer Checkboxes */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Multi-Horizon Hydro-Meteorological Continuum
          </div>
          <div style={{ fontSize: '16px', color: '#F1F5F9', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>Operational Risk Timeline (-6h Observed → +48h Calibrated Forecast)</span>
            <span style={{ fontSize: '11px', color: '#CBD5E1', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ display: 'inline-block', width: '16px', height: '3px', background: '#F97316' }} /> Solid: Observed
              <span style={{ display: 'inline-block', width: '16px', height: '3px', background: '#F97316', borderTop: '2px dashed #F97316', marginLeft: '6px' }} /> Dashed: Forecast
            </span>
          </div>
        </div>

        {/* Metric Layer Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {/* Risk Toggle */}
          <button
            onClick={() => setShowRisk(!showRisk)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              background: showRisk ? 'rgba(249, 115, 22, 0.22)' : 'rgba(8, 24, 46, 0.45)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              border: `1px solid ${showRisk ? '#F97316' : 'rgba(56, 189, 248, 0.20)'}`,
              borderTop: `1px solid ${showRisk ? '#FB923C' : 'rgba(255, 255, 255, 0.15)'}`,
              color: showRisk ? '#F97316' : '#CBD5E1',
              transition: 'all 0.15s ease',
              boxShadow: showRisk ? '0 0 10px rgba(249, 115, 22, 0.25)' : 'none',
            }}
          >
            {showRisk ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>Risk Index</span>
          </button>

          {/* Uncertainty Band Toggle */}
          <button
            onClick={() => setShowUncertainty(!showUncertainty)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              background: showUncertainty ? 'rgba(251, 146, 60, 0.22)' : 'rgba(8, 24, 46, 0.45)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              border: `1px solid ${showUncertainty ? '#FB923C' : 'rgba(56, 189, 248, 0.20)'}`,
              borderTop: `1px solid ${showUncertainty ? '#FDBA74' : 'rgba(255, 255, 255, 0.15)'}`,
              color: showUncertainty ? '#FB923C' : '#CBD5E1',
              transition: 'all 0.15s ease',
              boxShadow: showUncertainty ? '0 0 10px rgba(251, 146, 60, 0.25)' : 'none',
            }}
          >
            <Layers size={12} />
            <span>P10–P90 Band</span>
          </button>

          {/* Rainfall Toggle */}
          <button
            onClick={() => setShowRainfall(!showRainfall)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              background: showRainfall ? 'rgba(56, 189, 248, 0.22)' : 'rgba(8, 24, 46, 0.45)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              border: `1px solid ${showRainfall ? '#38BDF8' : 'rgba(56, 189, 248, 0.20)'}`,
              borderTop: `1px solid ${showRainfall ? '#BAE6FD' : 'rgba(255, 255, 255, 0.15)'}`,
              color: showRainfall ? '#38BDF8' : '#CBD5E1',
              transition: 'all 0.15s ease',
              boxShadow: showRainfall ? '0 0 10px rgba(56, 189, 248, 0.25)' : 'none',
            }}
          >
            {showRainfall ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>Precipitation (mm/h)</span>
          </button>

          {/* River Stage Toggle */}
          <button
            onClick={() => setShowRiver(!showRiver)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              background: showRiver ? 'rgba(45, 212, 191, 0.22)' : 'rgba(8, 24, 46, 0.45)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              border: `1px solid ${showRiver ? '#2DD4BF' : 'rgba(56, 189, 248, 0.20)'}`,
              borderTop: `1px solid ${showRiver ? '#99F6E4' : 'rgba(255, 255, 255, 0.15)'}`,
              color: showRiver ? '#2DD4BF' : '#CBD5E1',
              transition: 'all 0.15s ease',
              boxShadow: showRiver ? '0 0 10px rgba(45, 212, 191, 0.25)' : 'none',
            }}
          >
            {showRiver ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>River Stage (m)</span>
          </button>

          {/* Soil Moisture Toggle */}
          <button
            onClick={() => setShowSoil(!showSoil)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              background: showSoil ? 'rgba(192, 132, 252, 0.22)' : 'rgba(8, 24, 46, 0.45)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              border: `1px solid ${showSoil ? '#C084FC' : 'rgba(56, 189, 248, 0.20)'}`,
              borderTop: `1px solid ${showSoil ? '#E9D5FF' : 'rgba(255, 255, 255, 0.15)'}`,
              color: showSoil ? '#C084FC' : '#CBD5E1',
              transition: 'all 0.15s ease',
              boxShadow: showSoil ? '0 0 10px rgba(192, 132, 252, 0.25)' : 'none',
            }}
          >
            {showSoil ? <Eye size={12} /> : <EyeOff size={12} />}
            <span>Soil Saturation (%)</span>
          </button>
        </div>
      </div>

      {/* Main Recharts Visualizer */}
      <div style={{ width: '100%', height: '340px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: -10, bottom: 0 }}>
            <defs>
              {/* Uncertainty Area Gradient */}
              <linearGradient id="uncertaintyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F97316" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#F97316" stopOpacity={0.03} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(51, 65, 85, 0.4)" vertical={false} />

            {/* X-Axis: Relative Horizon Hours */}
            <XAxis
              dataKey="label"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />

            {/* Left Y-Axis: Risk Score (0 - 100) and Soil Moisture */}
            <YAxis
              yAxisId="left"
              domain={[0, 100]}
              stroke="#F97316"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              label={{ value: 'Risk Index / Soil %', angle: -90, position: 'insideLeft', fill: '#94A3B8', fontSize: 10, dx: 15 }}
            />

            {/* Right Y-Axis: Rainfall Rate (mm/h) */}
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 'auto']}
              stroke="#38BDF8"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              label={{ value: 'Rain (mm/h)', angle: 90, position: 'insideRight', fill: '#38BDF8', fontSize: 10, dx: -5 }}
            />

            {/* Hidden Independent Y-Axis for River Stage (m MSL) to preserve accurate scaling */}
            <YAxis
              yAxisId="river"
              orientation="right"
              domain={['auto', 'auto']}
              hide={true}
            />

            <Tooltip content={<CustomTooltip />} />

            {/* Operational Threshold Reference Lines */}
            <ReferenceLine
              yAxisId="left"
              y={25}
              stroke="#EAB308"
              strokeDasharray="4 4"
              label={{ value: 'WATCH (25)', fill: '#EAB308', fontSize: 10, position: 'insideTopLeft' }}
            />
            <ReferenceLine
              yAxisId="left"
              y={50}
              stroke="#F97316"
              strokeDasharray="4 4"
              label={{ value: 'HIGH (50)', fill: '#F97316', fontSize: 10, position: 'insideTopLeft' }}
            />
            <ReferenceLine
              yAxisId="left"
              y={75}
              stroke="#EF4444"
              strokeDasharray="4 4"
              label={{ value: 'CRITICAL (75)', fill: '#EF4444', fontSize: 10, position: 'insideTopLeft' }}
            />

            {/* Strict Vertical NOW Reference Line */}
            <ReferenceLine
              yAxisId="left"
              x="NOW"
              stroke="#38BDF8"
              strokeWidth={2}
              label={{
                value: 'NOW (LIVE)',
                fill: '#38BDF8',
                fontSize: 11,
                fontWeight: 800,
                position: 'top',
              }}
            />

            {/* P10 - P90 Shaded Uncertainty Area (Forecast Horizon) */}
            {showUncertainty && (
              <Area
                yAxisId="left"
                type="linear"
                dataKey="p90"
                stroke="none"
                fill="url(#uncertaintyGradient)"
                fillOpacity={1}
                isAnimationActive={false}
              />
            )}

            {/* Past Observed Risk Line (Solid Line) */}
            {showRisk && (
              <Line
                yAxisId="left"
                type="linear"
                dataKey="observedRisk"
                stroke="#F97316"
                strokeWidth={3}
                dot={{ r: 4, fill: '#F97316', stroke: '#0b1329', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#F97316' }}
                connectNulls={false}
                name="Observed Risk"
              />
            )}

            {/* Future Forecast Risk Line (Dashed Line) */}
            {showRisk && (
              <Line
                yAxisId="left"
                type="linear"
                dataKey="forecastRisk"
                stroke="#F97316"
                strokeWidth={3}
                strokeDasharray="6 4"
                dot={{ r: 4, fill: '#0b1329', stroke: '#F97316', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#F97316' }}
                connectNulls={false}
                name="Forecast Risk"
              />
            )}

            {/* Past Observed Rainfall (Solid Line) */}
            {showRainfall && (
              <Line
                yAxisId="right"
                type="linear"
                dataKey="observedRain"
                stroke="#38BDF8"
                strokeWidth={2}
                dot={{ r: 3, fill: '#38BDF8' }}
                connectNulls={false}
                name="Observed Rain"
              />
            )}

            {/* Future Forecast Rainfall (Dashed Line) */}
            {showRainfall && (
              <Line
                yAxisId="right"
                type="linear"
                dataKey="forecastRain"
                stroke="#38BDF8"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={{ r: 3, fill: '#0b1329', stroke: '#38BDF8', strokeWidth: 1.5 }}
                connectNulls={false}
                name="Forecast Rain"
              />
            )}

            {/* Past Observed River Stage (Solid Line) */}
            {showRiver && (
              <Line
                yAxisId="river"
                type="linear"
                dataKey="observedRiver"
                stroke="#2DD4BF"
                strokeWidth={2}
                dot={{ r: 3, fill: '#2DD4BF' }}
                connectNulls={false}
                name="Observed River"
              />
            )}

            {/* Future Forecast River Stage (Dashed Line) */}
            {showRiver && (
              <Line
                yAxisId="river"
                type="linear"
                dataKey="forecastRiver"
                stroke="#2DD4BF"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={{ r: 3, fill: '#0b1329', stroke: '#2DD4BF', strokeWidth: 1.5 }}
                connectNulls={false}
                name="Forecast River"
              />
            )}

            {/* Soil Moisture (Solid / Dashed) */}
            {showSoil && (
              <Line
                yAxisId="left"
                type="linear"
                dataKey="observedSoil"
                stroke="#C084FC"
                strokeWidth={1.5}
                dot={false}
                connectNulls={false}
                name="Observed Soil"
              />
            )}
            {showSoil && (
              <Line
                yAxisId="left"
                type="linear"
                dataKey="forecastSoil"
                stroke="#C084FC"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                dot={false}
                connectNulls={false}
                name="Forecast Soil"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Operational Threshold Legend Footer */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '8px 14px',
          borderRadius: '6px',
          border: '1px solid rgba(51, 65, 85, 0.4)',
          fontSize: '11px',
          color: '#94A3B8',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#10B981' }} />
            <span>&lt; 25: LOW</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#EAB308' }} />
            <span>25–50: WATCH</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#F97316' }} />
            <span>50–75: HIGH</span>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#EF4444' }} />
            <span>&ge; 75: CRITICAL</span>
          </span>
        </div>
        <div>
          <span style={{ color: '#CBD5E1' }}>Vertical Divider:</span> <strong>Relative 0h (NOW)</strong> | Left of divider is Sensor Ground Truth; Right is ECMWF 0.1° Projected Inference
        </div>
      </div>
    </div>
  );
};
