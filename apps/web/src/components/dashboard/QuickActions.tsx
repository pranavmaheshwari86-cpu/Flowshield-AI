import React from 'react';
import { Play, FileText, Navigation, Sparkles } from 'lucide-react';

interface QuickActionsProps {
  onRunSimulation?: () => void;
  onGenerateReport?: () => void;
  onToggleRoutes?: () => void;
  onOpenAssistant?: () => void;
  isSimulating?: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({
  onRunSimulation,
  onGenerateReport,
  onToggleRoutes,
  onOpenAssistant,
  isSimulating = false,
}) => {
  return (
    <div
      className="cc-card"
      style={{
        padding: '10px 14px',
        flexShrink: 0,
        gap: '8px',
      }}
    >
      <div
        style={{
          fontSize: '10.5px',
          fontWeight: 700,
          color: '#7F95A5',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
        }}
      >
        QUICK ACTIONS
      </div>

      {/* 2x2 Interactive Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
        }}
      >
        {/* 1. Run Simulation */}
        <button
          onClick={onRunSimulation}
          style={{
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0 10px',
            borderRadius: 'var(--radius-button)',
            background: 'rgba(20, 184, 166, 0.14)',
            border: '1px solid rgba(20, 184, 166, 0.40)',
            color: '#FFFFFF',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            textAlign: 'left',
          }}
          title="Advance Simulation by 1 Substep (15m)"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(20, 184, 166, 0.25)';
            e.currentTarget.style.borderColor = '#22D3EE';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(20, 184, 166, 0.14)';
            e.currentTarget.style.borderColor = 'rgba(20, 184, 166, 0.40)';
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '5px',
              background: 'rgba(34, 211, 238, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Play size={13} color="#22D3EE" fill="#22D3EE" />
          </div>
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {isSimulating ? 'Stepping...' : 'Run Simulation'}
          </span>
        </button>

        {/* 2. Generate Report */}
        <button
          onClick={onGenerateReport}
          style={{
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0 10px',
            borderRadius: 'var(--radius-button)',
            background: 'rgba(17, 38, 58, 0.70)',
            border: '1px solid rgba(61, 139, 180, 0.28)',
            color: '#C5D4DF',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            textAlign: 'left',
          }}
          title="Download National Situation Report (PDF)"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(20, 48, 75, 0.9)';
            e.currentTarget.style.borderColor = '#38BDF8';
            e.currentTarget.style.color = '#FFFFFF';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(17, 38, 58, 0.70)';
            e.currentTarget.style.borderColor = 'rgba(61, 139, 180, 0.28)';
            e.currentTarget.style.color = '#C5D4DF';
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '5px',
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <FileText size={13} color="#38BDF8" />
          </div>
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            Generate Report
          </span>
        </button>

        {/* 3. View Evacuation Routes */}
        <button
          onClick={onToggleRoutes}
          style={{
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0 10px',
            borderRadius: 'var(--radius-button)',
            background: 'rgba(17, 38, 58, 0.70)',
            border: '1px solid rgba(61, 139, 180, 0.28)',
            color: '#C5D4DF',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            textAlign: 'left',
          }}
          title="Highlight Mandi & Valley Evacuation Corridors"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(20, 48, 75, 0.9)';
            e.currentTarget.style.borderColor = '#10B981';
            e.currentTarget.style.color = '#FFFFFF';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(17, 38, 58, 0.70)';
            e.currentTarget.style.borderColor = 'rgba(61, 139, 180, 0.28)';
            e.currentTarget.style.color = '#C5D4DF';
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '5px',
              background: 'rgba(16, 185, 129, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Navigation size={13} color="#10B981" />
          </div>
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            Evacuation Routes
          </span>
        </button>

        {/* 4. Open AI Assistant */}
        <button
          onClick={onOpenAssistant}
          style={{
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '0 10px',
            borderRadius: 'var(--radius-button)',
            background: 'rgba(17, 38, 58, 0.70)',
            border: '1px solid rgba(61, 139, 180, 0.28)',
            color: '#C5D4DF',
            fontSize: '11.5px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            textAlign: 'left',
          }}
          title="Launch Tactical AI Decision Support Assistant"
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(20, 48, 75, 0.9)';
            e.currentTarget.style.borderColor = '#A78BFA';
            e.currentTarget.style.color = '#FFFFFF';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(17, 38, 58, 0.70)';
            e.currentTarget.style.borderColor = 'rgba(61, 139, 180, 0.28)';
            e.currentTarget.style.color = '#C5D4DF';
          }}
        >
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '5px',
              background: 'rgba(139, 92, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Sparkles size={13} color="#A78BFA" />
          </div>
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            Open AI Assistant
          </span>
        </button>
      </div>
    </div>
  );
};
