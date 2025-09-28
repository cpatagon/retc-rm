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
├── metadata/                   # fichas ISO 19115/19115-2 y catálogos
└── docs/
    └── metodologias/
```

## Comandos Clave
- Preparar entorno: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Descargar datos RAW: `python codigo/src/descarga_retc.py`.
- Normalizar por año: `python codigo/src/convertir_raw_a_csv_por_ano.py --indir ../data/raw/descargas_retc --outdir ../data/interim/01_emisiones_por_ano`.
- Filtrar Región Metropolitana: `python codigo/src/filtrar_region_metropolitana.py --indir ../data/interim/01_emisiones_por_ano --outdir ../data/interim/02_emisiones_por_ano_rm`.
- Fusionar tramos RM: `python codigo/src/fusionar_emisiones_por_grupo.py --indir ../data/interim/02_emisiones_por_ano_rm --outdir ../data/interim/03_emisiones_rm_fusionadas`.
- Canonizar contaminantes: `python codigo/src/estandarizar_contaminantes_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Canonizar actividad (CIIU + macro): `python codigo/src/estandarizar_ciiu_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Homologar emisiones totales: `python codigo/src/agregar_emision_total_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Generar ID único: `python codigo/src/agregar_id_unico_rm.py --indir ../data/interim/03_emisiones_rm_fusionadas`.
- Consolidar tabla única: `python codigo/src/fusionar_emisiones_consolidadas.py --indir ../data/interim/03_emisiones_rm_fusionadas --outdir ../data/interim/04_emisiones_consolidadas`.
- Completar coordenadas + unidad de paisaje:
  * `python codigo/src/completar_coordenadas_con_centros.py --centros ../data/raw/comunas/comunas_rm_centros.csv --consolidado ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`
  * `python codigo/src/asignar_unidad_paisaje_rm.py --consolidado ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv --poligonos ../geo/insumos/UnidadesPaisajeRM/unidades-paisaje-V1.gpkg`
- Productos analíticos:
  * Totales anuales: `python codigo/src/graficar_totales_por_variable.py --indir ../data/interim/emisiones_por_variable_fusionadas --outdir ../outputs/graficos/emisiones_totales`
  * Distribuciones de emisiones: `python codigo/src/graficar_distribucion_emisiones_por_contaminante.py --input ../data/interim/04_emisiones_consolidadas/retc_RM_consolidado.csv`
  * Totales 2023 por unidad de paisaje: ver `outputs/graficos/emisiones_totales_por_paisaje/2023/`
- Extractos por contaminante: `python codigo/src/reconstruir_emisiones_por_variable.py` + `python codigo/src/exportar_extractos_por_variable.py`
- Referencia rápida del flujo: `notebooks/20_geoespacial/022_pipeline_emisiones_rm.ipynb`

## Estilo de Código y Notebooks
- Python 3.8+, indentación de 4 espacios, PEP 8 (`snake_case`, `CamelCase`, constantes en mayúsculas). Usa `pathlib.Path` y encapsula CLI en `main()`.
- Notebooks con prefijo numérico; limpia salidas pesadas antes de versionar.

## Flujo Geoespacial
- CRS oficial: `EPSG:4326 (WGS84)`; documenta cualquier reproyección en `geo/processed/`.
- Resguarda insumos QGIS (`*.qgz`, `*.shp`, `*.gpkg`) en `geo/insumos/`; publica derivados livianos (`GeoJSON`, `GPKG` filtrados) en `geo/public/`.
- Documenta cada capa con ficha ISO (título, alcance, CRS, linaje, fecha) bajo `metadata/iso19115/`.
- Exporta resultados espaciales con prefijo `LBP_AIRE_<DATETIME>_` y README con comandos de generación.

## Plantilla de Análisis de Brechas
- Documenta cada informe siguiendo la jerarquía:

```
4.1 Aire
  4.1.1 Meteorológicas y Climáticas (variables típicas de la Dirección Meteorológica de Chile: temperatura, humedad relativa, precipitación, radiación, viento, presión)
    4.1.1.1 Variable(s) Tipo #1
      Análisis de brechas en variable(s) tipo #1
        Unidad Alta Cordillera:
        Unidad Precordillera:
        Unidad Valle Central Agrícola:
        Unidad Valle Central Espinales:
        Unidad Cordillera de la Costa Sur:
        Unidad Cordillera de la Costa Norte:
        Unidad Áreas Urbanas:
      Análisis de brechas espaciales
        (mismas unidades)
      Análisis de brechas temporales
        (mismas unidades)
    4.1.1.2 Variable(s) Tipo #2
      (repetir estructura anterior)
    …
    4.1.1.N Variable(s) Tipo #N
      …
  4.1.2 Calidad del Aire
    (Repetir la estructura para cada Variable(s) Tipo #N, priorizando variables medidas por la red SINCA [`SO2`, `NOx`, `PM10`, `PM2.5`, etc.])
```

- Completa las secciones de cada unidad del paisaje con hallazgos cuantitativos y referencias a los scripts/notebooks utilizados.
- Incluye tablas o gráficos derivados en `outputs/tablas/publicados/` y `outputs/graficos/publicados/` con el prefijo `LBP_AIRE_<DATETIME>_`.
- Utiliza la plantilla editable en `docs/metodologias/plantilla_analisis_brechas.md`.

## Homologación de Términos y Formatos
- Consulta `docs/metodologias/homologacion_terminos_formatos.md` para unificar unidades, estilos tipográficos, numeración y uso de acrónimos.
- Asegura que tablas, figuras y anexos sigan las convenciones descritas antes de publicarlos en `outputs/`.

## Pruebas y Validación
- Agrega `pytest` para helpers reutilizables usando CSV/GeoJSON de muestra.
- Tras cada corrida compara salidas con `wc -l`, `head`, `geopandas.GeoDataFrame.plot()` y totales frente a `outputs/tablas/`.

## Commits y Pull Requests
- Commits en presente y de alcance acotado (`filtrado: normaliza CRS a EPSG:4326`).
- PRs deben detallar scripts/notebooks tocados, comandos de reproducción, artefactos regenerados y dependencias nuevas.
