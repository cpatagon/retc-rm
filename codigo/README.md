# Descargador RETC — Emisiones al Aire

Este directorio contiene los scripts de línea de comandos que automatizan la descarga, filtrado regional y consolidación de las emisiones RETC (fuentes puntuales) para la Región Metropolitana.

## Requisitos
- Python 3.8 o superior
- Paquetes: `requests`, `beautifulsoup4`, `pandas`, `openpyxl` (para XLSX), `matplotlib` (para gráficos)
- Dependencias opcionales: `geopandas`, `shapely` cuando se realicen análisis geoespaciales en notebooks

## Estructura resumida
```
RetC/
├── codigo/
│   └── src/
│       ├── descarga_retc.py
│       ├── filtrado_region_todo.py
│       ├── consolidar_efp.py
│       ├── consolidar_global_2005_2023.py
│       ├── graficar_emisiones_por_grupo.py
│       └── inspeccionar_ruea_headers.py
├── data/
│   ├── raw/descargas_retc/
│   ├── interim/filtrados_region/
│   └── processed/
└── outputs/
    ├── tablas/
    └── graficos/
```

## Flujos principales
1. **Descarga:**
   ```bash
   cd codigo/src
   python descarga_retc.py
   ```
   Los archivos CSV/XLS/XLSX se guardarán en `../data/raw/descargas_retc/`.

2. **Diagnóstico opcional de encabezados:**
   ```bash
   python inspeccionar_ruea_headers.py
   ```
   Esto genera metadatos en `../data/interim/diagnostico_archivos_originales/`.

3. **Filtrado Región Metropolitana:**
   ```bash
   python filtrado_region_todo.py --region "Metropolitana de Santiago"
   ```
   Los resultados quedan en `../data/interim/filtrados_region/` (CSV y XLSX).

4. **Consolidación EFP 2005–2022 y mezcla con RUEA 2023:**
   ```bash
   python consolidar_efp.py --indir ../data/interim/filtrados_region/CSV
   python consolidar_global_2005_2023.py --indir ../outputs/tablas/retc_consolidados/RETConsolidado_original
   ```

5. **Gráficos históricos:**
   ```bash
 python graficar_emisiones_por_grupo.py \
    --in ../outputs/tablas/datos_resumidos/LBP_AIRE_<DATETIME>_emisiones_por_anio_y_grupo_pivot.csv \
    --outdir ../outputs/graficos
   ```

## Verificación rápida
```bash
ls -lh ../data/raw/descargas_retc | head
wc -l ../outputs/tablas/retc_consolidados/RETConsolidado_original/EFP_RM_2005_2022_consolidado.csv
ls ../outputs/graficos | head
```

## Notas
- Todos los scripts aceptan rutas absolutas o relativas; ajusta los argumentos `--indir`, `--out` y `--root` según necesites.
- Trabaja desde un entorno virtual (`python -m venv .venv`) y sincroniza las dependencias en `requirements.txt`.
- Para análisis geoespacial utiliza los notebooks de `notebooks/20_geoespacial/` y guarda los resultados listos en `geo/public/` y `outputs/mapas/`.
