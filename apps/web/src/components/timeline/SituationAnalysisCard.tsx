import React from 'react';
import {
  ThresholdCrossingAnalysis,
  RiskDriverContribution,
} from '../../types';
import {
  TrendingUp,
  TrendingDown,
  Zap,
} from 'lucide-react';

interface SituationAnalysisCardProps {
  situationSummary: Record<string, string>;
  thresholdAnalysis: ThresholdCrossingAnalysis;
  peaks: {
    rainfall_peak_hours?: number | null;
    river_crest_peak_hours?: number | null;
    risk_peak_hours?: number | null;
    [key: string]: number | null | undefined;
  };
  riskDrivers: RiskDriverContribution[];
  trendRatePointsPerHr: number;
}

export const SituationAnalysisCard: React.FC<SituationAnalysisCardProps> = ({
  situationSummary,
  thresholdAnalysis,
  peaks,
  riskDrivers,
  trendRatePointsPerHr,
}) => {
  // Sum of driver contributions
  const totalDriverPoints = riskDrivers.reduce((acc, d) => acc + d.contribution_points, 0);

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
        gap: '14px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 0 20px rgba(34, 211, 238, 0.04)',
      }}
    >
      {/* Header: Commander Situation Brief */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Mission Commander Decision Support
          </div>
          <div style={{ fontSize: '16px', color: '#F1F5F9', fontWeight: 700, marginTop: '2px' }}>
            Tactical Situation Brief & Explainable Risk Attribution
          </div>
        </div>

        {/* Trend Rate Vector Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: trendRatePointsPerHr > 1.5 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
            border: `1px solid ${trendRatePointsPerHr > 1.5 ? 'rgba(239, 68, 68, 0.45)' : 'rgba(16, 185, 129, 0.45)'}`,
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 700,
            color: trendRatePointsPerHr > 1.5 ? '#EF4444' : '#10B981',
            boxShadow: `0 0 8px ${trendRatePointsPerHr > 1.5 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
          }}
        >
          {trendRatePointsPerHr > 1.5 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>
            {trendRatePointsPerHr > 0 ? '+' : ''}
            {trendRatePointsPerHr.toFixed(1)} pts/hr ({trendRatePointsPerHr > 1.5 ? 'Rapid Ascent' : trendRatePointsPerHr < -1.5 ? 'Decaying' : 'Stable'})
          </span>
        </div>
      </div>

      {/* Summary Narrative Box */}
      <div
        className="timeline-glass-subcard"
        style={{
          background: 'rgba(8, 24, 46, 0.48)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderLeft: '4px solid #38BDF8',
          borderTop: '1px solid rgba(255, 255, 255, 0.16)',
          borderRight: '1px solid rgba(56, 189, 248, 0.18)',
          borderBottom: '1px solid rgba(56, 189, 248, 0.18)',
          borderRadius: '6px',
          padding: '12px 14px',
          fontSize: '13px',
          color: '#F1F5F9',
          lineHeight: '1.5',
          boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.2)',
        }}
      >
        <p style={{ margin: 0, fontWeight: 500 }}>
          {situationSummary.headline || 'Operational risk monitoring active across basin.'}
        </p>
        <div style={{ marginTop: '8px', display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '11px', color: '#CBD5E1' }}>
          <span><strong>Trend:</strong> {situationSummary.trend}</span>
          <span><strong>Peak Forecast:</strong> {situationSummary.peak_forecast}</span>
          <span><strong>Hydraulic State:</strong> {situationSummary.river_status}</span>
        </div>
      </div>

      {/* Analytical Triad: Peaks, Lead-Time & Threshold Crossing */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {/* Sub-Card 1: Disaggregated Multi-Stream Peaks */}
        <div
          className="timeline-glass-subcard"
          style={{
            background: 'rgba(8, 24, 46, 0.42)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.18)',
            borderTop: '1px solid rgba(255, 255, 255, 0.16)',
            borderRadius: '8px',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.25)',
          }}
        >
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Disaggregated Peak Timing
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#38BDF8', fontWeight: 600 }}>Rainfall Intensity Peak:</span>
              <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {peaks.rainfall_peak_hours !== null && peaks.rainfall_peak_hours !== undefined
                  ? `+${peaks.rainfall_peak_hours}h window`
                  : 'No distinct peak (< 2mm/h)'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#2DD4BF', fontWeight: 600 }}>River Crest Peak:</span>
              <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {peaks.river_crest_peak_hours !== null && peaks.river_crest_peak_hours !== undefined
                  ? `+${peaks.river_crest_peak_hours}h crest`
                  : 'No crest surge expected'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#F97316', fontWeight: 600 }}>Composite Risk Peak:</span>
              <span style={{ fontWeight: 700, color: '#F1F5F9', fontFamily: 'monospace' }}>
                {peaks.risk_peak_hours !== null && peaks.risk_peak_hours !== undefined
                  ? `+${peaks.risk_peak_hours}h maximum`
                  : 'Flat risk curve (range < 5pts)'}
              </span>
            </div>
          </div>
        </div>

        {/* Sub-Card 2: Continuous Lead-Time Solver */}
        <div
          className="timeline-glass-subcard"
          style={{
            background: 'rgba(8, 24, 46, 0.42)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: `1px solid ${thresholdAnalysis.is_crossed ? 'rgba(239, 68, 68, 0.45)' : 'rgba(56, 189, 248, 0.18)'}`,
            borderTop: '1px solid rgba(255, 255, 255, 0.16)',
            borderRadius: '8px',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 4px 12px rgba(0, 0, 0, 0.25)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Lead-Time to Threshold Breach
            </span>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 800,
                padding: '2px 6px',
                borderRadius: '4px',
                background: thresholdAnalysis.is_crossed ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)',
                color: thresholdAnalysis.is_crossed ? '#EF4444' : '#10B981',
                border: `1px solid ${thresholdAnalysis.is_crossed ? 'rgba(239, 68, 68, 0.5)' : 'rgba(16, 185, 129, 0.5)'}`,
                boxShadow: `0 0 6px ${thresholdAnalysis.is_crossed ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
              }}
            >
              {thresholdAnalysis.threshold_name} (≥ {thresholdAnalysis.threshold_value})
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '20px', fontWeight: 800, color: thresholdAnalysis.is_crossed ? '#F97316' : '#10B981', fontFamily: 'monospace' }}>
              {thresholdAnalysis.lead_time_hours !== null && thresholdAnalysis.lead_time_hours !== undefined
                ? `${thresholdAnalysis.lead_time_hours.toFixed(1)}h Lead Time`
                : 'No Breach Predicted'}
            </span>
            {thresholdAnalysis.earliest_crossing_hour !== null && thresholdAnalysis.earliest_crossing_hour !== undefined && (
              <span style={{ fontSize: '11px', color: '#FDBA74' }}>
                (Earliest P90: ~{thresholdAnalysis.earliest_crossing_hour.toFixed(1)}h)
              </span>
            )}
          </div>

          <div style={{ fontSize: '11px', color: '#CBD5E1', lineHeight: '1.4' }}>
            {thresholdAnalysis.human_status_message}
          </div>
        </div>
      </div>

      {/* Additive Explainable Risk Drivers (Point Attribution) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#F1F5F9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Zap size={14} color="#38BDF8" />
            <span>Additive Risk Attribution Points (Decomposition of Total Index: {totalDriverPoints.toFixed(1)} pts)</span>
          </div>
          <div style={{ fontSize: '10px', color: '#94A3B8' }}>
            Formula: Risk = $0.40(100 \cdot P_&#123;\text&#123;cal&#125;&#125;) + 0.25 S_&#123;\text&#123;rain&#125;&#125; + 0.25 S_&#123;\text&#123;river&#125;&#125; + 0.10 S_&#123;\text&#123;slope&#125;&#125;$
          </div>
        </div>

        {/* Driver Contribution Rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {riskDrivers.map((driver, idx) => {
            const pctOfTotal = totalDriverPoints > 0 ? (driver.contribution_points / totalDriverPoints) * 100 : 0;
            const barColors = ['#38BDF8', '#0EA5E9', '#2DD4BF', '#C084FC'];
            const barColor = barColors[idx % barColors.length];

            return (
              <div
                key={driver.driver_name}
                className="timeline-glass-subcard"
                style={{
                  background: 'rgba(8, 24, 46, 0.40)',
                  backdropFilter: 'blur(8px)',
                  WebkitBackdropFilter: 'blur(8px)',
                  border: '1px solid rgba(56, 189, 248, 0.15)',
                  borderTop: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 600, color: '#F1F5F9' }}>{driver.driver_name}</span>
                    <span style={{ fontSize: '11px', color: '#CBD5E1', fontFamily: 'monospace' }}>
                      ({driver.metric_value_observed})
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 800, color: barColor, fontFamily: 'monospace' }}>
                      +{driver.contribution_points.toFixed(1)} pts
                    </span>
                    <span style={{ fontSize: '10px', color: '#64748B', width: '38px', textAlign: 'right' }}>
                      {pctOfTotal.toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div style={{ width: '100%', height: '4px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(100, Math.max(0, pctOfTotal))}%`,
                      background: barColor,
                    }}
                  />
                </div>

                <div style={{ fontSize: '10px', color: '#94A3B8' }}>
                  {driver.physical_impact_description}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
