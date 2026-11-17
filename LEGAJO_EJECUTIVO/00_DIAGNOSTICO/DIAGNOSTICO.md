# Diagnóstico de fuentes — revisión parcial

No se ha completado el legajo ejecutivo de 21 planos. Se organizaron nueve ventanas de revisión del dibujo original y un inventario parcial de carpinterías. Estas vistas no sustituyen planos específicos acotados. Las escalas de impresión no están validadas.

## Auditoría

Fuente: rama Casafus, commit 18d93d72e9ef2005a852a21963ea0a0b2518b2d1. DXF AC1032, 3903 entidades en modelo, 41 capas, 459 hatches, 775 INSERT, dos DIMENSION. Esas dos cotas están en el sector de plaza ajeno al edificio: no sirven para validar dimensiones de la cantina. El inventario JSON registra colores, grosores, tipos, bloques y estilos.

El archivo contiene documentación ajena (plaza, vegetación y biblioteca), relevamiento, relevamiento ajustado, plantas de proyecto, cubiertas y secciones. Las posiciones de presentación no son coordenadas reales de obra. No se incorporó la plaza como implantación del colegio.

La planta seleccionada se encuentra aproximadamente en X=2415–2480, Y=380–445. La cubierta está en X=2543–2608, Y=380–445. Hay plantas similares superiores desplazadas aproximadamente 376,226534 unidades en Y; no se contaron como obra adicional. Las secciones seleccionadas están aproximadamente en X=2438–2475, Y=289–329. No se da por demostrada su correspondencia con A–B y C–D.

## Contradicciones que no se corrigieron

- INSUNITS=4 declara milímetros. Puertas rotuladas 0,80/0,90/1,20 tienen envolventes horizontales del símbolo de 0,80/0,90/1,20 unidades, compatibles con metros. Se requiere confirmar la unidad antes de rotular o certificar escalas.
- Aula exterior: +2,11 en planta y +2,16 en corte. Explanada: +1,08 en planta y +1,16 en corte. Solado natural: +1,06 en corte. El informe menciona un desnivel existente de 1,05 m. No se unificaron referencias altimétricas ni se dedujeron pendientes de estos valores.
- La presencia de artefactos no determina recorridos de instalaciones. Los colores de bloques y capas tampoco confirman por sí solos demoliciones o condición de carpinterías.

## Espacio papel y referencias

Existen layouts Asiento, CASAFUS, PODU (3), PODU (4), PODU (5) y Model. CASAFUS usa A1; otros usan A3. Sus ventanas tienen factores diferentes y no validan automáticamente el nuevo legajo. Hay referencias PDF y una imagen satelital en modelo con rutas externas no disponibles. No se inventaron sustitutos. Las fuentes SHX y la tabla CTB no se adjuntaron; las vistas PDF pueden sustituir tipografías y no certifican el ploteo original.

## Producción y alcance

Se conservan modelo y layouts originales en una copia nueva. Se añaden REV_P01, REV_P03, REV_P04, REV_P08, REV_P16, REV_P17, REV_P18, REV_P20 y REV_P21, claramente marcados sin escala validada y no aptos para obra. Las vistas de planta repetidas son bases de coordinación, no planos de especialidad terminados. P19 tiene CSV parcial: una ocurrencia por código en la planta seleccionada; las copias del modelo no se suman. Se distinguen ancho rotulado y envolvente geométrica del símbolo; no se infiere altura.

Consultar matriz_planos.csv para el estado de las 21 piezas. No se produjeron fachadas, instalaciones o fundaciones mediante datos supuestos. Tampoco se completó el acotado integral. Las mediciones CSV son tramos verificables en unidades de dibujo, no cotas ejecutivas.
