# Lineamientos del Repositorio

## Objetivo y Alcance
- Analizar brechas temporales y espaciales de emisiones RETC para la Región Metropolitana, cruzándolas con las Unidades del Paisaje.
- Garantizar reproducibilidad: cada resultado debe reconstruirse desde datos descargados y scripts versionados.

## Estructura del Proyecto
```
RetC/
├── codigo/src/                 # scripts del pipeline principal
├── notebooks/
│   ├── 00_exploracion/
│   ├── 10_transformaciones/
│   └── 20_geoespacial/         # cruces emisiones ↔ paisaje
├── data/
│   ├── raw/                    # descargas originales (gitignored)
│   ├── interim/                # intermedios limpios (gitignored)
│   └── processed/              # tablas ligeras publicables
├── geo/
│   ├── insumos/                # shapes originales (gitignored)
│   ├── processed/              # reproyecciones/limpiezas (gitignored)
│   └── public/                 # extractos livianos para GitHub
├── outputs/
│   ├── tablas/
│   │   └── publicados/
│   ├── graficos/
│   │   └── publicados/
│   └── mapas/                  # `LBP_AIRE_<DATETIME>_<descripcion>`
├── metadata/                   # fichas ISO 19115/19115-2, diccionarios
└── docs/
    └── metodologias/           # plantillas y guías (brechas, homologación)
```

## Comandos Clave
- Preparar entorno: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Descargar datos RAW: `python codigo/src/descarga_retc.py`.
- Normalizar por año: `python codigo/src/convertir_raw_a_csv_por_ano.py --indir ../data/raw/descargas_retc --outdir ../data/interim/01_emisiones_por_ano`.
- Filtrar Región Metropolitana: `python codigo/src/filtrar_region_metropolitana.py --indir ../data/interim/01_emisiones_por_ano --outdir ../data/interim/02_emisiones_por_ano_rm`.
- Fusionar tramos RM: `python codigo/src/fusionar_emisiones_por_grupo.py --indir ../data/interim/02_emisiones_por_ano_rm --outdir ../data/interim/03_emisiones_rm_fusionadas`.
- Canonizar contaminantes: `python codigo/src/estandarizar_contaminantes_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Canonizar actividad: `python codigo/src/estandarizar_ciiu_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Homologar emisiones totales: `python codigo/src/agregar_emision_total_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Generar ID único: `python codigo/src/agregar_id_unico_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Consolidar tabla única: `python codigo/src/fusionar_emisiones_consolidadas.py --indir ../data/interim/03_emisiones_rm_fusionadas --outdir ../data/interim/04_emisiones_consolidadas`.
- Enriquecer coordenadas y paisaje:
  * `python codigo/src/completar_coordenadas_con_centros.py --centros ../data/raw/comunas/comunas_rm_centros.csv --consolidado ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`
  * `python codigo/src/asignar_unidad_paisaje_rm.py --consolidado ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv --poligonos ../geo/insumos/UnidadesPaisajeRM/unidades-paisaje-V1.gpkg`
- Productos analíticos:
  * `python codigo/src/graficar_totales_por_variable.py --indir ../data/interim/emisiones_por_variable_fusionadas --outdir ../outputs/graficos/emisiones_totales`
  * `python codigo/src/graficar_distribucion_emisiones_por_contaminante.py --input ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`
  * Gráficos por paisaje 2023 en `outputs/graficos/emisiones_totales_por_paisaje/2023/`
- Extractos por contaminante: `python codigo/src/reconstruir_emisiones_por_variable.py` + `python codigo/src/exportar_extractos_por_variable.py`
- Consulta el cuaderno `notebooks/20_geoespacial/022_pipeline_emisiones_rm.ipynb` para ver el flujo completo.

## Estilo de Código y Notebooks
- Python 3.8+, indentación de 4 espacios, PEP 8 (`snake_case`, `CamelCase`, constantes en mayúsculas). Usa `pathlib.Path` y encapsula CLI en `main()`.
- Notebooks con prefijo numérico; limpia salidas pesadas antes de versionar.

## Flujo Geoespacial
- CRS oficial: `EPSG:4326 (WGS84)`; documenta cualquier reproyección en `geo/processed/`.
- Resguarda insumos QGIS (`*.qgz`, `*.shp`, `*.gpkg`) en `geo/insumos/`; publica derivados livianos (`GeoJSON`, `GPKG` filtrados) en `geo/public/`.
- Documenta cada capa con ficha ISO (título, alcance, CRS, linaje, fecha) bajo `metadata/iso19115/`.
- Exporta resultados espaciales con prefijo `LBP_AIRE_<DATETIME>_` y README con comandos de generación.

## Pruebas y Validación
- Agrega `pytest` para helpers reutilizables usando CSV/GeoJSON de muestra.
- Tras cada corrida compara salidas con `wc -l`, `head`, `geopandas.GeoDataFrame.plot()` y totales frente a `outputs/tablas/`.

## Commits y Pull Requests
- Commits en presente y de alcance acotado (`filtrado: normaliza CRS a EPSG:4326`).
- PRs deben detallar scripts/notebooks tocados, comandos de reproducción, artefactos regenerados y dependencias nuevas.
