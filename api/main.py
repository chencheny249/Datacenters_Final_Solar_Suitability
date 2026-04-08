from fastapi import FastAPI, HTTPException, Query
from db import test_connection, fetch_all_tiles, fetch_tile_by_id, fetch_top_tiles

app = FastAPI(
    title="Solar Suitability Service",
    description="API for Boulder County solar suitability tiles",
    version="1.0.0",
)


@app.get("/")
def root() -> dict:
    return {
        "message": "Solar Suitability Service is running."
    }


@app.get("/health")
def health_check() -> dict:
    db_ok = test_connection()

    if not db_ok:
        raise HTTPException(status_code=500, detail="Database connection failed")

    return {
        "status": "ok",
        "database": "connected"
    }


@app.get("/tiles")
def get_tiles(
    limit: int = Query(default=100, ge=1, le=1000)
) -> list[dict]:
    return fetch_all_tiles(limit=limit)


@app.get("/tiles/top")
def get_top_tiles(
    limit: int = Query(default=10, ge=1, le=100)
) -> list[dict]:
    return fetch_top_tiles(limit=limit)


@app.get("/tiles/{tile_id}")
def get_tile(tile_id: str) -> dict:
    tile = fetch_tile_by_id(tile_id)

    if tile is None:
        raise HTTPException(status_code=404, detail=f"Tile '{tile_id}' not found")

    return tile