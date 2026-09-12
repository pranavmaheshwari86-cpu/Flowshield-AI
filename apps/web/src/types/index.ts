// Risk Tiers
export type RiskTier = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'SEVERE';

// Environmental Observation
export interface EnvironmentalObservation {
  id?: number | string;
  village_id?: number | string;
  rainfall_1h_mm: number;
  rainfall_3h_mm: number;
  rainfall_6h_mm: number;
  rainfall_24h_mm: number;
  rainfall_intensity_mm_hr: number;
  soil_moisture_pct: number;
  river_level_m: number;
  river_level_change_1h_m: number;
  source: string;
  data_quality_score: number;
  is_flagged: boolean;
  timestamp: string;
}

// Village Model
export interface Village {
  id: any;
  name: string;
  tehsil: string;
  basin?: string;
  district?: string;
  state?: string;
  latitude: number;
  longitude: number;
  elevation_m?: number;
  elevation?: number;
  slope_deg?: number;
  slope?: number;
  distance_to_river_m?: number;
  distance_to_river?: number;
  population: number;
  vulnerability_index: number;
  historical_flood_freq?: number;
  historical_flood_frequency?: number;
  current_risk_score: number;
  current_risk_tier: RiskTier;
  risk_score?: number;
  risk_level?: RiskTier;
  trend?: string;
  latest_rainfall_1h?: number;
  latest_river_level?: number;
  latest_soil_moisture?: number;
}

// SHAP Contribution
export interface SHAPContribution {
  feature_name: string;
  display_name: string;
  value: number;
  shap_value: number;
  contribution_direction: 'increases_risk' | 'decreases_risk' | 'neutral';
}

// Prediction Response
export interface PredictionResponse {
  id?: number | string;
  village_id: any;
  flood_probability: number;
  confidence_score: number;
  risk_tier: RiskTier;
  top_shap_factors: SHAPContribution[];
  data_quality_penalty_applied: boolean;
  model_version: string;
  inference_latency_ms: number;
  created_at: string;
}

// Risk Factor Breakdown
export interface RiskFactor {
  factor_name: string;
  display_name: string;
  weight: number;
  raw_value: number;
  weighted_contribution: number;
}

// Risk Score Response
export interface RiskScoreResponse {
  id?: number | string;
  village_id: any;
  composite_risk_score: number;
  risk_tier: RiskTier;
  flood_probability: number;
  rate_of_change: number;
  vulnerability_index: number;
  data_quality_penalty: number;
  confidence_score: number;
  factors: RiskFactor[];
  created_at: string;
}

// Alert Severity & Status
export type AlertSeverity = 'WATCH' | 'ADVISORY' | 'WARNING' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'ESCALATED' | 'RESOLVED';

export interface Alert {
  id: any;
  village_id: any;
  village_name?: string;
  severity: AlertSeverity;
  status: AlertStatus;
  headline?: string;
  trigger_reason?: string;
  lead_time_hours: number;
  recommended_actions: string[];
  created_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  resolved_at?: string | null;
}

// Recommended Action Plan
export interface RecommendedAction {
  action_id: string;
  title: string;
  description: string;
  priority: 'IMMEDIATE' | 'HIGH' | 'MEDIUM';
  target_audience: 'AUTHORITY' | 'CITIZEN' | 'FIRST_RESPONDER';
  requires_human_confirmation: boolean;
}

export interface ActionPlan {
  village_id: any;
  village_name: string;
  risk_tier: RiskTier;
  generated_at: string;
  actions: RecommendedAction[];
  legal_disclaimer: string;
}

// Shelter & Route
export interface Shelter {
  id: any;
  name: string;
  type: string;
  state?: string;
  district?: string;
  subdistrict_block?: string;
  village_town?: string;
  address?: string;
  latitude: number;
  longitude: number;
  capacity?: number | null;
  total_capacity?: number | null;
  current_occupancy?: number | null;
  available_capacity?: number | null;
  occupancy_percentage?: number | null;
  capacity_display?: string;
  occupancy_display?: string;
  available_display?: string;
  elevation_m?: number;
  status?: string;
  operational_status?: string;
  has_medical: boolean;
  medical_facility?: boolean;
  has_power_backup: boolean;
  generator_available?: boolean;
  water_available?: boolean;
  food_available?: boolean;
  toilets_available?: boolean;
  electricity_available?: boolean;
  communication_available?: boolean;
  wheelchair_accessible?: boolean;
  is_24x7?: boolean;
  contact_person?: string;
  contact_phone?: string;
  managing_authority?: string;
  distance_km?: number;
  estimated_travel_time_min?: number;
  source_name?: string;
  source_url?: string;
  source_type?: string;
  source_last_verified?: string;
  verification_status?: string;
  confidence_score?: number;
  suitability_score?: number;
  recommendation_label?: string;
  rationale?: string[];
  corridor_id?: string;
  corridor_name?: string;
  corridor_blocked?: boolean;
  is_safe_haven?: boolean;
  hazard_exposure_score?: number;
}

export interface EvacuationRoute {
  id: any;
  name: string;
  state?: string;
  district?: string;
  from_village_id?: any;
  to_shelter_id?: any;
  origin_village_id?: any;
  destination_shelter_id?: any;
  origin_village_name?: string;
  destination_shelter_name?: string;
  status: 'CLEAR' | 'CAUTION' | 'BLOCKED' | 'HIGH RISK' | 'CRITICAL';
  is_blocked?: boolean;
  distance_km: number;
  estimated_travel_time_min?: number;
  estimated_time_min?: number;
  assessed_risk_score?: number;
  safety_score?: number;
  is_river_crossing?: boolean;
  blocked_segments_count?: number;
  hazard_cost_multiplier?: number;
  hazard_exposure?: string;
  route_confidence?: number;
  last_verified?: string;
  recommendation?: string;
  route_label?: string;
  elevation_gain_m?: number;
  hazard_zones_crossed?: number;
  blockage_reason?: string;
  coordinates?: [number, number][];
  geometry?: any;
}

export interface DisasterEvent {
  id: string;
  event_id: string;
  disaster_type: 'LANDSLIDE' | 'FLASH_FLOOD' | 'HEAVY_RAINFALL' | 'ROAD_BLOCKAGE' | 'RIVER_SURGE' | string;
  severity: 'WATCH' | 'ADVISORY' | 'WARNING' | 'CRITICAL' | 'SEVERE' | string;
  status: 'ACTIVE' | 'MONITORING' | 'CONTAINED' | 'RESOLVED' | string;
  state: string;
  district: string;
  location_name: string;
  latitude: number;
  longitude: number;
  affected_radius_km: number;
  affected_population: number;
  confidence_score: number;
  description: string;
  triggered_by?: string;
  blocked_road_corridors?: string[];
  impacted_settlements?: string[];
  safe_evacuation_directions?: string[];
  source_agency?: string;
  created_at: string;
  updated_at: string;
}

export interface EmergencyFacility {
  name: string;
  type: string;
  phone: string;
  distance_km: number;
  status: string;
}

export interface RouteEvaluationResult {
  status: string;
  route_label: string;
  requires_authority_coordination: boolean;
  selected_route: EvacuationRoute | null;
  alternate_routes: EvacuationRoute[];
  blocked_routes?: EvacuationRoute[];
  shortest_route_hazardous_warning?: string | null;
  nearest_emergency_facilities?: EmergencyFacility[];
  snap_distance_km: number;
  hazard_penalty_applied?: number;
  message: string;
}

export interface RerouteResponse {
  route_invalidated: boolean;
  status: string;
  reroute_alert: string;
  old_eta_min: number | null;
  new_eta_min: number | null;
  reason: string;
  new_safe_route: EvacuationRoute | null;
  alternate_routes: EvacuationRoute[];
  nearest_emergency_facilities: EmergencyFacility[];
}

export interface GeographyState {
  state: string;
  districts_count: number;
  shelters_count: number;
  is_active: boolean;
  coverage_status: string;
}

export interface GeographyDistrict {
  district: string;
  state: string;
  center_lat: number;
  center_lon: number;
  default_zoom: number;
  river_basin: string;
  description: string;
  bounds: {
    min_lat: number;
    max_lat: number;
    min_lon: number;
    max_lon: number;
  };
  settlement_count: number;
  shelter_count: number;
  route_count: number;
  has_prediction?: boolean;
  has_shelter_data?: boolean;
}

export interface RoadIncident {
  id: string;
  route_id?: string;
  corridor_name: string;
  state: string;
  district: string;
  latitude?: number;
  longitude?: number;
  blockage_type: string;
  severity: string;
  description?: string;
  reported_by: string;
  status: string;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  name: string;
  jurisdiction: string;
  type: string;
  authority: string;
  url: string;
  coverage: string;
  description: string;
  verification_method: string;
  confidence_rating: string;
  last_audit_date: string;
}

// Village Detailed View with History
export interface VillageDetail extends Village {
  latest_observation?: EnvironmentalObservation;
  latest_prediction?: PredictionResponse;
  latest_risk?: RiskScoreResponse;
  active_alerts: Alert[];
  recommended_action_plan?: ActionPlan;
  nearest_shelters: Shelter[];
  routes: EvacuationRoute[];
  observation_history: EnvironmentalObservation[];
  risk_history: RiskScoreResponse[];
}

// Simulation Types
export interface SimulationStatus {
  is_active: boolean;
  current_substep: number;
  total_substeps: number;
  total_steps?: number;
  current_stage_name: string;
  stage_name?: string;
  current_stage_number: number;
  current_stage?: number;
  elapsed_simulated_minutes: number;
  seed: number;
  speed_multiplier: number;
  scenario_name: string;
  status?: string;
  progress_percentage?: number;
}

export interface SimulationStepResponse {
  substep: number;
  stage_name: string;
  stage_number: number;
  simulated_minutes: number;
  villages_updated: number;
  alerts_generated: number;
  status: SimulationStatus;
}

export interface SimulationResetResponse {
  message: string;
  seed: number;
  status: SimulationStatus;
}

// System Health & Telemetry
export interface SystemStatus {
  status: string;
  database: string;
  model_loaded: boolean;
  model_version: string;
  shap_explainer_ready: boolean;
  simulation_active: boolean;
  current_substep: number;
  uptime_seconds?: number;
}

// Auth Types
export interface User {
  id: number | string;
  username: string;
  email?: string;
  role: 'ADMIN' | 'OFFICER' | 'VIEWER';
  is_active?: boolean;
  full_name?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  role?: string;
  username?: string;
  user: User;
}

// GeoJSON Types
export interface GeoJSONFeature<G = any, P = any> {
  type: 'Feature';
  geometry: G;
  properties: P;
}

export interface GeoJSONFeatureCollection<G = any, P = any> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<G, P>[];
}

// National Live Flood Types (September 2026)
export interface RiverGauge {
  river: string;
  station: string;
  current_level_m: number;
  danger_level_m: number;
  warning_level_m: number;
  delta_danger_m: number;
  trend: string;
  status: string;
  state: string;
  impact: string;
}

export interface StateFloodDetail {
  status: string;
  risk_tier: RiskTier;
  headline: string;
  affected_population: number;
  districts_count: number;
  key_districts: string[];
  rivers_critical: string[];
  schools_submerged: number;
  ndrf_teams: number;
  flowshield_monitored_nodes: number;
}

export interface NationalFloodSummary {
  report_title: string;
  generated_at: string;
  national_overview: {
    critical_regions: string[];
    total_affected_population: number;
    total_districts_impacted: number;
    imd_forecast: string;
    major_rivers_above_danger: string[];
    schools_submerged_national: number;
    active_ndrf_sdrf_teams: number;
  };
  states: Record<string, StateFloodDetail>;
  live_gauges: RiverGauge[];
}

// Historical Flood Archive Types
export interface HistoricalFloodEvent {
  id: string;
  title: string;
  year: number;
  date_range: string;
  state: string;
  river_basin: string;
  severity: string;
  summary: string;
  meteorological_metrics: {
    peak_24h_rainfall_mm: number;
    rainfall_intensity_mm_hr: number;
    soil_moisture_peak_pct: number;
    max_river_surge_above_danger_m: number;
    discharge_peak_cusecs: number;
  };
  impact_statistics: {
    affected_population: number;
    casualties_count: number;
    districts_flooded: number;
    submerged_villages: number;
    economic_loss_inr_cr: number;
  };
  flowshield_ai_advantage: {
    conventional_warning_lead_hours: number;
    flowshield_predictive_lead_hours: number;
    hours_lead_time_gained: number;
    estimated_casualty_mitigation_pct: number;
    key_ml_contributor: string;
    decision_support_outcome: string;
  };
  coordinates: [number, number];
  zoom: number;
}

// Future Risk Forecasting Types
export interface FutureRiskHorizon {
  horizon_hours: number;
  forecast_timestamp: string;
  flood_probability: number;
  risk_score: number;
  risk_level: string;
  rainfall_intensity_mm_hr: number;
  cumulative_rainfall_mm: number;
  soil_saturation_pct: number;
  confidence: number;
  uncertainty_band: {
    p10: number;
    p90: number;
  };
  key_drivers: string[];
}

export interface FutureRiskTimelineResponse {
  village_id: string;
  village_name: string;
  latitude: number;
  longitude: number;
  generated_at: string;
  timeline: FutureRiskHorizon[];
  peak_risk_score: number;
  peak_risk_horizon_hours: number | null;
  model_version: string;
  calibration_method: string;
}

// AI Intelligence & Explanations
export interface AIExplanationRequest {
  village_id?: string;
  village_name?: string;
  risk_score: number;
  risk_level: string;
  flood_probability: number;
  key_factors?: string[];
  telemetry_summary?: Record<string, any>;
  language?: string;
}

export interface AIExplanationResponse {
  summary: string;
  detailed_analysis: string;
  immediate_actions: string[];
  confidence_assessment: string;
  provider: string;
  model: string;
  timestamp: string;
}

export interface WebIntelligenceItem {
  id: string;
  title: string;
  source: string;
  url?: string;
  published_at: string;
  summary: string;
  severity: 'INFO' | 'ADVISORY' | 'WARNING' | 'CRITICAL';
  region: string;
  tags: string[];
}

export interface WebIntelligenceResponse {
  items: WebIntelligenceItem[];
  total: number;
  last_updated: string;
  source_status: string;
  region_summary?: string;
}

export interface ModelStatusResponse {
  pipeline_version: string;
  selected_model: string;
  calibration_method: string;
  operational_threshold: number;
  status: string;
  evaluation_metrics: {
    recall: number;
    roc_auc: number;
    pr_auc: number;
    false_negative_rate: number;
  };
  feature_count: number;
}

export interface DriftStatusResponse {
  status: string;
  overall_drift_score: number;
  drift_level: 'HEALTHY' | 'MONITORING' | 'DRIFT_ALERT' | 'INSUFFICIENT_SAMPLES';
  drifted_features: string[];
  recommendation: string;
  last_evaluated: string;
}

// Real-Time Precipitation & Rainfall Layer Types
export type RainfallSeverity = 'green' | 'yellow' | 'orange' | 'red' | 'purple' | 'none';
export type IMDRainfallCategory =
  | 'Very light to light'
  | 'Moderate'
  | 'Heavy'
  | 'Very Heavy'
  | 'Extremely Heavy'
  | 'Dry / Trace';
export type RainfallQuality = 'live' | 'stale' | 'unavailable' | 'rate_limited';

export interface ForecastHorizonData {
  rain_mm: number;
  pop_pct: number;
  temp_c: number;
  condition: string;
}

export interface RiskAssessment {
  level: string;
  score: number;
  reasons: string[];
}

export interface RainfallReading {
  id: string;
  name: string;
  state?: string;
  district?: string;
  lat: number;
  lon: number;
  rainfallMmPerHour: number;
  rainfall_24h_mm: number;
  rainfall_3h_mm?: number;
  rainfall_6h_mm?: number;
  forecast_24h_mm?: number;
  historical_24h_available?: boolean;
  weather_main?: string;
  weather_description?: string;
  temperature_c?: number;
  feels_like_c?: number;
  humidity_pct?: number;
  pressure_hpa?: number;
  wind_speed_kmh?: number;
  wind_deg?: number;
  visibility_km?: number;
  cloud_cover_pct?: number;
  severity: RainfallSeverity;
  risk_level?: string;
  risk_score?: number;
  risk_reasons?: string[];
  risk_assessment?: RiskAssessment;
  forecast_horizons?: Record<string, ForecastHorizonData>;
  alerts?: any[];
  timestamp: string;
  source: string;
  quality: RainfallQuality;
  station_type?: string;
}

export interface TelemetryCategoryStats {
  category: string;
  count: number;
  min_rate: number;
  max_rate: number;
  percentage: number;
}

export interface RainfallReport {
  success: boolean;
  status: RainfallQuality;
  source: string;
  timestamp: string;
  units: string;
  thresholds: {
    green: { min: number; max: number; label: string };
    yellow: { min: number; max: number; label: string };
    red: { min: number; max: number | null; label: string };
  };
  total_monitored_points: number;
  rain_today_points_count?: number;
  active_rainfall_points_count: number;
  highest_rainfall_point?: {
    name: string;
    state?: string;
    district?: string;
    rainfall_24h_mm: number;
    forecast_24h_mm?: number;
    rainfall_rate_mm_hr: number;
    weather: string;
  } | null;
  telemetry_breakdown?: Record<string, TelemetryCategoryStats>;
  rate_limited?: boolean;
  data: RainfallReading[];
  error?: string | null;
}

// ==========================================
// PREDICTIVE RISK & MULTI-HORIZON TIMELINE TYPES
// ==========================================

export type TelemetryQualityStatus = 'GOOD' | 'DEGRADED' | 'STALE' | 'MISSING';

export interface TemporalProvenance {
  source_name: string;
  source_id?: string | null;
  observed_at?: string | null;
  valid_at: string;
  generated_at: string;
  fetched_at: string;
  quality_status: TelemetryQualityStatus;
  is_synthetic: boolean;
}

export interface ObservationSnapshot {
  rainfall_rate_mm_hr?: number | null;
  rainfall_1h_mm?: number | null;
  rainfall_3h_mm?: number | null;
  rainfall_6h_mm?: number | null;
  rainfall_12h_mm?: number | null;
  rainfall_24h_mm?: number | null;
  river_stage_meters?: number | null;
  river_danger_mark_meters?: number | null;
  river_surge_rate_m_hr?: number | null;
  soil_moisture_m3_m3?: number | null;
  soil_saturation_pct?: number | null;
  // Disambiguated scientific soil metrics
  soil_moisture_vwc_pct?: number | null;
  soil_effective_saturation_pct?: number | null;
  soil_telemetry_source?: string | null;
  soil_data_state?: string | null;
  // Disaggregated Precipitation Peaks
  observed_peak_rate_mm_hr?: number | null;
  forecast_peak_rate_mm_hr?: number | null;
  // Live atmospheric telemetry (OWM / Open-Meteo)
  temperature_c?: number | null;
  humidity_pct?: number | null;
  wind_speed_kmh?: number | null;
  atmospheric_telemetry_source?: string | null;
  atmospheric_freshness_status?: string | null;
  provenance: TemporalProvenance;
}

export interface HistoricalSeriesPoint {
  relative_hour: number;
  timestamp: string;
  observed_rainfall_rate?: number | null;
  observed_river_stage?: number | null;
  observed_soil_saturation?: number | null;
  operational_risk_score: number;
  is_forecast?: boolean;
  units?: Record<string, string>;
  source_attribution?: string;
  data_state?: string;
}

export interface ForecastHorizonPoint {
  horizon_hours: number;
  forecast_timestamp: string;
  projected_rainfall_rate_mm_hr?: number | null;
  cumulative_precipitation_mm?: number | null;
  projected_river_stage_meters?: number | null;
  projected_soil_saturation_pct?: number | null;
  raw_flood_probability?: number | null;
  calibrated_flood_probability?: number | null;
  operational_risk_score?: number | null;
  risk_tier: 'LOW' | 'WATCH' | 'HIGH' | 'CRITICAL' | 'UNSUPPORTED';
  uncertainty_band?: {
    p10?: number | null;
    p50?: number | null;
    p90?: number | null;
  } | null;
  primary_risk_driver: string;
  is_forecast?: boolean;
  units?: Record<string, string>;
  source_attribution?: string;
  data_state?: string;
}

export interface RiskDriverContribution {
  driver_name: string;
  contribution_points: number;
  metric_value_observed: string;
  physical_impact_description: string;
}

export interface ThresholdCrossingAnalysis {
  threshold_name: 'WATCH' | 'HIGH' | 'CRITICAL';
  threshold_value: number;
  is_crossed: boolean;
  earliest_crossing_hour?: number | null;
  most_likely_crossing_hour?: number | null;
  latest_crossing_hour?: number | null;
  lead_time_hours?: number | null;
  human_status_message: string;
}

export interface HydrologicalAnalysis {
  river_name: string;
  gauge_station_name: string;
  current_stage_meters?: number | null;
  danger_mark_meters?: number | null;
  warning_mark_meters?: number | null;
  hfl_meters?: number | null;
  margin_to_danger_meters?: number | null;
  rate_of_rise_m_per_hr?: number | null;
  hydraulic_trend: 'RISING' | 'STEADY' | 'FALLING' | 'UNKNOWN';
  upstream_dam_discharge_cumec?: number | null;
  dam_name?: string | null;
  telemetry_source?: string | null;
  bulletin_timestamp?: string | null;
  data_state?: string | null;
}

export interface ExposureAnalysis {
  village_population: number;
  vulnerable_demographic_pct: number;
  critical_infrastructure: {
    schools?: number;
    hospitals?: number;
    bridges?: number;
    road_segments?: number;
    [key: string]: number | undefined;
  };
  nearest_safe_shelter_name?: string | null;
  shelter_distance_km?: number | null;
  shelter_capacity_remaining?: number | null;
  shelter_elevation_advantage_m?: number | null;
  evacuation_route_status: 'CLEAR' | 'BLOCKED' | 'DATA_UNAVAILABLE';
  active_hazard_blockage_description?: string | null;
}

export interface DataStreamQuality {
  stream_name: string;
  status: TelemetryQualityStatus;
  last_updated_at?: string | null;
  staleness_seconds?: number | null;
  source_attribution: string;
}

export interface DataQualityMatrix {
  overall_health: 'OPTIMAL' | 'ACCEPTABLE' | 'DEGRADED' | 'COMPROMISED';
  active_mode: 'LIVE' | 'DEMO';
  streams: DataStreamQuality[];
}

export interface SettlementInfo {
  id: string;
  name: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  elevation_meters: number;
  river_basin: string;
}

export interface TimelineDetailedResponse {
  settlement: SettlementInfo;
  generated_at: string;
  current_situation: ObservationSnapshot;
  historical_series: HistoricalSeriesPoint[];
  forecast_horizons: ForecastHorizonPoint[];
  situation_summary: Record<string, string>;
  risk_drivers: RiskDriverContribution[];
  threshold_analysis: ThresholdCrossingAnalysis;
  peak_analysis: {
    rainfall_peak_hours?: number | null;
    river_crest_peak_hours?: number | null;
    risk_peak_hours?: number | null;
    [key: string]: number | null | undefined;
  };
  hydrology: HydrologicalAnalysis;
  exposure: ExposureAnalysis;
  data_quality: DataQualityMatrix;
  model_metadata: Record<string, string>;
  flood_outlook?: {
    village_id?: string;
    evaluated_at?: string;
    model_version?: string;
    horizons?: Record<string, {
      horizon: string;
      lead_hours: number;
      target_time?: string;
      projected_accumulated_rain_mm?: number | string;
      flood_probability: number;
      calibrated_probability: number;
      risk_score: number;
      risk_tier: 'LOW' | 'WATCH' | 'HIGH' | 'CRITICAL';
      threshold_exceeded: boolean;
      explanation?: string;
    }>;
    peak_risk?: {
      horizon: string;
      lead_hours: number;
      risk_score: number;
      risk_tier: string;
      calibrated_probability: number;
    };
    alert_level?: string;
  };
  location_capabilities?: LocationCapability | null;
  precipitation_forecast?: PrecipitationForecastResponse | null;
}

export type DataType = 'OBSERVED' | 'FORECAST_NWP' | 'ML_PREDICTION' | 'DERIVED_ESTIMATE' | 'STATIC' | 'CACHED' | 'UNAVAILABLE';

export type FreshnessStatus = 'LIVE' | 'RECENT' | 'VERIFIED_CACHE' | 'STALE' | 'UNAVAILABLE';

export type ModelSupport = 'SUPPORTED' | 'UNSUPPORTED' | 'VALIDATION_ONLY';

export interface LocationCapability {
  village_id: string;
  village_name: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  weather_observation: boolean;
  precipitation_forecast: boolean;
  river_monitoring: FreshnessStatus;
  river_station_name?: string | null;
  soil_estimation: DataType;
  terrain_attributes: boolean;
  flood_risk_model: ModelSupport;
  model_id?: string | null;
  model_name?: string | null;
  model_region?: string | null;
  target_region?: string | null;
  unsupported_reason?: string | null;
}

export interface PrecipitationPoint {
  timestamp_utc: string;
  timestamp_ist: string;
  relative_hour: number;
  value_mm_hr?: number | null;
  type: DataType;
  source: string;
  status: string;
  forecast_lead_hours?: number | null;
}

export interface PrecipitationForecastResponse {
  model_name: string;
  model_run_utc?: string | null;
  model_run_ist?: string | null;
  current_rate_mm_hr?: number | null;
  observed_points: PrecipitationPoint[];
  forecast_points: PrecipitationPoint[];
  peak_forecast_mm_hr?: number | null;
  peak_forecast_time_ist?: string | null;
  accumulated_24h_forecast_mm?: number | null;
  provenance: {
    source: string;
    source_id?: string | null;
    source_timestamp_utc?: string | null;
    ingestion_timestamp_utc: string;
    freshness_status: FreshnessStatus;
    data_type: DataType;
    is_live: boolean;
    derivation_formula?: string | null;
    quality_notes?: string | null;
  };
  freshness: FreshnessStatus;
}

export interface SettlementHierarchyItem {
  id: string;
  name: string;
  basin: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
}

export interface DistrictHierarchyItem {
  name: string;
  settlements: SettlementHierarchyItem[];
}

export interface StateHierarchyItem {
  name: string;
  districts: DistrictHierarchyItem[];
}

export interface TimelineLocationHierarchy {
  states: StateHierarchyItem[];
}

export interface AgroMonitoringPolygon {
  id: string;
  agro_polygon_id?: string;
  name: string;
  country: string;
  state?: string;
  district?: string;
  area_hectares: number;
  centroid_lat: number;
  centroid_lon: number;
  status: string;
  error_message?: string;
  last_soil_update?: string;
  latest_moisture?: number;
  moisture_tier?: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | 'UNKNOWN';
  latest_soil_temp?: number;
  latest_surface_temp?: number;
}

export interface AgroStatus {
  api_configured: boolean;
  total_cells_generated: number;
  registered_polygons: number;
  pending_polygons: number;
  failed_polygons: number;
  limit_exceeded_polygons: number;
  last_soil_sync?: string;
  plan_notice?: string;
  active_states: string[];
  active_districts: string[];
}

export interface SoilGeoJSONFeature {
  type: 'Feature';
  id: string;
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  properties: {
    id: string;
    agro_polygon_id?: string;
    name: string;
    country: string;
    state?: string;
    district?: string;
    area_ha: number;
    status: string;
    centroid: [number, number];
    soil_moisture?: number;
    moisture_tier?: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY_HIGH' | 'UNKNOWN';
    soil_temp_c?: number;
    surface_temp_c?: number;
    last_observation_dt?: string;
  };
}

export interface SoilGeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: SoilGeoJSONFeature[];
  metadata: {
    total_polygons: number;
    generated_at: string;
    source: string;
    units: {
      soil_moisture: string;
      temperature: string;
      area: string;
    };
  };
}


