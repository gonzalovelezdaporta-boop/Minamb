"""Limpieza de duplicados exactos heredados y ajuste de papel, a escala fija."""
from pathlib import Path
import os,re,json
os.environ.setdefault('MPLCONFIGDIR','/tmp/cassafus-mpl')
import ezdxf
from ezdxf import bbox
P=Path(__file__).resolve().parents[1];C=P/'01_CAD/PRODUCCION';F=P/'02_PDF/PRODUCCION';Q=P/'04_INFORMES/PRODUCCION'
def clean(layout):
 seen=set();n=0
 for e in list(layout.query('LINE')):
  a=tuple(round(x,8) for x in e.dxf.start);b=tuple(round(x,8) for x in e.dxf.end)
  k=(tuple(sorted([a,b])),e.dxf.layer,e.dxf.get('color',256),e.dxf.get('linetype','BYLAYER'),e.dxf.get('lineweight',-1),e.dxf.get('true_color',None))
  if k in seen:layout.delete_entity(e);n+=1
  else:seen.add(k)
 return n
removed={}
for i in range(1,22):
 code=f'P{i:02}';path=C/(code+'.dxf');d=ezdxf.readfile(path);removed[code]=clean(d.modelspace());l=d.layouts.get(code);v=list(l.query('VIEWPORT'))[-1];scale=200 if i==18 else 100
 b=bbox.extents([e for e in d.modelspace() if e.dxftype() not in ('MTEXT','TEXT')],fast=True)
 pw,ph=next((w,h) for w,h in [(420,297),(594,420),(841,594),(1189,841)] if b.size.x<(w-231)/(1000/scale) and b.size.y<(h-144)/(1000/scale))
 ow,oh=l.dxf_layout.dxf.paper_width,l.dxf_layout.dxf.paper_height
 for e in l.query('MTEXT'):
  x,y,z=e.dxf.insert
  if x>=ow-200:x+=pw-ow;y+=ph-oh
  elif y>=oh-80:y+=ph-oh
  e.dxf.insert=(x,y,z)
  if 'papel ' in e.text:e.text=re.sub(r'papel \d+ x \d+ mm',f'papel {pw} x {ph} mm',e.text)
 mc=tuple(v.dxf.view_center_point)[:2]
 l.page_setup(size=(pw,ph),margins=(0,0,0,0),units='mm');l.add_viewport(center=(20+(pw-231)/2,60+(ph-144)/2),size=(pw-231,ph-144),view_center_point=mc,view_height=(ph-144)/(1000/scale),status=2,dxfattribs={'layer':'Z-REF'})
 d.saveas(path)
m=ezdxf.readfile(C/'CASSAFFOUSTH_PRODUCCION.dxf')
for i in range(1,22):assert clean(m.blocks[f'DOC_P{i:02}'])==removed[f'P{i:02}']
m.saveas(C/'CASSAFFOUSTH_PRODUCCION.dxf')
(Q/'duplicados_retirados.json').write_text(json.dumps(removed,indent=2))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf.addons.drawing import RenderContext,Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
with PdfPages(F/'CASSAFFOUSTH_PRODUCCION.pdf') as compiled:
 for i in range(1,22):
  code=f'P{i:02}';doc=ezdxf.readfile(C/(code+'.dxf'));l=doc.layouts.get(code);v=list(l.query('VIEWPORT'))[-1];pw,ph=l.dxf_layout.dxf.paper_width,l.dxf_layout.dxf.paper_height;cx,cy=v.dxf.view_center_point.x,v.dxf.view_center_point.y;vh=v.dxf.view_height;vw=vh*v.dxf.width/v.dxf.height
  fig=plt.figure(figsize=(pw/25.4,ph/25.4));ctx=RenderContext(doc);ctx.set_current_layout(l)
  ax=fig.add_axes([(v.dxf.center.x-v.dxf.width/2)/pw,(v.dxf.center.y-v.dxf.height/2)/ph,v.dxf.width/pw,v.dxf.height/ph]);b=MatplotlibBackend(ax,adjust_figure=False);Frontend(ctx,b).draw_entities(doc.modelspace());b.finalize();ax.set_xlim(cx-vw/2,cx+vw/2);ax.set_ylim(cy-vh/2,cy+vh/2);ax.set_aspect('equal',adjustable='box');ax.axis('off')
  paper=fig.add_axes([0,0,1,1]);b=MatplotlibBackend(paper,adjust_figure=False);Frontend(ctx,b).draw_entities([e for e in l if e.dxftype()!='VIEWPORT']);b.finalize();paper.set_xlim(0,pw);paper.set_ylim(0,ph);paper.set_aspect('equal',adjustable='box');paper.axis('off');paper.patch.set_alpha(0)
  fig.savefig(F/(code+'.pdf'));compiled.savefig(fig);plt.close(fig);print(code,flush=True)
print('Duplicados retirados de copias derivadas:',sum(removed.values()))
