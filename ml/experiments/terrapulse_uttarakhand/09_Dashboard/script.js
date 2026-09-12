const API_URL = "http://127.0.0.1:5000/predict";

const terrainData = {
  "Almora": { elevation: 1431.83, slope: 22.82 },
  "Bageshwar": { elevation: 2313.36, slope: 27.95 },
  "Chamoli": { elevation: 3582.92, slope: 30.56 },
  "Champawat": { elevation: 1226.25, slope: 24.63 },
  "Dehra Dun": { elevation: 1077.79, slope: 17.60 },
  "Haridwar": { elevation: 297.87, slope: 3.63 },
  "Naini Tal": { elevation: 869.44, slope: 15.64 },
  "Pauri Garhwal": { elevation: 1145.08, slope: 23.01 },
  "Pithoragarh": { elevation: 3316.34, slope: 30.97 },
  "Rudra Prayag": { elevation: 2910.09, slope: 30.97 },
  "Tehri Garhwal": { elevation: 1913.85, slope: 28.40 },
  "Udham Singh Nagar": { elevation: 228.03, slope: 2.44 },
  "Uttarkashi": { elevation: 3255.01, slope: 30.13 }
};

let map = null;
let districtLayers = {};
let currentRisk = "LOW";
let hasPrediction = false;

const riskColors = {
  HIGH: "#ef4444",
  MODERATE: "#f59e0b",
  LOW: "#22c55e",
  NEUTRAL: "#38bdf8"
};


/* ============================================================
   GENERIC HELPERS
============================================================ */

function formatNumber(value, digits = 1) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number.toFixed(digits)
    : "0.0";
}


function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
}


/* ============================================================
   RAINFALL INPUT
============================================================ */

function getRainfallValues() {
  const input =
    document.getElementById("rainfallHistory");

  if (!input) {
    return [];
  }

  return input.value
    .split(",")
    .map(value => Number(value.trim()))
    .filter(value => Number.isFinite(value));
}


/* ============================================================
   RAINFALL FEATURE CALCULATION
============================================================ */

function calculateRainfallFeatures(values) {
  if (!values.length) {
    return {
      rain1d: 0,
      rain3d: 0,
      rain7d: 0,
      rain14d: 0,
      rain30d: 0,
      max3d: 0,
      max7d: 0,
      rainyDays7d: 0,
      ratio1d7d: 0,
      ratio3d7d: 0
    };
  }

  const last = values.length - 1;

  const sumLast = days => {
    const start =
      Math.max(0, values.length - days);

    return values
      .slice(start)
      .reduce((a, b) => a + b, 0);
  };

  const maxRolling = days => {
    if (values.length < days) {
      return Math.max(...values);
    }

    let max = 0;

    for (
      let i = days - 1;
      i < values.length;
      i++
    ) {
      const total = values
        .slice(
          i - days + 1,
          i + 1
        )
        .reduce(
          (a, b) => a + b,
          0
        );

      max = Math.max(max, total);
    }

    return max;
  };

  const rain1d =
    values[last] || 0;

  const rain3d =
    sumLast(3);

  const rain7d =
    sumLast(7);

  const rain14d =
    sumLast(14);

  const rain30d =
    sumLast(30);

  return {
    rain1d,
    rain3d,
    rain7d,
    rain14d,
    rain30d,
    max3d: maxRolling(3),
    max7d: maxRolling(7),

    rainyDays7d:
      values
        .slice(-7)
        .filter(value => value > 1)
        .length,

    ratio1d7d:
      rain7d > 0
        ? rain1d / rain7d
        : 0,

    ratio3d7d:
      rain7d > 0
        ? rain3d / rain7d
        : 0
  };
}


/* ============================================================
   RAINFALL SUMMARY
============================================================ */

function updateRainfallSummary() {
  const values =
    getRainfallValues();

  const total =
    values.reduce(
      (a, b) => a + b,
      0
    );

  const last =
    values.length
      ? values[values.length - 1]
      : 0;

  const rainyDays =
    values.filter(
      value => value > 1
    ).length;

  setText(
    "rainTotal",
    formatNumber(total, 1)
  );

  setText(
    "rainLast",
    formatNumber(last, 1)
  );

  setText(
    "rainDays",
    rainyDays
  );

  setText(
    "chartRainTotal",
    `${formatNumber(total, 1)} mm`
  );

  setText(
    "cumulativeTotal",
    `${formatNumber(total, 1)} mm`
  );

  drawRainfallChart(values);
  drawCumulativeChart(values);

  updateRainfallVisuals(values);
}


/* ============================================================
   RAINFALL BAR CHART
============================================================ */

function drawRainfallChart(values) {
  const chart =
    document.getElementById(
      "rainChart"
    );

  if (!chart) {
    return;
  }

  chart.innerHTML = "";

  if (!values.length) {
    return;
  }

  const max =
    Math.max(...values, 1);

  setText(
    "rainAxisMax",
    Math.ceil(max)
  );

  values.forEach(
    (value, index) => {
      const bar =
        document.createElement(
          "div"
        );

      bar.className =
        "rain-bar";

      const height =
        value > 0
          ? Math.max(
              (value / max) * 100,
              2
            )
          : 0;

      bar.style.height =
        `${height}%`;

      bar.title =
        `Day ${index + 1}: ${formatNumber(value, 1)} mm`;

      chart.appendChild(bar);
    }
  );
}


/* ============================================================
   CUMULATIVE CHART
============================================================ */

function drawCumulativeChart(values) {
  const container =
    document.getElementById(
      "cumulativeChart"
    );

  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!values.length) {
    return;
  }

  let cumulative = 0;

  const data =
    values.map(value => {
      cumulative += value;
      return cumulative;
    });

  const width = 1000;
  const height = 245;
  const paddingX = 18;
  const paddingY = 18;

  const max =
    Math.max(...data, 1);

  const points =
    data.map(
      (value, index) => {

        const x =
          paddingX +
          (
            index /
            Math.max(
              data.length - 1,
              1
            )
          ) *
          (
            width -
            paddingX * 2
          );

        const y =
          height -
          paddingY -
          (
            value / max
          ) *
          (
            height -
            paddingY * 2
          );

        return {
          x,
          y
        };
      }
    );

  const linePoints =
    points
      .map(
        point =>
          `${point.x},${point.y}`
      )
      .join(" ");

  const areaPoints =
    `${paddingX},${height - paddingY} ` +
    `${linePoints} ` +
    `${width - paddingX},${height - paddingY}`;

  const svgNS =
    "http://www.w3.org/2000/svg";

  const svg =
    document.createElementNS(
      svgNS,
      "svg"
    );

  svg.setAttribute(
    "viewBox",
    `0 0 ${width} ${height}`
  );

  svg.classList.add(
    "cumulative-svg"
  );

  const area =
    document.createElementNS(
      svgNS,
      "polygon"
    );

  area.setAttribute(
    "points",
    areaPoints
  );

  area.classList.add(
    "cumulative-area"
  );

  const line =
    document.createElementNS(
      svgNS,
      "polyline"
    );

  line.setAttribute(
    "points",
    linePoints
  );

  line.classList.add(
    "cumulative-line"
  );

  const lastPoint =
    points[points.length - 1];

  const point =
    document.createElementNS(
      svgNS,
      "circle"
    );

  point.setAttribute(
    "cx",
    lastPoint.x
  );

  point.setAttribute(
    "cy",
    lastPoint.y
  );

  point.setAttribute(
    "r",
    "6"
  );

  point.classList.add(
    "cumulative-point"
  );

  const label =
    document.createElementNS(
      svgNS,
      "text"
    );

  label.setAttribute(
    "x",
    Math.min(
      lastPoint.x - 20,
      width - 100
    )
  );

  label.setAttribute(
    "y",
    Math.max(
      lastPoint.y - 12,
      18
    )
  );

  label.setAttribute(
    "fill",
    "#8ea7c5"
  );

  label.setAttribute(
    "font-size",
    "13"
  );

  label.textContent =
    `${formatNumber(
      data[data.length - 1],
      1
    )} mm`;

  svg.appendChild(area);
  svg.appendChild(line);
  svg.appendChild(point);
  svg.appendChild(label);

  container.appendChild(svg);
}


/* ============================================================
   RAINFALL VISUALS
============================================================ */

function updateRainfallVisuals(values) {
  const features =
    calculateRainfallFeatures(
      values
    );

  setText(
    "rain1d",
    formatNumber(
      features.rain1d,
      1
    )
  );

  setText(
    "rain3d",
    formatNumber(
      features.rain3d,
      1
    )
  );

  setText(
    "rain7d",
    formatNumber(
      features.rain7d,
      1
    )
  );

  setText(
    "rain14d",
    formatNumber(
      features.rain14d,
      1
    )
  );

  setText(
    "rain30d",
    formatNumber(
      features.rain30d,
      1
    )
  );

  const maxValue =
    Math.max(
      features.rain1d,
      features.rain3d,
      features.rain7d,
      features.rain14d,
      features.rain30d,
      1
    );

  updateBar(
    "rain1dBar",
    features.rain1d,
    maxValue
  );

  updateBar(
    "rain3dBar",
    features.rain3d,
    maxValue
  );

  updateBar(
    "rain7dBar",
    features.rain7d,
    maxValue
  );

  updateBar(
    "rain14dBar",
    features.rain14d,
    maxValue
  );

  updateBar(
    "rain30dBar",
    features.rain30d,
    maxValue
  );

  updateIndicatorProfile(
    values,
    features
  );
}


/* ============================================================
   GENERIC PROGRESS BAR
============================================================ */

function updateBar(
  id,
  value,
  max
) {
  const element =
    document.getElementById(id);

  if (!element) {
    return;
  }

  const safeValue =
    Number(value) || 0;

  const safeMax =
    Number(max) || 1;

  const width =
    Math.min(
      (
        safeValue /
        safeMax
      ) * 100,
      100
    );

  element.style.width =
    `${width}%`;
}


/* ============================================================
   ENVIRONMENTAL INDICATOR PROFILE
============================================================ */

function updateIndicatorProfile(
  values,
  features
) {
  const maxRain =
    values.length
      ? Math.max(...values)
      : 0;

  const soil =
    Number(
      document.getElementById(
        "soilMoisture"
      )?.value || 0
    );

  const district =
    document.getElementById(
      "district"
    )?.value ||
    "Chamoli";

  const slope =
    terrainData[district]?.slope ||
    0;

  const rainIntensity =
    Math.min(
      maxRain,
      100
    );

  const buildUp =
    features.rain30d > 0
      ? Math.min(
          (
            features.rain30d /
            450
          ) * 100,
          100
        )
      : 0;

  const soilPercent =
    Math.min(
      soil * 100,
      100
    );

  const slopePercent =
    Math.min(
      (slope / 45) * 100,
      100
    );

  updateBar(
    "rainIntensityBar",
    rainIntensity,
    100
  );

  updateBar(
    "soilIndicatorBar",
    soilPercent,
    100
  );

  updateBar(
    "slopeIndicatorBar",
    slopePercent,
    100
  );

  updateBar(
    "buildUpIndicatorBar",
    buildUp,
    100
  );

  setText(
    "rainIntensityLabel",
    getRainIntensityLabel(
      maxRain
    )
  );

  setText(
    "soilIndicatorLabel",
    getSoilLabel(
      soil
    )
  );

  setText(
    "slopeIndicatorLabel",
    getSlopeLabel(
      slope
    )
  );

  setText(
    "buildUpIndicatorLabel",
    getBuildUpLabel(
      features.rain30d
    )
  );
}


/* ============================================================
   LABEL HELPERS
============================================================ */

function getRainIntensityLabel(
  value
) {
  if (value >= 50) {
    return "PEAK ACTIVITY";
  }

  if (value >= 25) {
    return "HIGH ACTIVITY";
  }

  if (value >= 10) {
    return "MODERATE ACTIVITY";
  }

  return "LOW ACTIVITY";
}


function getSoilLabel(value) {
  if (value >= 0.34) {
    return "VERY HIGH";
  }

  if (value >= 0.30) {
    return "ELEVATED";
  }

  if (value >= 0.25) {
    return "MODERATE";
  }

  return "LOW";
}


function getSlopeLabel(value) {
  if (value >= 30) {
    return "STEEP";
  }

  if (value >= 20) {
    return "HIGH";
  }

  if (value >= 10) {
    return "MODERATE";
  }

  return "LOW";
}


function getBuildUpLabel(value) {
  if (value >= 300) {
    return "VERY HIGH";
  }

  if (value >= 200) {
    return "HIGH";
  }

  if (value >= 100) {
    return "MODERATE";
  }

  return "LOW";
}


/* ============================================================
   TERRAIN
============================================================ */

function updateTerrain(district) {
  const terrain =
    terrainData[district];

  if (!terrain) {
    return;
  }

  setText(
    "elevation",
    formatNumber(
      terrain.elevation,
      2
    )
  );

  setText(
    "slope",
    formatNumber(
      terrain.slope,
      2
    )
  );

  const soil =
    Number(
      document.getElementById(
        "soilMoisture"
      )?.value || 0
    );

  const rainfall =
    getRainfallValues();

  const total =
    rainfall.reduce(
      (a, b) => a + b,
      0
    );

  setText(
    "soilDisplay",
    formatNumber(
      soil,
      3
    )
  );

  setText(
    "rainDisplay",
    formatNumber(
      total,
      1
    )
  );

  updateMapSelection(
    district
  );

  updateIndicatorProfile(
    rainfall,
    calculateRainfallFeatures(
      rainfall
    )
  );
}


/* ============================================================
   MAP
============================================================ */

function setMapLayerStyle(
  layer,
  risk = "NEUTRAL",
  selected = false
) {
  if (!layer) {
    return;
  }

  const color =
    riskColors[risk] ||
    riskColors.NEUTRAL;

  layer.setStyle({

    color:
      selected
        ? "#ffffff"
        : color,

    weight:
      selected
        ? 3
        : 1.5,

    fillColor:
      color,

    fillOpacity:
      selected
        ? 0.45
        : 0.24
  });
}


function resetMapLayers() {
  Object.keys(
    districtLayers
  ).forEach(
    district => {

      const layer =
        districtLayers[district];

      const risk =
        layer._risk ||
        "NEUTRAL";

      setMapLayerStyle(
        layer,
        risk,
        false
      );
    }
  );
}


function updateMapSelection(
  district
) {
  resetMapLayers();

  const layer =
    districtLayers[district];

  if (!layer) {
    return;
  }

  const risk =
    layer._risk ||
    "NEUTRAL";

  setMapLayerStyle(
    layer,
    risk,
    true
  );

  if (map) {

    map.panTo(
      layer
        .getBounds()
        .getCenter(),
      {
        animate: true,
        duration: 0.5
      }
    );
  }
}


function updateMapRisk(
  district,
  risk
) {
  const layer =
    districtLayers[district];

  if (!layer) {
    return;
  }

  layer._risk =
    risk;

  setMapLayerStyle(
    layer,
    risk,
    true
  );
}


function initializeMap() {

  const mapElement =
    document.getElementById(
      "uttarakhandMap"
    );

  if (
    !mapElement ||
    typeof L === "undefined"
  ) {
    return;
  }

  map =
    L.map(
      "uttarakhandMap",
      {
        zoomControl: true,
        attributionControl: true
      }
    );

  L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 12,
      attribution:
        "&copy; OpenStreetMap contributors"
    }
  ).addTo(map);


  fetch(
    "Uttarakhand_Districts.geojson"
  )
    .then(response => {

      if (!response.ok) {
        throw new Error(
          "GeoJSON file could not be loaded"
        );
      }

      return response.json();
    })

    .then(geojson => {

      const geoLayer =
        L.geoJSON(
          geojson,
          {

            style: () => ({

              color:
                riskColors.NEUTRAL,

              weight:
                1.5,

              fillColor:
                riskColors.NEUTRAL,

              fillOpacity:
                0.24

            }),


            onEachFeature:
              (
                feature,
                layer
              ) => {

                const district =
                  feature
                    .properties
                    ?.ADM2_NAME ||
                  "Unknown";

                districtLayers[
                  district
                ] = layer;

                layer._risk =
                  "NEUTRAL";


                layer.bindTooltip(
                  district,
                  {
                    sticky: true,
                    direction: "top"
                  }
                );


                layer.on({

                  mouseover: () => {

                    const risk =
                      layer._risk ||
                      "NEUTRAL";

                    layer.setStyle({

                      weight:
                        3,

                      color:
                        "#ffffff",

                      fillColor:
                        riskColors[
                          risk
                        ] ||
                        riskColors.NEUTRAL,

                      fillOpacity:
                        0.50

                    });

                  },


                  mouseout: () => {

                    const selected =
                      document.getElementById(
                        "district"
                      )?.value ===
                      district;

                    setMapLayerStyle(
                      layer,
                      layer._risk ||
                        "NEUTRAL",
                      selected
                    );

                  },


                  click: () => {

                    const districtSelect =
                      document.getElementById(
                        "district"
                      );

                    if (
                      districtSelect
                    ) {

                      districtSelect.value =
                        district;

                      districtSelect.dispatchEvent(
                        new Event(
                          "change"
                        )
                      );

                    }

                  }

                });

              }

          }
        ).addTo(map);


      map.fitBounds(
        geoLayer.getBounds(),
        {
          padding: [
            20,
            20
          ]
        }
      );


      setText(
        "mapStatus",
        `${Object.keys(
          districtLayers
        ).length} districts loaded`
      );


      const selectedDistrict =
        document.getElementById(
          "district"
        )?.value;


      if (
        selectedDistrict
      ) {

        updateMapSelection(
          selectedDistrict
        );

      }


      addMapLegend();

    })

    .catch(error => {

      console.error(
        "Map error:",
        error
      );

      setText(
        "mapStatus",
        "Map data unavailable"
      );

    });
}


/* ============================================================
   MAP LEGEND
============================================================ */

function addMapLegend() {

  if (
    !map ||
    document.querySelector(
      ".map-risk-legend"
    )
  ) {
    return;
  }

  const legend =
    document.createElement(
      "div"
    );

  legend.className =
    "map-risk-legend";

  legend.innerHTML = `
    <div class="legend-title">
      Risk Status
    </div>

    <div class="legend-item">
      <span class="legend-dot high"></span>
      High
    </div>

    <div class="legend-item">
      <span class="legend-dot moderate"></span>
      Moderate
    </div>

    <div class="legend-item">
      <span class="legend-dot low"></span>
      Low
    </div>

    <div class="legend-item">
      <span class="legend-dot neutral"></span>
      Not analyzed
    </div>
  `;

  map
    .getContainer()
    .appendChild(
      legend
    );
}


/* ============================================================
   FLOOD PROBABILITY GAUGE
============================================================ */

function updateRiskGauge(
  probability,
  risk
) {

  const safeProbability =
    Number.isFinite(
      Number(probability)
    )
      ? Number(probability)
      : 0;

  const percent =
    Math.max(
      0,
      Math.min(
        safeProbability * 100,
        100
      )
    );


  const fill =
    document.getElementById(
      "gaugeFill"
    );

  const marker =
    document.getElementById(
      "gaugeMarker"
    );


  if (fill) {

    fill.style.width =
      `${percent}%`;

  }


  if (marker) {

    marker.style.left =
      `${percent}%`;

  }


  setText(
    "gaugeProbability",
    `${formatNumber(
      percent,
      2
    )}%`
  );


  setText(
    "gaugeRisk",
    `${risk} RISK`
  );


  const riskElement =
    document.getElementById(
      "riskLevel"
    );

  const gaugeRisk =
    document.getElementById(
      "gaugeRisk"
    );


  const color =
    riskColors[risk] ||
    riskColors.NEUTRAL;


  if (gaugeRisk) {

    gaugeRisk.style.color =
      color;

  }


  if (riskElement) {

    riskElement.style.color =
      color;

  }


  if (marker) {

    marker.style.borderColor =
      color;

    marker.style.boxShadow =
      `0 0 18px ${color}66`;

  }
}


/* ============================================================
   NEW — ENVIRONMENTAL CONTEXT
============================================================ */

function updateEnvironmentalContext(data) {

  const environment =
    data?.environment || {};

  const river =
    environment.river || {};

  const weather =
    environment.weather || {};

  const terrain =
    environment.terrain || {};


  /* ----------------------------------------------------------
     RIVER
  ---------------------------------------------------------- */

  setText(
    "riverWaterLevel",
    Number.isFinite(
      Number(
        river.water_level_m
      )
    )
      ? formatNumber(
          river.water_level_m,
          2
        )
      : "—"
  );


  setText(
    "riverDangerLevel",
    Number.isFinite(
      Number(
        river.danger_level_m
      )
    )
      ? formatNumber(
          river.danger_level_m,
          2
        )
      : "—"
  );


  const riverRatio =
    Number(
      river.level_ratio_to_danger
    );


  setText(
    "riverLevelRatio",
    Number.isFinite(
      riverRatio
    )
      ? formatNumber(
          riverRatio * 100,
          1
        )
      : "—"
  );


  const riseRate =
    Number(
      river.rise_rate_m_per_hr
    );


  setText(
    "riverRiseRate",
    Number.isFinite(
      riseRate
    )
      ? formatNumber(
          riseRate,
          3
        )
      : "—"
  );


  /* ----------------------------------------------------------
     RIVER TREND
  ---------------------------------------------------------- */

  let riverTrend =
    "STABLE";


  if (
    Number.isFinite(
      riseRate
    )
  ) {

    if (riseRate >= 0.50) {

      riverTrend =
        "RISING FAST";

    } else if (
      riseRate >= 0.15
    ) {

      riverTrend =
        "RISING";

    } else if (
      riseRate > 0
    ) {

      riverTrend =
        "SLIGHT RISE";

    }

  }


  setText(
    "riverTrend",
    riverTrend
  );


  /* ----------------------------------------------------------
     WEATHER
  ---------------------------------------------------------- */

  setText(
    "weatherCondition",
    weather.condition ||
      "—"
  );


  setText(
    "weatherTemperature",
    Number.isFinite(
      Number(
        weather.temperature_c
      )
    )
      ? formatNumber(
          weather.temperature_c,
          1
        )
      : "—"
  );


  setText(
    "weatherHumidity",
    Number.isFinite(
      Number(
        weather.relative_humidity_pct
      )
    )
      ? formatNumber(
          weather.relative_humidity_pct,
          1
        )
      : "—"
  );


  setText(
    "weatherWind",
    Number.isFinite(
      Number(
        weather.wind_speed_kmh
      )
    )
      ? formatNumber(
          weather.wind_speed_kmh,
          1
        )
      : "—"
  );


  setText(
    "weatherPressure",
    Number.isFinite(
      Number(
        weather.atmospheric_pressure_hpa
      )
    )
      ? formatNumber(
          weather.atmospheric_pressure_hpa,
          1
        )
      : "—"
  );


  /* ----------------------------------------------------------
     SLOPE RISK
  ---------------------------------------------------------- */

  setText(
    "slopeRisk",
    terrain.slope_risk ||
      "—"
  );


  /* ----------------------------------------------------------
     SLOPE INDICATOR
  ---------------------------------------------------------- */

  if (
    terrain.mean_slope_degree !== undefined
  ) {

    setText(
      "slope",
      formatNumber(
        terrain.mean_slope_degree,
        2
      )
    );

  }

}


/* ============================================================
   MODEL EXPLANATION
============================================================ */

function updateRiskExplanation(
  data
) {

  const district =
    data.district ||
    document.getElementById(
      "district"
    )?.value ||
    "Unknown";


  const probability =
    Number(
      data.probability || 0
    );


  const risk =
    data.risk_level ||
    "LOW";


  const values =
    getRainfallValues();


  const features =
    calculateRainfallFeatures(
      values
    );


  const soil =
    Number(
      document.getElementById(
        "soilMoisture"
      )?.value || 0
    );


  const slope =
    terrainData[district]?.slope ||
    0;


  setText(
    "explainRain30",
    `${formatNumber(
      features.rain30d,
      1
    )} mm`
  );


  setText(
    "explainRain1",
    `${formatNumber(
      features.rain1d,
      1
    )} mm`
  );


  setText(
    "explainSoil",
    formatNumber(
      soil,
      3
    )
  );


  setText(
    "explainSlope",
    `${formatNumber(
      slope,
      2
    )}°`
  );


  let explanation =
    "";


  const percent =
    formatNumber(
      probability * 100,
      2
    );


  if (
    risk === "HIGH"
  ) {

    explanation =
      `${district} is showing a high modeled flood probability of ${percent}%. Recent rainfall, accumulated rainfall and environmental conditions are contributing to the elevated risk assessment.`;

  } else if (
    risk === "MODERATE"
  ) {

    explanation =
      `${district} is showing a moderate modeled flood probability of ${percent}%. The current rainfall and environmental conditions warrant continued monitoring.`;

  } else {

    explanation =
      `${district} is currently showing a low modeled flood probability of ${percent}%. Continue monitoring rainfall and soil conditions as they evolve.`;

  }


  setText(
    "riskExplanation",
    explanation
  );


  const warningPanel =
    document.getElementById(
      "warningPanel"
    );


  if (warningPanel) {

    warningPanel.classList.remove(
      "high",
      "moderate",
      "low"
    );


    if (
      hasPrediction
    ) {

      warningPanel.classList.add(
        risk.toLowerCase()
      );

    }

  }


  setText(
    "warningTitle",
    risk === "HIGH"
      ? "Early Warning Recommended"
      : risk === "MODERATE"
        ? "Continue Monitoring"
        : "Low Current Risk"
  );


  setText(
    "warningText",
    data.warning ||
      (
        risk === "HIGH"
          ? "Flash flood risk detected. Early warning recommended."
          : risk === "MODERATE"
            ? "Conditions require continued observation."
            : "No elevated flash flood signal detected at the current threshold."
      )
  );


  setText(
    "warningDistrict",
    district
  );


  setText(
    "warningRisk",
    risk
  );

}


/* ============================================================
   MAIN RISK DISPLAY
============================================================ */

function updateRiskDisplay(
  data
) {

  const probability =
    Number(
      data.probability || 0
    );


  const risk =
    data.risk_level ||
    "LOW";


  const district =
    data.district ||
    document.getElementById(
      "district"
    )?.value ||
    "Unknown";


  currentRisk =
    risk;


  hasPrediction =
    true;


  setText(
    "probability",
    `${formatNumber(
      probability * 100,
      2
    )}%`
  );


  setText(
    "riskLevel",
    risk
  );


  setText(
    "warning",
    data.warning ||
      "Analysis completed."
  );


  setText(
    "thresholdValue",
    `${formatNumber(
      (data.threshold || 0.3) * 100,
      0
    )}%`
  );


  setText(
    "modelName",
    data.model ||
      "Ensemble"
  );


  setText(
    "leadTarget",
    data.lead_target ||
      "Up to 3 Days"
  );


  const riskElement =
    document.getElementById(
      "riskLevel"
    );


  if (riskElement) {

    riskElement.classList.remove(
      "high",
      "moderate",
      "low"
    );


    riskElement.classList.add(
      risk.toLowerCase()
    );

  }


  const riskCard =
    document.getElementById(
      "riskDisplay"
    );


  if (riskCard) {

    riskCard.classList.remove(
      "high",
      "moderate",
      "low"
    );


    riskCard.classList.add(
      risk.toLowerCase()
    );

  }


  updateRiskGauge(
    probability,
    risk
  );


  updateMapRisk(
    district,
    risk
  );


  updateRiskExplanation(
    data
  );


  updateEnvironmentalContext(
    data
  );

}


/* ============================================================
   RESET DASHBOARD
============================================================ */

function resetDashboardState() {

  currentRisk =
    "LOW";

  hasPrediction =
    false;


  const riskElement =
    document.getElementById(
      "riskLevel"
    );


  const riskCard =
    document.getElementById(
      "riskDisplay"
    );


  const warningPanel =
    document.getElementById(
      "warningPanel"
    );


  [
    riskElement,
    riskCard,
    warningPanel
  ].forEach(
    element => {

      if (element) {

        element.classList.remove(
          "high",
          "moderate",
          "low"
        );

      }

    }
  );


  setText(
    "probability",
    "—"
  );


  setText(
    "riskLevel",
    "AWAITING ANALYSIS"
  );


  setText(
    "warning",
    "Enter conditions and run the analysis to generate a flood-risk assessment."
  );


  setText(
    "thresholdValue",
    "30%"
  );


  setText(
    "modelName",
    "Ensemble"
  );


  setText(
    "leadTarget",
    "Up to 3 Days"
  );


  setText(
    "gaugeProbability",
    "—"
  );


  setText(
    "gaugeRisk",
    "AWAITING ANALYSIS"
  );


  const fill =
    document.getElementById(
      "gaugeFill"
    );


  const marker =
    document.getElementById(
      "gaugeMarker"
    );


  if (fill) {

    fill.style.width =
      "0%";

  }


  if (marker) {

    marker.style.left =
      "0%";

    marker.style.borderColor =
      riskColors.NEUTRAL;

    marker.style.boxShadow =
      "0 0 18px #38bdf866";

  }


  const gaugeRisk =
    document.getElementById(
      "gaugeRisk"
    );


  if (gaugeRisk) {

    gaugeRisk.style.color =
      riskColors.NEUTRAL;

  }


  if (riskElement) {

    riskElement.style.color =
      riskColors.NEUTRAL;

  }


  setText(
    "warningTitle",
    "Awaiting Analysis"
  );


  setText(
    "warningText",
    "No prediction has been generated yet. Enter the environmental conditions and run the analysis."
  );


  setText(
    "warningDistrict",
    document.getElementById(
      "district"
    )?.value ||
      "—"
  );


  setText(
    "warningRisk",
    "NOT ANALYZED"
  );


  setText(
    "riskExplanation",
    "The dashboard is ready. Run the ensemble model to generate the current district-level flood-risk assessment."
  );


  // ==========================================================
  // NEW ENVIRONMENT RESET
  // ==========================================================

  setText(
    "riverWaterLevel",
    "—"
  );

  setText(
    "riverDangerLevel",
    "—"
  );

  setText(
    "riverLevelRatio",
    "—"
  );

  setText(
    "riverRiseRate",
    "—"
  );

  setText(
    "riverTrend",
    "—"
  );

  setText(
    "weatherCondition",
    "—"
  );

  setText(
    "weatherTemperature",
    "—"
  );

  setText(
    "weatherHumidity",
    "—"
  );

  setText(
    "weatherWind",
    "—"
  );

  setText(
    "weatherPressure",
    "—"
  );

  setText(
    "slopeRisk",
    "—"
  );

}


/* ============================================================
   ANALYZE RISK
============================================================ */

async function analyzeRisk() {

  const districtElement =
    document.getElementById(
      "district"
    );


  const soilElement =
    document.getElementById(
      "soilMoisture"
    );


  const button =
    document.getElementById(
      "analyzeBtn"
    );


  const district =
    districtElement?.value;


  const soil =
    Number(
      soilElement?.value
    );


  const rainfall =
    getRainfallValues();


  const errorBox =
    document.getElementById(
      "errorBox"
    );


  if (errorBox) {

    errorBox.style.display =
      "none";

    errorBox.textContent =
      "";

  }


  /* ----------------------------------------------------------
     VALIDATE DISTRICT
  ---------------------------------------------------------- */

  if (!district) {

    showError(
      "Please select a district."
    );

    return;

  }


  /* ----------------------------------------------------------
     VALIDATE SOIL
  ---------------------------------------------------------- */

  if (
    !Number.isFinite(soil) ||
    soil < 0 ||
    soil > 1
  ) {

    showError(
      "Soil moisture must be between 0 and 1."
    );

    return;

  }


  /* ----------------------------------------------------------
     VALIDATE RAINFALL
  ---------------------------------------------------------- */

  if (
    rainfall.length !== 30
  ) {

    showError(
      `Please enter exactly 30 rainfall values. Current values: ${rainfall.length}.`
    );

    return;

  }


  if (
    rainfall.some(
      value => value < 0
    )
  ) {

    showError(
      "Rainfall values cannot be negative."
    );

    return;

  }


  /* ----------------------------------------------------------
     BUTTON STATE
  ---------------------------------------------------------- */

  if (button) {

    button.disabled =
      true;

    button.innerHTML =
      "ANALYZING RISK <span>...</span>";

  }


  try {

    const response =
      await fetch(
        API_URL,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({

              district:
                district,

              rainfall_history:
                rainfall,

              soil_moisture:
                soil

            })

        }
      );


    const data =
      await response.json();


    if (!response.ok) {

      throw new Error(
        data.error ||
        data.details ||
        `Backend returned ${response.status}`
      );

    }


    /* --------------------------------------------------------
       UPDATE DASHBOARD
    -------------------------------------------------------- */

    updateRiskDisplay(
      data
    );


    updateRainfallSummary();


    updateTerrain(
      district
    );


  } catch (error) {

    console.error(
      "Prediction request error:",
      error
    );

    showError(
      `Prediction failed: ${error.message}`
    );

  } finally {

    if (button) {

      button.disabled =
        false;

      button.innerHTML =
        'ANALYZE FLOOD RISK <span>→</span>';

    }

  }

}


/* ============================================================
   ERROR DISPLAY
============================================================ */

function showError(
  message
) {

  const errorBox =
    document.getElementById(
      "errorBox"
    );


  if (errorBox) {

    errorBox.textContent =
      message;

    errorBox.style.display =
      "block";

    return;

  }


  alert(message);
}


/* ============================================================
   DASHBOARD INITIALIZATION
============================================================ */

function initializeDashboard() {

  const district =
    document.getElementById(
      "district"
    );


  const soil =
    document.getElementById(
      "soilMoisture"
    );


  const rainfall =
    document.getElementById(
      "rainfallHistory"
    );


  const analyzeButton =
    document.getElementById(
      "analyzeBtn"
    );


  /* ----------------------------------------------------------
     DISTRICT CHANGE
  ---------------------------------------------------------- */

  if (district) {

    district.addEventListener(
      "change",
      () => {

        hasPrediction =
          false;

        currentRisk =
          "LOW";

        resetDashboardState();

        updateTerrain(
          district.value
        );

        updateRainfallSummary();

      }
    );

  }


  /* ----------------------------------------------------------
     SOIL CHANGE
  ---------------------------------------------------------- */

  if (soil) {

    soil.addEventListener(
      "input",
      () => {

        updateRainfallSummary();

        const selectedDistrict =
          district?.value ||
          "Chamoli";

        updateTerrain(
          selectedDistrict
        );

        if (hasPrediction) {

          resetDashboardState();

        }

      }
    );

  }


  /* ----------------------------------------------------------
     RAINFALL CHANGE
  ---------------------------------------------------------- */

  if (rainfall) {

    rainfall.addEventListener(
      "input",
      () => {

        updateRainfallSummary();

        if (hasPrediction) {

          resetDashboardState();

        }

      }
    );

  }


  /* ----------------------------------------------------------
     ANALYZE BUTTON
  ---------------------------------------------------------- */

  if (analyzeButton) {

    analyzeButton.addEventListener(
      "click",
      analyzeRisk
    );

  }


  /* ----------------------------------------------------------
     INITIAL STATE
  ---------------------------------------------------------- */

  resetDashboardState();

  updateRainfallSummary();


  const selectedDistrict =
    district?.value ||
    "Chamoli";


  updateTerrain(
    selectedDistrict
  );


  initializeMap();

}


/* ============================================================
   DOM READY
============================================================ */

document.addEventListener(
  "DOMContentLoaded",
  initializeDashboard
);