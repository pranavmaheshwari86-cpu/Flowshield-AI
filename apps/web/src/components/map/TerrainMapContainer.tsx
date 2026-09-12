import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  Polyline,
  Tooltip,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import {
  Compass,
  Layers,
  MapPin,
  Plus,
  Minus,
  CloudRain,
  Droplets,
  RefreshCw,
  Search,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  Village,
  Shelter,
  EvacuationRoute,
  GeoJSONFeatureCollection,
  RainfallReading,
  RainfallQuality,
} from '../../types';
import { api } from '../../services/api';
import {
  getRainfallColor,
  getRainfallGlowColor,
  getRainfallCategoryLabel,
  formatRelativeTime,
  RAINFALL_SCALE_TIERS,
} from '../../utils/rainfall';

const REGION_MAPPING: Record<string, string[]> = {
  NORTH: ['Delhi', 'Himachal Pradesh', 'Uttarakhand', 'Punjab', 'Haryana', 'Jammu & Kashmir', 'Jammu and Kashmir', 'Uttar Pradesh', 'Rajasthan', 'Chandigarh', 'Ladakh'],
  SOUTH: ['Karnataka', 'Tamil Nadu', 'Kerala', 'Andhra Pradesh', 'Telangana', 'Puducherry', 'Goa', 'Lakshadweep', 'Andaman and Nicobar Islands'],
  EAST: ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand'],
  WEST: ['Maharashtra', 'Gujarat', 'Goa', 'Dadra and Nagar Haveli and Daman and Diu'],
  CENTRAL: ['Madhya Pradesh', 'Chhattisgarh'],
  NORTHEAST: ['Assam', 'Meghalaya', 'Arunachal Pradesh', 'Manipur', 'Mizoram', 'Nagaland', 'Tripura', 'Sikkim'],
};

export type RainfallSeverityFilter = 'ALL' | 'green' | 'yellow' | 'orange' | 'red' | 'purple';

export interface SeverityOption {
  key: RainfallSeverityFilter;
  label: string;
  fullLabel: string;
  range: string;
  color: string;
  glow: string;
  activeBg: string;
}

export const SEVERITY_OPTIONS: SeverityOption[] = [
  {
    key: 'ALL',
    label: 'All',
    fullLabel: 'All Intensities',
    range: 'All monitored rain stations',
    color: '#38BDF8',
    glow: 'rgba(56, 189, 248, 0.4)',
    activeBg: 'rgba(56, 189, 248, 0.22)',
  },
  {
    key: 'green',
    label: 'Very Light',
    fullLabel: 'Very Light to Light',
    range: '0.1 – 15.5 mm',
    color: '#10B981',
    glow: 'rgba(16, 185, 129, 0.45)',
    activeBg: 'rgba(16, 185, 129, 0.22)',
  },
  {
    key: 'yellow',
    label: 'Moderate',
    fullLabel: 'Moderate Rain',
    range: '15.6 – 64.4 mm',
    color: '#F59E0B',
    glow: 'rgba(245, 158, 11, 0.45)',
    activeBg: 'rgba(245, 158, 11, 0.22)',
  },
  {
    key: 'orange',
    label: 'Heavy',
    fullLabel: 'Heavy Rain',
    range: '64.5 – 115.5 mm',
    color: '#F97316',
    glow: 'rgba(249, 115, 22, 0.5)',
    activeBg: 'rgba(249, 115, 22, 0.22)',
  },
  {
    key: 'red',
    label: 'Very Heavy',
    fullLabel: 'Very Heavy Rain',
    range: '115.6 – 204.4 mm',
    color: '#EF4444',
    glow: 'rgba(239, 68, 68, 0.5)',
    activeBg: 'rgba(239, 68, 68, 0.22)',
  },
  {
    key: 'purple',
    label: 'Extremely Heavy',
    fullLabel: 'Extremely Heavy Rain',
    range: '> 204.4 mm',
    color: '#A855F7',
    glow: 'rgba(168, 85, 247, 0.55)',
    activeBg: 'rgba(168, 85, 247, 0.22)',
  },
];

interface TerrainMapContainerProps {
  villages?: Village[];
  shelters?: Shelter[];
  routes?: EvacuationRoute[];
  selectedVillage?: Village | null;
  onSelectVillage?: (village: Village) => void;
  selectedState?: string;
  isFullPage?: boolean;
  onBackToOverview?: () => void;
}

// Controller for programmatic zoom & recenter
const MapController: React.FC<{
  center: [number, number];
  zoom: number;
  triggerInvalidate?: boolean;
  isFullPage?: boolean;
}> = ({ center, zoom, triggerInvalidate, isFullPage }) => {
  const map = useMap();

  useEffect(() => {
    if (isFullPage) {
      map.fitBounds([
        [7.0, 68.0],
        [36.5, 97.5],
      ], { padding: [25, 25], maxZoom: 6 });
    } else {
      map.setView(center, zoom);
    }
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    return () => clearTimeout(timer);
  }, [center, zoom, map, triggerInvalidate, isFullPage]);

  return null;
};

// Custom Leaflet DivIcon for Primary Settlement Beacon (Mandi)
const createPrimaryBeaconIcon = (name: string) => {
  const html = `
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); cursor: pointer;">
      <div style="
        background: rgba(2, 15, 30, 0.9);
        border: 1.5px solid #22D3EE;
        box-shadow: 0 0 16px rgba(34, 211, 238, 0.6);
        color: #FFFFFF;
        font-family: var(--font-sans);
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        gap: 5px;
        white-space: nowrap;
      ">
        <span style="width: 7px; height: 7px; border-radius: 50%; background: #22D3EE; box-shadow: 0 0 8px #22D3EE;"></span>
        ${name}
      </div>
      <div style="
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #22D3EE;
        border: 2px solid #FFFFFF;
        box-shadow: 0 0 10px #22D3EE;
        margin-top: 4px;
      "></div>
    </div>
  `;
  return L.divIcon({
    html,
    className: 'custom-beacon-pin',
    iconSize: [80, 50],
    iconAnchor: [40, 50],
  });
};

// Custom Leaflet DivIcon for Standard Settlements
const createHazardPinIcon = (name: string, tier: string, score: number) => {
  const color = tier === 'CRITICAL' ? '#EF4444' : tier === 'SEVERE' ? '#F97316' : tier === 'HIGH' ? '#F59E0B' : '#10B981';
  const glow = tier === 'CRITICAL' ? 'rgba(239, 68, 68, 0.6)' : tier === 'SEVERE' ? 'rgba(249, 115, 22, 0.5)' : 'rgba(16, 185, 129, 0.4)';

  const html = `
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); cursor: pointer;">
      <div style="
        background: rgba(2, 15, 30, 0.88);
        border: 1px solid ${color};
        color: #FFFFFF;
        font-family: var(--font-sans);
        font-size: 10px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        box-shadow: 0 0 10px ${glow};
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
      ">
        <span style="width: 5px; height: 5px; border-radius: 50%; background: ${color};"></span>
        ${name} ${score ? `<span style="opacity: 0.7; font-size: 9px;">${score}</span>` : ''}
      </div>
      <div style="
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: ${color};
        border: 1.5px solid #FFFFFF;
        box-shadow: 0 0 6px ${color};
        margin-top: 3px;
      "></div>
    </div>
  `;
  return L.divIcon({
    html,
    className: 'hazard-pin',
    iconSize: [70, 40],
    iconAnchor: [35, 40],
  });
};

// Custom Leaflet DivIcon for Real-Time Rainfall Radar & 24h Cumulative Points
const createRainfallPinIcon = (reading: RainfallReading, matchedVillage?: Village) => {
  const sev = reading.severity;
  const color = getRainfallColor(sev);
  const glow = getRainfallGlowColor(sev);
  const isPurple = sev === 'purple';
  const isRed = sev === 'red';
  const size = isPurple ? 22 : isRed ? 20 : sev === 'orange' ? 18 : sev === 'yellow' ? 16 : 14;
  const rain24h = (reading.rainfall_24h_mm || 0).toFixed(1);
  const rate1h = (reading.rainfallMmPerHour || 0).toFixed(1);
  const isCurrentlyRaining = (reading.rainfallMmPerHour || 0) > 0.0;

  const html = `
    <div style="position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; transform: translate(-50%, -50%); cursor: pointer;">
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background: ${color};
        border: 2px solid #FFFFFF;
        box-shadow: 0 0 12px ${glow};
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2;
      ">
        <svg width="${size * 0.55}" height="${size * 0.55}" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
        </svg>
      </div>
      <div style="
        margin-top: 2px;
        background: rgba(2, 14, 32, 0.94);
        border: 1px solid ${color};
        color: #F8FAFC;
        font-family: var(--font-mono, monospace);
        font-size: 8.5px;
        font-weight: 700;
        padding: 1.5px 5px;
        border-radius: 4px;
        white-space: nowrap;
        box-shadow: 0 3px 8px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        gap: 3px;
        z-index: 2;
      ">
        <span style="width: 4px; height: 4px; border-radius: 50%; background: ${color};"></span>
        <span style="font-weight: 600; color: #E2E8F0;">${reading.name.split(' ')[0]}</span>
        <span style="color: ${color}; font-weight: 800;">${rain24h}mm</span>
        ${isCurrentlyRaining ? `<span style="font-size: 7.5px; opacity: 0.85; color: #38BDF8;">(${rate1h}/h)</span>` : ''}
        ${matchedVillage ? `<span style="font-size: 7.5px; font-weight: 700; color: ${matchedVillage.current_risk_score >= 75 ? '#F87171' : matchedVillage.current_risk_score >= 50 ? '#FBBF24' : '#34D399'}; padding-left: 2px;">• ${matchedVillage.current_risk_score}</span>` : ''}
      </div>
    </div>
  `;
  return L.divIcon({
    html,
    className: 'rainfall-pin',
    iconSize: [matchedVillage ? 82 : 68, 44],
    iconAnchor: [matchedVillage ? 41 : 34, 22],
  });
};

export const TerrainMapContainer: React.FC<TerrainMapContainerProps> = ({
  villages = [],
  shelters = [],
  routes = [],
  selectedVillage,
  onSelectVillage,
  selectedState = 'ALL',
  isFullPage = false,
  onBackToOverview: _onBackToOverview,
}) => {
  // Center on India (National Overview)
  const defaultCenter: [number, number] = [22.5, 82.0];
  const [center, setCenter] = useState<[number, number]>(defaultCenter);
  const [zoom, setZoom] = useState<number>(5);
  const [mapMode, setMapMode] = useState<'satellite' | 'terrain' | 'dark'>(isFullPage ? 'satellite' : 'terrain');
  const [zonesGeoJSON, setZonesGeoJSON] = useState<GeoJSONFeatureCollection | null>(null);
  const [riversGeoJSON, setRiversGeoJSON] = useState<GeoJSONFeatureCollection | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  // Real-Time Rainfall Layer States
  const [showRainfallLayer, setShowRainfallLayer] = useState<boolean>(true);
  const [rainfallData, setRainfallData] = useState<RainfallReading[]>([]);
  const [rainfallQuality, setRainfallQuality] = useState<RainfallQuality>('live');
  const [rainfallTimestamp, setRainfallTimestamp] = useState<string | null>(null);
  const [rainfallSource, setRainfallSource] = useState<string>('Open-Meteo ECMWF');
  const [rainfallLoading, setRainfallLoading] = useState<boolean>(false);
  const [activeRainCount, setActiveRainCount] = useState<number>(0);
  const [totalMonitored, setTotalMonitored] = useState<number>(0);
  const [highestRainPoint, setHighestRainPoint] = useState<any>(null);

  // Real-time active rain and 24h rain counts
  const liveActiveRainingCount = useMemo(() => {
    return rainfallData.filter(r => (r.rainfallMmPerHour || 0) > 0.0).length;
  }, [rainfallData]);

  const liveRainTodayCount = useMemo(() => {
    const calculated = rainfallData.filter(r => (r.rainfall_24h_mm || 0) >= 0.1 || (r.rainfallMmPerHour || 0) > 0.0).length;
    return calculated > 0 ? calculated : activeRainCount;
  }, [rainfallData, activeRainCount]);

  // Interactive Search & Filter states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [rainfallFilterMode, setRainfallFilterMode] = useState<'all_today' | 'active_rain' | 'all_stations'>('all_today');
  const [selectedRegion, setSelectedRegion] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<RainfallSeverityFilter>('ALL');
  const [isPanelExpanded, setIsPanelExpanded] = useState<boolean>(true);

  // Dynamic counts by rainfall severity under current filter & region
  const severityCounts = useMemo(() => {
    let base = rainfallData;
    if (rainfallFilterMode === 'active_rain') {
      base = base.filter(r => (r.rainfallMmPerHour || 0) > 0.0);
    } else if (rainfallFilterMode === 'all_today') {
      base = base.filter(r => (r.rainfall_24h_mm || 0) >= 0.1 || (r.rainfallMmPerHour || 0) > 0.0);
    }
    if (selectedRegion !== 'ALL' && REGION_MAPPING[selectedRegion]) {
      const allowedStates = REGION_MAPPING[selectedRegion].map(s => s.toLowerCase());
      base = base.filter(r => r.state && allowedStates.includes(r.state.toLowerCase()));
    }
    return {
      ALL: base.length,
      green: base.filter(r => r.severity === 'green' || ((r.rainfall_24h_mm || 0) >= 0.1 && (r.rainfall_24h_mm || 0) <= 15.5)).length,
      yellow: base.filter(r => r.severity === 'yellow' || ((r.rainfall_24h_mm || 0) > 15.5 && (r.rainfall_24h_mm || 0) <= 64.4)).length,
      orange: base.filter(r => r.severity === 'orange' || ((r.rainfall_24h_mm || 0) > 64.4 && (r.rainfall_24h_mm || 0) <= 115.5)).length,
      red: base.filter(r => r.severity === 'red' || ((r.rainfall_24h_mm || 0) > 115.5 && (r.rainfall_24h_mm || 0) <= 204.4)).length,
      purple: base.filter(r => r.severity === 'purple' || (r.rainfall_24h_mm || 0) > 204.4).length,
    };
  }, [rainfallData, rainfallFilterMode, selectedRegion]);

  // Fetch real-time precipitation telemetry
  const fetchRainfallTelemetry = async (force: boolean = false) => {
    try {
      setRainfallLoading(true);
      const report = await api.getLiveRainfall(false, force);
      if (report && (report.success || report.data?.length > 0)) {
        setRainfallData(report.data || []);
        setRainfallQuality(report.status || 'live');
        setRainfallTimestamp(report.timestamp);
        setRainfallSource(report.source || 'Open-Meteo ECMWF');
        const rainTodayCount = (report as any).rain_today_points_count ?? report.active_rainfall_points_count ?? (report.data?.filter((r: any) => (r.rainfall_24h_mm || 0) >= 0.1 || (r.rainfallMmPerHour || 0) > 0.0).length ?? 0);
        setActiveRainCount(rainTodayCount);
        setTotalMonitored(report.total_monitored_points || report.data?.length || 0);
        if (report.highest_rainfall_point) {
          setHighestRainPoint(report.highest_rainfall_point);
        }
      }
    } catch (err) {
      console.warn('Real-time rainfall telemetry fetch encountered error', err);
      setRainfallQuality('unavailable');
    } finally {
      setRainfallLoading(false);
    }
  };

  // Poll live precipitation telemetry on mount and every 5 minutes
  useEffect(() => {
    fetchRainfallTelemetry(false);
    const timer = setInterval(() => {
      fetchRainfallTelemetry(false);
    }, 300000); // 5 minutes
    return () => clearInterval(timer);
  }, []);

  // Filtered Rainfall Readings based on Search Query, Region, Severity, and Filter Mode
  const filteredRainfallData = useMemo(() => {
    let list = rainfallData;
    if (rainfallFilterMode === 'active_rain') {
      list = list.filter(r => (r.rainfallMmPerHour || 0) > 0.0);
    } else if (rainfallFilterMode === 'all_today') {
      list = list.filter(r => (r.rainfall_24h_mm || 0) >= 0.1 || (r.rainfallMmPerHour || 0) > 0.0);
    }

    if (selectedRegion !== 'ALL' && REGION_MAPPING[selectedRegion]) {
      const allowedStates = REGION_MAPPING[selectedRegion].map(s => s.toLowerCase());
      list = list.filter(r => r.state && allowedStates.includes(r.state.toLowerCase()));
    }

    if (selectedSeverity !== 'ALL') {
      list = list.filter(r => {
        const rain24 = r.rainfall_24h_mm || 0;
        if (selectedSeverity === 'green') {
          return r.severity === 'green' || (rain24 >= 0.1 && rain24 <= 15.5);
        }
        if (selectedSeverity === 'yellow') {
          return r.severity === 'yellow' || (rain24 > 15.5 && rain24 <= 64.4);
        }
        if (selectedSeverity === 'orange') {
          return r.severity === 'orange' || (rain24 > 64.4 && rain24 <= 115.5);
        }
        if (selectedSeverity === 'red') {
          return r.severity === 'red' || (rain24 > 115.5 && rain24 <= 204.4);
        }
        if (selectedSeverity === 'purple') {
          return r.severity === 'purple' || rain24 > 204.4;
        }
        return true;
      });
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(r => 
        r.name.toLowerCase().includes(q) ||
        (r.state && r.state.toLowerCase().includes(q)) ||
        (r.district && r.district.toLowerCase().includes(q)) ||
        (r.weather_description && r.weather_description.toLowerCase().includes(q))
      );
    }
    return list;
  }, [rainfallData, rainfallFilterMode, selectedRegion, selectedSeverity, searchQuery]);

  // Quick Autocomplete search suggestions
  const searchSuggestions = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 1) return [];
    const q = searchQuery.toLowerCase().trim();
    return rainfallData
      .filter(r => 
        r.name.toLowerCase().includes(q) ||
        (r.state && r.state.toLowerCase().includes(q)) ||
        (r.district && r.district.toLowerCase().includes(q))
      )
      .slice(0, 5);
  }, [rainfallData, searchQuery]);

  // Fly to specific city / point on map
  const handleFlyToLocation = (lat: number, lon: number, zoomLevel: number = 9) => {
    if (mapRef.current) {
      mapRef.current.flyTo([lat, lon], zoomLevel, { duration: 1.2 });
    }
  };

  // Helper to match a village with a rainfall reading or coordinates
  const findMatchingVillage = (name: string, lat?: number, lon?: number) => {
    const qName = name.toLowerCase().replace(/\s*\(.*?\)/g, '').trim();
    return villages.find(v => {
      const vName = v.name.toLowerCase().replace(/\s*\(.*?\)/g, '').trim();
      if (vName === qName || vName.includes(qName) || qName.includes(vName)) return true;
      if (lat !== undefined && lon !== undefined) {
        const dLat = Math.abs(v.latitude - lat);
        const dLon = Math.abs(v.longitude - lon);
        if (dLat < 0.25 && dLon < 0.25) return true;
      }
      return false;
    });
  };

  // Auto-fit map camera when selectedRegion or filter changes
  useEffect(() => {
    if (!mapRef.current) return;
    if (selectedRegion !== 'ALL' && filteredRainfallData.length > 0) {
      const bounds = L.latLngBounds(filteredRainfallData.map(r => [r.lat, r.lon]));
      mapRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    } else if (selectedRegion === 'ALL' && isFullPage) {
      mapRef.current.fitBounds([
        [7.0, 68.0],
        [36.5, 97.5],
      ], { padding: [25, 25], maxZoom: 6 });
    }
  }, [selectedRegion, isFullPage]);

  // When full page mode is toggled, ensure view encompasses all of India
  useEffect(() => {
    if (isFullPage) {
      setCenter(defaultCenter);
      setZoom(5);
      if (mapRef.current) {
        mapRef.current.fitBounds([
          [7.0, 68.0],
          [36.5, 97.5],
        ], { padding: [25, 25], maxZoom: 6 });
        setTimeout(() => {
          mapRef.current?.invalidateSize();
        }, 150);
      }
    }
  }, [isFullPage]);

  // Fetch GeoJSON catchment layers
  useEffect(() => {
    let isMounted = true;
    api.getMapLayer('zones', selectedState)
      .then((data) => {
        if (isMounted) setZonesGeoJSON(data);
      })
      .catch(() => {});

    api.getMapLayer('rivers', selectedState)
      .then((data) => {
        if (isMounted) setRiversGeoJSON(data);
      })
      .catch(() => {});

    return () => { isMounted = false; };
  }, [selectedState]);

  // Handle Village Select from Props
  useEffect(() => {
    if (selectedVillage && !isFullPage) {
      setCenter([selectedVillage.latitude, selectedVillage.longitude]);
      setZoom(13);
    }
  }, [selectedVillage, isFullPage]);

  // Risk Color Mapping
  const getRiskColor = (tier: string) => {
    switch (tier) {
      case 'CRITICAL':
      case 'SEVERE':
        return '#C62828';
      case 'HIGH':
      case 'WARNING':
        return '#E05A33';
      case 'MODERATE':
      case 'ADVISORY':
        return '#D99A06';
      case 'WATCH':
        return '#0F766E';
      default:
        return '#2D6A4F';
    }
  };

  // Voronoi Polygon Style
  const zoneStyle = (feature: any) => {
    const tier = feature?.properties?.current_risk_tier || 'LOW';
    const color = getRiskColor(tier);
    return {
      fillColor: color,
      weight: 1.2,
      opacity: 0.6,
      color: '#1E355B',
      dashArray: '2',
      fillOpacity: tier === 'CRITICAL' || tier === 'SEVERE' ? 0.32 : tier === 'HIGH' ? 0.22 : 0.12,
    };
  };

  // Major flood-prone settlements across India (used only as fallback when rainfall layer is disabled)
  const referenceSettlements = useMemo(() => [
    { name: 'Delhi', coords: [28.6139, 77.2090] as [number, number], isPrimary: true, tier: 'CRITICAL', score: 88, state: 'Delhi' },
    { name: 'Patna', coords: [25.6093, 85.1376] as [number, number], isPrimary: false, tier: 'CRITICAL', score: 86, state: 'Bihar' },
    { name: 'Guwahati', coords: [26.1445, 91.7362] as [number, number], isPrimary: false, tier: 'CRITICAL', score: 92, state: 'Assam' },
    { name: 'Kolkata', coords: [22.5726, 88.3639] as [number, number], isPrimary: false, tier: 'WARNING', score: 74, state: 'West Bengal' },
    { name: 'Lucknow', coords: [26.8467, 80.9462] as [number, number], isPrimary: false, tier: 'WARNING', score: 70, state: 'Uttar Pradesh' },
    { name: 'Varanasi', coords: [25.3176, 82.9739] as [number, number], isPrimary: false, tier: 'HIGH', score: 78, state: 'Uttar Pradesh' },
    { name: 'Budaun', coords: [28.0315, 79.1235] as [number, number], isPrimary: false, tier: 'CRITICAL', score: 84, state: 'Uttar Pradesh' },
    { name: 'Mandi', coords: [31.7087, 76.9320] as [number, number], isPrimary: false, tier: 'HIGH', score: 76, state: 'Himachal Pradesh' },
    { name: 'Srinagar', coords: [34.0837, 74.7973] as [number, number], isPrimary: false, tier: 'ADVISORY', score: 54, state: 'Jammu & Kashmir' },
    { name: 'Mumbai', coords: [19.0760, 72.8777] as [number, number], isPrimary: false, tier: 'SEVERE', score: 82, state: 'Maharashtra' },
    { name: 'Surat', coords: [21.1702, 72.8311] as [number, number], isPrimary: false, tier: 'ADVISORY', score: 58, state: 'Gujarat' },
    { name: 'Ahmedabad', coords: [23.0225, 72.5714] as [number, number], isPrimary: false, tier: 'WATCH', score: 42, state: 'Gujarat' },
    { name: 'Bhubaneswar', coords: [20.2961, 85.8245] as [number, number], isPrimary: false, tier: 'WARNING', score: 68, state: 'Odisha' },
    { name: 'Vijayawada', coords: [16.5062, 80.6480] as [number, number], isPrimary: false, tier: 'HIGH', score: 72, state: 'Andhra Pradesh' },
    { name: 'Chennai', coords: [13.0827, 80.2707] as [number, number], isPrimary: false, tier: 'ADVISORY', score: 56, state: 'Tamil Nadu' },
    { name: 'Dibrugarh', coords: [27.4728, 94.9120] as [number, number], isPrimary: false, tier: 'CRITICAL', score: 89, state: 'Assam' },
  ], []);

  // Filtered reference settlements (only shown when rainfall layer is disabled, respecting region & search)
  const visibleReferenceSettlements = useMemo(() => {
    if (showRainfallLayer) return [];
    let list = referenceSettlements;
    if (selectedRegion !== 'ALL' && REGION_MAPPING[selectedRegion]) {
      const allowedStates = REGION_MAPPING[selectedRegion].map(s => s.toLowerCase());
      list = list.filter(s => s.state && allowedStates.includes(s.state.toLowerCase()));
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(s => s.name.toLowerCase().includes(q) || (s.state && s.state.toLowerCase().includes(q)));
    }
    return list;
  }, [showRainfallLayer, referenceSettlements, selectedRegion, searchQuery]);

  // Filtered villages: strictly respect rainfall layer, active rain filter, region, and search
  const filteredVillages = useMemo(() => {
    // When isFullPage and showRainfallLayer are active, rainfall stations represent the map data.
    // We do NOT render separate village hazard pins so only data matching the active filter appears.
    if (isFullPage && showRainfallLayer) {
      return [];
    }

    let list = villages;

    // Filter by Region
    if (selectedRegion !== 'ALL' && REGION_MAPPING[selectedRegion]) {
      const allowedStates = REGION_MAPPING[selectedRegion].map(s => s.toLowerCase());
      list = list.filter(v => v.state && allowedStates.includes(v.state.toLowerCase()));
    }

    // Filter by Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(v => 
        v.name.toLowerCase().includes(q) ||
        (v.district && v.district.toLowerCase().includes(q)) ||
        (v.state && v.state.toLowerCase().includes(q)) ||
        (v.tehsil && v.tehsil.toLowerCase().includes(q))
      );
    }

    return list;
  }, [villages, isFullPage, showRainfallLayer, selectedRegion, searchQuery]);

  // Controls Handlers
  const handleZoomIn = () => {
    if (mapRef.current) mapRef.current.zoomIn();
  };

  const handleZoomOut = () => {
    if (mapRef.current) mapRef.current.zoomOut();
  };

  const handleRecenter = () => {
    setCenter(defaultCenter);
    setZoom(5);
    if (mapRef.current) {
      if (isFullPage) {
        mapRef.current.fitBounds([
          [7.0, 68.0],
          [36.5, 97.5],
        ], { padding: [25, 25], maxZoom: 6 });
      } else {
        mapRef.current.flyTo(defaultCenter, 5, { duration: 1.2 });
      }
    }
  };

  return (
    <div
      className="cc-card"
      style={{
        height: '100%',
        width: '100%',
        position: 'relative',
        borderRadius: isFullPage ? '12px' : 'var(--radius-card)',
        overflow: 'hidden',
        border: '1px solid var(--flow-border-normal)',
        background: '#020A17',
      }}
    >
      {/* Interactive Floating HUD: India Real-Time Rainfall & Full-Day Accumulation Explorer (Full Page Map Only) */}
      {isFullPage && (
        <div
          style={{
            position: 'absolute',
            top: '14px',
            left: '14px',
          zIndex: 450,
          maxWidth: '560px',
          width: 'min(560px, calc(100% - 28px))',
          background: 'rgba(3, 14, 30, 0.92)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '12px',
          padding: isPanelExpanded ? '12px 14px' : '8px 12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.55), 0 0 12px rgba(56, 189, 248, 0.15)',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Panel Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: rainfallQuality === 'live' ? '#10B981' : rainfallQuality === 'stale' ? '#F59E0B' : '#EF4444',
                boxShadow: `0 0 8px ${rainfallQuality === 'live' ? '#10B981' : rainfallQuality === 'stale' ? '#F59E0B' : '#EF4444'}`,
              }}
            />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '0.02em', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CloudRain size={13} color="#38BDF8" />
                  India 24H Rainfall Data
                </span>
                <span style={{
                  fontSize: '8px',
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: '3px',
                  background: rainfallQuality === 'live' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  color: rainfallQuality === 'live' ? '#10B981' : '#F59E0B',
                }}>
                  {rainfallQuality.toUpperCase()}
                </span>
              </div>
              <span style={{ fontSize: '9.5px', color: '#94A3B8' }}>
                {rainfallFilterMode === 'active_rain'
                  ? `${liveActiveRainingCount} stations actively raining now`
                  : rainfallFilterMode === 'all_stations'
                  ? `${totalMonitored} total stations monitored across India`
                  : `${liveRainTodayCount} zones with rain today (24h)`} • {rainfallTimestamp ? formatRelativeTime(rainfallTimestamp) : 'Syncing'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => fetchRainfallTelemetry(true)}
              disabled={rainfallLoading}
              style={{
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38BDF8',
                cursor: rainfallLoading ? 'not-allowed' : 'pointer',
                padding: '3px 7px',
                borderRadius: '6px',
                fontSize: '9.5px',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                transition: 'all 0.15s ease',
              }}
              title="Refresh Telemetry"
            >
              <RefreshCw size={11} className={rainfallLoading ? 'animate-spin' : ''} />
              <span>{rainfallLoading ? 'Syncing' : 'Refresh'}</span>
            </button>

            <button
              onClick={() => setIsPanelExpanded(prev => !prev)}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#CBD5E1',
                cursor: 'pointer',
                padding: '3px 5px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
              }}
              title={isPanelExpanded ? 'Minimize Panel' : 'Expand Panel'}
            >
              {isPanelExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          </div>
        </div>

        {/* Panel Expanded Content */}
        {isPanelExpanded && (
          <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Search Input Bar with Clear Button */}
            <div style={{ position: 'relative' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                background: 'rgba(2, 10, 24, 0.85)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                borderRadius: '8px',
                padding: '5px 8px',
                gap: '6px',
              }}>
                <Search size={13} color="#38BDF8" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search state, district, or city (e.g. Raipur, Maharashtra, Mandi)..."
                  style={{
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#F8FAFC',
                    fontSize: '11px',
                    width: '100%',
                    fontFamily: 'inherit',
                  }}
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#94A3B8',
                      cursor: 'pointer',
                      padding: '2px',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>

              {/* Autocomplete Dropdown suggestions */}
              {searchSuggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: '4px',
                  background: 'rgba(3, 14, 30, 0.97)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  borderRadius: '8px',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
                  zIndex: 500,
                  overflow: 'hidden',
                  maxHeight: '220px',
                }}>
                  {searchSuggestions.map((s) => {
                    const sevColor = getRainfallColor(s.severity);
                    return (
                      <div
                        key={`sugg-${s.id}`}
                        onClick={() => {
                          setSearchQuery(s.name);
                          handleFlyToLocation(s.lat, s.lon, 9);
                        }}
                        style={{
                          padding: '7px 10px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                          cursor: 'pointer',
                          transition: 'background 0.15s ease',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.12)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#FFFFFF' }}>
                            {s.name}
                          </div>
                          <div style={{ fontSize: '9px', color: '#94A3B8' }}>
                            {s.district ? `${s.district}, ` : ''}{s.state || 'India'}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{
                            fontSize: '10px',
                            fontWeight: 800,
                            color: sevColor,
                            fontFamily: 'var(--font-mono, monospace)',
                            background: `${sevColor}15`,
                            padding: '1px 6px',
                            borderRadius: '4px',
                            border: `1px solid ${sevColor}40`,
                          }}>
                            {(s.rainfall_24h_mm || 0).toFixed(1)} mm 24h
                          </span>
                          {(s.rainfallMmPerHour || 0) > 0 && (
                            <span style={{ fontSize: '8.5px', color: '#38BDF8', fontWeight: 600 }}>
                              ⚡ {(s.rainfallMmPerHour || 0).toFixed(1)}/h
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Filter Mode Tabs: 24h Rain Today | Active Raining Now | All Stations */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '4px' }}>
              <button
                onClick={() => setRainfallFilterMode('all_today')}
                style={{
                  background: rainfallFilterMode === 'all_today' ? 'rgba(56, 189, 248, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                  border: rainfallFilterMode === 'all_today' ? '1px solid #38BDF8' : '1px solid rgba(255, 255, 255, 0.1)',
                  color: rainfallFilterMode === 'all_today' ? '#38BDF8' : '#94A3B8',
                  padding: '4px 6px',
                  borderRadius: '6px',
                  fontSize: '9.5px',
                  fontWeight: rainfallFilterMode === 'all_today' ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '3px',
                }}
              >
                <span>🌧️ Rain Today ({liveRainTodayCount})</span>
              </button>

              <button
                onClick={() => setRainfallFilterMode('active_rain')}
                style={{
                  background: rainfallFilterMode === 'active_rain' ? 'rgba(16, 185, 129, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                  border: rainfallFilterMode === 'active_rain' ? '1px solid #10B981' : '1px solid rgba(255, 255, 255, 0.1)',
                  color: rainfallFilterMode === 'active_rain' ? '#10B981' : '#94A3B8',
                  padding: '4px 6px',
                  borderRadius: '6px',
                  fontSize: '9.5px',
                  fontWeight: rainfallFilterMode === 'active_rain' ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '3px',
                }}
              >
                <span>⚡ Active Rain ({liveActiveRainingCount})</span>
              </button>

              <button
                onClick={() => setRainfallFilterMode('all_stations')}
                style={{
                  background: rainfallFilterMode === 'all_stations' ? 'rgba(147, 51, 234, 0.22)' : 'rgba(255, 255, 255, 0.04)',
                  border: rainfallFilterMode === 'all_stations' ? '1px solid #C084FC' : '1px solid rgba(255, 255, 255, 0.1)',
                  color: rainfallFilterMode === 'all_stations' ? '#C084FC' : '#94A3B8',
                  padding: '4px 6px',
                  borderRadius: '6px',
                  fontSize: '9.5px',
                  fontWeight: rainfallFilterMode === 'all_stations' ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '3px',
                }}
              >
                <span>🌐 All ({totalMonitored})</span>
              </button>
            </div>

            {/* Quick Regional Filters */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span style={{ fontSize: '8.5px', fontWeight: 700, color: '#64748B', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                Region
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', overflowX: 'auto', paddingBottom: '2px' }}>
                {['ALL', 'NORTH', 'CENTRAL', 'WEST', 'EAST', 'NORTHEAST', 'SOUTH'].map((reg) => (
                  <button
                    key={`reg-${reg}`}
                    onClick={() => setSelectedRegion(reg)}
                    style={{
                      background: selectedRegion === reg ? 'rgba(34, 211, 238, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                      border: selectedRegion === reg ? '1px solid #22D3EE' : '1px solid rgba(255, 255, 255, 0.08)',
                      color: selectedRegion === reg ? '#22D3EE' : '#94A3B8',
                      padding: '3px 8px',
                      borderRadius: '5px',
                      fontSize: '9.5px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      textTransform: 'capitalize',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {reg === 'ALL' ? 'All India' : reg.toLowerCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Rainfall Severity / Intensity Filters (IMD Classification) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', paddingTop: '1px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '8.5px', fontWeight: 700, color: '#64748B', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Rainfall Intensity (IMD)
                </span>
                {selectedSeverity !== 'ALL' && (
                  <button
                    onClick={() => setSelectedSeverity('ALL')}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#38BDF8',
                      fontSize: '8.5px',
                      cursor: 'pointer',
                      padding: '0 2px',
                      fontWeight: 600,
                      textDecoration: 'underline',
                    }}
                  >
                    Reset Intensity
                  </button>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '3px', overflowX: 'auto', paddingBottom: '2px' }}>
                {SEVERITY_OPTIONS.map((opt) => {
                  const isActive = selectedSeverity === opt.key;
                  const count = severityCounts[opt.key] ?? 0;
                  return (
                    <button
                      key={`sev-${opt.key}`}
                      onClick={() => setSelectedSeverity(isActive && opt.key !== 'ALL' ? 'ALL' : opt.key)}
                      style={{
                        background: isActive ? opt.activeBg : 'rgba(255, 255, 255, 0.03)',
                        border: isActive ? `1px solid ${opt.color}` : '1px solid rgba(255, 255, 255, 0.08)',
                        color: isActive ? opt.color : '#94A3B8',
                        boxShadow: isActive ? `0 0 10px ${opt.glow}` : 'none',
                        padding: '2.5px 6px',
                        borderRadius: '5px',
                        fontSize: '8.5px',
                        fontWeight: isActive ? 700 : 500,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '3.5px',
                        transition: 'all 0.15s ease',
                      }}
                      title={`${opt.fullLabel} (${opt.range})`}
                    >
                      {opt.color && (
                        <span
                          style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            background: opt.color,
                            boxShadow: isActive ? `0 0 6px ${opt.color}` : 'none',
                            flexShrink: 0,
                          }}
                        />
                      )}
                      <span>{opt.label}</span>
                      <span
                        style={{
                          fontSize: '8px',
                          padding: '0.5px 4px',
                          borderRadius: '3px',
                          background: isActive ? `${opt.color}30` : 'rgba(255, 255, 255, 0.06)',
                          color: isActive ? '#FFFFFF' : '#64748B',
                          fontWeight: 700,
                        }}
                      >
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Highest Recorded Rainfall (24h) Spotlight Banner */}
            {highestRainPoint && highestRainPoint.rainfall_24h_mm > 0 && (
              <div
                onClick={() => {
                  const match = rainfallData.find(r => r.name.toLowerCase().includes(highestRainPoint.name.toLowerCase()));
                  if (match) {
                    handleFlyToLocation(match.lat, match.lon, 9);
                  }
                }}
                style={{
                  background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.15))',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '8px',
                  padding: '7px 10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  transition: 'transform 0.15s ease',
                  gap: '8px',
                }}
                title="Click to Zoom to Highest Recorded Rainfall Station"
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '7px', width: '100%' }}>
                  <span style={{ fontSize: '11px', marginTop: '1px', color: '#F87171' }}>⚡</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <span style={{ fontSize: '10px', fontWeight: 800, color: '#FECACA', letterSpacing: '0.01em' }}>
                        Highest Recorded Rainfall (24h): {highestRainPoint.name}, {highestRainPoint.state} — {highestRainPoint.rainfall_24h_mm} mm
                      </span>
                      <span style={{ fontSize: '8px', color: '#38BDF8', fontWeight: 600, background: 'rgba(56, 189, 248, 0.12)', padding: '1px 5px', borderRadius: '3px', border: '1px solid rgba(56, 189, 248, 0.25)' }}>
                        Focus ↗
                      </span>
                    </div>
                    <span style={{ fontSize: '8.5px', color: '#CBD5E1' }}>
                      {highestRainPoint.weather ? `${highestRainPoint.weather} • ` : ''}Current Rate: {highestRainPoint.rainfall_rate_mm_hr} mm/h
                    </span>
                    <span style={{ fontSize: '8px', color: '#94A3B8' }}>
                      Last updated: {rainfallTimestamp ? formatRelativeTime(rainfallTimestamp) : 'Just now'} • Data source: {rainfallSource} Telemetry Pipeline
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Showing Count Status */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '8.5px', color: '#64748B', paddingTop: '2px' }}>
              <span>
                Showing <strong>{filteredRainfallData.length}</strong> matching points
                {selectedSeverity !== 'ALL' && (
                  <span style={{ color: SEVERITY_OPTIONS.find(o => o.key === selectedSeverity)?.color || '#38BDF8', marginLeft: '5px', fontWeight: 600 }}>
                    • {SEVERITY_OPTIONS.find(o => o.key === selectedSeverity)?.label}
                  </span>
                )}
              </span>
              <span>Units: 24H Total (mm) & Hourly (mm/h)</span>
            </div>
          </div>
        )}
      </div>
      )}

      {/* 3D Digital Twin Terrain Backdrop (Only in local overview mode) */}
      {!isFullPage && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 0,
            overflow: 'hidden',
          }}
        >
          <img
            src="/assets/mandi_terrain.jpg"
            alt="India Terrain Overview"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              filter: 'brightness(0.45) saturate(0.8) blur(2px)',
            }}
          />
          {/* Storm cloud atmosphere overlay */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '40%',
              height: '35%',
              background: 'radial-gradient(ellipse at 30% 20%, rgba(100, 130, 160, 0.25) 0%, transparent 70%)',
              animation: 'fogDrift 30s ease-in-out infinite alternate',
              pointerEvents: 'none',
            }}
          />
          {/* River glow shimmer at center */}
          <div
            style={{
              position: 'absolute',
              top: '30%',
              left: '20%',
              width: '60%',
              height: '40%',
              background: 'radial-gradient(ellipse at 50% 50%, rgba(56, 189, 248, 0.08) 0%, transparent 60%)',
              animation: 'waterShimmer 15s linear infinite',
              pointerEvents: 'none',
            }}
          />
        </div>
      )}

      {/* Leaflet Map Hero Container */}
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%', background: '#020A17', position: 'relative', zIndex: 1 }}
        zoomControl={false}
        preferCanvas={true}
        ref={mapRef}
      >
        <MapController center={center} zoom={zoom} isFullPage={isFullPage} />

        {/* Dynamic Basemap Layer */}
        <TileLayer
          attribution='&copy; OpenStreetMap &copy; CARTO &copy; Esri'
          url={
            mapMode === 'satellite'
              ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
              : mapMode === 'dark'
              ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
              : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
          }
          opacity={isFullPage ? 0.95 : 0.65}
          maxZoom={18}
        />

        {/* Voronoi Risk Polygons Overlay */}
        {zonesGeoJSON && (!showRainfallLayer || !isFullPage) && (selectedRegion === 'ALL' || selectedRegion === 'NORTH') && (rainfallFilterMode !== 'active_rain') && (
          <GeoJSON
            data={zonesGeoJSON as any}
            style={zoneStyle}
            onEachFeature={(feature, layer) => {
              const villageId = feature?.properties?.village_id;
              const v = villages.find(vil => vil.id === villageId);
              if (v && onSelectVillage) {
                layer.on({ click: () => onSelectVillage(v) });
              }
            }}
          />
        )}

        {/* Beas River Vector Reach with Glow */}
        {riversGeoJSON && (!showRainfallLayer || !isFullPage) && (selectedRegion === 'ALL' || selectedRegion === 'NORTH') && (
          <GeoJSON
            data={riversGeoJSON as any}
            style={{
              color: '#38BDF8',
              weight: 3.5,
              opacity: 0.9,
            }}
          />
        )}

        {/* Safe Evacuation Corridors */}
        {(!showRainfallLayer || !isFullPage) && (selectedRegion === 'ALL' || selectedRegion === 'NORTH') && routes.map((route) => {
          if (!route.coordinates || route.coordinates.length < 2) return null;
          const isBlocked = route.status === 'BLOCKED' || route.is_blocked;
          const color = isBlocked ? '#EF4444' : '#10B981';

          return (
            <Polyline
              key={`route-${route.id}`}
              positions={route.coordinates as [number, number][]}
              pathOptions={{
                color,
                weight: isBlocked ? 3.5 : 2.5,
                dashArray: isBlocked ? '6, 6' : undefined,
                opacity: 0.85,
              }}
            >
              <Tooltip sticky>
                <div style={{ fontSize: '11px' }}>
                  <strong>{route.name}</strong> • <span style={{ color }}>{isBlocked ? 'BLOCKED' : 'CLEAR'}</span>
                </div>
              </Tooltip>
            </Polyline>
          );
        })}

        {/* Primary Mandi Beacon & Key Mountain Settlements (Only when rainfall layer disabled & matching filter) */}
        {!showRainfallLayer && visibleReferenceSettlements.map((s) => (
          <Marker
            key={s.name}
            position={s.coords}
            icon={s.isPrimary ? createPrimaryBeaconIcon(s.name) : createHazardPinIcon(s.name, s.tier, s.score)}
            eventHandlers={{
              click: () => {
                const match = villages.find(v => v.name.toLowerCase() === s.name.toLowerCase());
                if (match && onSelectVillage) onSelectVillage(match);
              },
            }}
          />
        ))}

        {/* Dynamic Village & Regional Settlement Markers (Strictly filtered according to active filters) */}
        {filteredVillages.map((v) => {
          if (!showRainfallLayer && visibleReferenceSettlements.some(r => r.name.toLowerCase() === v.name.toLowerCase())) return null;
          return (
            <Marker
              key={`v-${v.id}`}
              position={[v.latitude, v.longitude]}
              icon={createHazardPinIcon(v.name, v.current_risk_tier, v.current_risk_score)}
              eventHandlers={{
                click: () => onSelectVillage && onSelectVillage(v),
              }}
            />
          );
        })}

        {/* Designated Disaster Relief Shelters */}
        {(!showRainfallLayer || !isFullPage) && (selectedRegion === 'ALL' || selectedRegion === 'NORTH') && shelters.map((sh) => (
          <Marker
            key={`sh-${sh.id}`}
            position={[sh.latitude, sh.longitude]}
            icon={L.divIcon({
              html: `
                <div style="background: rgba(2, 15, 30, 0.9); border: 1.5px solid #10B981; border-radius: 4px; padding: 2px 5px; color: #FFFFFF; font-family: var(--font-sans); font-size: 9px; font-weight: 600; display: flex; align-items: center; gap: 3px; box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);">
                  <span style="width: 5px; height: 5px; border-radius: 50%; background: #10B981;"></span>
                  🏥 ${sh.name.split(' ')[0]}
                </div>
              `,
              className: 'shelter-pin',
              iconSize: [65, 20],
              iconAnchor: [32, 10],
            })}
          >
            <Tooltip>
              <div style={{ fontSize: '11px' }}>
                <strong>{sh.name}</strong> • Cap: {sh.current_occupancy}/{sh.capacity}
              </div>
            </Tooltip>
          </Marker>
        ))}

        {/* Real-Time Precipitation / Rainfall Layer Markers */}
        {showRainfallLayer && filteredRainfallData.map((r) => {
          const matchedVillage = findMatchingVillage(r.name, r.lat, r.lon);
          return (
            <Marker
              key={`rain-${r.id}`}
              position={[r.lat, r.lon]}
              icon={createRainfallPinIcon(r, matchedVillage)}
              eventHandlers={{
                click: () => {
                  if (matchedVillage && onSelectVillage) {
                    onSelectVillage(matchedVillage);
                  } else {
                    handleFlyToLocation(r.lat, r.lon, 9);
                  }
                },
              }}
            >
              <Tooltip direction="top" offset={[0, -20]} opacity={0.95}>
                <div style={{ fontSize: '11px', color: '#0F172A', lineHeight: 1.35 }}>
                  <strong style={{ color: '#0369A1' }}>{r.name}</strong> {r.state ? `(${r.state})` : ''}<br />
                  🌧️ <strong>24H Rain:</strong> {(r.rainfall_24h_mm || 0).toFixed(1)} mm<br />
                  ⚡ <strong>Rate:</strong> {(r.rainfallMmPerHour || 0).toFixed(1)} mm/h {r.weather_description ? `• ${r.weather_description}` : ''}<br />
                  {matchedVillage && (
                    <div style={{ margin: '3px 0', padding: '2px 5px', borderRadius: '3px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#991B1B', fontWeight: 600, fontSize: '10px' }}>
                      🚨 Flood Risk: <strong>{matchedVillage.current_risk_tier}</strong> (Score: {matchedVillage.current_risk_score}/100)
                    </div>
                  )}
                  <span style={{
                    display: 'inline-block',
                    marginTop: '3px',
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: `${getRainfallColor(r.severity)}18`,
                    color: getRainfallColor(r.severity),
                    fontWeight: 700,
                    fontSize: '9.5px',
                    border: `1px solid ${getRainfallColor(r.severity)}50`,
                  }}>
                    {getRainfallCategoryLabel(r.severity, r.rainfall_24h_mm)}
                  </span>
                  {matchedVillage && (
                    <div style={{ fontSize: '9px', color: '#64748B', marginTop: '3px', fontStyle: 'italic' }}>
                      Click to inspect settlement intelligence
                    </div>
                  )}
                </div>
              </Tooltip>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Floating Map HUD Controls (Right Margin) */}
      <div
        style={{
          position: 'absolute',
          top: '14px',
          right: '14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          zIndex: 400,
        }}
        aria-label="Map Navigation Controls"
      >
        <button
          onClick={handleRecenter}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(80, 140, 170, 0.30)',
            color: '#22D3EE',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-control)',
          }}
          title="Compass (North Reset)"
        >
          <Compass size={18} />
        </button>

        <button
          onClick={() => {
            const nextMode = mapMode === 'satellite' ? 'dark' : mapMode === 'dark' ? 'terrain' : 'satellite';
            setMapMode(nextMode);
          }}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(80, 140, 170, 0.30)',
            color: '#C5D4DF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-control)',
          }}
          title={`Switch Basemap (Current: ${mapMode})`}
        >
          <Layers size={18} />
        </button>

        {/* Rainfall Layer Toggle Button */}
        <button
          onClick={() => setShowRainfallLayer(prev => !prev)}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: showRainfallLayer ? 'rgba(16, 185, 129, 0.22)' : 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: showRainfallLayer ? '1.5px solid #10B981' : '1px solid rgba(80, 140, 170, 0.30)',
            color: showRainfallLayer ? '#10B981' : '#7F95A5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: showRainfallLayer ? '0 0 12px rgba(16, 185, 129, 0.4)' : 'var(--shadow-control)',
            transition: 'all 0.2s ease',
          }}
          title={`Rainfall Telemetry Layer: ${showRainfallLayer ? 'VISIBLE (Click to Hide)' : 'HIDDEN (Click to Show)'}`}
        >
          <CloudRain size={18} />
        </button>

        <button
          onClick={handleRecenter}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(80, 140, 170, 0.30)',
            color: '#C5D4DF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-control)',
          }}
          title="Center on India"
        >
          <MapPin size={18} />
        </button>

        <button
          onClick={handleZoomIn}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(80, 140, 170, 0.30)',
            color: '#F1F7FA',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-control)',
          }}
          title="Zoom In"
        >
          <Plus size={18} />
        </button>

        <button
          onClick={handleZoomOut}
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            background: 'rgba(5, 20, 37, 0.85)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(80, 140, 170, 0.30)',
            color: '#F1F7FA',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-control)',
          }}
          title="Zoom Out"
        >
          <Minus size={18} />
        </button>
      </div>

      {/* Floating HUD: Risk Heatmap & Real-Time Rainfall Legend (Bottom Left - Full Page Map Only) */}
      {isFullPage && (
        <div
          style={{
            position: 'absolute',
            bottom: '76px',
            left: '14px',
            background: 'rgba(5, 20, 37, 0.88)',
            backdropFilter: 'blur(14px)',
            border: '1px solid rgba(80, 140, 170, 0.35)',
            borderRadius: '10px',
            padding: '10px 12px',
            zIndex: 400,
            boxShadow: 'var(--shadow-control)',
            width: '240px',
          }}
        >
          <div style={{ fontSize: '10px', fontWeight: 800, color: '#C5D4DF', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '5px' }}>
            Risk Heatmap
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', color: '#F1F7FA' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#C62828' }} />
              <span>Critical</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', color: '#F1F7FA' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#E05A33' }} />
              <span>Warning</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', color: '#F1F7FA' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#D99A06' }} />
              <span>Advisory</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', color: '#F1F7FA' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#0F766E' }} />
              <span>Watch</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9.5px', color: '#F1F7FA' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#2D6A4F' }} />
              <span>Low</span>
            </div>
          </div>

          {/* Real-Time Rainfall Precipitation Scale (IMD Standard Categories) */}
          <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.12)', marginTop: '8px', paddingTop: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
              <div style={{ fontSize: '10px', fontWeight: 800, color: '#38BDF8', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Droplets size={12} color="#38BDF8" />
                <span>Rainfall Telemetry</span>
              </div>
              <span style={{
                fontSize: '8px',
                fontWeight: 700,
                padding: '1px 5px',
                borderRadius: '3px',
                background: rainfallQuality === 'live' ? 'rgba(16, 185, 129, 0.2)' : rainfallQuality === 'stale' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: rainfallQuality === 'live' ? '#10B981' : rainfallQuality === 'stale' ? '#F59E0B' : '#EF4444',
              }}>
                {rainfallQuality.toUpperCase()}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '3.5px' }}>
              {RAINFALL_SCALE_TIERS.map((tier) => {
                const isSelected = selectedSeverity === tier.severity;
                return (
                  <div
                    key={tier.severity}
                    onClick={() => setSelectedSeverity(isSelected ? 'ALL' : tier.severity as RainfallSeverityFilter)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '9.5px',
                      color: isSelected ? tier.color : '#F1F7FA',
                      cursor: 'pointer',
                      padding: '2px 5px',
                      borderRadius: '4px',
                      background: isSelected ? `${tier.color}22` : 'transparent',
                      border: isSelected ? `1px solid ${tier.color}80` : '1px solid transparent',
                      boxShadow: isSelected ? `0 0 8px ${tier.color}40` : 'none',
                      transition: 'all 0.15s ease',
                    }}
                    title={`Click to filter by ${tier.category}`}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: tier.color,
                          boxShadow: `0 0 6px ${tier.color}`,
                          flexShrink: 0,
                        }}
                      />
                      <span style={{ fontWeight: isSelected ? 700 : 400 }}>{tier.category}</span>
                    </div>
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '9px',
                        color: tier.color,
                        fontWeight: 600,
                        marginLeft: '8px',
                        flexShrink: 0,
                      }}
                    >
                      {tier.label}
                    </span>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: '6px', fontSize: '8px', color: '#64748B', display: 'flex', justifyContent: 'space-between' }}>
              <span>Source: {rainfallSource}</span>
              <span>{activeRainCount} of {totalMonitored} Zones</span>
            </div>
          </div>
        </div>
      )}

      {/* Floating HUD: Elevation Gradient (Bottom Left under Risk Legend) */}
      <div
        style={{
          position: 'absolute',
          bottom: '14px',
          left: '14px',
          background: 'rgba(5, 20, 37, 0.85)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(80, 140, 170, 0.30)',
          borderRadius: '8px',
          padding: '6px 12px',
          zIndex: 400,
          boxShadow: 'var(--shadow-control)',
          width: '180px',
        }}
      >
        <div style={{ fontSize: '9.5px', fontWeight: 700, color: '#C5D4DF', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '3px' }}>
          Elevation (m)
        </div>
        <div
          style={{
            height: '5px',
            borderRadius: '2px',
            background: 'linear-gradient(90deg, #10B981, #06B6D4, #3B82F6, #6366F1, #FFFFFF)',
            marginBottom: '3px',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '8.5px', color: '#7F95A5', fontFamily: 'var(--font-mono)' }}>
          <span>500</span>
          <span>1,000</span>
          <span>1,500</span>
          <span>2,000</span>
          <span>3,000+</span>
        </div>
      </div>

      {/* Floating HUD: Mandi District Inset Radar Mini-Map (Bottom Right) */}
      <div
        style={{
          position: 'absolute',
          bottom: '14px',
          right: '14px',
          background: 'rgba(5, 20, 37, 0.88)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(80, 140, 170, 0.35)',
          borderRadius: '8px',
          padding: '8px 10px',
          zIndex: 400,
          boxShadow: 'var(--shadow-control)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <div style={{ width: '88px', height: '64px', position: 'relative', background: '#020F20', borderRadius: '4px', overflow: 'hidden', border: '1px solid rgba(34, 211, 238, 0.2)' }}>
          {/* Contour Silhouette */}
          <svg width="88" height="64" viewBox="0 0 88 64" fill="none">
            <path d="M 12 10 Q 30 18 52 14 T 80 32 T 60 55 T 20 48 Z" fill="rgba(34, 211, 238, 0.08)" stroke="#22D3EE" strokeWidth="1" opacity="0.6" />
            <path d="M 24 22 Q 40 26 50 24 T 66 38 T 46 48 Z" fill="rgba(34, 211, 238, 0.15)" stroke="#38BDF8" strokeWidth="0.8" />
            {/* Center Pin Radar */}
            <circle cx="44" cy="32" r="3.5" fill="#22D3EE" />
            <circle cx="44" cy="32" r="8" stroke="#22D3EE" strokeWidth="0.8" opacity="0.6" />
          </svg>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9.5px', fontWeight: 600, color: '#C5D4DF' }}>
          <MapPin size={10} color="#22D3EE" />
          <span>India Overview</span>
        </div>
      </div>
    </div>
  );
};
