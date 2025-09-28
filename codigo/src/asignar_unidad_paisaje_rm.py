#!/usr/bin/env python3
"""Asigna unidades de paisaje a las emisiones consolidadas según lat/lon."""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

DEFAULT_CONSOLIDADO = "../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv"
DEFAULT_Polygons = "../geo/insumos/UnidadesPaisajeRM/unidades-paisaje-V1.gpkg"

LAT_COLS = ["latitud_nueva", "latitud"]
LON_COLS = ["longitud_nueva", "longitud"]


def coalesce(series, fallbacks):
    for col in fallbacks:
        if col in series and pd.notna(series[col]):
            val = series[col]
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def build_geometry(row):
    lat = coalesce(row, LAT_COLS)
    lon = coalesce(row, LON_COLS)
    if lat is None or lon is None:
        return None
    try:
        return Point(float(lon), float(lat))  # lon, lat
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Intersección con unidades del paisaje")
    parser.add_argument("--consolidado", default=DEFAULT_CONSOLIDADO, help="CSV consolidado RM")
    parser.add_argument("--poligonos", default=DEFAULT_Polygons, help="GPKG de unidades del paisaje")
    parser.add_argument("--unidad-col", default="unidad_paisaje", help="Nombre de la columna de salida")
    args = parser.parse_args()

    consolidado_path = Path(args.consolidado).expanduser().resolve()
    polygons_path = Path(args.poligonos).expanduser().resolve()

    if not consolidado_path.exists():
        raise SystemExit(f"No se encontró el consolidado: {consolidado_path}")
    if not polygons_path.exists():
        raise SystemExit(f"No se encontró el archivo de polígonos: {polygons_path}")

    df = pd.read_csv(consolidado_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip')
    df.columns = [c.lstrip('\ufeff') for c in df.columns]

    df['geometry'] = df.apply(build_geometry, axis=1)
    gdf_points = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')

    gdf_polygons = gpd.read_file(polygons_path)
    if gdf_polygons.crs is None:
        gdf_polygons = gdf_polygons.set_crs('EPSG:4326')
    else:
        gdf_polygons = gdf_polygons.to_crs('EPSG:4326')

    gdf_joined = gpd.sjoin(gdf_points, gdf_polygons[['Nombre', 'geometry']], how='left', op='within')

    df_result = pd.DataFrame(gdf_joined.drop(columns=['index_right']))
    df_result.rename(columns={'Nombre': args.unidad_col}, inplace=True)

    if args.unidad_col not in df_result.columns:
        df_result[args.unidad_col] = None

    df_result.drop(columns=['geometry'], inplace=True)
    df_result.to_csv(consolidado_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"[✓] Unidades del paisaje asignadas en {consolidado_path}")


if __name__ == '__main__':
    main()
