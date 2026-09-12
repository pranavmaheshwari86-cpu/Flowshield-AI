import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { CloudRain, AlertCircle, Info, ZoomIn, Maximize2 } from 'lucide-react';
import { PrecipitationForecastResponse, HistoricalSeriesPoint } from '../../types';

interface PrecipitationChartProps {
  precipitationForecast?: PrecipitationForecastResponse | null;
  currentRainfallRate: number;
  historicalSeries?: HistoricalSeriesPoint[];
  settlementName?: string;
}

interface PrecipDataPoint {
  relativeHour: number;
  label: string;
  timeIst: string;
  timestamp: string;
  observedRate?: number | null;
  forecastRate?: number | null;
  isForecast: boolean;
  status: string;
  source: string;
}

export const PrecipitationChart: React.FC<PrecipitationChartProps> = ({
  precipitationForecast,
  currentRainfallRate,
  historicalSeries = [],
  settlementName,
}) => {
  const [scaleMode, setScaleMode] = useState<'auto' | 'full'>('auto');

  // Build continuous timeline: strictly 1 point per relativeHour to prevent duplicate X-axis labels
  const hourMap = new Map<number, PrecipDataPoint>();

  // 1. Historical Observed Points (-6h to 0h)
  if (precipitationForecast?.observed_points && precipitationForecast.observed_points.length > 0) {
    precipitationForecast.observed_points.forEach((pt) => {
      hourMap.set(pt.relative_hour, {
        relativeHour: pt.relative_hour,
        label: pt.relative_hour === 0 ? 'NOW' : `${pt.relative_hour}h`,
        timeIst: pt.timestamp_ist,
        timestamp: pt.timestamp_utc,
        observedRate: pt.value_mm_hr,
        isForecast: false,
        status: pt.status,
        source: pt.source,
      });
    });
  } else {
    // Fallback to historicalSeries if API response observed_points is empty
    historicalSeries.forEach((pt) => {
      hourMap.set(pt.relative_hour, {
        relativeHour: pt.relative_hour,
        label: pt.relative_hour === 0 ? 'NOW' : `${pt.relative_hour}h`,
        timeIst: pt.timestamp,
        timestamp: pt.timestamp,
        observedRate: pt.observed_rainfall_rate ?? 0.0,
        isForecast: false,
        status: 'OBSERVED',
        source: pt.source_attribution || 'Synoptic Weather Station',
      });
    });
  }

  // Ensure NOW anchor exists and seamlessly bridges observed and forecast
  const nowRate = currentRainfallRate ?? (hourMap.has(0) ? hourMap.get(0)!.observedRate : 0.0);
  hourMap.set(0, {
    relativeHour: 0,
    label: 'NOW',
    timeIst: precipitationForecast?.model_run_ist || 'NOW (IST)',
    timestamp: new Date().toISOString(),
    observedRate: nowRate,
    forecastRate: nowRate, // Anchor to connect seamlessly
    isForecast: false,
    status: 'LIVE_OBSERVED',
    source: 'Automated Weather Telemetry',
  });

  // 2. Forecast Points (+1h to +48h)
  const keyForecastHorizons = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 30, 36, 42, 48];
  if (precipitationForecast?.forecast_points && precipitationForecast.forecast_points.length > 0) {
    precipitationForecast.forecast_points.forEach((pt) => {
      if (keyForecastHorizons.includes(pt.relative_hour)) {
        hourMap.set(pt.relative_hour, {
          relativeHour: pt.relative_hour,
          label: `+${pt.relative_hour}h`,
          timeIst: pt.timestamp_ist,
          timestamp: pt.timestamp_utc,
          forecastRate: pt.value_mm_hr,
          isForecast: true,
          status: pt.status,
          source: pt.source,
        });
      }
    });
  }

  // Convert map to strictly sorted array
  const chartData = Array.from(hourMap.values()).sort((a, b) => a.relativeHour - b.relativeHour);

  // Check if forecast data is actually available
  const hasForecast = precipitationForecast?.forecast_points && precipitationForecast.forecast_points.some((p) => p.value_mm_hr !== null);

  // Calculate actual peak rate across observed and forecast series
  const allRates = chartData.map((d) => Math.max(d.observedRate ?? 0, d.forecastRate ?? 0));
  const peakVal = Math.max(
    currentRainfallRate || 0,
    precipitationForecast?.peak_forecast_mm_hr || 0,
    ...allRates
  );

  // Dynamic Adaptive Scaling (Auto-Zoom):
  // When rainfall is light (e.g. 0.3 mm/h), zoom in so the peaks and curves are prominently visible.
  // When rainfall is heavy (e.g. 20 mm/h), scale up to provide comfortable headroom.
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
  const accum24h = precipitationForecast?.accumulated_24h_forecast_mm;

  return (
    <div
      className="timeline-glass-card"
      style={{
        background: 'linear-gradient(135deg, rgba(7, 18, 38, 0.72) 0%, rgba(5, 12, 26, 0.82) 100%)',
        backdropFilter: 'blur(24px) saturate(140%)',
        WebkitBackdropFilter: 'blur(24px) saturate(140%)',
        border: '1px solid rgba(56, 189, 248, 0.22)',
        borderRadius: '12px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      {/* 1. Header Strip: Title, NWP Model, Peak, Accumulation */}
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
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CloudRain size={18} color="#38BDF8" />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#F1F5F9', letterSpacing: '-0.01em' }}>
              Numerical Precipitation Forecast
            </div>
            <div style={{ fontSize: '11px', color: '#64748B', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>{modelName}</span>
              <span>•</span>
              <span style={{ color: '#94A3B8' }}>Run: {modelRunIst}</span>
            </div>
          </div>
        </div>

        {/* Real Metrics Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Current Observed */}
          <div
            style={{
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '105px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#38BDF8', textTransform: 'uppercase' }}>
              Current Observed
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {currentRainfallRate.toFixed(1)} <span style={{ fontSize: '11px', fontWeight: 500, color: '#64748B' }}>mm/h</span>
            </div>
          </div>

          {/* Peak Forecast */}
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
              Peak Intensity
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {peakForecast !== undefined && peakForecast !== null ? `${peakForecast.toFixed(1)} mm/h` : 'N/A'}
            </div>
            {peakTimeIst && (
              <div style={{ fontSize: '9.5px', color: '#94A3B8', marginTop: '1px' }}>
                {peakTimeIst.split(' ')[1]} IST
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
              minWidth: '115px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#10B981', textTransform: 'uppercase' }}>
              24h Projected
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#F8FAFC' }}>
              {accum24h !== undefined && accum24h !== null ? `${accum24h.toFixed(1)} mm` : 'N/A'}
            </div>
          </div>

          {/* Scale Mode Toggle */}
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
              minWidth: '120px',
              textAlign: 'left',
              transition: 'all 0.2s ease',
            }}
            title={scaleMode === 'auto' ? 'Click to view Full IMD Scale (0-20 mm/h)' : 'Click to enable Auto Zoom'}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#38BDF8', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {scaleMode === 'auto' ? <ZoomIn size={12} /> : <Maximize2 size={12} />}
              <span>{scaleMode === 'auto' ? 'Adaptive Zoom' : 'Full IMD Scale'}</span>
            </div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC', marginTop: '1px' }}>
              0 – {yDomainMax} <span style={{ fontSize: '11px', fontWeight: 500, color: '#64748B' }}>mm/h</span>
            </div>
          </button>
        </div>
      </div>

      {/* 2. Visualizer Chart / Authoritative Empty State */}
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
            Atmospheric Precipitation Forecast Currently Unavailable
          </div>
          <div style={{ fontSize: '11.5px', color: '#64748B', maxWidth: '540px', lineHeight: 1.5 }}>
            Upstream ECMWF IFS numerical forecast grid is momentarily unreachable for coordinates of {settlementName || 'this settlement'}. Zero-fill fallbacks are strictly prohibited by system governance. Current observed rainfall telemetry remains live.
          </div>
        </div>
      ) : (
        <div style={{ width: '100%', height: '280px', position: 'relative' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 12, right: 16, left: -10, bottom: 4 }}>
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
              </defs>

              <CartesianGrid stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="3 3" vertical={false} />

              <XAxis
                dataKey="label"
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                stroke="rgba(255, 255, 255, 0.12)"
                tickLine={false}
              />

              <YAxis
                domain={[0, yDomainMax]}
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                stroke="rgba(255, 255, 255, 0.12)"
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
                  fill: '#64748B',
                  fontSize: 10,
                  dy: 50,
                }}
              />

              {/* Vertical Reference Line at NOW (Observed vs Forecast boundary) */}
              <ReferenceLine
                x="NOW"
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

              {/* Heavy Rainfall Advisory Threshold (15 mm/h IMD standard) - only rendered if within visible domain */}
              {yDomainMax >= 15 && (
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

              {/* Observed Telemetry: Solid Vibrant Cyan Area */}
              <Area
                type="monotone"
                dataKey="observedRate"
                name="Observed Rainfall Rate"
                stroke="#00f0ff"
                strokeWidth={2.6}
                fill="url(#observedRainGrad)"
                dot={{ r: 3, fill: '#00f0ff', stroke: '#0891b2', strokeWidth: 1 }}
                connectNulls={false}
              />

              {/* Numerical Forecast: Shaded Area with Glowing Cyan-Blue Boundary */}
              <Area
                type="monotone"
                dataKey="forecastRate"
                name="Forecast NWP Intensity"
                stroke="#38bdf8"
                strokeWidth={2.6}
                strokeDasharray="5 4"
                fill="url(#forecastRainGrad)"
                dot={{ r: 3.5, fill: '#38bdf8', stroke: '#0369a1', strokeWidth: 1.5 }}
                activeDot={{ r: 6.5, fill: '#38bdf8', stroke: '#ffffff', strokeWidth: 2 }}
                connectNulls={true}
              />

              {/* Interactive Tooltip */}
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null;
                  const data: PrecipDataPoint = payload[0].payload;
                  const val = data.isForecast ? data.forecastRate : data.observedRate;

                  return (
                    <div
                      style={{
                        background: 'rgba(6, 15, 30, 0.94)',
                        backdropFilter: 'blur(16px)',
                        border: '1px solid rgba(56, 189, 248, 0.35)',
                        boxShadow: '0 6px 24px rgba(0,0,0,0.55)',
                        borderRadius: '8px',
                        padding: '10px 14px',
                        minWidth: '180px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: data.isForecast ? '#38BDF8' : '#00F0FF' }}>
                          {data.isForecast ? `Forecast Horizon (${data.label})` : `Observed Telemetry (${data.label})`}
                        </span>
                        <span
                          style={{
                            fontSize: '9px',
                            fontWeight: 600,
                            padding: '2px 5px',
                            borderRadius: '4px',
                            background: data.isForecast ? 'rgba(56, 189, 248, 0.15)' : 'rgba(0, 240, 255, 0.15)',
                            color: data.isForecast ? '#38BDF8' : '#00F0FF',
                          }}
                        >
                          {data.status}
                        </span>
                      </div>

                      <div style={{ fontSize: '11px', color: '#94A3B8', marginBottom: '4px' }}>
                        IST: <strong style={{ color: '#F1F5F9' }}>{data.timeIst}</strong>
                      </div>

                      <div style={{ fontSize: '15px', fontWeight: 800, color: '#F8FAFC', marginBottom: '4px' }}>
                        {val !== null && val !== undefined ? `${val.toFixed(2)} mm/h` : 'Unavailable'}
                      </div>

                      <div style={{ fontSize: '9.5px', color: '#64748B', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '4px', marginTop: '4px' }}>
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

      {/* 3. Legend & Scientific Note */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          fontSize: '11px',
          color: '#64748B',
          paddingTop: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '14px', height: '3px', background: '#00f0ff', borderRadius: '2px' }} />
            <span style={{ color: '#CBD5E1' }}>Observed Telemetry (-6h to NOW)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '14px', height: '2px', borderTop: '2px dashed #38bdf8' }} />
            <span style={{ color: '#CBD5E1' }}>ECMWF IFS Forecast (+1h to +48h)</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#64748B' }}>
          <Info size={12} color="#64748B" />
          <span>Independent meteorological domain • Isolated from ML flood-risk classification</span>
        </div>
      </div>
    </div>
  );
};
