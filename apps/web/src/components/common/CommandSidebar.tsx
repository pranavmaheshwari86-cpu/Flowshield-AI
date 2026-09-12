import React from 'react';
import {
  LayoutDashboard,
  Map as MapIcon,
  Waves,
  TriangleAlert,
  Building2,
  BarChart3,
  TrendingUp,
  Sparkles,
} from 'lucide-react';

interface CommandSidebarProps {
  activeItem?: string;
  onSelectItem?: (item: string) => void;
}

export const CommandSidebar: React.FC<CommandSidebarProps> = ({
  activeItem = 'Map',
  onSelectItem,
}) => {
  const selected = activeItem;

  // Feature toggle: Set to true when you want to restore the secondary operations navigation buttons
  const SHOW_EXTENDED_NAV = false;

  // Preserved for future re-activation per user request:
  const extendedNavItems = [
    { id: 'Overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'Rivers', label: 'Rivers', icon: Waves },
    { id: 'Hazards', label: 'Hazards', icon: TriangleAlert },
    { id: 'Districts', label: 'Districts', icon: Building2 },
    { id: 'Reports', label: 'Reports', icon: BarChart3 },
  ];

  const navItems = [
    { id: 'Map', label: 'Map', icon: MapIcon },
    { id: 'Timeline', label: 'Timeline', icon: TrendingUp },
    { id: 'AI Intel', label: 'AI Intel', icon: Sparkles },
    ...(SHOW_EXTENDED_NAV ? extendedNavItems : []),
  ];

  const handleSelect = (id: string) => {
    if (onSelectItem) onSelectItem(id);
  };

  return (
    <aside
      className="cc-sidebar-zone"
      style={{
        width: '148px',
        margin: '6px 0 10px 14px',
        background: 'transparent',
        border: 'none',
        boxShadow: 'none',
        backdropFilter: 'none',
        WebkitBackdropFilter: 'none',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        paddingTop: '8px',
        paddingBottom: '12px',
        userSelect: 'none',
        flexShrink: 0,
      }}
    >
      {/* Navigation Items */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '14px' }} aria-label="Operations Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = selected === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleSelect(item.id)}
              className={`cc-nav-btn ${isActive ? 'active' : ''}`}
              title={item.label}
            >
              {/* Active Page Indicator Line */}
              {isActive && <div className="cc-nav-indicator" />}

              <Icon
                size={21}
                className="cc-nav-icon"
              />
              <span className="cc-nav-label">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Branding & Tricolor Bar */}
      <div
        style={{
          padding: '0 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div
          style={{
            fontSize: '10px',
            lineHeight: 1.25,
            fontWeight: 600,
            color: '#7F95A5',
            letterSpacing: '0.02em',
          }}
        >
          Safer Communities
          <br />
          <span style={{ color: '#C5D4DF' }}>Stronger India</span>
        </div>

        {/* India Tricolor Horizontal Line */}
        <div
          style={{
            display: 'flex',
            height: '3px',
            width: '100%',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
          title="Republic of India National Initiative"
        >
          <div style={{ flex: 1, background: '#FF9933' }} /> {/* Saffron */}
          <div style={{ flex: 1, background: '#FFFFFF' }} /> {/* White */}
          <div style={{ flex: 1, background: '#138808' }} /> {/* Green */}
        </div>
      </div>
    </aside>
  );
};
