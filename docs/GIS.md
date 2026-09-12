# Flowshield — GIS & Spatial Intelligence Documentation

## 1. Spatial Foundation
- **Spatial Engine**: PostgreSQL 16 with PostGIS 3.4 extensions.
- **Coordinate Reference System**: EPSG:4326 (WGS84).
- **Region of Interest**: Mandakini River Basin (Kedarnath / Rudraprayag Corridor, Uttarakhand).
  - Latitude: 30.25°N to 30.75°N
  - Longitude: 78.90°E to 79.25°E

## 2. Spatial Layers & PostGIS Queries

### 2.1 Settlements (`villages`)
20 settlements stored as `Point(4326)`. Attributes include elevation, slope, river proximity, and population.

### 2.2 Risk Catchments (`risk_zones`)
Precomputed Voronoi catchment polygons around village centroids clipped to the watershed boundary. Joined dynamically at query time with the village's current operational risk level to avoid runtime geometry recomputation.

### 2.3 River Network (`rivers`)
LineStrings representing the Mandakini River, Vasuki Ganga, and Madhyamaheshwar Ganga. Attributes include danger and warning level thresholds.

### 2.4 Disaster Relief Shelters (`shelters`)
8 designated shelters stored as `Point(4326)`. Distance calculations use PostGIS geography casting:
```sql
SELECT s.id, s.name, s.total_capacity, s.current_occupancy,
       ST_Distance(s.geom::geography, v.geom::geography) / 1000.0 AS distance_km
FROM shelters s, villages v
WHERE v.id = :village_id AND s.status != 'CLOSED'
ORDER BY ST_Distance(s.geom::geography, v.geom::geography) ASC
LIMIT 3;
```

### 2.5 Evacuation Corridors (`routes`)
Precomputed `LineString(4326)` vectors connecting settlements to designated shelters. In high flood stages, segments crossing flooded river channels are marked `is_blocked = TRUE`.

## 3. Offline Resilience Strategy
If the Leaflet frontend is unable to reach public OpenStreetMap tile servers due to network issues at the evaluation venue, a styled dark-slate topography canvas grid provides a clean vector background, ensuring uninterrupted map interaction.
