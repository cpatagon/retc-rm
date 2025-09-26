# Geo

Estructura para los insumos y resultados geoespaciales del proyecto.

- `insumos/`: capas originales (shapefiles, GeoPackages, proyectos QGIS). Mantenerlas fuera de Git y documentar su procedencia.
- `processed/`: versiones reproyectadas o saneadas. Registrar CRS y transformaciones aplicadas.
- `public/`: extractos livianos listos para publicar (GeoJSON, GPKG reducidos, CSV con geometría WKT). Usa el prefijo `LBP_AIRE_<DATETIME>_` y describe los pasos para reproducirlos.

Todas las capas deben trabajar en `EPSG:4326` salvo que se indique lo contrario. Anexa su metadato ISO 19115/19115-2 correspondiente en `metadata/iso19115/`.
