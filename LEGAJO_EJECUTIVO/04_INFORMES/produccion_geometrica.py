"""Producción de dibujos derivados. Originales inmutables. Unidad: metro.
Los borradores no sustituyen decisiones de proyecto ni relevamiento.
"""
from pathlib import Path
from collections import Counter
import os,math,json,csv,hashlib,importlib.util
os.environ.setdefault('MPLCONFIGDIR','/tmp/cassafus-mpl')
import ezdxf
from ezdxf.math import Matrix44
from ezdxf import bbox
P=Path(__file__).resolve().parents[1];ROOT=P.parent
CAD=P/'01_CAD/PRODUCCION';PDF=P/'02_PDF/PRODUCCION';QA=P/'04_INFORMES/PRODUCCION'
for p in [CAD,PDF,QA]:p.mkdir(exist_ok=True,parents=True)
SRC=ROOT/'CASAFUS_99.dxf';SHASH=hashlib.sha256(SRC.read_bytes()).hexdigest()
S=ezdxf.readfile(SRC)
X=2456.240591050409;Y=392.9952486034458;F=296.3008907962164
LAY={'cut':'AR-01-Muro 01','view':'AR-02- Vista 02-010','fine':'AR-02- Vista 03-015','proj':'AR-03- Proyeccion 01','dim':'AR-07- Cota 1_1','steel':'AR-01-Acero','text':'AR-07- Cota 1_1'}
log=[];registry=[];A={};CODES={}

def pts(e):
 if e.dxftype()=='LINE':return [e.dxf.start,e.dxf.end]
 if e.dxftype()=='LWPOLYLINE':return list(e.get_points('xy'))
 return []
def bounds(h):
 pp=pts(S.entitydb[h]);return min(p[0] for p in pp),max(p[0] for p in pp),min(p[1] for p in pp),max(p[1] for p in pp)
def template():
 d=ezdxf.readfile(SRC);d.units=6;m=d.modelspace()
 for e in list(m):m.delete_entity(e)
 for l in list(d.layouts):
  if l.name not in ('Model','CASAFUS'):d.layouts.delete(l.name)
 for e in list(d.layouts.get('CASAFUS')):d.layouts.get('CASAFUS').delete_entity(e)
 return d
class Sheet:
 def __init__(self,code,title,scale=100):
  self.code=code;self.title=title;self.scale=scale;self.d=template();self.m=self.d.modelspace();self.pending=[];self.sources=[];self.notes=[];self.new=Counter();self.dims=[];A[code]=self
 def line(self,a,b,k='view',source='',kind='derivada'):
  if math.dist(a[:2],b[:2])<1e-8:return
  e=self.m.add_line(a,b,dxfattribs={'layer':LAY[k]});self.new['LINE']+=1
  log.append(dict(plano=self.code,handle=e.dxf.handle,tipo='LINE',fuente=source,clase=kind));return e
 def poly(self,p,k='view',close=False,source='',kind='derivada'):
  e=self.m.add_lwpolyline(p,close=close,dxfattribs={'layer':LAY[k]});self.new['LWPOLYLINE']+=1;log.append(dict(plano=self.code,handle=e.dxf.handle,tipo='LWPOLYLINE',fuente=source,clase=kind));return e
 def rect(self,x,y,w,h,k='view',source=''):
  return self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],k,True,source)
 def text(self,t,x,y,h=.22):
  self.m.add_mtext(t,dxfattribs={'insert':(x,y),'char_height':h,'width':12,'style':'Arial','layer':LAY['text']})
 def dim(self,a,b,base,angle=0,source=''):
  if math.dist(a[:2],b[:2])<.009:return
  q=self.m.add_linear_dim(base=base,p1=a,p2=b,angle=angle,dimstyle='COTAS50',dxfattribs={'layer':LAY['dim']},override={'dimscale':2.5,'dimdec':2,'dimzin':0,'dimpost':'<>','dimlfac':1})
  q.render();value=abs(b[1]-a[1]) if angle==90 else abs(b[0]-a[0]);self.dims.append((q.dimension.dxf.handle,value,source))
 def copy(self,e,origin):
  try:
   c=e.copy();c.transform(Matrix44.translate(-origin[0],-origin[1],0));self.m.add_entity(c);return c
  except (NotImplementedError,ezdxf.DXFError):return None
 def source_window(self,box,origin,only=None):
  x1,x2,y1,y2=box
  for e in S.modelspace():
   if e.dxftype() in ('IMAGE','PDFUNDERLAY','DIMENSION','ATTDEF'):continue
   if only and e.dxf.layer not in only:continue
   pp=pts(e)
   if pp:
    # Keep complete entities only. No trimming or alteration of design geometry.
    if not all(x1-1e-6<=p[0]<=x2+1e-6 and y1-1e-6<=p[1]<=y2+1e-6 for p in pp):continue
   elif e.dxf.is_supported('insert') and e.dxf.hasattr('insert'):
    p=e.dxf.insert
    if not(x1<=p.x<=x2 and y1<=p.y<=y2):continue
   elif e.dxftype() in ('ARC','CIRCLE'):
    p=e.dxf.center
    if not(x1<=p.x<=x2 and y1<=p.y<=y2):continue
   elif e.dxftype()=='HATCH':
    b=bbox.extents([e],fast=True)
    if not b.has_data or not(x1<=b.extmin.x and b.extmax.x<=x2 and y1<=b.extmin.y and b.extmax.y<=y2):continue
   else:continue
   c=self.copy(e,origin)
   if c:self.sources.append(e.dxf.handle)
 def level(self,x,z,value,label=''):
  self.poly([(x,z+.10),(x+.10,z),(x-.1,z)],'dim',source='símbolo de nivel original: convención triangular')
  self.line((x,z),(x+.9,z),'dim');self.text(f'{value:+.2f} {label}',x+.15,z+.35,.18)
 def finish(self):
  # Fixed plotting scale: model metres -> paper millimetres.
  self.d.layouts.rename('CASAFUS',self.code);l=self.d.layouts.get(self.code)
  b=bbox.extents([e for e in self.m if e.dxftype() not in ('MTEXT','TEXT')],fast=True);assert b.has_data
  center=((b.extmin.x+b.extmax.x)/2,(b.extmin.y+b.extmax.y)/2)
  factor=1000/self.scale
  pw,ph=(841,594) if b.size.x<61 and b.size.y<45 else (1189,841)
  vpw,vph=pw-231,ph-144;vh=vph/factor;vw=vpw/factor
  assert b.size.x<vw and b.size.y<vh,(self.code,b.size,vw,vh)
  l.page_setup(size=(pw,ph),margins=(0,0,0,0),units='mm')
  l.add_viewport(center=(20+vpw/2,60+vph/2),size=(vpw,vph),view_center_point=center,view_height=vh,status=2,dxfattribs={'layer':'Z-REF'})
  def note(t,x,y,h=3,width=180):l.add_mtext(t,dxfattribs={'insert':(x,y),'char_height':h,'width':width,'style':'Arial','layer':'0'})
  state='BORRADOR - DATOS INDISPENSABLES PENDIENTES' if self.pending else 'DOCUMENTACION GEOMETRICA DERIVADA'
  note(f'{self.code} | {self.title}',20,ph-24,5,pw-40)
  note(f'1:{self.scale} | Modelo en metros | papel {pw} x {ph} mm | Imprimir al 100 %',20,ph-42,3,pw-40)
  note(state,20,ph-56,3,pw-40)
  texts=['FUENTES Y ALCANCE']+self.notes+(['PENDIENTES']+self.pending if self.pending else [])
  note('\\P\\P'.join(texts),pw-191,ph-89,2.8,170)
  note('Sin rediseño. Cotas en metros. Originales conservados. La escala de impresión no certifica datos técnicos pendientes.',20,30,2.5,800)
  l.add_line((20,45),(20+factor,45),dxfattribs={'layer':LAY['dim']})
  note('Control: 1 metro',25+factor,47,2.5,100)
  path=CAD/(self.code+'.dxf');self.d.saveas(path)
  r=ezdxf.readfile(path);au=r.audit();assert not au.errors and not au.fixes,(self.code,len(au.errors),len(au.fixes))
  for handle,value,source in self.dims:
   e=r.entitydb[handle];assert math.isclose(e.get_measurement(),value,abs_tol=1e-7)
  registry.append(dict(plano=self.code,titulo=self.title,escala=self.scale,estado=state,entidades_nuevas=dict(self.new),cotas=len(self.dims),pendientes=self.pending,fuentes=self.sources))
  return r

# References: exact floor/roof/bar offsets from the two source sections.
hclear=2.45;hpergola=2.60;hbeam=2.70
roof_front=bounds('2B058D')[2]-318.544512714517
width=9.25;length=35.0
openings=[]
for i,h in enumerate(['2AD035','2AD037','2AD039','2AD045','2AD048'],1):
 e=S.entitydb[h];aa,bb=sorted([e.dxf.start.y-Y,e.dxf.end.y-Y]);openings.append((aa,bb,f'A{i:02}',h));CODES[f'A{i:02}']=(bb-aa,'Altura y tipo no definidos',h)

# P09 first: a genuinely constructed elevation, not another viewport of plan.
s=Sheet('P09','Fachada hacia patio: proyeccion coordinada')
s.line((0,0),(length,0),'cut','2AD03F / 2AD811')
s.line((0,hclear),(length,hclear),'view','2AD8AE / 2B0623')
s.line((0,roof_front),(length,roof_front),'view','2AD812 / 2B058D')
s.line((0,0),(0,roof_front),'cut','2AD031');s.line((length,0),(length,roof_front),'cut','2AD04F')
# The longitudinal band is derived from a straight continuous canopy in roof plan.
lo=388.2304294685407-Y;hi=424.245248603446-Y
s.rect(lo,hpergola,hi-lo,.10,'steel','2AD8B9 / 2AD265 / 2AD26F')
for a,b,c,h in openings:
 # Vertical guides locate widths without asserting unknown sill/head.
 s.line((a,-.75),(a,hclear),'proj',h);s.line((b,-.75),(b,hclear),'proj',h)
 s.dim((a,0),(b,0),((a+b)/2,-1.25),source=h);s.text(c,(a+b)/2-.2,-1.7,.18)
s.dim((0,0),(length,0),(0,-2.5),source='2AD03F');s.dim((length,0),(length,hclear),(length+1.3,0),90,'2AD8AE')
s.dim((0,0),(0,roof_front),(-1.3,0),90,'2B058D');s.level(-1.8,0,2.16,'NPT interior, referencia de corte')
s.notes=['Silueta longitudinal derivada de planta y alturas coincidentes en las dos secciones.','Guías de vanos A01-A05: posición y ancho verificados; NO son contornos de ventanas.','Banda de pérgola: sección 2AD8B9 y desarrollo de planta. No se repiten columnas supuestas.']
s.pending=['Antepechos, dinteles y tipología de vanos exteriores.','Posición completa de columnas y terminaciones de borde.','Cotas altimétricas de plataforma contradictorias.']

# P05: curved ramp: actual plan geometry and level endpoints, not an invented profile.
s=Sheet('P05','Rampa: seccion y desarrollo geometricos')
arc=S.entitydb['2AEEFA'];L=arc.dxf.radius*math.radians(arc.dxf.end_angle-arc.dxf.start_angle)
# End levels in adjacent floor zones are kept visible; no fabricated constant grade.
s.line((-1,1.08),(0,1.08),'cut','2ACFDF');s.line((L,2.11),(L+1,2.11),'cut','2AEF5D')
s.line((0,1.08),(L,2.11),'proj','2AEEFA + 2ACFDF + 2AEF5D')
s.text('SECANTE DE NIVELES ADYACENTES; NO PERFIL CONSTRUIDO',0,3.4,.20)
s.level(-.7,1.08,1.08,'explanada, planta');s.level(L-.6,2.11,2.11,'aula exterior, planta')
s.dim((0,1.08),(L,2.11),(0,.0),source='longitud de arco de 2AEEFA')
s.dim((L,1.08),(L,2.11),(L+2,0),90,'2ACFDF + 2AEF5D')
s.text(f'L desarrollada del eje dibujado: {L:.3f} m. Delta Z adyacente: 1.030 m.\nCociente geometrico: {100*1.03/L:.2f} %. No certifica pendiente de rampa.',0,-.8,.20)
# True cross width from arc intersections at a documented station.
theta=math.radians((arc.dxf.start_angle+arc.dxf.end_angle)/2)
normal=(math.cos(theta),math.sin(theta));station=(arc.dxf.center.x+arc.dxf.radius*normal[0],arc.dxf.center.y+arc.dxf.radius*normal[1]);tt=[]
for h in ['2AEE5C','2AEE5D']:
 a=S.entitydb[h];delta=(station[0]-a.dxf.center.x,station[1]-a.dxf.center.y);dot=sum(x*y for x,y in zip(delta,normal));disc=dot*dot-sum(x*x for x in delta)+a.dxf.radius**2;tt.append(min([-dot+math.sqrt(disc),-dot-math.sqrt(disc)],key=abs))
w=abs(tt[1]-tt[0]);s.line((0,-3.2),(0,-3.7),'cut','2AEE5C');s.line((w,-3.2),(w,-3.7),'cut','2AEE5D')
s.dim((0,-3.2),(w,-3.2),(0,-4.3),source='intersección normal al eje medio 2AEEFA con 2AEE5C/5D')
s.text('CORTE R-R: NORMAL AL TRAZO ORIGINAL EN ESTACION MEDIA\nCota de superficie, pendiente transversal y terreno: pendientes.',0,-4.7,.20)
s.notes=['Contornos y eje curvos del DXF; no se sustituyen por una rampa recta.','Se construyen cotas de longitud desarrollada, ancho transversal y diferencia de niveles.']
s.pending=['Perfil real de terreno y superficie de rampa.','Confirmar qué niveles corresponden a sus extremos: el corte usa +1.16/+2.16.','No se adopta pendiente constante ni se rediseña para accesibilidad.']

# P06: transverse interior cut facing canteen, drawn from actual section coordinates.
s=Sheet('P06','Seccion transversal interior hacia cantina')
# Redraw principal constructive profiles from source, omitting library people/trees.
for h in ['2B058B','2B058D','2B0590','2B0591','2B0592','2B0593','2B0594','2B0596','2B0598','2B0599','2B059F','2B05A9','2B05AA','2B05AB','2B05AC','2B061E','2B061F','2B0620','2B0623','2B0624','2B060B','2B060C','2B0756']:
 e=S.entitydb[h];pp=[(float(p[0])-X,float(p[1])-318.544512714517) for p in pts(e)]
 s.poly(pp,'cut' if e.dxf.layer==LAY['cut'] else 'view',e.dxftype()=='LWPOLYLINE' and e.closed,h)
s.dim((.3,0),(8.95,0),(0,-1.8),source='2B0591');s.dim((.3,0),(.3,2.45),(-1,0),90,'2B0623')
s.dim((-3,0),(-3,2.60),(-4.2,0),90,'2B059F');s.dim((.3,0),(4.75016216215,0),(0,-2.6),source='2B05AC')
s.dim((8.95,0),(8.95,3.0),(10.6,0),90,'2B058B')
s.level(9.7,0,2.16,'NPT corte');s.level(-5,-1.18,-1.18,'geometrica relativa; NO NPT de terreno')
s.text('Barra: altura medida 1.10 m (2B05AC).\nDintel de paso: 2.45 m. Cubierta: conservar perfil original.',.6,4.5,.20)
s.notes=['Geometría principal reconstruida de la sección original superior.','Frente de barra en proyección, no corte del mueble.','Se eliminan de esta pieza personas/árboles de biblioteca, sin alterar originales.']
s.pending=['Confirmar asociación con traza A-B y sentido de observación.','Plataforma exterior de planta +2.11, sección a NPT +2.16: no unificadas.','Materiales y cielorraso en sectores no seccionados.']

# P07: newly derived longitudinal cut: station dimensions from plan.
s=Sheet('P07','Seccion longitudinal hacia pergola')
s.rect(0,-.15,length,.15,'cut','2AD811 / 2AD871 + 2AD03F')
s.line((0,hclear),(length,hclear),'view','2AD8AE/2B0623; proyección longitudinal')
s.line((0,roof_front),(length,roof_front),'cut','2AD812/2B058D; frente de cubierta')
s.line((0,0),(0,roof_front),'cut','2AD031');s.line((length,0),(length,roof_front),'cut','2AD04F')
# Transverse partitions intersect a cut in the clear room width (source polygons).
for h in ['2AD2C4','2AD92D']:
 x1,x2,y1,y2=bounds(h);a=y1-Y;b=y2-Y
 # Wall height is only established for the partial divider where explicitly labeled.
 if h=='2AD2C4':
  s.rect(a,0,b-a,.55,'cut',h+'; dibujo interrumpido, altura pendiente');s.poly([(a-.12,.6),(a+.12,.7),(a-.12,.8)],'proj',False,h);s.text('H pendiente; tramo interrumpido',a-3,1.25,.18)
 else:
  # Counter elevation established in transverse section, rather than full wall.
  s.rect(a,0,b-a,1.10,'view',h+' + 2B05AC')
 s.dim((0,0),(a,0),(0,-1.4 if h=='2AD2C4' else -2.2),source=h)
s.rect(lo,hpergola,hi-lo,.1,'proj','2AD8B9 + planta de pérgola; detrás del corte')
for a,b,c,h in openings:
 s.line((a,0),(a,hclear),'proj',h);s.line((b,0),(b,hclear),'proj',h)
s.dim((0,0),(length,0),(0,-3),source='2AD03F');s.dim((length,0),(length,hclear),(length+1.3,0),90,'secciones coincidentes')
s.level(-2,0,2.16,'NPT interior')
s.notes=['Nuevo corte longitudinal en coordenada X=2458.00 m de dibujo, mirando hacia el patio (X decreciente).','Posición de tabique y barra obtenida por intersección con planta. Barra 1.10 documentada. El tabique se representa interrumpido, sin asignar altura.','Guías de vanos y pérgola en proyección: no reemplazan sus elevaciones completas.']
s.pending=['La cubierta representada es el perfil frontal derivado de las secciones: confirmar continuidad fuera de esas trazas.','Antepechos y dinteles de vanos exteriores; cielorraso longitudinal.','Apoyos completos de pérgola y relación de niveles exteriores.']

# Architecture plan and its disciplines use actual source geometry plus specific construction.
planbox=(2428,2471,386,435);origin=(X,Y)
def baseplan(code,title,scale=100):
 s=Sheet(code,title,scale);s.source_window(planbox,origin);s.notes=['Base arquitectónica original en coordenadas locales, sin modificar el diseño.','Todas las cotas numéricas nuevas están expresadas en metros.'];return s

def plan_dims(s):
 s.dim((0,0),(9.25,0),(0,-1.3),source='2AD031/2AD03F');s.dim((9.25,0),(9.25,35),(11,0),90,'2AD03F')
 s.dim((.3,35),(.3,34.7),(-1.2,0),90,'2AD04F espesor')
 for a,b,c,h in openings:
  s.dim((0,a),(0,b),(-.8,0),90,h)

s=baseplan('P01','Planta arquitectonica general');plan_dims(s)
s.line((-4,418.296721712646-Y),(11,418.296721712646-Y),'proj','traza de sección asociada en cubierta')
s.text('E-E / P06: direccion hacia cocina; asociacion A-B por confirmar',-3,26.2,.18)
s.line((1.759408949591,-1),(1.759408949591,36),'proj','X=2458.00: traza nueva P07')
s.text('L-L / P07: mirar al patio',2.1,34,.18)
s.pending=['Acotado total del entorno y materiales por local.','Los niveles originales contradictorios se conservan.']

s=baseplan('P02','Demoliciones y obra nueva: intervenciones localizadas')
# Locate the source-backed canteen wall replacement, not all red entities.
x1,x2,y1,y2=bounds('2AD92D');s.poly([(x1-X,y1-Y),(x2-X,y1-Y),(x2-X,y2-Y),(x1-X,y2-Y)],'proj',True,'Informe: demolicion muro divisorio con cocina + 2AD92D')
s.text('D01: intervencion en frente cocina/barra.\nInforme: demolicion del muro divisorio.\nExtension exacta de demolicion a confirmar.',-10,30,.20)
s.dim((x1-X,y1-Y),(x2-X,y1-Y),(0,y1-Y-1),source='2AD92D: frente proyectado, no longitud certificada de demolición')
s.pending=['Correspondencia completa entre relevamiento ajustado y proyecto.','Límites de demolición y clasificación de carpinterías. No se interpreta color rojo como demolición.']

s=baseplan('P03','Pisos, plataformas, niveles y rampa');plan_dims(s)
p1=(station[0]+(min(tt)-.5)*normal[0]-X,station[1]+(min(tt)-.5)*normal[1]-Y);p2=(station[0]+(max(tt)+.5)*normal[0]-X,station[1]+(max(tt)+.5)*normal[1]-Y)
s.line(p1,p2,'proj','2AEEFA / 2AEE5C / 2AEE5D: traza R-R')
s.text('R-R / P05: normal al trazo de referencia',-11,3.7,.18)

for h in ['2AEF08','2AEE47']:
 a,b,c,e=bounds(h);s.dim((a-X,c-Y),(b-X,c-Y),(a-X,c-Y-1.2),source=h);s.dim((a-X,c-Y),(a-X,e-Y),(a-X-1,0),90,h)
s.text('Rampa: ver P05. No deducir pendientes uniformes.\nSe conservan los niveles rotulados en planta.',-16,9,.22)
s.pending=['Materiales por sector y pendientes de solados.','Resolver +2.11/+2.16 y +1.08/+1.16 sin corregirlos unilateralmente.']

s=Sheet('P04','Cubiertas y pergola: modulacion')
s.source_window((2555,2601,386,436),(2584.323494508538,Y))
# Dimension the actual transverse lines of the roof drawing.
beams=['2AF200','2AF202','2AF204','2AF206','2AF208','2AF20A']
ys=[]
for i,h in enumerate(beams):
 e=S.entitydb[h];yy=e.dxf.start.y-Y;ys.append(yy);s.text(f'T{i+1}',-4.7,yy+.3,.20)
 if i:s.dim((-3,ys[i-1]),(-3,yy),(-5.7,0),90,h+' / '+beams[i-1])
s.dim((-3,ys[0]),(0,ys[0]),(0,ys[0]+1.3),source='2AF200')
s.text('Trama de elementos proyectados.\nNo equivale a ejes confirmados de columnas.',-13,34,.20)
s.pending=['Pendientes de cubierta, encuentros y sistema completo de apoyos.'];s.notes=['Planta de cubierta original con cotas nuevas de modulación.','Sobretecho de chapa: rótulo fuente 75 m2, sin certificar cómputo.']

s=Sheet('P08','Secciones existentes A-B / C-D: coordinacion')
# Rebuild source profiles in two separated positions, preserving their geometry.
for box,org in [((2440,2470,294,302),(X,F)),((2440,2470,316,324),(X,318.544512714517-10))]:
 s.source_window(box,org,only={LAY['cut'],LAY['view'],LAY['steel'],LAY['fine']})
for dy in [0,10]:
 s.dim((.3,dy),(8.95,dy),(0,dy-2),source='secciones fuente: ancho interior 8.65')
 s.dim((.3,dy),(.3,dy+2.45),(-1.2,dy),90,'altura explícita en secciones')
 s.level(10,dy,2.16,'NPT original')
s.pending=['Asociación inequívoca entre los cortes dibujados y rótulos A-B/C-D.','Materiales y coordinación de niveles de plataforma.'];s.notes=['Geometría original de secciones, sin personas/vegetación ajenas al corte.','Cotas y referencias incorporadas; no se alteran perfiles.']

s=Sheet('P10','Elevacion interior del frente de atencion')
# Direct geometry of the actual bar, no cabinet division invented.
barw=2460.990753212559-2456.54059105041
bbase=bounds('2B05AC')[2]-318.544512714517;btop=bounds('2B0620')[2]-318.544512714517
s.rect(0,bbase,barw,btop-bbase,'view','2B05AC/2B0620')
s.line((0,bbase-.05),(barw,bbase-.05),'view','2B061E')
s.rect(.02,bbase+.02,barw-.04,btop-bbase-.04,'fine','2B0509')
s.line((0,0),(8.65,0),'cut','2AD811');s.line((0,2.45),(8.65,2.45),'proj','2B0623')
s.rect(2461.136672131489-2456.54059105041,0,1.2,2.45,'view','2B060B: PD-0')
s.dim((0,0),(barw,0),(0,-.8),source='2B05AC ancho');s.dim((0,0),(0,bbase),(-.8,0),90,'2B05AC altura')
s.dim((barw,bbase),(barw,btop),(barw+.6,0),90,'2B0620/2B05AC');s.level(-1.5,0,2.16,'NPT')
s.notes=['Desarrollo frontal construido con el frente de barra documentado en sección.','Códigos y ancho de la puerta PD-0 conservados; no se inventan divisiones de muebles.']
s.pending=['Detalles y materiales del mueble, espesor de perfiles y terminaciones.','Cielorraso y equipamiento no visibles en las fuentes.']

# Remaining complementary drawings.
s=baseplan('P15','Cielorrasos: perimetros y encuentros documentados');plan_dims(s)
s.line((.3,0),(.3,35),'proj','proyección del límite interior de fachada')
s.line((8.95,0),(8.95,35),'proj','proyección del límite interior de muro lateral')
s.text('Reposicion de placas y pintura: informe.\nNo se dibuja una reticula de placas sin modulo definido.',-15,26,.22)
s.pending=['Modulación, alturas, luminarias y ventiladores: posiciones no definidas.','No se atribuye a cielorraso el intradós inclinado de cubierta.']

s=baseplan('P16','Carpinterias: ubicacion y codigos');plan_dims(s)
for a,b,c,h in openings:
 s.line((0,(a+b)/2),(-2.5,(a+b)/2),'dim',h);s.text(c,-3.4,(a+b)/2+.25,.22)
for name in ['PD-0 (1)','P-3 (1)','P-4 (1)']:
 e=next(e for e in S.modelspace().query('INSERT') if e.dxf.name==name and 2450<e.dxf.insert.x<2470 and 390<e.dxf.insert.y<435)
 s.text(name.split(' (')[0],e.dxf.insert.x-X+.5,e.dxf.insert.y-Y+.5,.20)
s.pending=['Completar codificación de aberturas secundarias sueltas.','Alturas y condición existente/nueva de los vanos exteriores.'];s.notes+=['A01-A05 son códigos documentales nuevos coordinados con P19; no decisiones de diseño.']

s=baseplan('P17','Equipamiento y mobiliario');plan_dims(s)
for h in ['2AD018','2AD01C','2AD020']:
 a,b,c,e=bounds(h);s.dim((a-X,c-Y),(b-X,c-Y),(0,c-Y-.5),source=h);s.dim((a-X,c-Y),(a-X,e-Y),(a-X-.5,0),90,h)
s.pending=['Mobiliario no dibujado en fuente: no se agrega.','Referencias técnicas y circulaciones a coordinar con todas las aperturas.']

s=baseplan('P18','Implantacion del entorno inmediato',200);plan_dims(s)
s.text('Edificios proximos y patio: geometria original disponible.\nSin orientacion ni limites catastrales inferidos.',-18,33,.28)
s.pending=['Conjunto escolar completo, orientación y límites reales de intervención.'];s.notes+=['No se incorpora la plaza ajena presente en otra zona del DXF.']

s=Sheet('P19','Carpinterias: elevaciones y anchos')
# PD-0 is supported by a labeled frontal representation in the source section.
s.rect(0,0,1.2,2.45,'view','2B060B');s.rect(.04,0,1.12,2.41,'fine','2B060C')
s.line((.6,0),(.6,2.41),'view','2B04BD/BE: dos hojas')
s.poly([(.04,0),(.6,1.205),(.04,2.41)],'proj',False,'2B04C5')
s.poly([(1.16,0),(.6,1.205),(1.16,2.41)],'proj',False,'2B04C4')
s.text('PD-0 | 1 ud. en planta elegida',-.5,3.2,.20);s.dim((0,0),(1.2,0),(0,-.7),source='2B060B');s.dim((1.2,0),(1.2,2.45),(1.9,0),90,'2B060B')
# Other types have measured widths but no invented rectangular height.
items=[('P-3',.9,'2AD00A'),('P-4',.8,'2AD00B')]+[(c,b-a,h) for a,b,c,h in openings]
for i,(code,w,h) in enumerate(items):
 x=4+(i%4)*5;y=0-(i//4)*6
 s.line((x,y),(x,y+.45),'view',h);s.line((x+w,y),(x+w,y+.45),'view',h)
 s.poly([(x-.1,y+.6),(x+.1,y+.8),(x-.1,y+1)],'proj',False,h)
 s.poly([(x+w-.1,y+.6),(x+w+.1,y+.8),(x+w-.1,y+1)],'proj',False,h)
 s.text(f'{code} | ancho {w:.3f} m\nAltura no definida\nNO es elevacion completa',x-.2,y+2.8,.18)
 s.dim((x,y),(x+w,y),(x,y-.7),source=h)
s.notes=['PD-0: elevación construida a partir del símbolo frontal rotulado de sección; ancho 1.20 y alto 2.45 m.','Resto: ancho geométrico y arranques de jambas con interrupción; sin asignar alturas.']
s.pending=['Todas las otras alturas, materiales, vidrios, terminaciones y condición.','Inventario restante de aberturas secundarias.']

# Installations: source-backed fixture positions, no fabricated engineering routes.
fixture_handles=[]
for e in S.modelspace().query('INSERT'):
 if e.dxf.name in ['INODORO1','BACHA-C','inodoro','bidet','Bide-r~1','Tarja-p02'] and 2450<e.dxf.insert.x<2470 and 390<e.dxf.insert.y<435:fixture_handles.append(e.dxf.handle)
for code,title in [('P11','Electricidad: equipamiento y puntos por definir'),('P12','Agua: artefactos y conexiones pendientes'),('P13','Cloacal: artefactos y descargas pendientes')]:
 s=baseplan(code,title)
 for i,h in enumerate(fixture_handles):
  e=S.entitydb[h];x=e.dxf.insert.x-X;y=e.dxf.insert.y-Y
  # Location references end at actual source insert; no service stub implied.
  s.line((x,y),(12+(i%2)*3,25-i*1.1),'dim',h)
  s.text(f'F{i+1:02} {e.dxf.name}',12+(i%2)*3,25.3-i*1.1,.16)
 s.dim((.3,35),(8.95,35),(0,36.4),source='2AD04F')
 s.pending=['No existen posiciones confirmadas de tableros/luminarias/tomas ni circuitos.' if code=='P11' else 'Recorridos, diámetros, conexiones, llaves/cámaras y condición existente/proyectada no definidos.','Las referencias F son de localización gráfica; no representan conexiones de instalación.']

for code,title in [('P14','Pluvial: captacion y descargas pendientes'),('P20','Zingueria: bordes documentados de cubierta')]:
 s=Sheet(code,title);s.source_window((2555,2601,386,436),(2584.323494508538,Y))
 # New dimensioned edge reference drawing, not an assumed gutter.
 s.line((14,0),(14,35),'dim','longitud de fachada: 2AD03F');s.text('B01: borde de referencia.\nNo es trazado de canaleta definido.',15,25,.20)
 s.dim((14,0),(14,35),(13,0),90,'2AD03F')
 s.pending=['Canaletas, cenefas, babetas, bajadas, pendientes y descargas: trazados no definidos.','Patologías señaladas en informe sin localización suficiente para asignar cada intervención.'];s.notes=['Cubierta original y referencia longitudinal acotada.','Informe: rehacer canaletas y zinguería de borde. No se inventan secciones ni recorridos.']

s=baseplan('P21','Pergola: planta de referencia para fundaciones')
# Axes of drawn projected steel bands, explicitly not claimed to be column axes.
for i,h in enumerate(['2AD265','2AD27F']):
 e=S.entitydb[h];xx=e.dxf.start.x-X
 s.line((xx,-6),(xx,33),'proj',h)
 s.text('R'+str(i+1)+' / referencia de banda',xx-3,34+i*.5,.18)
s.dim((-3,0),(-.1,0),(0,-2),source='2AD265/2AD27F separación de bandas')
s.pending=['Ejes y cantidad de columnas reales no definidos inequívocamente en planta.','No se confunden las líneas de vigas proyectadas con columnas.','Dimensiones de fundación, suelo, profundidades, armaduras, placas y anclajes requieren cálculo.'];s.notes+=['Se construye geometría acotada de referencia. No es planta de bases resuelta.']

# Finish and validate each independent drawing, then compose master with source preserved.
for code in ['P09','P05','P06','P07']+[f'P{i:02}' for i in range(1,22) if i not in (9,5,6,7)]:
 print('CAD',code,flush=True)
 if not os.environ.get('PRODUCCION_REANUDAR'):A[code].finish()
# Master uses immutable source model + separate derived drawing blocks at disjoint locations.
master=ezdxf.readfile(SRC);master.units=6
from ezdxf.xref import Loader
for i,code in enumerate(sorted(A)):
 src=ezdxf.readfile(CAD/(code+'.dxf'))
 # Import the complete model as a block, keeping its own dimension render blocks.
 blockname='DOC_'+code
 b=master.blocks.new(blockname)
 loader=Loader(src,master);loader.load_modelspace(target_layout=b);loader.execute()
 master.modelspace().add_blockref(blockname,((i%4)*90,-1000-(i//4)*80))
master.saveas(CAD/'CASSAFFOUSTH_PRODUCCION.dxf')
re=ezdxf.readfile(CAD/'CASSAFFOUSTH_PRODUCCION.dxf');au=re.audit();assert not au.errors and not au.fixes
# Verify original geometries through exported tags after harmless default normalization.
sp=importlib.util.spec_from_file_location('old',P/'04_INFORMES/preparar_revision.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
for e in S.modelspace():assert old.tags(e)==old.tags(re.entitydb[e.dxf.handle])
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==SHASH
# Export each drawing at exact metric scale, with paper annotations independent of model scale.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf.addons.drawing import RenderContext,Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
with PdfPages(PDF/'CASSAFFOUSTH_PRODUCCION.pdf') as compiled:
 for code in sorted(A):
  s=A[code];doc=ezdxf.readfile(CAD/(code+'.dxf'));lay=doc.layouts.get(code);v=list(lay.query('VIEWPORT'))[-1];cx,cy=v.dxf.view_center_point.x,v.dxf.view_center_point.y;vh=v.dxf.view_height;vw=vh*v.dxf.width/v.dxf.height;pw=lay.dxf_layout.dxf.paper_width;ph=lay.dxf_layout.dxf.paper_height
  fig=plt.figure(figsize=(pw/25.4,ph/25.4));ctx=RenderContext(doc);ctx.set_current_layout(lay)
  ax=fig.add_axes([(v.dxf.center.x-v.dxf.width/2)/pw,(v.dxf.center.y-v.dxf.height/2)/ph,v.dxf.width/pw,v.dxf.height/ph]);bk=MatplotlibBackend(ax,adjust_figure=False);Frontend(ctx,bk).draw_entities(doc.modelspace());bk.finalize();ax.set_xlim(cx-vw/2,cx+vw/2);ax.set_ylim(cy-vh/2,cy+vh/2);ax.set_aspect('equal',adjustable='box');ax.axis('off')
  paper=fig.add_axes([0,0,1,1]);b=MatplotlibBackend(paper,adjust_figure=False);Frontend(ctx,b).draw_entities([e for e in lay if e.dxftype()!='VIEWPORT']);b.finalize();paper.set_xlim(0,pw);paper.set_ylim(0,ph);paper.set_aspect('equal',adjustable='box');paper.axis('off');paper.patch.set_alpha(0)
  fig.savefig(PDF/(code+'.pdf'));compiled.savefig(fig);plt.close(fig);print('PDF',code,flush=True)
if not registry:
 for code in sorted(A):
  s=A[code];registry.append(dict(plano=code,titulo=s.title,escala=s.scale,estado='BORRADOR - DATOS INDISPENSABLES PENDIENTES',entidades_nuevas=dict(s.new),cotas=len(s.dims),pendientes=s.pending,fuentes=s.sources))
(QA/'produccion.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2))
with (P/'03_PLANILLAS/trazabilidad_geometria_nueva.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(log[0]));w.writeheader();w.writerows(log)
print('Hecho',len(A),'dibujos; geometría nueva',len(log),flush=True)
