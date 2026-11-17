from pathlib import Path
import json,math,csv,hashlib
import ezdxf,fitz
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];C=P/'01_CAD/PRODUCCION';F=P/'02_PDF/PRODUCCION';Q=P/'04_INFORMES/PRODUCCION'
rows=[];previews=[]
for i in range(1,22):
 code=f'P{i:02}';d=ezdxf.readfile(C/(code+'.dxf'));l=d.layouts.get(code);v=list(l.query('VIEWPORT'))[-1];scale=200 if i==18 else 100
 assert d.units==6
 assert math.isclose(v.dxf.height/v.dxf.view_height,1000/scale,abs_tol=1e-9)
 doc=fitz.open(F/(code+'.pdf'));assert len(doc)==1;p=doc[0]
 pw,ph=l.dxf_layout.dxf.paper_width,l.dxf_layout.dxf.paper_height
 assert abs(p.rect.width-pw*72/25.4)<.01 and abs(p.rect.height-ph*72/25.4)<.01
 assert not p.get_images()
 # Calibration stroke at paper y45: one metre in model = 1000/scale mm.
 expected=1000/scale*72/25.4;target_y=(ph-45)*72/25.4;found=False
 for dr in p.get_drawings():
  for item in dr['items']:
   if item[0]=='l':
    a,b=item[1:];length=abs(b.x-a.x)
    if abs(a.y-target_y)<.02 and abs(b.y-target_y)<.02 and abs(length-expected)<.02:found=True
 assert found,(code,'calibración ausente')
 assert any('BORRADOR' in e.plain_text() for e in l.query('MTEXT')) # PDF glyphs are vector outlines.
 assert all('u' not in e.override().get('dimpost','') for e in d.modelspace().query('DIMENSION'))
 # Count exact duplicate LINE entities in the individual drawing.
 seen=set();dups=0
 for e in d.modelspace().query('LINE'):
  a=tuple(round(x,7) for x in e.dxf.start);b=tuple(round(x,7) for x in e.dxf.end)
  sig=(e.dxf.layer,tuple(sorted([a,b])))
  if sig in seen:dups+=1
  seen.add(sig)
 rows.append(dict(plano=code,escala=scale,papel_mm=[pw,ph],calibracion_pdf=True,lineas_duplicadas_exactas=dups,entidades_modelo=len(d.modelspace()),cotas=len(d.modelspace().query('DIMENSION')),imagenes_pdf=0))
 pix=p.get_pixmap(matrix=fitz.Matrix(.25,.25));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((590,415));preview=Q/(code+'.png');im.save(preview);previews.append(im)
comp=fitz.open(F/'CASSAFFOUSTH_PRODUCCION.pdf');assert len(comp)==21
mosaic=Image.new('RGB',(2400,6*440),'#ddd');draw=ImageDraw.Draw(mosaic)
for i,im in enumerate(previews):
 x=(i%4)*600;y=(i//4)*440;mosaic.paste(im,(x,y));draw.text((x+5,y+420),f'P{i+1:02}',fill='black')
mosaic.save(Q/'control_21.png')
(Q/'control_escala.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
print('21 PDF vectoriales y DXF individuales verificados. Calibración física de escala: correcta.')
print('Duplicados LINE:',[(x['plano'],x['lineas_duplicadas_exactas']) for x in rows if x['lineas_duplicadas_exactas']])
