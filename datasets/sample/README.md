# Sample Datasets Provenance & Data Dictionary

> **DATA PROVENANCE NOTICE**: All five CSV files in `datasets/sample/` are **synthetic & transformed benchmark datasets** designed for reproducible testing of the NagarNexus Data Cleaning, EDA, Statistical Analysis, Machine Learning, and Urban Risk Detection engines. They are **not** raw official government measurements and must not be cited as verified historical Chennai or Indian municipal station records.

## Included Sample Files

1. `sample_weather_observations.csv`
   - **Data Nature**: Synthetic benchmark dataset with intentional missing values and outliers for testing data cleaning and time-series regression.
   - **Columns**: `observation_date`, `locality_code`, `zone_type`, `temperature_c`, `humidity_pct`, `wind_speed_kmh`, `surface_pressure_hpa`, `heat_index_c`.
   - **Units**: `°C`, `%`, `km/h`, `hPa`.

2. `sample_air_quality_observations.csv`
   - **Data Nature**: Synthetic benchmark dataset representing multi-pollutant urban air quality telemetry.
   - **Columns**: `observation_date`, `locality_code`, `traffic_density_index`, `pm25`, `pm10`, `no2`, `o3`, `co_mg_m3`, `aqi`, `air_quality_category`.
   - **Units**: `µg/m³` (`pm25`, `pm10`, `no2`, `o3`), `mg/m³` (`co_mg_m3`), dimensionless index (`aqi`).

3. `sample_rainfall_observations.csv`
   - **Data Nature**: Synthetic monsoon & pre-monsoon hydrological dataset with drainage saturation proxies and waterlogging risk labels.
   - **Columns**: `observation_date`, `locality_code`, `elevation_m`, `rainfall_mm`, `soil_moisture_pct`, `drainage_capacity_mm_hr`, `impervious_surface_pct`, `waterlogging_risk_class`.
   - **Units**: `m`, `mm`, `%`, `mm/hr`.

4. `sample_location_metadata.csv`
   - **Data Nature**: Transformed geographical reference catalog of urban monitoring zones with explicit `geographical_resolution` labels.
   - **Columns**: `locality_code`, `name`, `city`, `state`, `latitude`, `longitude`, `geographical_resolution`, `elevation_m`, `zone_type`.

5. `sample_environmental_indicators.csv`
   - **Data Nature**: Unified multi-indicator urban environmental dataset combining weather, air quality, and hydrological features for multivariate clustering, anomaly detection, and predictive modeling.
   - **Columns**: `observation_date`, `locality_code`, `zone_type`, `temperature_c`, `rainfall_mm`, `humidity_pct`, `wind_speed_kmh`, `pm25`, `pm10`, `no2`, `aqi`, `waterlogging_risk_score`, `risk_category`.

