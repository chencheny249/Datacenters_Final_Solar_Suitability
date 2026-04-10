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
        return json.load(f)


def extract_geometries(geojson_data: dict) -> list[str]:
    geojson_type = geojson_data.get("type")

    if geojson_type == "FeatureCollection":
        features = geojson_data.get("features", [])
        if not features:
            raise ValueError("GeoJSON FeatureCollection has no features")

        geometries = [f.get("geometry") for f in features if f.get("geometry") is not None]

    elif geojson_type == "Feature":
        geometry = geojson_data.get("geometry")
        if geometry is None:
            raise ValueError("No geometry found in GeoJSON Feature")
        geometries = [geometry]

    elif geojson_type in {"Polygon", "MultiPolygon"}:
        geometries = [geojson_data]

    else:
        raise ValueError(f"Unsupported GeoJSON format: {geojson_type}")

    if not geometries:
        raise ValueError("No geometries found in GeoJSON")

    return [json.dumps(g) for g in geometries]


def insert_boundary(conn, geometry_json_list: list[str]):
    conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY;"))

    if len(geometry_json_list) == 1:
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
        """), {"geometry_json": geometry_json_list[0]})
    else:
        values_sql = ", ".join(
            f"(:geom_{i})" for i in range(len(geometry_json_list))
        )
        params = {f"geom_{i}": g for i, g in enumerate(geometry_json_list)}

        conn.execute(text(f"""
            INSERT INTO {TABLE_NAME} (geometry)
            SELECT
                ST_Multi(
                    ST_Union(
                        ST_SetSRID(ST_GeomFromGeoJSON(geom_json), 4326)
                    )
                )::geometry(MULTIPOLYGON, 4326)
            FROM (
                VALUES {values_sql}
            ) AS t(geom_json)
        """), params)


def main():
    geojson_data = load_geojson(GEOJSON_PATH)
    geometry_json_list = extract_geometries(geojson_data)
    engine = build_engine()

    with engine.begin() as conn:
        insert_boundary(conn, geometry_json_list)

    print(f"Loaded Boulder County boundary into {TABLE_NAME}.")


if __name__ == "__main__":
    main()