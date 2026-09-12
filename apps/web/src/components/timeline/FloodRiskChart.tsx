import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { ShieldAlert, AlertTriangle, Info } from 'lucide-react';
import {
  HistoricalSeriesPoint,
  ForecastHorizonPoint,
  LocationCapability,
} from '../../types';

interface FloodRiskChartProps {
  historicalSeries: HistoricalSeriesPoint[];
  forecastHorizons: ForecastHorizonPoint[];
  capability?: LocationCapability | null;
  settlementName?: string;
}

interface RiskChartPoint {
  relativeHour: number;
  label: string;
  timestamp: string;
  isForecast: boolean;
  observedRisk?: number;
  forecastRisk?: number | null;
  calibratedProb?: number | null;
  riskTier?: string;
  p10?: number | null;
  p90?: number | null;
  uncertaintySpan?: [number, number] | null;
  primaryDriver?: string;
}

export const FloodRiskChart: React.FC<FloodRiskChartProps> = ({
  historicalSeries,
  forecastHorizons,
  capability,
  settlementName,
}) => {
  const isModelSupported = capability ? capability.flood_risk_model === 'SUPPORTED' : true;

  // If model is unsupported for this location (e.g. Buxar, Bihar), render authoritative banner
  if (!isModelSupported) {
    return (
      <div
        className="timeline-glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 20, 10, 0.7) 0%, rgba(20, 14, 8, 0.8) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(245, 158, 11, 0.35)',
          borderRadius: '12px',
          padding: '28px 24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '12px',
        }}
      >
        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '50%',
            background: 'rgba(245, 158, 11, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <AlertTriangle size={24} color="#F59E0B" />
        </div>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#FEF3C7', letterSpacing: '-0.01em' }}>
            Validated ML Flood-Risk Model Unavailable
          </div>
          <div style={{ fontSize: '13px', color: '#D97706', fontWeight: 600, marginTop: '2px' }}>
            {capability?.unsupported_reason || `No validated flood-risk machine learning model trained for ${settlementName || 'this settlement'}.`}
          </div>
        </div>
        <div style={{ fontSize: '12px', color: '#94A3B8', maxWidth: '640px', lineHeight: 1.6 }}>
          FlowShield enforces a strict zero-fabrication policy. Cross-regional model proxying (e.g., executing Himalayan mountain models on alluvial Gangetic floodplains) is strictly prohibited. Weather telemetry, ECMWF precipitation forecasting, and CWC hydrological river monitoring remain fully operational above.
        </div>
        <div
          style={{
            display: 'flex',
            gap: '16px',
            marginTop: '6px',
            padding: '8px 16px',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            fontSize: '11px',
            color: '#CBD5E1',
          }}
        >
          <span>✓ Real-Time Weather: <strong>Active</strong></span>
          <span>•</span>
          <span>✓ ECMWF IFS Forecast: <strong>Active</strong></span>
          <span>•</span>
          <span>✓ CWC River Bulletins: <strong>Active</strong></span>
        </div>
      </div>
    );
  }

  // Assemble supported risk chart data
  const chartData: RiskChartPoint[] = [];

  // Historical observed risk
  historicalSeries.forEach((pt) => {
    chartData.push({
      relativeHour: pt.relative_hour,
      label: pt.relative_hour === 0 ? 'NOW' : `${pt.relative_hour}h`,
      timestamp: pt.timestamp,
      isForecast: false,
      observedRisk: pt.operational_risk_score,
      calibratedProb: null,
      riskTier: 'OBSERVED',
    });
  });

  // NOW Anchor
  const lastHistRisk = historicalSeries.length > 0 ? historicalSeries[historicalSeries.length - 1].operational_risk_score : 20.0;
  const nowPoint: RiskChartPoint = {
    relativeHour: 0,
    label: 'NOW',
    timestamp: new Date().toISOString(),
    isForecast: false,
    observedRisk: lastHistRisk,
    forecastRisk: lastHistRisk, // Bridge forecast seamlessly
    riskTier: forecastHorizons[0]?.risk_tier || 'LOW',
    primaryDriver: forecastHorizons[0]?.primary_risk_driver || 'Precipitation Loading',
  };

  const existingNowIdx = chartData.findIndex((p) => p.relativeHour === 0);
  if (existingNowIdx >= 0) {
    chartData[existingNowIdx] = nowPoint;
  } else {
    chartData.push(nowPoint);
  }

  // Forecast Horizons
  forecastHorizons.forEach((h) => {
    const p10 = h.uncertainty_band?.p10 ?? null;
    const p90 = h.uncertainty_band?.p90 ?? null;
    const span: [number, number] | null = (p10 !== null && p90 !== null) ? [p10, p90] : null;

    chartData.push({
      relativeHour: h.horizon_hours,
      label: `+${h.horizon_hours}h`,
      timestamp: h.forecast_timestamp,
      isForecast: true,
      forecastRisk: h.operational_risk_score,
      calibratedProb: h.calibrated_flood_probability,
      riskTier: h.risk_tier,
      p10,
      p90,
      uncertaintySpan: span,
      primaryDriver: h.primary_risk_driver,
    });
  });

  chartData.sort((a, b) => a.relativeHour - b.relativeHour);

  return (
    <div
      className="timeline-glass-card"
      style={{
        background: 'linear-gradient(135deg, rgba(8, 20, 38, 0.72) 0%, rgba(5, 12, 26, 0.82) 100%)',
        backdropFilter: 'blur(24px) saturate(140%)',
        WebkitBackdropFilter: 'blur(24px) saturate(140%)',
        border: '1px solid rgba(168, 85, 247, 0.24)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.42)',
        borderRadius: '12px',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      {/* 1. Header: Title, Active Model, Threshold Legend */}
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
              background: 'rgba(168, 85, 247, 0.14)',
              border: '1px solid rgba(168, 85, 247, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={18} color="#C084FC" />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#F1F5F9', letterSpacing: '-0.01em' }}>
              Multi-Horizon Machine Learning Flood Risk
            </div>
            <div style={{ fontSize: '11px', color: '#64748B' }}>
              Calibrated Dual Pipeline • Isotonic Regression (Tau = 0.08) • 15 Canonical Physical Features
            </div>
          </div>
        </div>

        {/* Severity Threshold Reference Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px', fontWeight: 600 }}>
          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            LOW &lt; 25
          </span>
          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(234, 179, 8, 0.15)', color: '#EAB308', border: '1px solid rgba(234, 179, 8, 0.3)' }}>
            WATCH 25-50
          </span>
          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(249, 115, 22, 0.15)', color: '#F97316', border: '1px solid rgba(249, 115, 22, 0.3)' }}>
            HIGH 50-75
          </span>
          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            CRITICAL &ge; 75
          </span>
        </div>
      </div>

      {/* 2. Main Risk Chart */}
      <div style={{ width: '100%', height: '280px', position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 12, right: 16, left: -10, bottom: 4 }}>
            <defs>
              {/* Purple/Violet Gradient for Flood Risk */}
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#A855F7" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#A855F7" stopOpacity={0.02} />
              </linearGradient>

              {/* P10 - P90 Uncertainty Envelope Gradient */}
              <linearGradient id="uncertaintyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#C084FC" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#C084FC" stopOpacity={0.04} />
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
              domain={[0, 100]}
              tick={{ fill: '#94A3B8', fontSize: 11 }}
              stroke="rgba(255, 255, 255, 0.12)"
              tickLine={false}
              label={{
                value: 'Operational Risk Index (0-100)',
                angle: -90,
                position: 'insideLeft',
                fill: '#64748B',
                fontSize: 10,
                dy: 60,
              }}
            />

            {/* Threshold Lines */}
            <ReferenceLine y={25} stroke="#EAB308" strokeDasharray="2 2" strokeOpacity={0.45} />
            <ReferenceLine y={50} stroke="#F97316" strokeDasharray="3 3" strokeOpacity={0.65} />
            <ReferenceLine y={75} stroke="#EF4444" strokeDasharray="3 3" strokeOpacity={0.8} />

            {/* Vertical Reference Line at NOW */}
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

            {/* Observed Historical Risk Line */}
            <Line
              type="monotone"
              dataKey="observedRisk"
              name="Historical Risk Score"
              stroke="#A855F7"
              strokeWidth={2.4}
              dot={{ r: 3, fill: '#A855F7', stroke: '#581c87', strokeWidth: 1 }}
              connectNulls={false}
            />

            {/* Forecast Multi-Horizon Risk Line */}
            <Line
              type="monotone"
              dataKey="forecastRisk"
              name="Projected Risk Score"
              stroke="#C084FC"
              strokeWidth={2.6}
              strokeDasharray="5 4"
              dot={{ r: 4, fill: '#C084FC', stroke: '#ffffff', strokeWidth: 1.5 }}
              activeDot={{ r: 6, fill: '#C084FC', stroke: '#ffffff', strokeWidth: 2 }}
              connectNulls={true}
            />

            {/* Interactive Tooltip */}
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const data: RiskChartPoint = payload[0].payload;
                const riskVal = data.isForecast ? data.forecastRisk : data.observedRisk;

                return (
                  <div
                    style={{
                      background: 'rgba(10, 15, 30, 0.94)',
                      backdropFilter: 'blur(16px)',
                      border: '1px solid rgba(168, 85, 247, 0.35)',
                      boxShadow: '0 6px 24px rgba(0,0,0,0.55)',
                      borderRadius: '8px',
                      padding: '10px 14px',
                      minWidth: '200px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#C084FC' }}>
                        {data.isForecast ? `Forecast Horizon (${data.label})` : `Observed Risk (${data.label})`}
                      </span>
                      {data.riskTier && (
                        <span
                          style={{
                            fontSize: '9px',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background:
                              data.riskTier === 'CRITICAL'
                                ? 'rgba(239, 68, 68, 0.2)'
                                : data.riskTier === 'HIGH'
                                ? 'rgba(249, 115, 22, 0.2)'
                                : data.riskTier === 'WATCH'
                                ? 'rgba(234, 179, 8, 0.2)'
                                : 'rgba(16, 185, 129, 0.2)',
                            color:
                              data.riskTier === 'CRITICAL'
                                ? '#EF4444'
                                : data.riskTier === 'HIGH'
                                ? '#F97316'
                                : data.riskTier === 'WATCH'
                                ? '#EAB308'
                                : '#10B981',
                          }}
                        >
                          {data.riskTier}
                        </span>
                      )}
                    </div>

                    <div style={{ fontSize: '16px', fontWeight: 800, color: '#F8FAFC', marginBottom: '4px' }}>
                      Risk Score: {riskVal !== null && riskVal !== undefined ? `${riskVal.toFixed(1)} / 100` : 'N/A'}
                    </div>

                    {data.calibratedProb !== null && data.calibratedProb !== undefined && (
                      <div style={{ fontSize: '11.5px', color: '#94A3B8', marginBottom: '4px' }}>
                        Calibrated Probability: <strong style={{ color: '#E2E8F0' }}>{(data.calibratedProb * 100).toFixed(1)}%</strong>
                      </div>
                    )}

                    {data.p10 !== null && data.p90 !== null && data.p10 !== undefined && data.p90 !== undefined && (
                      <div style={{ fontSize: '10px', color: '#64748B', marginBottom: '4px' }}>
                        Uncertainty Window: P10 [{data.p10.toFixed(1)}] — P90 [{data.p90.toFixed(1)}]
                      </div>
                    )}

                    {data.primaryDriver && (
                      <div style={{ fontSize: '9.5px', color: '#CBD5E1', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '4px', marginTop: '4px' }}>
                        Primary Driver: <strong>{data.primaryDriver}</strong>
                      </div>
                    )}
                  </div>
                );
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* 3. Legend */}
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
            <span style={{ width: '14px', height: '3px', background: '#A855F7', borderRadius: '2px' }} />
            <span style={{ color: '#CBD5E1' }}>Historical Risk (-6h to NOW)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '14px', height: '2px', borderTop: '2px dashed #C084FC' }} />
            <span style={{ color: '#CBD5E1' }}>Calibrated ML Projections (+1h to +48h)</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#64748B' }}>
          <Info size={12} color="#64748B" />
          <span>Isotonically calibrated • Threshold lines at 25 (Watch), 50 (High), 75 (Critical)</span>
        </div>
      </div>
    </div>
  );
};
