import React, { useEffect, useState } from 'react';
import { Radio, ExternalLink, RefreshCw, FileText } from 'lucide-react';
import { api } from '../../services/api';
import { WebIntelligenceResponse } from '../../types';

interface WebIntelligencePanelProps {
  region?: string;
}

export const WebIntelligencePanel: React.FC<WebIntelligencePanelProps> = ({
  region = 'Himachal Pradesh / Mandi',
}) => {
  const [intelData, setIntelData] = useState<WebIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const fetchIntel = (isManual: boolean = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);

    api
      .getWebIntelligence(region)
      .then((res) => {
        setIntelData(res);
        setLoading(false);
        setRefreshing(false);
      })
      .catch((err) => {
        console.error('Failed to load web intelligence:', err);
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    fetchIntel();
  }, [region]);

  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 0.5)', color: '#EF4444' };
      case 'WARNING':
        return { bg: 'rgba(249, 115, 22, 0.2)', border: 'rgba(249, 115, 22, 0.5)', color: '#F97316' };
      case 'ADVISORY':
        return { bg: 'rgba(234, 179, 8, 0.2)', border: 'rgba(234, 179, 8, 0.5)', color: '#EAB308' };
      default:
        return { bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.4)', color: '#38BDF8' };
    }
  };

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(30, 41, 59, 0.65) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '20px 24px',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
            <Radio size={20} color="#38BDF8" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px', fontWeight: 700, color: '#F8FAFC' }}>
                Disaster Field Intelligence & Official Advisories
              </span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: '#10B981',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                }}
              >
                LIVE FEED
              </span>
            </div>
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>
              Central Water Commission (CWC), IMD Shimla Doppler Radar, and HP SDMA
            </span>
          </div>
        </div>

        <button
          onClick={() => fetchIntel(true)}
          disabled={refreshing}
          style={{
            background: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            padding: '6px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#94A3B8',
            fontSize: '11px',
            cursor: refreshing ? 'not-allowed' : 'pointer',
          }}
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          <span>Sync Feeds</span>
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#94A3B8' }}>
          <span>Connecting to official disaster telemetry and weather radars...</span>
        </div>
      ) : intelData ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Executive Regional Summary */}
          {intelData.region_summary && (
            <div
              style={{
                background: 'rgba(30, 41, 59, 0.45)',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: '10px',
                padding: '12px 16px',
                fontSize: '12px',
                lineHeight: '1.5',
                color: '#CBD5E1',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
              }}
            >
              <FileText size={18} color="#38BDF8" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ color: '#F1F5F9' }}>Sector Executive Brief: </strong>
                {intelData.region_summary}
              </div>
            </div>
          )}

          {/* Feed Items Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {intelData.items.map((item) => {
              const sev = getSeverityStyle(item.severity);
              return (
                <div
                  key={item.id}
                  style={{
                    background: 'rgba(15, 23, 42, 0.45)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '10px',
                    padding: '12px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 800,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: sev.bg,
                          color: sev.color,
                          border: `1px solid ${sev.border}`,
                        }}
                      >
                        {item.severity}
                      </span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#F8FAFC' }}>
                        {item.title}
                      </span>
                    </div>

                    <span style={{ fontSize: '11px', color: '#64748B' }}>
                      {item.source}
                    </span>
                  </div>

                  <p style={{ margin: 0, fontSize: '12px', color: '#94A3B8', lineHeight: '1.45' }}>
                    {item.summary}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px', fontSize: '11px', color: '#64748B' }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {item.tags.map((t) => (
                        <span key={t} style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1px 6px', borderRadius: '4px' }}>
                          #{t}
                        </span>
                      ))}
                    </div>

                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38BDF8', textDecoration: 'none' }}
                      >
                        <span>Agency Portal</span>
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
};
