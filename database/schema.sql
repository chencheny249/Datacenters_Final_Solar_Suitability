-- schema.sql
-- Solar suitability service: Boulder County tile database schema
-- https://github.com/chencheny249/Datacenters_Final_Solar_Suitability/tree/main#
-- Data file: processed/boulder_tiles.parquet
-- This schema provides types for the variables, checks whether the values are 
-- within the expected ranges based on the data-quality constraints, provides 
-- notes for each column by explaining the PostGIS-compatible metadata.
-- Notes:
--   - geometry in parquet is stored as WKB bytes
--   - database geometry is stored as PostGIS geometry(Polygon, 4326)
--   - all columns are NOT NULL based on current dataset inspection
-- Also added boundary for Boulder County for checks.

CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS solar_tiles CASCADE;

CREATE TABLE solar_tiles (
    tile_id TEXT PRIMARY KEY,

    geometry geometry(Polygon, 4326) NOT NULL,

    mean_elevation DOUBLE PRECISION NOT NULL,
    std_elevation DOUBLE PRECISION NOT NULL,
    mean_slope DOUBLE PRECISION NOT NULL,
    std_slope DOUBLE PRECISION NOT NULL,
    mean_aspect DOUBLE PRECISION NOT NULL,
    max_slope DOUBLE PRECISION NOT NULL,

    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m INTEGER NOT NULL,

    mean_dni DOUBLE PRECISION NOT NULL,
    mean_dhi DOUBLE PRECISION NOT NULL,
    mean_ghi_proxy DOUBLE PRECISION NOT NULL,
    mean_temp DOUBLE PRECISION NOT NULL,

    aspect_score DOUBLE PRECISION NOT NULL,
    slope_score DOUBLE PRECISION NOT NULL,
    solar_score DOUBLE PRECISION NOT NULL,
    rugged_penalty INTEGER NOT NULL,
    suitability_score DOUBLE PRECISION NOT NULL,

    CONSTRAINT chk_geometry_valid
        CHECK (ST_IsValid(geometry)),

    CONSTRAINT chk_geometry_type
        CHECK (GeometryType(geometry) IN ('POLYGON', 'ST_Polygon')),

    CONSTRAINT chk_latitude_range
        CHECK (latitude >= -90 AND latitude <= 90),

    CONSTRAINT chk_longitude_range
        CHECK (longitude >= -180 AND longitude <= 180),

    CONSTRAINT chk_aspect_score_range
        CHECK (aspect_score >= 0 AND aspect_score <= 1),

    CONSTRAINT chk_slope_score_range
        CHECK (slope_score >= 0 AND slope_score <= 1),

    CONSTRAINT chk_solar_score_range
        CHECK (solar_score >= 0 AND solar_score <= 1),

    CONSTRAINT chk_suitability_score_range
        CHECK (suitability_score >= 0 AND suitability_score <= 100),

    CONSTRAINT chk_nonnegative_std_elevation
        CHECK (std_elevation >= 0),

    CONSTRAINT chk_nonnegative_mean_slope
        CHECK (mean_slope >= 0),

    CONSTRAINT chk_nonnegative_std_slope
        CHECK (std_slope >= 0),

    CONSTRAINT chk_nonnegative_max_slope
        CHECK (max_slope >= 0)
);

CREATE INDEX idx_solar_tiles_geometry_gist
    ON solar_tiles
    USING GIST (geometry);

CREATE INDEX idx_solar_tiles_suitability_score
    ON solar_tiles (suitability_score DESC);

CREATE INDEX idx_solar_tiles_lat_lon
    ON solar_tiles (latitude, longitude);

COMMENT ON TABLE solar_tiles IS
'Boulder County solar suitability tiles loaded from boulder_tiles.parquet.';

COMMENT ON COLUMN solar_tiles.tile_id IS
'Unique tile identifier from source parquet file, e.g. TILE_032.';

COMMENT ON COLUMN solar_tiles.geometry IS
'Tile polygon in EPSG:4326. Source parquet stores geometry as WKB bytes.';

COMMENT ON COLUMN solar_tiles.mean_elevation IS
'Mean elevation across the tile. Units assumed to match source raster processing pipeline.';

COMMENT ON COLUMN solar_tiles.std_elevation IS
'Standard deviation of elevation across the tile.';

COMMENT ON COLUMN solar_tiles.mean_slope IS
'Mean slope across the tile.';

COMMENT ON COLUMN solar_tiles.std_slope IS
'Standard deviation of slope across the tile.';

COMMENT ON COLUMN solar_tiles.mean_aspect IS
'Mean aspect across the tile.';

COMMENT ON COLUMN solar_tiles.max_slope IS
'Maximum slope across the tile.';

COMMENT ON COLUMN solar_tiles.latitude IS
'Representative tile latitude from source dataset.';

COMMENT ON COLUMN solar_tiles.longitude IS
'Representative tile longitude from source dataset.';

COMMENT ON COLUMN solar_tiles.elevation_m IS
'Representative elevation in meters from source dataset.';

COMMENT ON COLUMN solar_tiles.mean_dni IS
'Mean direct normal irradiance feature from source dataset.';

COMMENT ON COLUMN solar_tiles.mean_dhi IS
'Mean diffuse horizontal irradiance feature from source dataset.';

COMMENT ON COLUMN solar_tiles.mean_ghi_proxy IS
'Mean GHI proxy feature from source dataset.';

COMMENT ON COLUMN solar_tiles.mean_temp IS
'Mean temperature feature from source dataset.';

COMMENT ON COLUMN solar_tiles.aspect_score IS
'Normalized aspect-based component score. Expected range 0 to 1.';

COMMENT ON COLUMN solar_tiles.slope_score IS
'Normalized slope-based component score. Expected range 0 to 1.';

COMMENT ON COLUMN solar_tiles.solar_score IS
'Normalized solar resource component score. Expected range 0 to 1.';

COMMENT ON COLUMN solar_tiles.rugged_penalty IS
'Penalty term applied for rugged terrain in source scoring pipeline.';

COMMENT ON COLUMN solar_tiles.suitability_score IS
'Final composite solar suitability score. Observed current range approximately 5 to 96, constrained to 0 to 100.';

-- Boulder County boundary table

DROP TABLE IF EXISTS boulder_county_boundary CASCADE;

CREATE TABLE boulder_county_boundary (
    id SERIAL PRIMARY KEY,
    geometry geometry(MULTIPOLYGON, 4326) NOT NULL,

    CONSTRAINT chk_boundary_geometry_valid
        CHECK (ST_IsValid(geometry)),

    CONSTRAINT chk_boundary_geometry_type
        CHECK (
            GeometryType(geometry) IN (
                'MULTIPOLYGON',
                'ST_MultiPolygon',
                'POLYGON',
                'ST_Polygon'
            )
        )
);

CREATE INDEX idx_boulder_county_boundary_geometry_gist
    ON boulder_county_boundary
    USING GIST (geometry);

COMMENT ON TABLE boulder_county_boundary IS
'Boundary polygon for Boulder County used to validate whether coordinates fall inside the service area.';