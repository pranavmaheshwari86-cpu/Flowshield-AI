import { RainfallSeverity, RainfallQuality } from '../types';

export interface RainfallThresholdConfig {
  min: number;
  max: number | null;
  label: string;
  category: string;
  color: string;
  glowColor: string;
  twBadgeClass: string;
}

export const RAINFALL_THRESHOLDS: Record<Exclude<RainfallSeverity, 'none'>, RainfallThresholdConfig> = {
  green: {
    min: 0.1,
    max: 15.5,
    label: '0.1 – 15.5 mm',
    category: 'Very light to light',
    color: '#10B981', // Emerald green
    glowColor: 'rgba(16, 185, 129, 0.45)',
    twBadgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  },
  yellow: {
    min: 15.6,
    max: 64.4,
    label: '15.6 – 64.4 mm',
    category: 'Moderate',
    color: '#F59E0B', // Amber / Gold
    glowColor: 'rgba(245, 158, 11, 0.55)',
    twBadgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  },
  orange: {
    min: 64.5,
    max: 115.5,
    label: '64.5 – 115.5 mm',
    category: 'Heavy 🌧️',
    color: '#F97316', // Vibrant Orange
    glowColor: 'rgba(249, 115, 22, 0.65)',
    twBadgeClass: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  },
  red: {
    min: 115.6,
    max: 204.4,
    label: '115.6 – 204.4 mm',
    category: 'Very Heavy 🌧️🌧️',
    color: '#EF4444', // Crimson / Red
    glowColor: 'rgba(239, 68, 68, 0.75)',
    twBadgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
  },
  purple: {
    min: 204.5,
    max: null,
    label: '> 204.4 mm',
    category: 'Extremely Heavy ⛈️',
    color: '#A855F7', // Violet / Purple
    glowColor: 'rgba(168, 85, 247, 0.85)',
    twBadgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
  },
};

export const RAINFALL_SCALE_TIERS = [
  { severity: 'purple' as RainfallSeverity, ...RAINFALL_THRESHOLDS.purple },
  { severity: 'red' as RainfallSeverity, ...RAINFALL_THRESHOLDS.red },
  { severity: 'orange' as RainfallSeverity, ...RAINFALL_THRESHOLDS.orange },
  { severity: 'yellow' as RainfallSeverity, ...RAINFALL_THRESHOLDS.yellow },
  { severity: 'green' as RainfallSeverity, ...RAINFALL_THRESHOLDS.green },
];

/**
 * Categorize raw precipitation into standard 5-tier IMD severity considering both 24h accumulation and hourly rate.
 */
export function getRainfallSeverity(mmPerHour: number, rainfall24hMm: number = 0): RainfallSeverity {
  const rain24h = rainfall24hMm != null && !isNaN(rainfall24hMm) ? rainfall24hMm : 0;
  const rate = mmPerHour != null && !isNaN(mmPerHour) ? mmPerHour : 0;

  if (rain24h < 0.1 && rate < 0.1) {
    return 'none';
  }

  // Official IMD 24-hour rainfall classification & corresponding high hourly rates
  if (rain24h > 204.4 || rate >= 30.0) {
    return 'purple';
  }
  if (rain24h >= 115.6 || rate >= 15.6) {
    return 'red';
  }
  if (rain24h >= 64.5 || rate >= 7.5) {
    return 'orange';
  }
  if (rain24h >= 15.6 || rate >= 2.5) {
    return 'yellow';
  }
  if (rain24h >= 0.1 || rate >= 0.1) {
    return 'green';
  }
  return 'none';
}

/**
 * Return primary hex color for rainfall severity.
 */
export function getRainfallColor(severity: RainfallSeverity): string {
  if (severity === 'purple') return RAINFALL_THRESHOLDS.purple.color;
  if (severity === 'red') return RAINFALL_THRESHOLDS.red.color;
  if (severity === 'orange') return RAINFALL_THRESHOLDS.orange.color;
  if (severity === 'yellow') return RAINFALL_THRESHOLDS.yellow.color;
  if (severity === 'green') return RAINFALL_THRESHOLDS.green.color;
  return '#64748B'; // slate-500 fallback
}

/**
 * Return glow rgba color for rainfall severity.
 */
export function getRainfallGlowColor(severity: RainfallSeverity): string {
  if (severity === 'purple') return RAINFALL_THRESHOLDS.purple.glowColor;
  if (severity === 'red') return RAINFALL_THRESHOLDS.red.glowColor;
  if (severity === 'orange') return RAINFALL_THRESHOLDS.orange.glowColor;
  if (severity === 'yellow') return RAINFALL_THRESHOLDS.yellow.glowColor;
  if (severity === 'green') return RAINFALL_THRESHOLDS.green.glowColor;
  return 'rgba(100, 116, 139, 0.2)';
}

/**
 * Return user-friendly IMD category label.
 */
export function getRainfallCategoryLabel(severity: RainfallSeverity, rainfall24hMm: number = 0): string {
  if (severity === 'purple' || rainfall24hMm > 204.4) return 'Extremely Heavy ⛈️';
  if (severity === 'red' || (rainfall24hMm >= 115.6 && rainfall24hMm <= 204.4)) return 'Very Heavy 🌧️🌧️';
  if (severity === 'orange' || (rainfall24hMm >= 64.5 && rainfall24hMm < 115.6)) return 'Heavy 🌧️';
  if (severity === 'yellow' || (rainfall24hMm >= 15.6 && rainfall24hMm < 64.5)) return 'Moderate';
  if (severity === 'green' || (rainfall24hMm >= 0.1 && rainfall24hMm < 15.6)) return 'Very light to light';
  return 'Dry / Trace';
}

/**
 * Compute marker radius scaled dynamically by rainfall intensity and 24h accumulation.
 */
export function getRainfallMarkerRadius(mmPerHour: number, rainfall24hMm: number = 0): number {
  const maxRain = Math.max(mmPerHour * 4, rainfall24hMm);
  if (maxRain <= 0.1) return 5;
  if (maxRain <= 5.0) return 7;
  if (maxRain <= 20.0) return 9;
  if (maxRain <= 50.0) return 12;
  return 15;
}

/**
 * Format rainfall mm/h string with unit.
 */
export function formatRainfall(mmPerHour: number): string {
  if (mmPerHour == null || isNaN(mmPerHour)) return '0.0 mm/h';
  return `${mmPerHour.toFixed(1)} mm/h`;
}

/**
 * Format 24-hour cumulative rainfall in mm.
 */
export function formatDailyRainfall(rainfall24hMm: number): string {
  if (rainfall24hMm == null || isNaN(rainfall24hMm)) return '0.0 mm';
  return `${rainfall24hMm.toFixed(1)} mm`;
}

/**
 * Format relative elapsed time from ISO timestamp.
 */
export function formatRelativeTime(isoString: string): string {
  try {
    const timestamp = new Date(isoString).getTime();
    if (isNaN(timestamp)) return 'Just now';
    const elapsedMinutes = Math.floor((Date.now() - timestamp) / 60000);
    if (elapsedMinutes <= 1) return 'Just now';
    if (elapsedMinutes < 60) return `${elapsedMinutes}m ago`;
    const hours = Math.floor(elapsedMinutes / 60);
    return `${hours}h ${elapsedMinutes % 60}m ago`;
  } catch {
    return 'Recently';
  }
}

/**
 * Quality badge display metadata.
 */
export function getQualityBadge(quality: RainfallQuality) {
  switch (quality) {
    case 'live':
      return { label: 'LIVE TELEMETRY', colorClass: 'text-emerald-400 bg-emerald-950/70 border-emerald-500/50' };
    case 'stale':
      return { label: 'STALE CACHE (<1h)', colorClass: 'text-amber-400 bg-amber-950/70 border-amber-500/50' };
    case 'unavailable':
    default:
      return { label: 'OFFLINE / UNAVAILABLE', colorClass: 'text-rose-400 bg-rose-950/70 border-rose-500/50' };
  }
}
