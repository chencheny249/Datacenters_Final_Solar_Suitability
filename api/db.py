import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_database_url() -> str:
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "solar")

    return (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def test_connection() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def fetch_all_tiles(limit: int = 100) -> list[dict]:
    query = text("""
        SELECT
            tile_id,
            latitude,
            longitude,
            mean_elevation,
            mean_slope,
            mean_aspect,
            mean_dni,
            mean_dhi,
            mean_ghi_proxy,
            mean_temp,
            aspect_score,
            slope_score,
            solar_score,
            rugged_penalty,
            suitability_score
        FROM solar_tiles
        ORDER BY suitability_score DESC
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {"limit": limit})
        return [dict(row._mapping) for row in result]


def fetch_tile_by_id(tile_id: str) -> dict | None:
    query = text("""
        SELECT
            tile_id,
            latitude,
            longitude,
            mean_elevation,
            std_elevation,
            mean_slope,
            std_slope,
            mean_aspect,
            max_slope,
            elevation_m,
            mean_dni,
            mean_dhi,
            mean_ghi_proxy,
            mean_temp,
            aspect_score,
            slope_score,
            solar_score,
            rugged_penalty,
            suitability_score,
            ST_AsText(geometry) AS geometry_wkt
        FROM solar_tiles
        WHERE tile_id = :tile_id
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {"tile_id": tile_id}).fetchone()
        return dict(result._mapping) if result else None


def fetch_top_tiles(limit: int = 10) -> list[dict]:
    query = text("""
        SELECT
            tile_id,
            latitude,
            longitude,
            suitability_score
        FROM solar_tiles
        ORDER BY suitability_score DESC
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {"limit": limit})
        return [dict(row._mapping) for row in result]
    
    
def fetch_tiles_within_bbox(xmin, ymin, xmax, ymax):
    query = text("""
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geometry)::jsonb,
                    'properties', jsonb_build_object(
                        'tile_id', tile_id,
                        'suitability_score', suitability_score
                    )
                )
            )
        ) AS geojson
        FROM solar_tiles
        WHERE geometry && ST_MakeEnvelope(:xmin, :ymin, :xmax, :ymax, 4326);
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax
        }).fetchone()

        return result.geojson if result else None    
    

def fetch_tile_by_point(lat: float, lon: float):
    query = text("""
        SELECT
            tile_id,
            latitude,
            longitude,
            mean_elevation,
            std_elevation,
            mean_slope,
            std_slope,
            mean_aspect,
            max_slope,
            elevation_m,
            mean_dni,
            mean_dhi,
            mean_ghi_proxy,
            mean_temp,
            aspect_score,
            slope_score,
            solar_score,
            rugged_penalty,
            suitability_score,
            ST_AsGeoJSON(geometry)::json AS geometry            
        FROM solar_tiles
        WHERE ST_Covers(
            geometry,
            ST_SetSRID(ST_Point(:lon, :lat), 4326)
        )
        LIMIT 1
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {"lat": lat, "lon": lon}).mappings().first()
        return dict(result) if result else None
    


def is_in_boulder_county(lat: float, lon: float) -> bool:
    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM boulder_county_boundary
            WHERE ST_Covers(
                geometry,
                ST_SetSRID(ST_Point(:lon, :lat), 4326)
            )
        )
    """)

    with get_engine().connect() as conn:
        result = conn.execute(query, {"lat": lat, "lon": lon}).scalar()
        return bool(result)    