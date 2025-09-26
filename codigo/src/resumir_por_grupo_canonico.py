#!/usr/bin/env python3
"""Genera un resumen de valores nulos/no nulos por columna en la carpeta `por_grupo_canonico`.

Uso típico:
  python resumir_por_grupo_canonico.py \
    --indir ../data/interim/filtrados_region/por_grupo_canonico \
    --out ../outputs/tablas/resumenes/LBP_AIRE_$(date +%Y%m%d)_no_nulos_por_grupo.csv
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

# archivos que no representan contaminantes individuales
SKIP_FILES = {
    "diccionario_id_nombre_por_grupo.csv",
    "resumen_por_grupo.csv",
}


def load_dataframe(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    # considerar cadenas vacías como nulos para el conteo
    return df.apply(lambda col: col.replace({"": pd.NA}))


def summarize_file(path: Path) -> pd.DataFrame:
    df = load_dataframe(path)
    rows = []
    for column in df.columns:
        serie = df[column]
        total = len(serie)
        non_null = int(serie.notna().sum())
        nulls = total - non_null
        rows.append(
            {
                "contaminante": path.stem,
                "columna": column,
                "no_nulos": non_null,
                "nulos": nulls,
                "total": total,
            }
        )
    return pd.DataFrame(rows)


def resolve_output(default_dir: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    today = datetime.now().strftime("%Y%m%d")
    default_dir.mkdir(parents=True, exist_ok=True)
    return default_dir / f"LBP_AIRE_{today}_no_nulos_por_grupo.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Resumen de valores nulos/no nulos por grupo canónico")
    parser.add_argument(
        "--indir",
        default="../data/interim/filtrados_region/por_grupo_canonico",
        help="Directorio con CSV por contaminante",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ruta del CSV de salida (por defecto outputs/tablas/resumenes/LBP_AIRE_<fecha>_no_nulos_por_grupo.csv)",
    )
    args = parser.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    if not indir.is_dir():
        raise SystemExit(f"No se encontró el directorio de entrada: {indir}")

    output_default_dir = Path(__file__).resolve().parents[2] / "outputs" / "tablas" / "resumenes"
    out_path = resolve_output(output_default_dir, args.out)

    summaries = []
    for csv_path in sorted(indir.glob("*.csv")):
        if csv_path.name in SKIP_FILES:
            continue
        summaries.append(summarize_file(csv_path))

    if not summaries:
        raise SystemExit("No se encontraron archivos CSV de contaminantes para resumir.")

    result = pd.concat(summaries, ignore_index=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[✓] Resumen generado: {out_path}")


if __name__ == "__main__":
    main()
