# Datacenters_Final_Solar_Suitability
Team: Vanessa Thorsten, Chenchen Yuan

The goal of this project was to build a cloud-based service that takes a latitude and longitude for a location within Boulder County, Colorado and returns a terrain-aware solar suitability score for that location. Traditionally, finding the best locations for solar-panel systems required users to manually interpret raw geospatial and weather data. Our service aimed to automate this process by combining these data into a single interpretable score that indicates the potential suitability of a location for solar development. 

Project Architecture Overview

The workflow consists of two stages:

Offline preprocessing

DEM terrain features extracted
NSRDB solar radiation aggregated
Boulder County divided into 4 km × 4 km tiles (based on the available data)
Suitability score computed per tile
Results exported as GeoJSON + Parquet
Data loaded into PostgreSQL (Cloud SQL + PostGIS)

Online query service

FastAPI container deployed on Cloud Run
Queries Cloud SQL using spatial lookup
Returns suitability score and predictors

## Offline Preprocessing Scripts
These scripts deal with the geospatial analysis before the data is moved to Google Cloud.
- `test_boulder_terrain.py` ensures that the terrain features are computed correctly
- `make_tiles.py` divides Boulder County into a grid of 128 4km by 4km tiles
- `aggregate_solar.py` processes historical solar radiation data from NSRDB to make a lookup table of solar averages
- `derive_terrain_features.py` gets avergae elevation, slope, aspect, ruggedness from NASA DEMs for each tile
- `compute_suitability.py` merges terrain and solar data to get final suitability score from 0 to 100
- `plot_suitability.py` creates a map (suitability_map.png) to visualize the solar suitability results

## API 
- `/health`
    - Checks service + database connectivity
- `/tiles` 
   - Inputs:
   - Output: JSON?
- `/tiles/top` gets top X tiles by suitability scores
   - Inputs: limit (top X tiles, int)
   - Output: JSON?
- `/tiles/within_bbox` gets tiles within specified boundary box
   - Inputs: xmin (x minimum point, int), ymin (y minimum point, int), xmax (x maximum point, int), ymax (y maximum point, int)
   - Output: JSON?
- `/tiles/{tile_id}` gets that specific tile
   - Inputs: tile_id (tile ID, string)
   - Output: JSON?
- `/score` gets the solar suitability score.
   - Inputs: lat (latitude, int), lon (longitude, int)
   - Output: JSON with suitability score and score breakdown
- `/score_plot` gets a mapping of the solar suitability score.
   - Inputs: lat (latitude, int), lon (longitude, int)
   - Output: image with suitability score on the geographic location and coloring based on the strength of the solar suitability score

## How to Run Locally
### 1. Preprocessing
1. Run `python make_tiles.py` to create `boulder_grid.geojson`.
2. Run `python aggregate_solar.py` to create `solar_averages.csv`
3. Run `python derive_terrain_features.py` to get `terrain_features.csv`
4. Run `python compute_suitability.py` to create `boulder_tiles.parquet`
### 2. Deployment
1. Make sure requirements are met: `pip install -r requirements.txt `
2. Create containers: `docker run -d --name solar-postgis -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=solar -p 5432:5432 postgis/postgis:15-3.4 `
3. Start the existing container: `docker start solar-postgis`
4. Verify it’s running: `docker ps`
5. Run schema: `Get-Content database/schema.sql | docker exec -i solar-postgis psql -U postgres -d solar `
6. Run:
   - `python database/load_tiles.py`
   - `python database/load_boundary.py`
   - `uvicorn api.main:app --reload `
7. Go to `http://127.0.0.1:8000/docs`

Example:

/score?lat=40.015&lon=-105.27

Returns:

tile_id
mean_elevation
mean_slope
mean_aspect
mean_ghi_proxy
aspect_score
slope_score
solar_score
rugged_penalty
suitability_score

Example:

/score_plot?lat=40.015&lon=-105.27

Returns map visualization highlighting selected tile

## How to Run on Cloud Deployment (Google Cloud Run)

The API is deployed using:

Cloud Build
Artifact Registry
Cloud Run
Cloud SQL (PostgreSQL + PostGIS)

Deploy container:

gcloud builds submit --config cloudbuild.yaml .

Deploy service:

gcloud run deploy solar-api-demo \
  --image us-central1-docker.pkg.dev/solar-suitability-demo/solar-images/solar-cloud \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances solar-suitability-demo:us-central1:solar-postgis-cloud \
  --env-vars-file cloud/cloudrun.env
Example Live Deployment

Service URL:

https://solar-api-demo-759546826359.us-central1.run.app

Example query:

/score?lat=39.97&lon=-105.06
Data Sources

Terrain:

NASA DEM datasets

Solar radiation:

NSRDB (NREL)

Notes on Architecture Decisions

Suitability scores are precomputed offline and stored in PostGIS to enable fast lookup performance during API requests. The deployed service performs read-only spatial queries and does not persist user requests, allowing the system to remain lightweight and stateless.
