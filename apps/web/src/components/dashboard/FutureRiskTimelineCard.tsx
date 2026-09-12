import React, { useEffect, useState } from 'react';
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Clock, TrendingUp, AlertTriangle, Droplets } from 'lucide-react';
import { api } from '../../services/api';
import { FutureRiskTimelineResponse, FutureRiskHorizon } from '../../types';

interface FutureRiskTimelineCardProps {
  villageId: string;
  villageName?: string;
}

export const FutureRiskTimelineCard: React.FC<FutureRiskTimelineCardProps> = ({
  villageId,
  villageName,
}) => {
  const [timelineData, setTimelineData] = useState<FutureRiskTimelineResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState<FutureRiskHorizon | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getFutureRiskTimeline(villageId)
      .then((res) => {
        if (mounted) {
          setTimelineData(res);
          if (res.timeline && res.timeline.length > 0) {
            setSelectedHorizon(res.timeline[0]);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          console.error('Error fetching future risk timeline:', err);
          setError('Failed to load forecast risk timeline');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [villageId]);

  if (loading) {
    return (
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px',
          color: '#94A3B8',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <Clock className="animate-spin" size={20} color="#38BDF8" />
        <span>Computing multi-horizon ML risk forecast (+1h to +48h)...</span>
      </div>
    );
  }

  if (error || !timelineData) {
    return null;
  }

  const chartData = timelineData.timeline.map((item) => ({
    horizon: `+${item.horizon_hours}h`,
    hours: item.horizon_hours,
    risk_score: item.risk_score,
    probability: Math.round(item.flood_probability * 100),
    rainfall_rate: item.rainfall_intensity_mm_hr,
    soil_sat: Math.round(item.soil_saturation_pct),
    uncertainty_min: Math.round(item.uncertainty_band.p10 * 100),
    uncertainty_max: Math.round(item.uncertainty_band.p90 * 100),
    risk_level: item.risk_level,
    raw: item,
  }));

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return '#EF4444';
      case 'HIGH':
        return '#F97316';
      case 'WATCH':
        return '#EAB308';
      default:
        return '#10B981';
    }
  };

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.65) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '16px',
        padding: '20px 24px',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <TrendingUp size={20} color="#38BDF8" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC' }}>
                Predictive Risk Timeline: {villageName || timelineData.village_name}
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                }}
              >
                ML V2 CALIBRATED
              </span>
            </div>
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>
              Numerical Weather Forecasts passed through Isotonic Logistic Regression (τ=0.08)
            </span>
          </div>
        </div>

        {/* Peak Risk Badge */}
        {timelineData.peak_risk_score !== undefined && (
          <div
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              background: timelineData.peak_risk_score >= 70 ? 'rgba(239, 68, 68, 0.18)' : 'rgba(249, 115, 22, 0.18)',
              border: `1px solid ${timelineData.peak_risk_score >= 70 ? 'rgba(239, 68, 68, 0.5)' : 'rgba(249, 115, 22, 0.5)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertTriangle size={16} color={timelineData.peak_risk_score >= 70 ? '#EF4444' : '#F97316'} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#F1F5F9' }}>
              Anticipated Peak at +{timelineData.peak_risk_horizon_hours}h (Score:{' '}
              <strong style={{ color: timelineData.peak_risk_score >= 70 ? '#EF4444' : '#F97316' }}>
                {timelineData.peak_risk_score}
              </strong>
              /100)
            </span>
          </div>
        )}
      </div>

      {/* Chart Section */}
      <div style={{ height: '220px', width: '100%', marginTop: '6px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            onClick={(state) => {
              if (state && state.activePayload && state.activePayload.length > 0) {
                const raw = state.activePayload[0].payload.raw;
                setSelectedHorizon(raw);
              }
            }}
          >
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.45} />
                <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey="horizon" stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis yAxisId="left" domain={[0, 100]} stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis yAxisId="right" orientation="right" domain={[0, 40]} stroke="#64748B" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#F8FAFC',
                boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
              }}
              formatter={(value: any, name: string) => {
                if (name === 'probability') return [`${value}%`, 'Flood Probability'];
                if (name === 'risk_score') return [`${value}/100`, 'Risk Score'];
                if (name === 'rainfall_rate') return [`${value} mm/h`, 'Rainfall Rate'];
                if (name === 'soil_sat') return [`${value}%`, 'Soil Saturation'];
                return [value, name];
              }}
            />
            {/* Rainfall Intensity Bars */}
            <Bar yAxisId="right" dataKey="rainfall_rate" fill="rgba(96, 165, 250, 0.4)" radius={[4, 4, 0, 0]} maxBarSize={28} />
            {/* Risk Probability Area */}
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="risk_score"
              stroke="#38BDF8"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#riskGradient)"
            />
            {/* Soil Moisture Line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="soil_sat"
              stroke="#A78BFA"
              strokeWidth={1.8}
              strokeDasharray="4 4"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Horizon Selector & Granular Inspection */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '10px',
          marginTop: '4px',
        }}
      >
        {timelineData.timeline.map((h) => {
          const isSelected = selectedHorizon?.horizon_hours === h.horizon_hours;
          const color = getRiskColor(h.risk_level);
          return (
            <button
              key={h.horizon_hours}
              onClick={() => setSelectedHorizon(h)}
              style={{
                background: isSelected ? 'rgba(56, 189, 248, 0.18)' : 'rgba(30, 41, 59, 0.45)',
                border: `1px solid ${isSelected ? 'rgba(56, 189, 248, 0.7)' : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: '10px',
                padding: '10px',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: '#F1F5F9' }}>
                  +{h.horizon_hours}h Horizon
                </span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: `${color}25`,
                    color: color,
                    border: `1px solid ${color}60`,
                  }}
                >
                  {h.risk_level}
                </span>
              </div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: color, marginTop: '4px' }}>
                {h.risk_score} <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 400 }}>/100</span>
              </div>
              <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px', display: 'flex', gap: '8px' }}>
                <span>🌧️ {h.rainfall_intensity_mm_hr} mm/h</span>
                <span>💧 {Math.round(h.soil_saturation_pct)}%</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Horizon Deep Details */}
      {selectedHorizon && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.45)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '10px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Droplets size={18} color="#38BDF8" />
            <span style={{ fontSize: '12px', color: '#CBD5E1' }}>
              <strong>+{selectedHorizon.horizon_hours}h Outlook:</strong> Cumulative Precip:{' '}
              <span style={{ color: '#38BDF8' }}>{selectedHorizon.cumulative_rainfall_mm} mm</span> | Soil Saturation:{' '}
              <span style={{ color: '#A78BFA' }}>{selectedHorizon.soil_saturation_pct}%</span> | Calibrated Prob:{' '}
              <span style={{ color: getRiskColor(selectedHorizon.risk_level) }}>
                {Math.round(selectedHorizon.flood_probability * 100)}%
              </span>
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: '#64748B' }}>Uncertainty Bounds:</span>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>
              [{Math.round(selectedHorizon.uncertainty_band.p10 * 100)}% –{' '}
              {Math.round(selectedHorizon.uncertainty_band.p90 * 100)}%]
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
