from pathlib import Path
import math,json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/cassafus-mpl')
import ezdxf,fitz
P=Path(__file__).resolve().parents[1];C=P/'01_CAD/PRODUCCION';F=P/'02_PDF/PRODUCCION';S=ezdxf.readfile(P.parent/'CASAFUS_99.dxf');arc=S.entitydb['2AEEFA'];theta=math.radians((arc.dxf.start_angle+arc.dxf.end_angle)/2);normal=(math.cos(theta),math.sin(theta));station=(arc.dxf.center.x+arc.dxf.radius*normal[0],arc.dxf.center.y+arc.dxf.radius*normal[1]);tt=[]
for h in ['2AEE5C','2AEE5D']:
 e=S.entitydb[h];delta=(station[0]-e.dxf.center.x,station[1]-e.dxf.center.y);dot=sum(x*y for x,y in zip(delta,normal));disc=dot*dot-sum(x*x for x in delta)+e.dxf.radius**2;tt.append(min([-dot+math.sqrt(disc),-dot-math.sqrt(disc)],key=abs))
w=abs(tt[1]-tt[0]);X=2456.240591050409;Y=392.9952486034458
point1=(station[0]+(min(tt)-.5)*normal[0]-X,station[1]+(min(tt)-.5)*normal[1]-Y);point2=(station[0]+(max(tt)+.5)*normal[0]-X,station[1]+(max(tt)+.5)*normal[1]-Y)
def patch5(m):
 for e in m.query('LINE'):
  a,b=e.dxf.start,e.dxf.end
  if abs(a.y+3.2)<1e-8 and abs(b.y+3.7)<1e-8 and a.x>.5 and abs(a.x-b.x)<1e-8:e.dxf.start=(w,-3.2,0);e.dxf.end=(w,-3.7,0)
 for e in m.query('DIMENSION'):
  if abs(e.dxf.defpoint2.y+3.2)<1e-8 and abs(e.dxf.defpoint3.y+3.2)<1e-8:
   e.dxf.defpoint3=(w,-3.2,0);e.render();assert math.isclose(e.get_measurement(),w)
 for e in m.query('MTEXT'):
  if 'CORTE TRANSVERSAL:' in e.text:e.text=e.text.replace('CORTE TRANSVERSAL: ANCHO GEOMETRICO EN Y=397.20','CORTE R-R: NORMAL AL TRAZO ORIGINAL EN ESTACION MEDIA')
def patch3(m):
 if not any('R-R / P05' in e.text for e in m.query('MTEXT')):
  m.add_line(point1,point2,dxfattribs={'layer':'AR-03- Proyeccion 01'})
  m.add_mtext('R-R / P05: normal al trazo de referencia',dxfattribs={'insert':(-11,3.7),'width':12,'char_height':.18,'style':'Arial','layer':'AR-07- Cota 1_1'})
for code,fun in [('P05',patch5),('P03',patch3)]:
 d=ezdxf.readfile(C/(code+'.dxf'));fun(d.modelspace());d.saveas(C/(code+'.dxf'))
m=ezdxf.readfile(C/'CASSAFFOUSTH_PRODUCCION.dxf');patch5(m.blocks['DOC_P05']);patch3(m.blocks['DOC_P03']);m.saveas(C/'CASSAFFOUSTH_PRODUCCION.dxf')
# Only changed pages are re-rendered. Compilation is assembled from canonical PDFs.
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext,Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
for code in ['P03','P05']:
 d=ezdxf.readfile(C/(code+'.dxf'));l=d.layouts.get(code);v=list(l.query('VIEWPORT'))[-1];pw,ph=l.dxf_layout.dxf.paper_width,l.dxf_layout.dxf.paper_height;cx,cy=v.dxf.view_center_point.x,v.dxf.view_center_point.y;vh=v.dxf.view_height;vw=vh*v.dxf.width/v.dxf.height;ctx=RenderContext(d);ctx.set_current_layout(l);fig=plt.figure(figsize=(pw/25.4,ph/25.4))
 ax=fig.add_axes([(v.dxf.center.x-v.dxf.width/2)/pw,(v.dxf.center.y-v.dxf.height/2)/ph,v.dxf.width/pw,v.dxf.height/ph]);b=MatplotlibBackend(ax,adjust_figure=False);Frontend(ctx,b).draw_entities(d.modelspace());b.finalize();ax.set_xlim(cx-vw/2,cx+vw/2);ax.set_ylim(cy-vh/2,cy+vh/2);ax.set_aspect('equal',adjustable='box');ax.axis('off')
 a=fig.add_axes([0,0,1,1]);b=MatplotlibBackend(a,adjust_figure=False);Frontend(ctx,b).draw_entities([e for e in l if e.dxftype()!='VIEWPORT']);b.finalize();a.set_xlim(0,pw);a.set_ylim(0,ph);a.set_aspect('equal',adjustable='box');a.axis('off');a.patch.set_alpha(0);fig.savefig(F/(code+'.pdf'));plt.close(fig)
out=fitz.open()
for i in range(1,22):
 with fitz.open(F/f'P{i:02}.pdf') as page:out.insert_pdf(page)
out.save(F/'CASSAFFOUSTH_PRODUCCION.pdf');out.close()
(P/'04_INFORMES/PRODUCCION/seccion_normal_rampa.json').write_text(json.dumps(dict(ancho_normal_m=w,estacion=station,direccion=normal,contornos=['2AEE5C','2AEE5D'],arco_referencia='2AEEFA',traza_P03=[point1,point2],perfil_superficie='PENDIENTE'),indent=2))
print('P03 y P05 coordinados; ancho normal:',w)
