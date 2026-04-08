import os
import pandas as pd
from sqlalchemy import create_engine, text

PARQUET_PATH = "processed/boulder_tiles.parquet"
TABLE_NAME = "solar_tiles"


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


def load_parquet(parquet_path: str) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path)

    expected_columns = [
        "tile_id",
        "geometry",
        "mean_elevation",
        "std_elevation",
        "mean_slope",
        "std_slope",
        "mean_aspect",
        "max_slope",
        "latitude",
        "longitude",
        "elevation_m",
        "mean_dni",
        "mean_dhi",
        "mean_ghi_proxy",
        "mean_temp",
        "aspect_score",
        "slope_score",
        "solar_score",
        "rugged_penalty",
        "suitability_score",
    ]

    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        raise ValueError(f"Found null values:\n{null_counts[null_counts > 0]}")

    return df[expected_columns].copy()


def create_temp_table(conn):
    conn.execute(text("""
        DROP TABLE IF EXISTS solar_tiles_staging;

        CREATE TEMP TABLE solar_tiles_staging (
            tile_id TEXT,
            geometry BYTEA,
            mean_elevation DOUBLE PRECISION,
            std_elevation DOUBLE PRECISION,
            mean_slope DOUBLE PRECISION,
            std_slope DOUBLE PRECISION,
            mean_aspect DOUBLE PRECISION,
            max_slope DOUBLE PRECISION,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            elevation_m INTEGER,
            mean_dni DOUBLE PRECISION,
            mean_dhi DOUBLE PRECISION,
            mean_ghi_proxy DOUBLE PRECISION,
            mean_temp DOUBLE PRECISION,
            aspect_score DOUBLE PRECISION,
            slope_score DOUBLE PRECISION,
            solar_score DOUBLE PRECISION,
            rugged_penalty INTEGER,
            suitability_score DOUBLE PRECISION
        );
    """))


def copy_to_staging(df: pd.DataFrame, conn):
    df.to_sql(
        "solar_tiles_staging",
        con=conn,
        if_exists="append",
        index=False,
        method="multi",
    )


def insert_into_final_table(conn):
    conn.execute(text(f"""
        INSERT INTO {TABLE_NAME} (
            tile_id,
            geometry,
            mean_elevation,
            std_elevation,
            mean_slope,
            std_slope,
            mean_aspect,
            max_slope,
            latitude,
            longitude,
            elevation_m,
            mean_dni,
            mean_dhi,
            mean_ghi_proxy,
            mean_temp,
            aspect_score,
            slope_score,
            solar_score,
            rugged_penalty,
            suitability_score
        )
        SELECT
            tile_id,
            ST_GeomFromWKB(geometry, 4326)::geometry(Polygon, 4326),
            mean_elevation,
            std_elevation,
            mean_slope,
            std_slope,
            mean_aspect,
            max_slope,
            latitude,
            longitude,
            elevation_m,
            mean_dni,
            mean_dhi,
            mean_ghi_proxy,
            mean_temp,
            aspect_score,
            slope_score,
            solar_score,
            rugged_penalty,
            suitability_score
        FROM solar_tiles_staging
        ON CONFLICT (tile_id) DO UPDATE SET
            geometry = EXCLUDED.geometry,
            mean_elevation = EXCLUDED.mean_elevation,
            std_elevation = EXCLUDED.std_elevation,
            mean_slope = EXCLUDED.mean_slope,
            std_slope = EXCLUDED.std_slope,
            mean_aspect = EXCLUDED.mean_aspect,
            max_slope = EXCLUDED.max_slope,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            elevation_m = EXCLUDED.elevation_m,
            mean_dni = EXCLUDED.mean_dni,
            mean_dhi = EXCLUDED.mean_dhi,
            mean_ghi_proxy = EXCLUDED.mean_ghi_proxy,
            mean_temp = EXCLUDED.mean_temp,
            aspect_score = EXCLUDED.aspect_score,
            slope_score = EXCLUDED.slope_score,
            solar_score = EXCLUDED.solar_score,
            rugged_penalty = EXCLUDED.rugged_penalty,
            suitability_score = EXCLUDED.suitability_score;
    """))


def main():
    if not os.path.exists(PARQUET_PATH):
        raise FileNotFoundError(f"Parquet file not found: {PARQUET_PATH}")

    df = load_parquet(PARQUET_PATH)
    engine = build_engine()

    with engine.begin() as conn:
        create_temp_table(conn)
        copy_to_staging(df, conn)
        insert_into_final_table(conn)

    print(f"Loaded {len(df)} rows into {TABLE_NAME}.")


if __name__ == "__main__":
    main()