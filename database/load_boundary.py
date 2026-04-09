import json
import os
from sqlalchemy import create_engine, text

GEOJSON_PATH = "processed/boulder_grid.geojson"
TABLE_NAME = "boulder_county_boundary"


def build_engine():
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "solar")

    db_url = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )
    return create_engine(db_url)


def load_geojson(geojson_path: str) -> dict:
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def extract_geometry(geojson_data: dict) -> str:
    if geojson_data.get("type") == "FeatureCollection":
        features = geojson_data.get("features", [])
        if not features:
            raise ValueError("GeoJSON FeatureCollection has no features")
        geometry = features[0].get("geometry")
    elif geojson_data.get("type") == "Feature":
        geometry = geojson_data.get("geometry")
    elif geojson_data.get("type") in {"Polygon", "MultiPolygon"}:
        geometry = geojson_data
    else:
        raise ValueError("Unsupported GeoJSON format")

    if geometry is None:
        raise ValueError("No geometry found in GeoJSON")

    return json.dumps(geometry)


def insert_boundary(conn, geometry_json: str):
    conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY;"))

    conn.execute(text(f"""
        INSERT INTO {TABLE_NAME} (geometry)
        VALUES (
            ST_Multi(
                ST_SetSRID(
                    ST_GeomFromGeoJSON(:geometry_json),
                    4326
                )
            )::geometry(MULTIPOLYGON, 4326)
        )
    """), {"geometry_json": geometry_json})


def main():
    geojson_data = load_geojson(GEOJSON_PATH)
    geometry_json = extract_geometry(geojson_data)
    engine = build_engine()

    with engine.begin() as conn:
        insert_boundary(conn, geometry_json)

    print(f"Loaded Boulder County boundary into {TABLE_NAME}.")


if __name__ == "__main__":
    main()