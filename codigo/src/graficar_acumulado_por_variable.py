#!/usr/bin/env python3
"""Genera gráficos de emisiones acumuladas por año para cada contaminante.

Usa los CSV de `emisiones_por_variable_extractos` para calcular el total anual y
su acumulado, guardando:
  - Un PNG por contaminante mostrando la serie acumulada.
  - Un CSV global con columnas (`contaminante`, `year`, `emision`, `emision_acumulada`).
"""
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd

SKIP_FILES = {
    "diccionario_id_nombre_por_grupo.csv",
    "resumen_por_grupo.csv",
}


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "contaminante"


def to_year(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")


def to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.apply(normalize_number), errors="coerce")


def normalize_number(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"na", "nan", "none"}:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "")
    text = text.replace(",", ".")
    return text


def aggregate_cumulative(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    if "año" not in df.columns and "ano" not in df.columns:
        raise ValueError(f"El archivo {path.name} no contiene columna año/ano")
    year_col = "año" if "año" in df.columns else "ano"
    df["year"] = to_year(df[year_col])

    if "cantidad_toneladas" not in df.columns:
        raise ValueError(f"El archivo {path.name} no tiene columna cantidad_toneladas")
    df["emision"] = to_float(df["cantidad_toneladas"])

    agg = (
        df.dropna(subset=["year"])
        .groupby("year", as_index=False)["emision"]
        .sum(min_count=1)
        .sort_values("year")
    )
    agg["emision_acumulada"] = agg["emision"].cumsum()
    agg["contaminante"] = path.stem
    return agg


def plot_cumulative(df: pd.DataFrame, out_png: Path, contaminant: str) -> None:
    if df.empty:
        return
    plt.figure(figsize=(8, 4.5))
    plt.plot(df["year"], df["emision_acumulada"], marker="o")
    plt.title(f"{contaminant} — Emisión acumulada (t/año)")
    plt.xlabel("Año")
    plt.ylabel("Emisión acumulada (t)")
    plt.grid(True)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=150)
    plt.close()


def resolve_summary_path(default_dir: Path, summary: str | None) -> Path:
    if summary:
        return Path(summary).expanduser().resolve()
    default_dir.mkdir(parents=True, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    return default_dir / f"LBP_AIRE_{date_tag}_acumulado_por_variable.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Gráficos de emisiones acumuladas por contaminante")
    parser.add_argument(
        "--indir",
        default="../data/interim/emisiones_por_variable_extractos",
        help="Carpeta con los CSV de columnas clave",
    )
    parser.add_argument(
        "--outdir",
        default="../outputs/graficos/emisiones_totales_acumuladas",
        help="Carpeta de salida para los gráficos",
    )
    parser.add_argument(
        "--summary",
        default=None,
        help="Ruta del CSV resumen (por defecto outputs/tablas/datos_resumidos/LBP_AIRE_<fecha>_acumulado_por_variable.csv)",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    default_summary_dir = Path(__file__).resolve().parents[2] / "outputs" / "tablas" / "datos_resumidos"
    summary_path = resolve_summary_path(default_summary_dir, args.summary)

    frames = []
    for csv_path in sorted(indir.glob("*.csv")):
        if csv_path.name in SKIP_FILES:
            continue
        agg = aggregate_cumulative(csv_path)
        frames.append(agg)
        plot_cumulative(agg, outdir / f"{safe_name(csv_path.stem)}.png", csv_path.stem)
        print(f"[✓] Graficado acumulado {csv_path.name}")

    if not frames:
        raise SystemExit("No se encontraron archivos a procesar")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).sort_values(["contaminante", "year"]).to_csv(
        summary_path, index=False, encoding="utf-8-sig"
    )
    print(f"[✓] Resumen acumulado guardado en: {summary_path}")
    print(f"[✓] Gráficos acumulados en: {outdir}")


if __name__ == "__main__":
    main()
