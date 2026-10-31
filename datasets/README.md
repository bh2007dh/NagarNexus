# NagarNexus Datasets Directory

## Overview

This directory manages structured datasets used by the **NagarNexus – AI-Powered Hyperlocal Urban Intelligence and Prediction Platform**:

- `raw/`: Raw ingested files from external APIs or archival drops.
- `processed/`: Cleaned, imputed, scaled, or encoded datasets produced by the NagarNexus Data Cleaning Engine (`POST /api/analysis/{id}/clean`). Original files are never overwritten.
- `sample/`: Pre-integrated, clearly labeled sample CSV datasets for immediate out-of-the-box exploration, statistical testing, EDA, and ML training.

## Provenance & Transparency Policy

1. **Sample Datasets (`datasets/sample/*.csv`)**:
   - Explicitly labeled as **calibrated synthetic / transformed benchmark datasets** modeled on Indian coastal-urban meteorological and air quality distributions.
   - **Important Disclaimer**: Sample CSV files are synthetic analytical benchmarks created for reproducible testing and demonstration. They are **not** claimed to be official verified station measurements from CPCB or IMD.
2. **Live External APIs**:
   - Weather telemetry fetched via **Open-Meteo** (`https://open-meteo.com/`) carries `source_type="open_meteo"` and `geographical_resolution="grid_cell (~11km)"`.
   - Air quality station data fetched via **OpenAQ** (`https://openaq.org/`) carries `source_type="openaq"` and `geographical_resolution="monitoring_station"`.
   - Geocoding data fetched via **OpenStreetMap Nominatim** (`https://www.openstreetmap.org/`) carries ODbL attribution.

