# Cassaffousth — producción geométrica vigente

Los dibujos nuevos están en **01_CAD/PRODUCCION/** y **02_PDF/PRODUCCION/**. Las entregas anteriores fuera de esas carpetas se conservan como antecedentes y no representan esta producción.

- Maestro: `01_CAD/PRODUCCION/CASSAFFOUSTH_PRODUCCION.dxf`.
- Individuales: `P01.dxf` a `P21.dxf`.
- PDF individuales y compilado: `02_PDF/PRODUCCION/`.
- Carpinterías coordinadas: `03_PLANILLAS/PRODUCCION_carpinterias.csv`.

## Qué cambió

Se construyeron elevación de fachada hacia patio, sección longitudinal, reconstrucción de corte interior y desarrollo geométrico de rampa. Se agregó la elevación PD-0, referencias de vanos y modulación, cotas y geometría de coordinación. Las guías de vanos sin alturas NO son ventanas resueltas. El desarrollo de rampa NO adopta como perfil construido la secante entre niveles vecinos. Consultar las notas dibujadas en cada pieza.

## Unidades y escala

Los archivos nuevos usan metros, verificados mediante anchos rotulados y geométricos 0.80/0.90/1.20 de los bloques de puertas, dimensiones del símbolo frontal PD-0 y peldaños de 0.18 m. El INSUNITS=4 del original no es coherente con estas referencias; el original no se modifica. Los PDF usan 1:100, excepto P18 a 1:200, en A3, A2, A1 o A0 según extensión, a imprimir al 100 %. La sección R-R se coordina entre P03 y P05 sobre una normal al arco de referencia original, con ancho geométrico 1.198524 m. El tamaño del papel y un trazo de calibración de 1 m permiten comprobar la escala.

## Estado real

**No es un legajo ejecutivo completo ni apto para obra.** Todas las piezas mantienen datos indispensables pendientes y están marcadas como borrador. P11–P14 y P20 contienen bases de coordinación, no instalaciones diseñadas. P21 no contiene zapatas ni columnas supuestas. No se inventaron alturas de vanos, recorridos de instalaciones ni dimensionados estructurales para completar artificialmente los dibujos.

El maestro conserva intacta la geometría original y agrega los dibujos derivados como bloques `DOC_P01` a `DOC_P21`, separados al sur de la documentación original (Y menor que -900). Los archivos individuales contienen geometría editable local en metros. El cambio de origen de presentación no modifica posiciones relativas de obra.

Los pendientes están escritos en cada lámina y registrados en `04_INFORMES/PRODUCCION/produccion.json`. Las superficies parciales anteriores no son un cómputo general del edificio.

## Regeneración

Desde la raíz del repositorio, ejecutar en orden:

    python LEGAJO_EJECUTIVO/04_INFORMES/produccion_geometrica.py
    python LEGAJO_EJECUTIVO/04_INFORMES/limpiar_y_exportar.py
    python LEGAJO_EJECUTIVO/04_INFORMES/coordinar_maestro.py
    python LEGAJO_EJECUTIVO/04_INFORMES/verificar_produccion.py

Las fuentes originales no se sobrescriben. El paso de limpieza sólo elimina líneas exactamente duplicadas en copias derivadas y ajusta el papel sin cambiar la escala ni la geometría de proyecto.
