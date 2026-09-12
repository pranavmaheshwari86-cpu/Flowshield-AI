import React from 'react';
import { Users, Building, Waves, School } from 'lucide-react';

interface ExecutiveKpiGridProps {
  affectedPopFormatted?: string;
  affectedPopDelta?: string;
  biharPop?: string;
  othersPop?: string;
  districtsCount?: number;
  criticalDists?: number;
  warningDists?: number;
  watchDists?: number;
  highRiskPct?: number;
  riversAboveDanger?: string;
  keyRiversList?: string;
  schoolsCount?: string;
  schoolsFloodedPct?: number;
}

export const ExecutiveKpiGrid: React.FC<ExecutiveKpiGridProps> = ({
  affectedPopFormatted = '47.74 Lakh',
  affectedPopDelta = '↑ 12.4% (6h)',
  biharPop = '43.64 L',
  othersPop = '4.10 L',
  districtsCount = 42,
  criticalDists = 13,
  warningDists = 21,
  watchDists = 8,
  highRiskPct = 67,
  riversAboveDanger = '7 / 9',
  keyRiversList = 'Ganga • Kosi • Gandak • Punpun • ...',
  schoolsCount = '4,120+',
  schoolsFloodedPct = 68,
}) => {
  // Donut circumference for 67%
  const donutRadius = 22;
  const donutCircumference = 2 * Math.PI * donutRadius;
  const donutOffset = donutCircumference - (highRiskPct / 100) * donutCircumference;

  return (
    <section className="executive-kpi-grid" aria-label="Executive KPI Metrics">
      {/* 1. Affected Population Card */}
      <div className="cc-card" style={{ padding: '12px 14px', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '6px',
                background: 'rgba(20, 184, 166, 0.18)',
                border: '1px solid rgba(20, 184, 166, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Users size={15} color="#22D3EE" />
            </div>
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#7F95A5', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              AFFECTED POPULATION
            </span>
          </div>
        </div>

        {/* Value + Sparkline */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              {affectedPopFormatted}
            </div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: '#10B981', marginTop: '3px' }}>
              {affectedPopDelta}
            </div>
          </div>

          {/* Smooth Cyan Sparkline */}
          <div style={{ width: '85px', height: '38px', position: 'relative' }}>
            <svg width="85" height="38" viewBox="0 0 85 38" fill="none">
              <path
                d="M 2 30 Q 18 24 30 22 T 55 12 T 80 4"
                stroke="#22D3EE"
                strokeWidth="2.2"
                strokeLinecap="round"
                style={{ filter: 'drop-shadow(0 0 6px rgba(34, 211, 238, 0.6))' }}
              />
              <circle cx="80" cy="4" r="3" fill="#22D3EE" style={{ filter: 'drop-shadow(0 0 4px #22D3EE)' }} />
            </svg>
          </div>
        </div>

        {/* Sub-breakdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11px', color: '#7F95A5', borderTop: '1px solid rgba(61, 139, 180, 0.15)', paddingTop: '6px' }}>
          <span>Bihar <strong style={{ color: '#C5D4DF' }}>{biharPop}</strong></span>
          <span style={{ color: 'rgba(127, 149, 165, 0.4)' }}>|</span>
          <span>Others <strong style={{ color: '#C5D4DF' }}>{othersPop}</strong></span>
        </div>
      </div>

      {/* 2. Impacted Districts Card */}
      <div className="cc-card" style={{ padding: '12px 14px', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'rgba(59, 130, 246, 0.18)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Building size={15} color="#38BDF8" />
          </div>
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#7F95A5', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            IMPACTED DISTRICTS
          </span>
        </div>

        {/* Value + Donut Gauge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span style={{ fontSize: '24px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                {districtsCount}
              </span>
              <span style={{ fontSize: '12.5px', fontWeight: 600, color: '#C5D4DF' }}>Districts</span>
            </div>

            {/* Severity Counts */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10.5px', fontWeight: 600, marginTop: '4px' }}>
              <span style={{ color: '#EF4444' }}>{criticalDists} <span style={{ color: '#7F95A5', fontWeight: 400 }}>Crit</span></span>
              <span style={{ color: '#F97316' }}>{warningDists} <span style={{ color: '#7F95A5', fontWeight: 400 }}>Warn</span></span>
              <span style={{ color: '#06B6D4' }}>{watchDists} <span style={{ color: '#7F95A5', fontWeight: 400 }}>Watch</span></span>
            </div>
          </div>

          {/* 67% Donut Chart */}
          <div style={{ position: 'relative', width: '56px', height: '56px', flexShrink: 0 }}>
            <svg width="56" height="56" viewBox="0 0 56 56">
              <circle
                cx="28"
                cy="28"
                r={donutRadius}
                fill="transparent"
                stroke="#173149"
                strokeWidth="4.5"
              />
              <circle
                cx="28"
                cy="28"
                r={donutRadius}
                fill="transparent"
                stroke="#22D3EE"
                strokeWidth="4.5"
                strokeDasharray={donutCircumference}
                strokeDashoffset={donutOffset}
                strokeLinecap="round"
                transform="rotate(-90 28 28)"
                style={{ filter: 'drop-shadow(0 0 4px rgba(34, 211, 238, 0.5))' }}
              />
            </svg>
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 800,
                color: '#FFFFFF',
              }}
            >
              {highRiskPct}%
            </div>
          </div>
        </div>

        <div style={{ fontSize: '10.5px', color: '#7F95A5', borderTop: '1px solid rgba(61, 139, 180, 0.15)', paddingTop: '6px' }}>
          High Risk Areas across North-East Basin
        </div>
      </div>

      {/* 3. Major Rivers Card */}
      <div className="cc-card" style={{ padding: '12px 14px', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'rgba(6, 182, 212, 0.18)',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Waves size={15} color="#22D3EE" />
          </div>
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#7F95A5', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            MAJOR RIVERS
          </span>
        </div>

        {/* Value + Flow Wave Graphic */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1, fontFamily: 'var(--font-mono)' }}>
              {riversAboveDanger}
            </div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: '#C5D4DF', marginTop: '3px' }}>
              Above Danger Mark
            </div>
          </div>

          {/* Smooth Sine Wave Line Graphic */}
          <div style={{ width: '85px', height: '32px', position: 'relative', overflow: 'hidden' }}>
            <svg width="85" height="32" viewBox="0 0 85 32" fill="none">
              <path
                d="M 0 16 Q 14 6 28 16 T 56 16 T 85 16"
                stroke="#38BDF8"
                strokeWidth="2"
                strokeLinecap="round"
                fill="none"
                style={{ filter: 'drop-shadow(0 0 4px rgba(56, 189, 248, 0.6))' }}
              />
              <path
                d="M 0 22 Q 14 12 28 22 T 56 22 T 85 22"
                stroke="#06B6D4"
                strokeWidth="1.2"
                opacity="0.5"
                fill="none"
              />
            </svg>
          </div>
        </div>

        {/* River list */}
        <div style={{ fontSize: '10.5px', color: '#7F95A5', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', borderTop: '1px solid rgba(61, 139, 180, 0.15)', paddingTop: '6px' }}>
          {keyRiversList}
        </div>
      </div>

      {/* 4. Submerged Schools Card */}
      <div className="cc-card" style={{ padding: '12px 14px', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'rgba(139, 92, 246, 0.18)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <School size={15} color="#A78BFA" />
          </div>
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#7F95A5', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            SUBMERGED SCHOOLS
          </span>
        </div>

        {/* Value */}
        <div style={{ marginTop: '2px' }}>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
            {schoolsCount}
          </div>
          <div style={{ fontSize: '10.5px', color: '#7F95A5', marginTop: '3px' }}>
            Classrooms flooded; relief converted
          </div>
        </div>

        {/* Progress Bar with 68% */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderTop: '1px solid rgba(61, 139, 180, 0.15)', paddingTop: '6px' }}>
          <div style={{ flex: 1, height: '4px', background: 'rgba(23, 49, 73, 0.8)', borderRadius: '2px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${schoolsFloodedPct}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #14B8A6, #22D3EE)',
                borderRadius: '2px',
                boxShadow: '0 0 8px rgba(34, 211, 238, 0.5)',
              }}
            />
          </div>
          <span style={{ fontSize: '10.5px', fontWeight: 700, color: '#22D3EE', fontFamily: 'var(--font-mono)' }}>
            {schoolsFloodedPct}%
          </span>
        </div>
      </div>
    </section>
  );
};
