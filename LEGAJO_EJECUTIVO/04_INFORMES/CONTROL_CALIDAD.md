# Control de calidad de la entrega parcial

- Originales: SHA-256 sin cambios, registrados en validacion.json.
- Copia CAD reabierta con ezdxf; 3903 entidades de modelo conservadas. Comparación de etiquetas por handle normalizando únicamente atributos predeterminados omitidos por el escritor (ver función tags del script). No es una comparación binaria del DXF ni una certificación de compatibilidad en AutoCAD.
- Auditoría ezdxf: cero errores, cero correcciones en entrada y salida.
- Nueve layouts de revisión añadidos; layouts originales preservados. No se certifica aún identidad de renderizado por ausencia de CTB/fuentes y referencias externas.
- Compilado PDF: nueve páginas; cada página tiene más de cien trazados vectoriales y ninguna imagen incrustada. Tamaño de página verificado. Los PDF son de revisión SIN escala validada.
- Se inspeccionó visualmente el mosaico control_pdf.png de las nueve páginas después de corregir el ajuste automático de tamaño de figura. No sustituye una revisión ejecutiva a tamaño de impresión.
- Matriz de estado: 21 entradas. No se declararon completas piezas no producidas. Sin instalaciones ejecutivas, sin fundaciones dimensionadas, sin acotado integral.
- P19: tres códigos extraídos de una sola planta; no equivale al total de carpinterías.
- Faltan controles de escalas, correspondencias completas, niveles coordinados y acotado integral. No apto para obra.

## Reproducción

En la raíz del repositorio, con Python, ezdxf, python-docx, matplotlib, PyMuPDF y Pillow disponibles:

    python LEGAJO_EJECUTIVO/04_INFORMES/preparar_revision.py
    python LEGAJO_EJECUTIVO/04_INFORMES/organizar.py

El primer script genera en la raíz de LEGAJO_EJECUTIVO; el segundo organiza las salidas y verifica los PDF. No modifica los archivos originales. Los informes Markdown y la matriz se conservan como documentación de esta revisión.

## Ampliación de datos verificables

Salida vigente: CASSAFFOUSTH_datos_verificables.dxf/pdf. Se verificaron 21 cotas nativas contra las coordenadas fuente y el factor DIMLFAC, con tolerancia absoluta de 1e-8 unidades. Las 3903 entidades originales de modelo conservan sus etiquetas normalizadas. Auditoría de salida: cero errores/correcciones. Compilado de diez páginas vectoriales, sin imágenes incrustadas, tamaño A1 comprobado; no implica escala de obra validada. Se inspeccionó el mosaico P01/P16/P17/P19 y se corrigió el contexto de color del renderizado de espacio papel. Las otras seis vistas conservan el encuadre anterior. No se certifica el legajo completo.

Se añadieron inventarios de artefactos y referencias explícitas de materiales, sin definir instalaciones ni asignar cantidades por símbolos superpuestos.
