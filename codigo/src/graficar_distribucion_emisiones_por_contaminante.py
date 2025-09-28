#!/usr/bin/env python3
"""Genera histogramas de la distribución de emisiones por contaminante."""
from __future__ import annotations

import argparse
import math
from collections import defaultdict, Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CHUNKSIZE = 200000
MIN_POSITIVE = 1e-20  # evita log(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Distribución de emisiones por contaminante")
    parser.add_argument(
        "--input",
        default="../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv",
        help="CSV consolidado con columna emision_total",
    )
    parser.add_argument(
        "--outdir",
        default="../outputs/graficos/emisiones_distribucion",
        help="Carpeta de salida para los histogramas",
    )
    parser.add_argument(
        "--summary",
        default="../outputs/tablas/datos_resumidos/LBP_AIRE_20250926_resumen_distribucion_emisiones.csv",
        help="Ruta del CSV resumido",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise SystemExit(f"No se encuentra el archivo de entrada: {input_path}")

    values = defaultdict(list)
    zero_counts = Counter()

    for chunk in pd.read_csv(input_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip', chunksize=CHUNKSIZE):
        chunk['emision_total'] = pd.to_numeric(chunk['emision_total'], errors='coerce')
        chunk = chunk.dropna(subset=['emision_total', 'contaminante_canon'])
        zero_counts.update(chunk[chunk['emision_total'] <= 0]['contaminante_canon'])
        positives = chunk[chunk['emision_total'] > 0]
        for contaminant, series in positives.groupby('contaminante_canon')['emision_total']:
            values[contaminant].extend(series.tolist())

    summary_rows = []
    for contaminant, emis in values.items():
        series = pd.Series(emis, dtype=float)
        positive_count = len(series)
        zero_count = int(zero_counts.get(contaminant, 0))
        total_count = positive_count + zero_count

        if positive_count == 0:
            continue

        # log10 para mejor visualización
        log_values = series.clip(lower=MIN_POSITIVE).apply(lambda x: math.log10(x))

        plt.figure(figsize=(8, 4.5))
        plt.hist(log_values, bins=40, color='#2c7fb8', alpha=0.8)
        plt.title(f"{contaminant} — Distribución log10(emisión)")
        plt.xlabel('log10(emisión total t/año)')
        plt.ylabel('Frecuencia')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        outfile = outdir / f"{contaminant}_hist.png"
        plt.savefig(outfile, dpi=150)
        plt.close()

        summary_rows.append({
            'contaminante_canon': contaminant,
            'total_registros': total_count,
            'registros_positivos': positive_count,
            'registros_cero_o_negativos': zero_count,
            'emision_min': series.min(),
            'emision_max': series.max(),
            'emision_media': series.mean(),
            'emision_mediana': series.median()
        })
        print(f"[✓] Histograma generado para {contaminant}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(Path(args.summary).expanduser().resolve(), index=False, encoding='utf-8-sig')
    print(f"[✓] Resumen exportado a {args.summary}")
    print(f"[✓] Histogramas disponibles en {outdir}")


if __name__ == '__main__':
    main()
