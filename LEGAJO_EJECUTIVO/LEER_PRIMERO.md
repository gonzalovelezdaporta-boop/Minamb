# Cassaffousth — documentación disponible

La entrega vigente es `01_CAD/CASSAFFOUSTH_datos_verificables.dxf` y `02_PDF/CASSAFFOUSTH_datos_verificables.pdf`. Son diez láminas de datos disponibles, no un legajo ejecutivo completo de 21 planos. Los archivos anteriores `revision_parcial` y `revision_fuentes` se conservan como antecedente; no incluyen las cotas añadidas.

## Avance nuevo

- 21 cotas nativas editables en espacio papel: longitud del muro lateral, cabecera, huecos representados en planta y envolventes de equipamiento. Coordenadas, valor y entidad fuente en `03_PLANILLAS/cotas_fuente.csv`. No se altera ninguna geometría de obra en el modelo.
- Planilla gráfica parcial P19 con tres símbolos originales en planta. No se sustituyen por elevaciones supuestas ni se inventan alturas. Las representaciones ampliadas no tienen escala de obra.
- Trama geométrica de pérgola: ancho y separaciones de líneas de proyección en CSV y notas de P04/P20/P21. Las vigas proyectadas no se declaran columnas ni bases.
- Superficies geométricas de tres polígonos de equipamiento en u². No son superficies de locales ni un cómputo total.

## Unidades y referencias

Las cotas se expresan en **u**, unidad de dibujo sin conversión. El DXF original declara milímetros y los símbolos son compatibles con metros. Las ventanas siguen ajustadas para revisión: no están certificadas a 1:100 o 1:200. Los niveles contradictorios de planta/corte se conservan. No se infieren pendientes.

## Alcance no resuelto

No están producidos los planos ejecutivos P02, P05, P06, P07, P09, P10, P11, P12, P13, P14 y P15. Las otras piezas son parciales. Faltan el acotado integral, clasificación de intervenciones, coordinación de secciones, alturas verificadas, recorridos de instalaciones, materiales definidos y cálculo de fundaciones. La matriz de 21 piezas detalla el estado. No se dibujaron trazados ni bases supuestos para completar artificialmente la lista.

## Reproducción del avance

Desde la raíz del repositorio:

    python LEGAJO_EJECUTIVO/04_INFORMES/completar_datos_verificables.py

Requiere el antecedente DXF guardado y las dependencias de Python del entorno. Es idempotente respecto del antecedente: regenera una salida nueva sin acumular cotas. No modifica originales ni configuración de entorno. No publica ni hace push.
