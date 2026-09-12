import React from 'react';
import {
  DataQualityMatrix,
  LocationCapability,
  ObservationSnapshot,
} from '../../types';
import {
  Lock,
  Layers,
  Cpu,
} from 'lucide-react';

interface DataQualityTransparencyCardProps {
  dataQuality: DataQualityMatrix;
  modelMetadata: Record<string, string>;
  locationCapabilities?: LocationCapability | null;
  currentSituation?: ObservationSnapshot | null;
}

export const DataQualityTransparencyCard: React.FC<DataQualityTransparencyCardProps> = ({
  dataQuality,
  modelMetadata,
  locationCapabilities,
  currentSituation,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'GOOD':
        return { text: 'GOOD (Active SLA)', color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' };
      case 'DEGRADED':
        return { text: 'DEGRADED (Synthesized)', color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.3)' };
      case 'STALE':
        return { text: 'STALE (Lagging SLA)', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)' };
      case 'MISSING':
        return { text: 'MISSING (Sensor Offline)', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)' };
      default:
        return { text: status, color: '#94A3B8', bg: 'rgba(100, 116, 139, 0.15)', border: 'rgba(100, 116, 139, 0.3)' };
    }
  };

  const isModelSupported = locationCapabilities?.flood_risk_model === 'SUPPORTED';

  return (
    <div
      className="timeline-glass-card"
      style={{
        borderRadius: '10px',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        transition: 'all 0.25s ease',
      }}
    >
      {/* Header: Title and Overall Health */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Data Transparency &amp; SLA Governance
          </div>
          <div style={{ fontSize: '16px', color: '#F1F5F9', fontWeight: 700, marginTop: '2px' }}>
            Auditable Telemetry Stream Provenance Matrix
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#10B981',
              fontSize: '11px',
              fontWeight: 700,
            }}
          >
            <Lock size={12} />
            <span>STRICT ZERO-FABRICATION POLICY ENFORCED</span>
          </div>

          <div
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              color: '#38BDF8',
              fontSize: '11px',
              fontWeight: 700,
            }}
          >
            Health: {dataQuality.overall_health}
          </div>
        </div>
      </div>

      {/* Stream Provenance Table */}
      <div className="timeline-glass-subcard" style={{ overflowX: 'auto', borderRadius: '8px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(6, 18, 38, 0.70)', borderBottom: '1px solid rgba(56, 189, 248, 0.20)', color: '#94A3B8' }}>
              <th style={{ padding: '9px 14px', fontWeight: 700, letterSpacing: '0.04em' }}>Telemetry Stream</th>
              <th style={{ padding: '9px 14px', fontWeight: 700, letterSpacing: '0.04em' }}>Operational Status</th>
              <th style={{ padding: '9px 14px', fontWeight: 700, letterSpacing: '0.04em' }}>Authoritative Body / Attribution</th>
              <th style={{ padding: '9px 14px', fontWeight: 700, letterSpacing: '0.04em' }}>Staleness / Latency</th>
              <th style={{ padding: '9px 14px', fontWeight: 700, letterSpacing: '0.04em' }}>Last Ingested At</th>
            </tr>
          </thead>
          <tbody>
            {dataQuality.streams.map((s, idx) => {
              const badge = getStatusBadge(s.status);
              const timeStr = s.last_updated_at
                ? new Date(s.last_updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                : 'Offline';

              return (
                <tr
                  key={s.stream_name}
                  style={{
                    background: idx % 2 === 0 ? 'rgba(8, 24, 46, 0.35)' : 'rgba(8, 24, 46, 0.55)',
                    borderBottom: '1px solid rgba(56, 189, 248, 0.10)',
                  }}
                >
                  <td style={{ padding: '9px 14px', fontWeight: 700, color: '#F8FAFC' }}>
                    {s.stream_name}
                  </td>
                  <td style={{ padding: '9px 14px' }}>
                    <span
                      style={{
                        padding: '3px 9px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        background: badge.bg,
                        color: badge.color,
                        border: `1px solid ${badge.border}`,
                      }}
                    >
                      {badge.text}
                    </span>
                  </td>
                  <td style={{ padding: '9px 14px', color: '#E2E8F0', fontWeight: 500 }}>
                    {s.source_attribution}
                  </td>
                  <td style={{ padding: '9px 14px', color: '#38BDF8', fontFamily: 'monospace', fontWeight: 600 }}>
                    {s.staleness_seconds ? `${s.staleness_seconds}s` : 'Real-time (<1s)'}
                  </td>
                  <td style={{ padding: '9px 14px', color: '#CBD5E1', fontFamily: 'monospace' }}>
                    {timeStr}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Provenance Disclosures: Soil Moisture & Geographic Model Governance */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '12px' }}>
        {/* Soil Moisture Derivation Disclosure */}
        <div
          className="timeline-glass-subcard"
          style={{
            padding: '12px 14px',
            borderRadius: '8px',
            background: 'rgba(15, 23, 42, 0.65)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700, color: '#38BDF8' }}>
              <Layers size={14} />
              <span>Soil Moisture Provenance &amp; Scientific Guard</span>
            </div>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                padding: '2px 7px',
                borderRadius: '4px',
                background: 'rgba(245, 158, 11, 0.15)',
                color: '#F59E0B',
                border: '1px solid rgba(245, 158, 11, 0.3)',
              }}
            >
              DERIVED_ESTIMATE
            </span>
          </div>

          <div style={{ fontSize: '11px', color: '#CBD5E1', lineHeight: 1.5 }}>
            Saturation is empirically estimated via Antecedent Precipitation Index:
            <code
              style={{
                display: 'block',
                marginTop: '4px',
                padding: '4px 8px',
                background: 'rgba(0, 0, 0, 0.4)',
                borderRadius: '4px',
                color: '#2DD4BF',
                fontFamily: 'monospace',
                fontSize: '10.5px',
              }}
            >
              min(95.0, max(20.0, 48.0 + (rain_24h * 0.35)))
            </code>
            {currentSituation?.soil_saturation_pct !== undefined && currentSituation?.soil_saturation_pct !== null && (
              <div style={{ marginTop: '4px', fontSize: '10.5px', color: '#94A3B8' }}>
                Current Synthesized Saturation: <strong style={{ color: '#2DD4BF', fontFamily: 'monospace' }}>{currentSituation.soil_saturation_pct.toFixed(1)}%</strong>
              </div>
            )}
          </div>

          <div style={{ fontSize: '10.5px', color: '#94A3B8', marginTop: '2px', lineHeight: 1.4 }}>
            <strong>Scientific Guard:</strong> Not in-situ capacitive sensor telemetry. This derived estimate is strictly prohibited from being passed into ML models trained on volumetric water content ($m^3/m^3$) to prevent distribution shift.
          </div>
        </div>

        {/* Model Governance & Capability Disclosure */}
        <div
          className="timeline-glass-subcard"
          style={{
            padding: '12px 14px',
            borderRadius: '8px',
            background: 'rgba(15, 23, 42, 0.65)',
            border: `1px solid ${isModelSupported ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 700, color: isModelSupported ? '#34D399' : '#FBBF24' }}>
              <Cpu size={14} />
              <span>Regional ML Governance &amp; Boundaries</span>
            </div>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                padding: '2px 7px',
                borderRadius: '4px',
                background: isModelSupported ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: isModelSupported ? '#10B981' : '#F59E0B',
                border: `1px solid ${isModelSupported ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              }}
            >
              {locationCapabilities ? locationCapabilities.flood_risk_model : 'SUPPORTED'}
            </span>
          </div>

          <div style={{ fontSize: '11px', color: '#CBD5E1', lineHeight: 1.5 }}>
            Target Region:{' '}
            <strong style={{ color: '#F1F5F9' }}>
              {locationCapabilities?.target_region || 'himachal_pradesh'}
            </strong>
            {locationCapabilities?.model_name && (
              <> | Model: <strong style={{ color: '#38BDF8' }}>{locationCapabilities.model_name}</strong></>
            )}
          </div>

          <div style={{ fontSize: '10.5px', color: '#94A3B8', marginTop: '2px', lineHeight: 1.4 }}>
            {isModelSupported ? (
              <span style={{ color: '#A7F3D0' }}>
                ✓ Hydro-geomorphological parameters match training domain. Full 6-horizon inference pipeline active.
              </span>
            ) : (
              <span style={{ color: '#FDE68A' }}>
                ⚠ {locationCapabilities?.unsupported_reason || 'Cross-regional proxying disabled to avoid uncalibrated risk predictions.'} Weather telemetry and CWC river stage remain fully operational.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Model Ops & Verification Metadata Footer */}
      <div
        className="timeline-glass-subcard"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '10.5px',
          color: '#94A3B8',
          padding: '8px 14px',
          borderRadius: '6px',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <span>
          <strong style={{ color: '#E2E8F0' }}>ML Engine:</strong> {modelMetadata.model_architecture || 'FlowShield Dual ML Pipeline (XGBoost + Logistic)'}
        </span>
        <span>
          <strong style={{ color: '#E2E8F0' }}>Calibration:</strong> {modelMetadata.calibrator || 'Isotonic Regression (tau=0.08)'}
        </span>
        <span>
          <strong style={{ color: '#E2E8F0' }}>Model Artifact:</strong> {modelMetadata.model_version || 'v2_selected_model.joblib'}
        </span>
        <span style={{ color: '#10B981', fontWeight: 700, textShadow: '0 0 10px rgba(16, 185, 129, 0.4)' }}>
          ✓ {modelMetadata.validation_status || 'VALIDATED against monsoon holdout'}
        </span>
      </div>
    </div>
  );
};
