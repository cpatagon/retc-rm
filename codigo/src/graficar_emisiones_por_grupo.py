#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera gráficos (PNG) de emisiones por año para cada grupo/contaminante.

Entrada: un CSV en formato *pivot* o *largo*:
  - PIVOT: columnas = ['año', 'PM2.5', 'PM10', 'SO2', ...]
  - LARGO: columnas = ['año','grupo_canonico','emision_total_ton_anio']

Uso típico (desde la raíz del repo o desde src):
  python graficar_emisiones_por_grupo.py \
    --in "../outputs/tablas/datos_resumidos/LBP_AIRE_<DATETIME>_emisiones_por_anio_y_grupo_pivot.csv" \
    --outdir "../outputs/graficos"

Opciones útiles:
  --longitudinal            # fuerza formato largo (si la detección automática no aplica)
  --pivot                   # fuerza formato pivot
  --grupos "PM2.5,PM10,SO2" # grafica solo esos grupos (separados por coma)
  --start 2005 --end 2023   # restringe rango de años
  --zip                     # crea un ZIP con todos los PNG generados

Requisitos:
  pip install pandas matplotlib
"""

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd


def to_float(s):
    """Convierte string con coma/punto/científica a float (None si vacío)."""
    if s is None:
        return None
    s = str(s).strip()
    if s == "" or s.lower() in {"na", "nan", "none"}:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def safe_name(s: str) -> str:
    """Nombre de archivo seguro."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(s)).strip("_") or "plot"


def detect_format(df: pd.DataFrame, force_pivot=False, force_long=False) -> str:
    if force_pivot:
        return "pivot"
    if force_long:
        return "long"
    cols_lower = [c.lower() for c in df.columns]
    if "año" in df.columns or "ano" in df.columns:
        # si además hay muchas columnas aparte del año, parece pivot
        if len(df.columns) > 3 and not {"grupo_canonico", "emision_total_ton_anio"}.issubset(set(cols_lower)):
            return "pivot"
    if {"año", "grupo_canonico", "emision_total_ton_anio"}.issubset(set(cols_lower)):
        return "long"
    # fallback: si hay "año" y >2 columnas, intenta pivot
    return "pivot"


def load_csv_any(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str)
    except Exception:
        return pd.read_csv(path, dtype=str, encoding="latin-1")


def plot_series(x_years, y_vals, title, out_png):
    plt.figure(figsize=(8, 4.5))
    plt.plot(x_years, y_vals, marker="o")
    ax = plt.gca()
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # ticks de enteros
    plt.title(title)
    plt.xlabel("Año")
    plt.ylabel("Emisión total (t/año)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser(description="Graficar emisiones por año por grupo/contaminante")
    ap.add_argument("--in", dest="infile", required=True, help="CSV de entrada (pivot o largo)")
    ap.add_argument("--outdir", required=True, help="Carpeta de salida para PNG")
    ap.add_argument("--pivot", action="store_true", help="Forzar modo PIVOT")
    ap.add_argument("--longitudinal", action="store_true", help="Forzar modo LARGO")
    ap.add_argument("--grupos", type=str, default=None, help="Lista de grupos separados por coma (opcional)")
    ap.add_argument("--start", type=int, default=None, help="Año inicio (opcional)")
    ap.add_argument("--end", type=int, default=None, help="Año fin (opcional)")
    ap.add_argument("--zip", action="store_true", help="Comprimir todos los PNG a un ZIP")
    args = ap.parse_args()

    infile = Path(args.infile).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_csv_any(infile)
    fmt = detect_format(df, force_pivot=args.pivot, force_long=args.longitudinal)

    targets = None
    if args.grupos:
        targets = [g.strip() for g in args.grupos.split(",") if g.strip()]

    n_plots = 0

    if fmt == "pivot":
        year_col = "año" if "año" in df.columns else ("ano" if "ano" in df.columns else None)
        if year_col is None:
            raise SystemExit("No encontré columna 'año'/'ano' para formato pivot.")
        # Año a entero
        df[year_col] = pd.to_numeric(df[year_col].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
        df = df.dropna(subset=[year_col]).sort_values(year_col)
        df[year_col] = df[year_col].astype(int)

        if args.start is not None:
            df = df[df[year_col] >= args.start]
        if args.end is not None:
            df = df[df[year_col] <= args.end]

        group_cols = [c for c in df.columns if c != year_col]
        if targets:
            group_cols = [c for c in group_cols if c in targets]

        for col in group_cols:
            y = df[col].map(to_float)
            if y.notna().any():
                out_png = outdir / f"{safe_name(col)}.png"
                title = f"{col} — Emisión total por año (t/año)"
                plot_series(df[year_col].tolist(), y.tolist(), title, out_png)
                n_plots += 1

    else:  # largo
        lower = {c.lower(): c for c in df.columns}
        need = {"año", "grupo_canonico", "emision_total_ton_anio"}
        if not need.issubset(set(lower)):
            raise SystemExit(f"El CSV no tiene columnas requeridas (esperadas: {sorted(need)}). "
                             f"Encontradas: {df.columns.tolist()}")
        df = df.rename(columns=lower)
        df["año"] = pd.to_numeric(df["año"].astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce")
        df["emision_total_ton_anio"] = df["emision_total_ton_anio"].map(to_float)
        df = df.dropna(subset=["año"]).sort_values("año")
        df["año"] = df["año"].astype(int)

        if args.start is not None:
            df = df[df["año"] >= args.start]
        if args.end is not None:
            df = df[df["año"] <= args.end]

        groups = sorted(df["grupo_canonico"].dropna().unique().tolist())
        if targets:
            groups = [g for g in groups if g in targets]

        for g in groups:
            sub = df[df["grupo_canonico"] == g].copy()
            if sub["emision_total_ton_anio"].notna().any():
                out_png = outdir / f"{safe_name(g)}.png"
                title = f"{g} — Emisión total por año (t/año)"
                plot_series(sub["año"].tolist(), sub["emision_total_ton_anio"].tolist(), title, out_png)
                n_plots += 1

    # ZIP opcional
    if args.zip and n_plots > 0:
        import zipfile
        zip_path = outdir.with_name(outdir.name + ".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for png in outdir.glob("*.png"):
                zf.write(png, arcname=png.name)
        print(f"[✓] ZIP creado: {zip_path}")

    print(f"[✓] Gráficos generados: {n_plots}")
    print(f"    Carpeta salida: {outdir}")
    print(f"    Formato detectado: {fmt}")


if __name__ == "__main__":
    main()
