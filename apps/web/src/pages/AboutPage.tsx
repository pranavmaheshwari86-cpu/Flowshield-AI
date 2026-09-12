import React from 'react';
import {
  ShieldAlert,
  Brain,
  Layers,
  Cpu,
  AlertTriangle,
  Scale
} from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '40px 24px', maxWidth: '960px', margin: '0 auto', width: '100%' }}>
      {/* Title */}
      <div style={{ borderBottom: '1px solid #1e355b', paddingBottom: '20px', marginBottom: '28px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#06b6d4', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          <ShieldAlert size={14} /> Smart India Hackathon 2026 • PS ID: 26192
        </div>
        <h1 style={{ fontSize: '32px', fontWeight: 800, color: '#ffffff', marginTop: '6px', letterSpacing: '-0.02em' }}>
          Scientific Methodology & Technical Architecture
        </h1>
        <p style={{ fontSize: '15px', color: '#94a3b8', lineHeight: 1.6, marginTop: '6px' }}>
          Flowshield provides an operational, explainable AI framework designed to mitigate flash flood casualties across steep Himalayan watersheds through early detection, automated explainability, and GIS-informed action.
        </p>
      </div>

      {/* Model Performance & Verification */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <span className="card-title">
            <Cpu size={18} color="#06b6d4" />
            Machine Learning Architecture & Evaluated Performance
          </span>
        </div>

        <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.6 }}>
          The machine learning pipeline utilizes an <strong>XGBoost (Extreme Gradient Boosting) Classifier</strong> trained on high-altitude mountainous hydro-meteorological scenarios. The model was evaluated on a held-out test split of 1,200 records using 5-fold stratified cross-validation.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px', marginTop: '8px' }}>
          <div style={{ background: '#162a4d', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>TEST ACCURACY</div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)' }}>93.0%</div>
          </div>

          <div style={{ background: '#162a4d', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>ROC-AUC SCORE</div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#06b6d4', fontFamily: 'var(--font-mono)' }}>98.2%</div>
          </div>

          <div style={{ background: '#162a4d', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>SAFETY RECALL</div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>87.8%</div>
          </div>

          <div style={{ background: '#162a4d', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>PRECISION</div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>80.0%</div>
          </div>

          <div style={{ background: '#162a4d', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>F1-SCORE</div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: '#a78bfa', fontFamily: 'var(--font-mono)' }}>83.7%</div>
          </div>
        </div>
      </div>

      {/* 12 Canonical Features Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <span className="card-title">
            <Layers size={18} color="#3b82f6" />
            12 Canonical Feature Definitions & Physical Bounds
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #2a4778', color: '#94a3b8' }}>
                <th style={{ padding: '8px 10px' }}>Feature Name</th>
                <th style={{ padding: '8px 10px' }}>Type</th>
                <th style={{ padding: '8px 10px' }}>Bounds</th>
                <th style={{ padding: '8px 10px' }}>Physical Relevance in Hilly Watersheds</th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: 'rainfall_1h', type: 'float', bounds: '0 - 150 mm', desc: 'Short-term burst indicating cloudburst intensity' },
                { name: 'rainfall_3h', type: 'float', bounds: '0 - 300 mm', desc: 'Intermediate accumulation triggering steep slope runoff' },
                { name: 'rainfall_6h', type: 'float', bounds: '0 - 450 mm', desc: 'Sub-catchment concentration time threshold' },
                { name: 'rainfall_24h', type: 'float', bounds: '0 - 600 mm', desc: 'Antecedent moisture buildup over the preceding day' },
                { name: 'rainfall_intensity', type: 'float', bounds: '0 - 200 mm/h', desc: 'Peak instantaneous precipitation rate' },
                { name: 'soil_moisture', type: 'float', bounds: '0 - 100 %', desc: 'Saturation level governing infiltration capacity vs immediate runoff' },
                { name: 'river_level', type: 'float', bounds: '0 - 25 m', desc: 'Current stream stage height relative to datum' },
                { name: 'river_level_change', type: 'float', bounds: '-5 - +10 m/h', desc: 'Hydraulic surge velocity indicating upstream pulse' },
                { name: 'elevation', type: 'float', bounds: '300 - 4500 m', desc: 'Settlement altitude affecting orographic rain and gravity flows' },
                { name: 'slope', type: 'float', bounds: '0 - 75 deg', desc: 'Terrain gradient governing water velocity and debris entrainment' },
                { name: 'distance_to_river', type: 'float', bounds: '10 - 15000 m', desc: 'Proximity to active stream channel' },
                { name: 'historical_flood_freq', type: 'float', bounds: '0 - 10 events', desc: 'Past 10-year documented inundation frequency' },
              ].map((f, i) => (
                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{f.name}</td>
                  <td style={{ padding: '8px 10px', color: '#94a3b8' }}>{f.type}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>{f.bounds}</td>
                  <td style={{ padding: '8px 10px', color: '#94a3b8' }}>{f.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Operational Risk Index Equation */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <span className="card-title">
            <Scale size={18} color="#f59e0b" />
            Operational Risk Engine Formulation
          </span>
        </div>

        <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.6 }}>
          Rather than relying solely on raw binary machine learning probabilities, Flowshield computes an operational multi-dimensional risk score:
        </p>

        <div style={{ background: '#0a1628', border: '1px solid #1e355b', padding: '16px', borderRadius: '8px', fontFamily: 'var(--font-mono)', fontSize: '14px', color: '#38bdf8', textAlign: 'center', margin: '10px 0' }}>
          Risk = (0.40 × P_ML) + (0.25 × T_surge) + (0.25 × V_vuln) − (0.10 × P_penalty)
        </div>

        <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div>• <strong>P_ML (40%):</strong> XGBoost flood probability from 12 environmental telemetry features.</div>
          <div>• <strong>T_surge (25%):</strong> Hydrological surge trend, derived from 1h river level rise rate.</div>
          <div>• <strong>V_vuln (25%):</strong> Village socio-geomorphic vulnerability index (elderly ratio, building materials, slope).</div>
          <div>• <strong>P_penalty (10%):</strong> Sensor data quality penalty applied if telemetry is missing, stale, or flagged.</div>
        </div>
      </div>

      {/* Explainable AI */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <span className="card-title">
            <Brain size={18} color="#8b5cf6" />
            Explainable AI: Authentic Feature Attribution
          </span>
        </div>

        <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.6 }}>
          In emergency disaster management, black-box predictions undermine operational trust. Flowshield computes exact mathematical feature attributions for every inference in real time (standardized marginal log-odds decomposition and TreeSHAP). Incident commanders can see immediately whether risk is driven by intense short-term rainfall, 72-hour antecedent saturation, steep terrain gradients, or river channel proximity.
        </p>
      </div>

      {/* Statutory Disclosures */}
      <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
        <div className="card-header">
          <span className="card-title">
            <AlertTriangle size={18} color="#f59e0b" />
            Statutory Disclosures & Ethical Guardrails
          </span>
        </div>

        <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div>
            <strong>1. Verified Baseline & Simulation Telemetry:</strong> Machine learning models are trained on verified ECMWF ERA5-Land reanalysis and DEM topographic datasets across Mandi district (Beas River basin), with interactive emergency scenarios powered by deterministic simulation seed <code>26192</code> for Smart India Hackathon 2026.
          </div>
          <div>
            <strong>2. Non-Forecast Disclaimer:</strong> Flowshield is an operational decision-support tool. It is not an official meteorological forecast and does not supersede public advisories issued by the India Meteorological Department (IMD) or Central Water Commission (CWC).
          </div>
          <div>
            <strong>3. Human-in-the-Loop Governance:</strong> Automated actions (such as mass SMS or SDRF team mobilization) require explicit confirmation and authorization by certified incident commanders.
          </div>
        </div>
      </div>
    </div>
  );
};
