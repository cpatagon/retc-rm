#!/usr/bin/env python3
"""Genera tablas en formato Markdown de emisiones 2023 por unidad de paisaje para cada contaminante."""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

DEFAULT_CONSOLIDADO = "../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv"
DEFAULT_OUTPUT = "../docs/tablas/emisiones_2023_por_paisaje.md"
CHUNKSIZE = 200000


def main() -> None:
    parser = argparse.ArgumentParser(description="Tablas Markdown emisiones 2023 por unidad de paisaje")
    parser.add_argument("--consolidado", default=DEFAULT_CONSOLIDADO)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    consolidado_path = Path(args.consolidado).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    acumulado = defaultdict(float)

    for chunk in pd.read_csv(consolidado_path, sep=';', dtype=str, encoding='utf-8', on_bad_lines='skip', chunksize=CHUNKSIZE):
        chunk = chunk[chunk['año'] == '2023']
        if chunk.empty:
            continue
        chunk['emision_total'] = pd.to_numeric(chunk['emision_total'], errors='coerce')
        chunk = chunk.dropna(subset=['emision_total', 'contaminante_canon', 'unidad_paisaje'])
        grouped = chunk.groupby(['contaminante_canon', 'unidad_paisaje'])['emision_total'].sum()
        for (contaminante, unidad), value in grouped.items():
            acumulado[(contaminante, unidad)] += float(value)

    if not acumulado:
        output_path.write_text("No se encontraron registros para 2023.\n", encoding='utf-8')
        print("[!] Sin datos 2023; archivo vacío creado.")
        return

    data = pd.Series(acumulado).rename('emision_total').reset_index()
    data.columns = ['contaminante_canon', 'unidad_paisaje', 'emision_total']

    sections = ["# Emisiones 2023 por unidad de paisaje"]
    for contaminante, group in data.groupby('contaminante_canon'):
        group = group.sort_values('emision_total', ascending=False)
        sections.append(f"\n## {contaminante}\n")
        sections.append("| Unidad de paisaje | Emisión total (t/año) |")
        sections.append("| --- | ---: |")
        for _, row in group.iterrows():
            unidad = row['unidad_paisaje']
            valor = f"{row['emision_total']:.6f}" if pd.notna(row['emision_total']) else ""
            sections.append(f"| {unidad} | {valor} |")

    output_path.write_text("\n".join(sections) + "\n", encoding='utf-8')
    print(f"[✓] Tablas markdown generadas en {output_path}")


if __name__ == '__main__':
    main()
