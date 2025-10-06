#!/usr/bin/env python3
"""Emisiones acumuladas 2023 por comuna y contaminante."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_CONSOLIDADO = "../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv"
DEFAULT_OUTDIR = "../outputs/graficos/emisiones_acumuladas_2023"
DEFAULT_SUMMARY = "../outputs/tablas/datos_resumidos/LBP_AIRE_20250926_emisiones_comuna_contaminante_2023.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Emisiones 2023 por comuna y contaminante")
    parser.add_argument("--consolidado", default=DEFAULT_CONSOLIDADO)
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    consolidado_path = Path(args.consolidado).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    chunks = pd.read_csv(consolidado_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip', chunksize=200000)
    rows = []
    for chunk in chunks:
        chunk = chunk[chunk['año'] == '2023']
        chunk['emision_total'] = pd.to_numeric(chunk['emision_total'], errors='coerce')
        chunk = chunk.dropna(subset=['emision_total', 'contaminante_canon', 'comuna'])
        rows.append(chunk)

    if not rows:
        print('[!] No se encontraron registros 2023 en el consolidado')
        return

    data = pd.concat(rows, ignore_index=True)
    summary = data.groupby(['comuna', 'contaminante_canon'], as_index=False)['emision_total'].sum()
    summary.to_csv(Path(args.summary).expanduser().resolve(), index=False, encoding='utf-8-sig')

    for contaminant, group in summary.groupby('contaminante_canon'):
        group = group.sort_values('emision_total', ascending=False).head(20)
        plt.figure(figsize=(10, 6))
        plt.barh(group['comuna'], group['emision_total'], color='#31a354')
        plt.title(f'{contaminant} — Emisión total 2023 por comuna (top 20)')
        plt.xlabel('Emisión total (t/año)')
        plt.ylabel('Comuna')
        plt.tight_layout()
        outfile = outdir / f'{contaminant}_comunas_2023.png'
        plt.savefig(outfile, dpi=150)
        plt.close()
        print('[✓] Gráfico generado:', outfile)

    print('[✓] Resumen en', args.summary)


if __name__ == '__main__':
    main()
