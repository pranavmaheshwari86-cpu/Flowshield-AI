import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Activity,
  Smartphone,
  Layers,
  Brain,
  Navigation,
  TrendingUp,
  ArrowRight,
  Database
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
      {/* Hero Section */}
      <div
        style={{
          background: 'linear-gradient(180deg, #0a1628 0%, #060d17 100%)',
          padding: '60px 24px',
          textAlign: 'center',
          borderBottom: '1px solid #1e355b',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '18px' }}>
          {/* Hackathon Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              borderRadius: '999px',
              fontSize: '12px',
              color: '#38bdf8',
              fontWeight: 600,
              letterSpacing: '0.04em'
            }}
          >
            <ShieldAlert size={14} />
            SMART INDIA HACKATHON 2026 • PROBLEM STATEMENT ID: 26192
          </div>

          {/* Main Title */}
          <h1
            style={{
              fontSize: '44px',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              lineHeight: 1.15,
              color: '#ffffff',
              margin: 0
            }}
          >
            Predict Early. Act Faster. <br />
            <span style={{ background: 'linear-gradient(90deg, #38bdf8, #3b82f6, #6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Save Lives in Hilly Watersheds.
            </span>
          </h1>

          {/* Subtitle */}
          <p style={{ fontSize: '16px', color: '#94a3b8', lineHeight: 1.6, maxWidth: '680px', margin: 0 }}>
            An operational AI-powered flash flood early warning and disaster decision support system for mountainous regions. Integrating multi-source hydro-meteorological telemetry, calibrated machine learning with authentic feature explainability, dynamic Voronoi catchments, and real-time safe route navigation.
          </p>

          {/* CTAs */}
          <div style={{ display: 'flex', gap: '14px', marginTop: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <Link to="/dashboard" className="btn btn-lg btn-primary">
              <Activity size={18} />
              Launch Authority Command Center
            </Link>

            <Link to="/citizen" className="btn btn-lg btn-secondary">
              <Smartphone size={18} />
              Open Citizen Mobile Mode
            </Link>

            <Link to="/about" className="btn btn-lg btn-outline">
              Scientific Methodology <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </div>

      {/* Multi-Source Pipeline Visualization */}
      <div style={{ maxWidth: '1100px', margin: '40px auto', padding: '0 24px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#f1f5f9' }}>
            End-to-End Decision Support Pipeline
          </h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
            From raw environmental sensors to verified citizen evacuation in under 1.2 seconds.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div className="card" style={{ textAlign: 'center', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(6,182,212,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#06b6d4' }}>
              <Database size={20} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>1. Multi-Source Ingestion</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Rainfall gauges (1h, 3h, 24h), radar reflectivity, soil moisture sensors, and river levels with schema bounds checking.
            </div>
          </div>

          <div className="card" style={{ textAlign: 'center', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(139,92,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}>
              <Brain size={20} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>2. Calibrated ML & Explainability</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Scientifically calibrated machine learning with authentic mathematical feature attributions (marginal log-odds and TreeSHAP) for disaster commanders.
            </div>
          </div>

          <div className="card" style={{ textAlign: 'center', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(245,158,11,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
              <TrendingUp size={20} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>3. Operational Risk Engine</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Composite risk formula blending ML probability (40%), hydrological surge trend (25%), vulnerability index (25%), and sensor penalties (10%).
            </div>
          </div>

          <div className="card" style={{ textAlign: 'center', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#3b82f6' }}>
              <Layers size={20} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>4. GIS Voronoi Catchments</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Spatial polygons mapped to Himalayan terrain with live river reaches and elevation hazard contours.
            </div>
          </div>

          <div className="card" style={{ textAlign: 'center', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(16,185,129,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
              <Navigation size={20} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>5. Evacuation Routing</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Automated route clearance checking, submerged causeway blockage alerts, and nearest safe shelter intake allocation.
            </div>
          </div>
        </div>
      </div>


    </div>
  );
};
