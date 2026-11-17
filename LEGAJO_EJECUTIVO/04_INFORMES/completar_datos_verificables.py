"""Añade cotas de fuente y planilla gráfica parcial, sin tocar el modelo."""
from pathlib import Path
import os, csv, json, hashlib, importlib.util
os.environ.setdefault('MPLCONFIGDIR','/tmp/cassafus-mpl')
import ezdxf
from ezdxf.math import Vec2
P=Path(__file__).resolve().parents[1]; R=P.parent
spec=importlib.util.spec_from_file_location('revision',P/'04_INFORMES/preparar_revision.py');rev=importlib.util.module_from_spec(spec);spec.loader.exec_module(rev)
source=ezdxf.readfile(R/'CASAFUS_99.dxf')
d=ezdxf.readfile(P/'01_CAD/CASSAFFOUSTH_revision_parcial.dxf')
original={e.dxf.handle:rev.tags(e) for e in source.modelspace()}
records=[]

def bounds(h):
 e=source.entitydb[h];pts=list(e.get_points('xy'))
 return min(p[0] for p in pts),max(p[0] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts)

def add_dim(l,a,b,offset,axis,handles,meaning):
 v=list(l.query('VIEWPORT'))[-1]; s=v.dxf.height/v.dxf.view_height
 c=Vec2(v.dxf.center); m=Vec2(v.dxf.view_center_point)
 def mp(p):return tuple(c+(Vec2(p)-m)*s)
 pa,pb=mp(a),mp(b)
 base=(min(pa[0],pb[0])-offset,(pa[1]+pb[1])/2) if axis=='Y' else ((pa[0]+pb[0])/2,min(pa[1],pb[1])-offset)
 q=l.add_linear_dim(base=base,p1=pa,p2=pb,angle=90 if axis=='Y' else 0,dimstyle='COTA200',
   dxfattribs={'layer':'AR-07- Cota 1_1'},override={'dimlfac':1/s,'dimscale':5,'dimpost':'<> u'})
 q.render()
 records.append(dict(plano=l.name,handles=handles,concepto=meaning,eje=axis,
  x1=a[0],y1=a[1],x2=b[0],y2=b[1],valor_u=abs(b[1]-a[1]) if axis=='Y' else abs(b[0]-a[0])))

for code in ['P01','P03','P16','P17']:
 l=d.layouts.get('REV_'+code)
 x1,x2,y1,y2=bounds('2AD03F')
 add_dim(l,(x2,y1),(x2,y2),-25,'Y','2AD03F','Longitud geométrica muro lateral')
 a,b,c,e=bounds('2AD04F');add_dim(l,(a,e),(b,e),-20,'X','2AD04F','Tramo de cabecera entre extremos de polilínea')
 # Huecos entre macizos: extremos reales de las líneas, sin clasificación supuesta.
 if code in ['P01','P16']:
  for h in ['2AD035','2AD037','2AD039','2AD045','2AD048']:
   ent=source.entitydb[h];add_dim(l,ent.dxf.start,ent.dxf.end,12,'Y',h,'Tramo vertical de abertura dibujada, no altura')
 if code=='P17':
  for i,h in enumerate(['2AD018','2AD01C','2AD020']):
   a,b,c,e=bounds(h);add_dim(l,(a,c),(b,c),20+i*10,'X',h,'Envolvente horizontal de equipamiento original')
 l.add_mtext('COTAS AGREGADAS: unidades de dibujo (u). No expresan metros confirmados. Las cotas de huecos en planta son longitudes en planta, no alturas. Trazabilidad: cotas_fuente.csv.',dxfattribs={'insert':(525,205),'width':270,'char_height':3,'style':'Arial','layer':'0'})

# Trama de pérgola: documentar vigas proyectadas sin convertirlas en apoyos.
beams=['2AD26F','2AD271','2AD273','2AD275','2AD277','2AD279','2AD27B','2AD27D']
beam_rows=[]
for h in beams:
 e=source.entitydb[h];a=e.dxf.start;b=e.dxf.end
 beam_rows.append(dict(handle=h,x1=a.x,x2=b.x,y=a.y,ancho_u=abs(b.x-a.x)))
for code in ['P04','P20','P21']:
 l=d.layouts.get('REV_'+code)
 # Cubierta es otra vista: sin asociar su posición con las coordenadas de planta.
 # Dimensiones nuevas se muestran como tabla de fuente, sin sobreponer ejes inventados.
 lines=['TRAMA EN PLANTA: FUENTE DE PROYECCION', 'No equivale a ejes de columnas ni fundaciones.']
 for i,(a,b) in enumerate(zip(beam_rows,beam_rows[1:]),1):
  lines.append(f'T{i:02}: separacion de lineas = {abs(b["y"]-a["y"]):.6f} u')
 l.add_mtext('\\P'.join(lines),dxfattribs={'insert':(525,220),'width':275,'char_height':3,'style':'Arial','layer':'0'})

# Carpinterías: representación existente en planta, sin inventar vistas frontales.
l=d.layouts.new('REV_P19');l.page_setup(size=(841,594),margins=(10,10,10,10),units='mm')
def txt(t,x,y,size=3):l.add_text(t,dxfattribs={'insert':(x,y),'height':size,'style':'Arial','layer':'0'})
txt('P19 | Inventario grafico parcial de carpinterias',20,550,5)
txt('SIMBOLOS EN PLANTA - NO SON ELEVACIONES - NO APTO PARA OBRA',20,537)
for i,(name,h,code,width) in enumerate([('PD-0 (1)','2AD007','PD-0','1.20'),('P-3 (1)','2AD00A','P-3','0.90'),('P-4 (1)','2AD00B','P-4','0.80')]):
 x=100+i*250;txt(code,x-50,485,5)
 l.add_blockref(name,(x,360),dxfattribs={'xscale':70,'yscale':70,'layer':source.entitydb[h].dxf.layer})
 txt('Ancho rotulado original: '+width+' (unidad pendiente)',x-65,330)
 txt('Cantidad en planta seleccionada: 1',x-65,318)
 txt('Fuente: INSERT '+h,x-65,306)
 txt('Alto, materiales y condicion: no definidos',x-65,294)
 txt('Representacion ampliada sin escala',x-65,282)
l.add_mtext('Inventario parcial: no se cuentan las plantas repetidas como unidades adicionales. Las carpinterias dibujadas con entidades sueltas siguen pendientes de identificacion. No se infieren alturas, vidrios, perfiles ni terminaciones. Coordenadas y anchos geometricos: P19_inventario_parcial.csv.',dxfattribs={'insert':(30,220),'width':740,'char_height':4,'style':'Arial','layer':'0'})

# Exact geometry-derived quantities; no area of premises inferred from walls.
areas=[]
for h in ['2AD018','2AD01C','2AD020']:
 e=source.entitydb[h]
 if e.closed:
  pts=list(e.get_points('xy'));area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))/2)
  areas.append(dict(handle=h,concepto='Proyeccion poligonal de equipamiento, no superficie de local',area_u2=area,material='No especificado'))
def savecsv(name,rows):
 with (P/'03_PLANILLAS'/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
savecsv('cotas_fuente.csv',records);savecsv('pergola_trama_proyectada.csv',beam_rows)
if areas:savecsv('superficies_geometricas_parciales.csv',areas)
path=P/'01_CAD/CASSAFFOUSTH_datos_verificables.dxf';d.saveas(path)
r=ezdxf.readfile(path)
assert original=={e.dxf.handle:rev.tags(e) for e in r.modelspace()}
audit=r.audit();assert not audit.errors and not audit.fixes
for e in r.layouts:
 for dim in e.query('DIMENSION'):
  assert dim.dxf.geometry in r.blocks
print('CAD verificado; cotas nuevas',len(records),flush=True)
# PDFs: fuente recortada y anotaciones de papel en el mismo encuadre físico.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf.addons.drawing import RenderContext,Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
ctx=RenderContext(r);codes=['P01','P03','P04','P08','P16','P17','P18','P19','P20','P21']
with PdfPages(P/'02_PDF/CASSAFFOUSTH_datos_verificables.pdf') as pdf:
 for code in codes:
  layout=r.layouts.get('REV_'+code);ctx.set_current_layout(layout);fig=plt.figure(figsize=(841/25.4,594/25.4))
  ax=fig.add_axes([0,0,1,1]);back=MatplotlibBackend(ax,adjust_figure=False)
  Frontend(ctx,back).draw_entities([e for e in layout if e.dxftype()!='VIEWPORT']);back.finalize();ax.set_xlim(0,841);ax.set_ylim(0,594);ax.set_aspect('equal',adjustable='box');ax.axis('off')
  vs=list(layout.query('VIEWPORT'))
  if vs:
   v=vs[-1];cx,cy=v.dxf.center.x,v.dxf.center.y;w,h=v.dxf.width,v.dxf.height
   va=fig.add_axes([(cx-w/2)/841,(cy-h/2)/594,w/841,h/594]);bk=MatplotlibBackend(va,adjust_figure=False)
   mx,my=v.dxf.view_center_point.x,v.dxf.view_center_point.y;mh=v.dxf.view_height;mw=mh*w/h
   selected=[]
   for e in r.modelspace():
    p=rev.anchor(e)
    if p is not None and mx-mw/2-20<p[0]<mx+mw/2+20 and my-mh/2-20<p[1]<my+mh/2+20 and e.dxftype() not in ('IMAGE','PDFUNDERLAY'):selected.append(e)
   Frontend(ctx,bk).draw_entities(selected);bk.finalize();va.set_xlim(mx-mw/2,mx+mw/2);va.set_ylim(my-mh/2,my+mh/2);va.set_aspect('equal',adjustable='box');va.axis('off');va.patch.set_alpha(0)
   ax.set_zorder(2);ax.patch.set_alpha(0)
  pdf.savefig(fig);fig.savefig(P/f'02_PDF/{code}_acotado.pdf');plt.close(fig);print(code,flush=True)
(P/'04_INFORMES/validacion_acotado.json').write_text(json.dumps(dict(cotas_nuevas=len(records),entidades_modelo_original=len(original),modelo_preservado=True,auditoria_errores=0,planos_con_datos_disponibles=codes,escala_obra_validada=False,legajo_ejecutivo_completo=False),indent=2))
