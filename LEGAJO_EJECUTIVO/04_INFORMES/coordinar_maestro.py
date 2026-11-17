from pathlib import Path
import ezdxf
P=Path(__file__).resolve().parents[1];C=P/'01_CAD/PRODUCCION';path=C/'CASSAFFOUSTH_PRODUCCION.dxf';d=ezdxf.readfile(path)
for i in range(1,22):
 code=f'P{i:02}';name=code+'_PROD'
 if name in d.layouts:d.layouts.delete(name)
 src=ezdxf.readfile(C/(code+'.dxf'));sl=src.layouts.get(code);v=list(sl.query('VIEWPORT'))[-1];idx=i-1;dx=(idx%4)*90;dy=-1000-(idx//4)*80
 l=d.layouts.new(name);l.page_setup(size=(sl.dxf_layout.dxf.paper_width,sl.dxf_layout.dxf.paper_height),margins=(0,0,0,0),units='mm')
 for e in sl:
  if e.dxftype()!='VIEWPORT':l.add_entity(e.copy())
 l.add_viewport(center=tuple(v.dxf.center)[:2],size=(v.dxf.width,v.dxf.height),view_center_point=(v.dxf.view_center_point.x+dx,v.dxf.view_center_point.y+dy),view_height=v.dxf.view_height,status=2,dxfattribs={'layer':'Z-REF'})
d.saveas(path);r=ezdxf.readfile(path);a=r.audit();assert not a.errors and not a.fixes
assert all(f'P{i:02}_PROD' in r.layouts for i in range(1,22))
print('21 layouts del maestro coordinados con sus bloques de dibujo.')
