"""Auditoría y documentación de fuentes; no resuelve decisiones del proyectista.

Ejecutar desde cualquier directorio con Python, ezdxf, python-docx y matplotlib.
No modifica los originales. Las láminas REV son documentos de revisión sin
escala de obra validada, no el legajo ejecutivo solicitado.
"""
from pathlib import Path
import os
import json
import csv
import hashlib
from collections import Counter

os.environ.setdefault('MPLCONFIGDIR', '/tmp/cassafus-mpl')
import ezdxf
from ezdxf.lldxf.tagwriter import TagCollector
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'LEGAJO_EJECUTIVO'
SOURCE = ROOT / 'CASAFUS_99.dxf'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def anchor(e):
    if e.dxftype() == 'LINE':
        return e.dxf.start
    if e.dxftype() == 'LWPOLYLINE' and len(e):
        return e.get_points()[0]
    for key in ('insert', 'center', 'defpoint'):
        if e.dxf.is_supported(key) and e.dxf.hasattr(key):
            return e.dxf.get(key)
    return None

def tags(e):
    # Omisiones documentadas del escritor para atributos DXF predeterminados.
    defaults = {
        'LWPOLYLINE': {(43, '0.0')},
        'MTEXT': {(72, '1'), (73, '1'), (44, '1.0')},
        'INSERT': {(280, '0')}, 'ATTDEF': {(280, '0')},
        'SPLINE': {(210, '0.0'), (220, '0.0'), (230, '1.0'),
                   (43, '1e-10'), (44, '1e-10')},
    }
    return [(t.code, str(t.value)) for t in TagCollector.dxftags(e)
            if (t.code, str(t.value)) not in defaults.get(e.dxftype(), set())]

def write_csv(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    OUT.mkdir(exist_ok=True)
    originals = {p.name: digest(p) for p in
                 [SOURCE, ROOT / 'informe IPET Ing Cassafousth.docx']}
    d = ezdxf.readfile(SOURCE)
    m = d.modelspace()
    original_tags = {e.dxf.handle: tags(e) for e in m}
    audit = d.audit()
    assert not audit.errors and not audit.fixes, 'Revisar auditoría antes de guardar'
    data = {
        'source_sha256': originals,
        'dxf_version': d.dxfversion,
        'declared_units': d.units,
        'unit_status': 'Pendiente de confirmación: INSUNITS=4 (mm); geometría compatible con m.',
        'counts_modelspace': dict(Counter(e.dxftype() for e in m)),
        'audit_errors': len(audit.errors), 'audit_fixes': len(audit.fixes),
        'layers': [x.dxf.all_existing_dxf_attribs() for x in d.layers],
        'text_styles': [x.dxf.all_existing_dxf_attribs() for x in d.styles],
        'dim_styles': [x.dxf.all_existing_dxf_attribs() for x in d.dimstyles],
        'linetypes': [x.dxf.all_existing_dxf_attribs() for x in d.linetypes],
        'blocks': [{'name': b.name, 'count': len(b),
                    'xref': b.block.dxf.flags & 12 != 0} for b in d.blocks],
        'hatches': [dict(handle=e.dxf.handle, layer=e.dxf.layer,
                         pattern=e.dxf.pattern_name, solid=e.dxf.solid_fill,
                         scale=e.dxf.pattern_scale) for e in m.query('HATCH')],
        'original_layouts': [{
            'name': l.name, 'settings': l.dxf_layout.dxf.all_existing_dxf_attribs(),
            'viewports': [v.dxf.all_existing_dxf_attribs() for v in l.query('VIEWPORT')]
        } for l in d.layouts],
        'external_references_in_model': [{
            'handle': e.dxf.handle, 'type': e.dxftype(),
            'definition': str(d.entitydb[e.dxf.image_def_handle].dxf.filename)
            if e.dxftype() == 'IMAGE' else
            str(d.entitydb[e.dxf.underlay_def_handle].dxf.filename)
        } for e in m if e.dxftype() in ('IMAGE', 'PDFUNDERLAY')],
    }
    (OUT / 'auditoria_dxf.json').write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    texts = []
    for e in m:
        if e.dxftype() in ('TEXT', 'MTEXT'):
            texts.append(dict(handle=e.dxf.handle, layer=e.dxf.layer,
                              position=list(e.dxf.insert), text=e.plain_text()))
        if e.dxftype() == 'INSERT':
            for a in e.attribs:
                texts.append(dict(handle=a.dxf.handle, parent=e.dxf.handle,
                                  block=e.dxf.name, layer=a.dxf.layer,
                                  position=list(a.dxf.insert), tag=a.dxf.tag, text=a.dxf.text))
    (OUT / 'textos_dxf.json').write_text(json.dumps(texts, indent=2, ensure_ascii=False))
    doc = Document(ROOT / 'informe IPET Ing Cassafousth.docx')
    paragraphs = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        paragraphs.extend(' | '.join(c.text for c in r.cells) for r in t.rows)
    (OUT / 'informe_extraido.txt').write_text('\n'.join(paragraphs))

    # Una sola planta de proyecto: no contar sus copias como unidades de obra.
    doors = []
    for e in m.query('INSERT'):
        if not (2450 < e.dxf.insert.x < 2470 and 390 < e.dxf.insert.y < 435):
            continue
        if e.dxf.name not in ('PD-0 (1)', 'P-3 (1)', 'P-4 (1)'):
            continue
        b = d.blocks[e.dxf.name]
        label = [t.dxf.text for t in b.query('TEXT')]
        xs = [float(p[0]) for v in b.query('LWPOLYLINE') for p in v.get_points('xy')]
        span = (max(xs)-min(xs))*abs(e.dxf.xscale)
        doors.append(dict(codigo=label[1], bloque=e.dxf.name, handle=e.dxf.handle,
                          x=e.dxf.insert.x, y=e.dxf.insert.y,
                          ancho_rotulado=label[0], envolvente_x_simbolo_u=f'{span:.12f}',
                          cantidad_en_planta_seleccionada=1,
                          representacion_apertura='Dos hojas batientes' if len(b.query('ARC')) == 2 else 'Una hoja batiente',
                          alto='No definido', material='No definido', vidrio='No definido',
                          terminacion='No definida', condicion='No confirmada',
                          observacion='Inventario parcial de bloques codificados; no incluye todas las aberturas dibujadas con entidades sueltas.'))
    write_csv('P19_inventario_parcial.csv', doors)
    levels=[]
    for e in m.query('INSERT'):
        if e.dxf.name in ('NIVEL', 'NIVEL-VI-P') and 2400 < e.dxf.insert.x < 2650:
            levels.append(dict(handle=e.dxf.handle, bloque=e.dxf.name,
                               x=e.dxf.insert.x, y=e.dxf.insert.y,
                               atributos=' | '.join(f'{a.dxf.tag}: {a.dxf.text}' for a in e.attribs)))
    write_csv('niveles_originales.csv', levels)

    # Geometría de tramos identificables, sin convertir unidades ni fijar niveles.
    measurements=[]
    for handle, name in [('2AD03F','Muro lateral: extensión longitudinal'),
                         ('2AD04F','Muro de cabecera: extensión horizontal'),
                         ('2AD2C4','Muro transversal: extensión horizontal')]:
        e=d.entitydb[handle]; pts=e.get_points('xy')
        for axis in [0,1]:
            lo=min(float(p[axis]) for p in pts); hi=max(float(p[axis]) for p in pts)
            measurements.append(dict(handle=handle,descripcion=name,eje='XY'[axis],
                                     coordenada_min=lo,coordenada_max=hi,longitud_u=hi-lo,
                                     unidad='Unidad de dibujo, sin conversión'))
    write_csv('mediciones_verificables.csv',measurements)

    plan=(2415,2480,380,445)
    roof=(2543,2608,380,445)
    cuts=(2438,2475,289,329)
    othercut=(2560,2610,290,335)
    sheets = [
        ('P01','Planta arquitectónica general',plan,
         'Planta original bajo el rótulo PROYECTO. Se conservan locales, mobiliario, carpinterías y niveles. Faltan acotado integral y referencias coordinadas. Ver mediciones_verificables.csv.'),
        ('P03','Pisos, niveles y pendientes',plan,
         'Se conservan plataforma, rampa, cantero y niveles originales. Aula exterior +2.11 en planta frente a +2.16 en corte; explanada +1.08 frente a +1.16. No se calculan pendientes con niveles contradictorios. Materiales por sector pendientes.'),
        ('P04','Cubiertas y pérgola',roof,
         'Planta de cubierta existente en el archivo. Rótulo original: Nuevo sobretecho de chapa, superficie 75 m2. Esa superficie es texto del proyectista, no cómputo certificado. Faltan pendientes y especificaciones verificables de desagüe.'),
        ('P08','Cortes existentes: revisión',cuts,
         'Se conservan ambas secciones originales, sin equipararlas automáticamente a A-B o C-D. Falta confirmar correspondencia y sentido de corte. No se corrigen niveles ni se deducen espesores constructivos.'),
        ('P16','Carpinterías: ubicación parcial',plan,
         'Códigos originales identificados: PD-0, P-3, P-4. Coordinación parcial con P19_inventario_parcial.csv. Las aberturas no codificadas requieren inventario geométrico adicional; no se asignan condiciones nueva/existente por color.'),
        ('P17','Equipamiento y mobiliario',plan,
         'Equipamiento dibujado en la fuente, en sus posiciones originales. No se agregan muebles ni se renombran bloques genéricos como artefactos específicos. Faltan cotas integrales y confirmación de características técnicas.'),
        ('P18','Implantación: entorno inmediato',plan,
         'Sólo entorno inmediato verificable del edificio. No se utiliza la plaza ajena dibujada en otro sector del modelo. Faltan implantación escolar completa, límites de intervención confirmados y orientación. Escala solicitada 1:200 pendiente de unidades.'),
        ('P20','Cubierta: base para zinguería',roof,
         'Base de cubierta coordinada con P04. El informe exige rehacer canaletas y zinguería de borde por infiltraciones; no define trazados, bajadas, secciones ni localización inequívoca de cada patología. No se inventan ni se dibujan estos datos como confirmados.'),
        ('P21','Pérgola: base de ubicación',roof,
         'Geometría original de pérgola conservada. Esta lámina NO representa fundaciones definidas. Pendientes: identificación inequívoca de columnas frente a elementos de cubierta, ejes de apoyo, dimensionado por cálculo, suelo, cotas de fundación, zapatas, armaduras, placas y anclajes. No se agregan bases supuestas.'),
    ]
    source_windows=[]
    for code,title,box,note in sheets:
        l=d.layouts.new('REV_'+code)
        l.page_setup(size=(841,594),margins=(10,10,10,10),units='mm')
        l.add_text(f'{code} | {title}',dxfattribs={'height':5,'style':'Arial','layer':'0','insert':(15,555)})
        l.add_text('REVISION PARCIAL - SIN ESCALA VALIDADA - NO APTO PARA OBRA',dxfattribs={'height':3,'style':'Arial','layer':'0','insert':(15,545)})
        x1,x2,y1,y2=box
        v=l.add_viewport(center=(260,280),size=(480,480),
                         view_center_point=((x1+x2)/2,(y1+y2)/2),
                         view_height=max(x2-x1,y2-y1)+4,status=2)
        v.dxf.layer='Z-REF'
        l.add_mtext(note+'\n\nFuente: CASAFUS_99.dxf, rama Casafus.\nGeometría original sin desplazamientos.\n\nUnidades: INSUNITS=4 (mm). La geometría es compatible con metros, pendiente de confirmación. La ventana está ajustada sólo para revisión; no representa 1:100 ni 1:200.\n\nConsultar DIAGNOSTICO.md y matriz_planos.csv antes de continuar.',
                    dxfattribs={'char_height':3,'width':275,'style':'Arial','layer':'0','insert':(525,510)})
        source_windows.append(dict(plano=code,layout=l.name,box=box,note=note))
    path=OUT/'CASSAFFOUSTH_revision_parcial.dxf'
    d.saveas(path)
    reopened=ezdxf.readfile(path)
    after={e.dxf.handle:tags(e) for e in reopened.modelspace()}
    assert original_tags==after, 'Cambió el espacio modelo original'
    for name,h in originals.items():
        assert digest(ROOT/name)==h, f'Cambió el original {name}'
    check=reopened.audit()
    assert not check.errors and not check.fixes
    validation=dict(original_sha256=originals, modelspace_entities=len(after),
                    preserved_modelspace_exported_tags_after_default_normalization=True,
                    added_layouts=[x['layout'] for x in source_windows],
                    output_audit_errors=len(check.errors),output_audit_fixes=len(check.fixes),
                    scale_validated=False,complete_legajo=False)
    (OUT/'validacion.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False))
    (OUT/'ventanas_revision.json').write_text(json.dumps(source_windows,indent=2,ensure_ascii=False))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import RenderContext,Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    with PdfPages(OUT/'CASSAFFOUSTH_revision_fuentes.pdf') as pdf:
        for code,title,box,note in sheets:
            x1,x2,y1,y2=box
            selected=[]
            for e in m:
                p=anchor(e)
                if p is not None and x1-20<p[0]<x2+20 and y1-20<p[1]<y2+20 and e.dxftype() not in ('PDFUNDERLAY','IMAGE'):
                    selected.append(e)
            fig=plt.figure(figsize=(16.55,11.7))
            ax=fig.add_axes([.03,.08,.60,.78])
            back=MatplotlibBackend(ax, adjust_figure=False)
            Frontend(RenderContext(d),back).draw_entities(selected)
            back.finalize()
            ax.set_xlim(x1,x2);ax.set_ylim(y1,y2)
            ax.set_aspect('equal',adjustable='box')
            ax.axis('off')
            fig.text(.04,.95,code+' | '+title,fontsize=16)
            fig.text(.04,.92,'REVISIÓN PARCIAL · SIN ESCALA VALIDADA · NO APTO PARA OBRA',fontsize=11)
            import textwrap
            fig.text(.66,.82,'\n'.join(textwrap.wrap(note,48)),fontsize=11,va='top',linespacing=1.6)
            fig.text(.66,.42,'\n'.join(textwrap.wrap('Fuente: DXF original, sin rediseño. La vista previa puede sustituir fuentes tipográficas y no reproduce el estilo de ploteo CTB ausente. El DXF editable conserva estilos y entidades originales.',48)),fontsize=10,va='top',linespacing=1.5)
            fig.text(.04,.03,'Documento de revisión de fuentes. No constituye un plano completo ni una impresión a escala de obra.',fontsize=10)
            pdf.savefig(fig)
            if code in ('P01','P04','P08'):
                fig.savefig(OUT/(code+'_revision.png'),dpi=140)
            plt.close(fig)
    print(json.dumps(validation,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
