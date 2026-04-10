# Datacenters_Final_Solar_Suitability
Team: Vanessa Thorsten, Chenchen Yuan

## Offline Preprocessing Scripts
These scripts deal with the geospatial analysis before the data is moved to Google Cloud.
- `test_boulder_terrain.py` ensures that the terrain features are computed correctly
- `make_tiles.py` divides Boulder County into a grid of 128 4km by 4km tiles
- `aggregate_solar.py` processes historical solar radiation data from NSRDB to make a lookup table of solar averages
- `derive_terrain_features.py` gets avergae elevation, slope, aspect, ruggedness from NASA DEMs for each tile
- `compute_suitability.py` merges terrain and solar data to get final suitability score from 0 to 100
- `plot_suitability.py` creates a map (suitability_map.png) to visualize the solar suitability results

## API 
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
### 3. Use the API 
