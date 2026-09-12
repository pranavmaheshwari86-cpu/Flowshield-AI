import React, { useState } from 'react';
import { ShieldAlert, Mountain, CloudRain, Home, Waves, ExternalLink } from 'lucide-react';
import { Alert } from '../../types';

interface AlertCenterProps {
  alerts?: Alert[];
  onSelectAlert?: (alert: any) => void;
}

// Reference crisis alerts matching the reference image exactly
const DEFAULT_ALERTS = [
  {
    id: 'alt_1',
    severity: 'CRITICAL',
    title: 'Kosi River — Gauge 3',
    subtitle: 'Level 35.14 m  •  +1.29 m above danger mark',
    time: '2 min ago',
    icon: ShieldAlert,
    color: '#C62828',
    bgColor: 'rgba(198, 40, 40, 0.16)',
    borderColor: 'rgba(198, 40, 40, 0.65)',
  },
  {
    id: 'alt_2',
    severity: 'WARNING',
    title: 'Landslide Risk — NH-21',
    subtitle: 'High probability in 3 districts',
    time: '12 min ago',
    icon: Mountain,
    color: '#E05A33',
    bgColor: 'rgba(224, 90, 51, 0.16)',
    borderColor: 'rgba(224, 90, 51, 0.60)',
  },
  {
    id: 'alt_3',
    severity: 'WARNING',
    title: 'Heavy Rainfall — Kullu',
    subtitle: '47.3 mm/h (Last 1 hr)',
    time: '25 min ago',
    icon: CloudRain,
    color: '#E05A33',
    bgColor: 'rgba(224, 90, 51, 0.16)',
    borderColor: 'rgba(224, 90, 51, 0.60)',
  },
  {
    id: 'alt_4',
    severity: 'ADVISORY',
    title: 'Flooding — Pandoh',
    subtitle: 'Low-lying areas at risk',
    time: '41 min ago',
    icon: Home,
    color: '#D99A06',
    bgColor: 'rgba(217, 154, 6, 0.16)',
    borderColor: 'rgba(217, 154, 6, 0.60)',
  },
  {
    id: 'alt_5',
    severity: 'WATCH',
    title: 'River Surge — Beas',
    subtitle: 'Rising trend detected',
    time: '1 hr ago',
    icon: Waves,
    color: '#0F766E',
    bgColor: 'rgba(15, 118, 110, 0.16)',
    borderColor: 'rgba(15, 118, 110, 0.60)',
  },
];

export const AlertCenter: React.FC<AlertCenterProps> = ({
  alerts = [],
  onSelectAlert,
}) => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'recent' | 'ai'>('alerts');

  const itemsToDisplay = alerts && alerts.length > 0
    ? alerts.slice(0, 6).map((a, idx) => ({
        id: a.id || `alt_${idx}`,
        severity: a.severity || 'WARNING',
        title: a.village_name || a.headline || `Station #${a.village_id || idx}`,
        subtitle: a.recommended_actions?.[0] || a.trigger_reason || 'Inundation risk detected in catchment',
        time: `${Math.round(a.lead_time_hours * 10 || 12)} min ago`,
        icon: a.severity === 'CRITICAL' ? ShieldAlert : Mountain,
        color: a.severity === 'CRITICAL' ? '#C62828' : a.severity === 'WARNING' ? '#E05A33' : '#0F766E',
        bgColor: a.severity === 'CRITICAL' ? 'rgba(198, 40, 40, 0.16)' : 'rgba(224, 90, 51, 0.16)',
        borderColor: a.severity === 'CRITICAL' ? 'rgba(198, 40, 40, 0.65)' : 'rgba(224, 90, 51, 0.60)',
      }))
    : DEFAULT_ALERTS;

  return (
    <div
      className="cc-card"
      style={{
        flex: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        padding: '12px 14px',
        overflow: 'hidden',
      }}
    >
      {/* Top Tabs */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(61, 139, 180, 0.20)',
          paddingBottom: '8px',
          marginBottom: '8px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Tab 1: Active Alerts */}
          <button
            onClick={() => setActiveTab('alerts')}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '4px 0',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              position: 'relative',
              color: activeTab === 'alerts' ? '#FFFFFF' : '#7F95A5',
              fontSize: '12px',
              fontWeight: 700,
            }}
          >
            <span>Active Alerts</span>
            <span
              style={{
                fontSize: '9.5px',
                fontWeight: 800,
                color: '#FFFFFF',
                background: '#C62828',
                padding: '1px 6px',
                borderRadius: '9999px',
                boxShadow: '0 0 6px rgba(198, 40, 40, 0.5)',
              }}
            >
              {alerts && alerts.length > 0 ? alerts.length : 12}
            </span>
            {activeTab === 'alerts' && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-9px',
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: '#22D3EE',
                  boxShadow: '0 0 6px #22D3EE',
                }}
              />
            )}
          </button>

          {/* Tab 2: Recent Events */}
          <button
            onClick={() => setActiveTab('recent')}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '4px 0',
              cursor: 'pointer',
              color: activeTab === 'recent' ? '#FFFFFF' : '#7F95A5',
              fontSize: '12px',
              fontWeight: 600,
              position: 'relative',
            }}
          >
            <span>Recent Events</span>
            {activeTab === 'recent' && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-9px',
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: '#22D3EE',
                }}
              />
            )}
          </button>

          {/* Tab 3: AI Insights */}
          <button
            onClick={() => setActiveTab('ai')}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '4px 0',
              cursor: 'pointer',
              color: activeTab === 'ai' ? '#FFFFFF' : '#7F95A5',
              fontSize: '12px',
              fontWeight: 600,
              position: 'relative',
            }}
          >
            <span>AI Insights</span>
            {activeTab === 'ai' && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-9px',
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: '#22D3EE',
                }}
              />
            )}
          </button>
        </div>

        {/* View All */}
        <a
          href="#alerts"
          onClick={(e) => { e.preventDefault(); }}
          style={{
            fontSize: '11px',
            color: '#22D3EE',
            textDecoration: 'none',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
          }}
        >
          <span>View All</span>
          <ExternalLink size={11} />
        </a>
      </div>

      {/* Alert Feed List */}
      <div
        className="cc-scrollable"
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '7px',
          paddingRight: '2px',
        }}
      >
        {itemsToDisplay.map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.id}
              onClick={() => onSelectAlert && onSelectAlert(item)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '7px 10px',
                borderRadius: '8px',
                background: 'rgba(5, 20, 37, 0.70)',
                border: `1px solid ${item.borderColor}40`,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = item.borderColor;
                e.currentTarget.style.background = 'rgba(8, 30, 55, 0.85)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = `${item.borderColor}40`;
                e.currentTarget.style.background = 'rgba(5, 20, 37, 0.70)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '9px', minWidth: 0 }}>
                {/* Severity Icon */}
                <div
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '6px',
                    background: item.bgColor,
                    border: `1px solid ${item.borderColor}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Icon size={16} color={item.color} />
                </div>

                {/* Info */}
                <div style={{ minWidth: 0, lineHeight: 1.25 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span
                      style={{
                        padding: '1px 5px',
                        borderRadius: '3px',
                        fontSize: '9px',
                        fontWeight: 800,
                        letterSpacing: '0.04em',
                        color: '#FFFFFF',
                        background: item.color,
                      }}
                    >
                      {item.severity}
                    </span>
                    <span
                      style={{
                        fontSize: '11.5px',
                        fontWeight: 700,
                        color: '#FFFFFF',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {item.title}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: '10.5px',
                      color: '#C5D4DF',
                      marginTop: '2px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {item.subtitle}
                  </div>
                </div>
              </div>

              {/* Timestamp */}
              <div
                style={{
                  fontSize: '10px',
                  color: '#7F95A5',
                  whiteSpace: 'nowrap',
                  marginLeft: '8px',
                  flexShrink: 0,
                }}
              >
                {item.time}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
