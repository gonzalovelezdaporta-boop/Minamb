from pathlib import Path
import shutil
import fitz
from PIL import Image
p=Path(__file__).resolve().parents[1]
for f in list(p.iterdir()):
 if not f.is_file():continue
 dest='01_CAD' if f.suffix=='.dxf' else '02_PDF' if f.suffix in ['.pdf','.png'] else '03_PLANILLAS' if f.suffix=='.csv' else '00_DIAGNOSTICO' if f.name in ['auditoria_dxf.json','textos_dxf.json','informe_extraido.txt'] else '04_INFORMES'
 shutil.move(str(f),str(p/dest/f.name))
d=fitz.open(p/'02_PDF/CASSAFFOUSTH_revision_fuentes.pdf')
assert len(d)==9
sheet=Image.new('RGB',(1500,1062),'#ddd')
for i,code in enumerate(['P01','P03','P04','P08','P16','P17','P18','P20','P21']):
 s=fitz.open();s.insert_pdf(d,from_page=i,to_page=i);s.save(p/f'02_PDF/{code}_revision.pdf')
 assert len(d[i].get_images())==0 and len(d[i].get_drawings())>100
 assert abs(d[i].rect.width-16.55*72)<1
 assert abs(d[i].rect.height-11.7*72)<1
 pix=d[i].get_pixmap(matrix=fitz.Matrix(.4,.4));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((490,345));sheet.paste(im,((i%3)*500,(i//3)*354))
sheet.save(p/'04_INFORMES/control_pdf.png')
print('9 PDF vectoriales individuales y compilado; dimensiones de página verificadas.')
