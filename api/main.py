from fastapi import FastAPI, HTTPException, Query

from api.db import (
    test_connection,
    fetch_all_tiles,
    fetch_tile_by_id,
    fetch_top_tiles,
    fetch_tiles_within_bbox,
    fetch_tile_by_point,
    is_in_boulder_county,
)

from io import BytesIO
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import shape, Point
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="Solar Suitability Service",
    description="API for Boulder County solar suitability tiles",
    version="1.0.0",
)

def validate_coordinates(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=400,
            detail="Invalid latitude. Must be between -90 and 90."
        )

    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=400,
            detail="Invalid longitude. Must be between -180 and 180."
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


@app.get("/tiles/within_bbox")
def get_tiles_within_bbox(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float
):
    geojson = fetch_tiles_within_bbox(xmin, ymin, xmax, ymax)

    if geojson is None:
        raise HTTPException(status_code=404, detail="No tiles found")

    return geojson


@app.get("/tiles/{tile_id}")
def get_tile(tile_id: str) -> dict:
    tile = fetch_tile_by_id(tile_id)

    if tile is None:
        raise HTTPException(status_code=404, detail=f"Tile '{tile_id}' not found")

    return tile


def create_score_plot(lat: float, lon: float):
    tile = fetch_tile_by_point(lat=lat, lon=lon)
    if tile is None:
        raise HTTPException(status_code=404, detail="Point not found in any tile")
    
    score = tile["suitability_score"]

    geometry_data = tile.get("geometry")
    if geometry_data is None:
        raise HTTPException(status_code=500, detail="Tile geometry missing")

    tile_gdf = gpd.GeoDataFrame(
        [{"suitability_score": tile["suitability_score"]}],
        geometry=[shape(geometry_data)],
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    point_gdf = gpd.GeoDataFrame(
        [{
        "label": (
            f"Lat: {lat:.5f}\n"
            f"Lon: {lon:.5f}\n"
            f"Suitability Score: {score:.2f}"
        )
        }],
        geometry=[Point(lon, lat)],
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(10, 8))

    tile_gdf.plot(
        column="suitability_score",
        vmin=0,
        vmax=100,
        ax=ax,
        legend=True,
        cmap="YlOrRd",
        alpha=0.6,
        edgecolor="white",
        linewidth=1.0,
        legend_kwds={"label": "Solar Suitability Score"}
    )

    point_gdf.plot(
        ax=ax,
        color="blue",
        markersize=120
    )

    x = point_gdf.geometry.iloc[0].x
    y = point_gdf.geometry.iloc[0].y

    ax.annotate(
        point_gdf.iloc[0]["label"],
        xy=(x, y),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8)
    )

    minx, miny, maxx, maxy = tile_gdf.total_bounds
    pad_x = (maxx - minx) * 1.5 if maxx > minx else 500
    pad_y = (maxy - miny) * 1.5 if maxy > miny else 500
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    plt.title("Solar Suitability Score Location", fontsize=16)
    ax.set_axis_off()

    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    plt.close(fig)
    img.seek(0)

    return img

@app.get("/score_plot")
def get_score_plot(lat: float, lon: float):
    validate_coordinates(lat, lon)

    if not is_in_boulder_county(lat, lon):
        raise HTTPException(
            status_code=400,
            detail="Coordinates are outside Boulder County"
        )

    img = create_score_plot(lat, lon)
    return StreamingResponse(img, media_type="image/png")


@app.get("/score")
def get_score(lat: float, lon: float):
    validate_coordinates(lat, lon)

    if not is_in_boulder_county(lat, lon):
        raise HTTPException(
            status_code=400,
            detail="Coordinates are outside Boulder County"
        )

    tile = fetch_tile_by_point(lat=lat, lon=lon)
    if tile is None:
        raise HTTPException(status_code=404, detail="Point not found in any tile")

    tile["plot_url"] = f"/score_plot?lat={lat}&lon={lon}"
    return tile