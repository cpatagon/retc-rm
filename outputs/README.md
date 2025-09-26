# Outputs

Resultados listos para compartir o referenciar en informes.

- `tablas/`: agregados curados en CSV u otros formatos livianos, con README o comando de regeneración.
- `graficos/`: figuras estáticas (PNG/SVG). Indicar scripts o notebooks que las producen.
- `mapas/`: productos geoespaciales finales (GeoJSON, imágenes, layouts). Utiliza el prefijo `LBP_AIRE_<DATETIME>_` y acompáñalos con la metadata pertinente.

Evita incluir archivos mayores a ~50 MB; considera comprimirlos externamente o documentar cómo generarlos bajo demanda.
