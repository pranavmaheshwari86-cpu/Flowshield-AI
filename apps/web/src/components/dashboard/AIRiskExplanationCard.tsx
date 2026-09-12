import React, { useEffect, useState } from 'react';
import { Bot, Sparkles, CheckCircle2, ShieldAlert, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { AIExplanationResponse } from '../../types';

interface AIRiskExplanationCardProps {
  villageId: string;
  villageName?: string;
  riskScore: number;
  riskLevel: string;
  floodProbability: number;
  keyFactors?: string[];
  telemetrySummary?: Record<string, any>;
}

export const AIRiskExplanationCard: React.FC<AIRiskExplanationCardProps> = ({
  villageId,
  villageName = 'Mandi Sadar',
  riskScore,
  riskLevel,
  floodProbability,
  keyFactors = [],
  telemetrySummary = {},
}) => {
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  const [explanation, setExplanation] = useState<AIExplanationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchExplanation = (lang: 'en' | 'hi', isManual: boolean = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);

    api
      .getAIExplanation({
        village_id: villageId,
        village_name: villageName,
        risk_score: riskScore,
        risk_level: riskLevel,
        flood_probability: floodProbability,
        key_factors: keyFactors,
        telemetry_summary: telemetrySummary,
        language: lang,
      })
      .then((res) => {
        setExplanation(res);
        setLoading(false);
        setRefreshing(false);
      })
      .catch((err) => {
        console.error('Failed to generate AI explanation:', err);
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    fetchExplanation(language);
  }, [villageId, riskScore, riskLevel, language]);

  const handleLanguageToggle = (lang: 'en' | 'hi') => {
    setLanguage(lang);
  };

  const getBadgeColor = () => {
    if (riskLevel === 'CRITICAL') return '#EF4444';
    if (riskLevel === 'HIGH') return '#F97316';
    if (riskLevel === 'WATCH') return '#EAB308';
    return '#10B981';
  };

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.78) 0%, rgba(30, 41, 59, 0.7) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(168, 85, 247, 0.3)',
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
              background: 'rgba(168, 85, 247, 0.18)',
              border: '1px solid rgba(168, 85, 247, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 14px rgba(168, 85, 247, 0.25)',
            }}
          >
            <Sparkles size={20} color="#C084FC" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC' }}>
                AI Disaster Intelligence & Natural Language Briefing
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(168, 85, 247, 0.2)',
                  color: '#C084FC',
                  border: '1px solid rgba(168, 85, 247, 0.4)',
                }}
              >
                {explanation?.provider === 'gemini'
                  ? 'GEMINI 1.5 FLASH'
                  : explanation?.provider === 'openrouter'
                  ? 'LLAMA-3.3 70B'
                  : 'HYDROLOGICAL RULE SYNTHESIS'}
              </span>
            </div>
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>
              Automated physical factor attribution for emergency incident commanders and citizens
            </span>
          </div>
        </div>

        {/* Controls: Language toggle & Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              display: 'flex',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              overflow: 'hidden',
            }}
          >
            <button
              onClick={() => handleLanguageToggle('en')}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                background: language === 'en' ? 'rgba(168, 85, 247, 0.4)' : 'transparent',
                color: language === 'en' ? '#FFFFFF' : '#94A3B8',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              English
            </button>
            <button
              onClick={() => handleLanguageToggle('hi')}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                background: language === 'hi' ? 'rgba(168, 85, 247, 0.4)' : 'transparent',
                color: language === 'hi' ? '#FFFFFF' : '#94A3B8',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              हिन्दी
            </button>
          </div>

          <button
            onClick={() => fetchExplanation(language, true)}
            disabled={refreshing}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: refreshing ? 'not-allowed' : 'pointer',
              color: '#94A3B8',
            }}
            title="Regenerate explanation"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#94A3B8', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
          <Bot className="animate-pulse" size={20} color="#C084FC" />
          <span>Generating multi-factor hydrological risk reasoning...</span>
        </div>
      ) : explanation ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Executive Warning Banner */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              borderLeft: `4px solid ${getBadgeColor()}`,
              borderRadius: '0 8px 8px 0',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}
          >
            <ShieldAlert size={20} color={getBadgeColor()} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#F8FAFC' }}>
                {explanation.summary}
              </div>
            </div>
          </div>

          {/* Detailed Hydrological Analysis */}
          <div
            style={{
              background: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: '10px',
              padding: '14px 18px',
              fontSize: '13px',
              lineHeight: '1.6',
              color: '#E2E8F0',
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#C084FC', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              Physical Hydrology & Geomorphological Breakdown
            </div>
            {explanation.detailed_analysis}
          </div>

          {/* Immediate Directives & Field Actions */}
          {explanation.immediate_actions && explanation.immediate_actions.length > 0 && (
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.4)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '10px',
                padding: '14px 18px',
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#38BDF8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
                Operational Field Recommendations (NDMA / SDRF Protocol)
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {explanation.immediate_actions.map((act, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12px', color: '#CBD5E1' }}>
                    <CheckCircle2 size={15} color="#38BDF8" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <span>{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence footer */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: '#64748B', paddingTop: '4px' }}>
            <span>{explanation.confidence_assessment}</span>
            <span>Generated: {new Date(explanation.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
};
