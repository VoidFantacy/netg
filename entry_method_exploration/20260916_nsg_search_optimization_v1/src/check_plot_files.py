"""Check rendered file integrity; explicitly not a manual visual inspection."""
import pathlib,json,hashlib
from PIL import Image,ImageStat
D=pathlib.Path(__file__).resolve().parent.parent
rows=[]
for name in ['webvid_recall_qps','webvid_speedup']:
 for ext in ['png','pdf']:
  p=D/'figures'/f'{name}.{ext}';b=p.read_bytes();assert len(b)>1000
  row={'path':str(p.relative_to(D)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  if ext=='png':
   with Image.open(p) as im:
    im.load();assert im.width>=1000 and im.height>=600
    assert sum(ImageStat.Stat(im.convert('RGB')).stddev)>10
    row['dimensions']=[im.width,im.height]
  else:assert b.startswith(b'%PDF-') and b'%%EOF' in b[-64:]
  rows.append(row)
(D/'reviews/figures_render_check.json').write_text(json.dumps({'status':'PASS','manual_visual_review':False,'check_scope':'file integrity, dimensions, nonblank raster; no claim of visual layout review','files':rows},indent=2)+'\n')
print('RENDER_FILE_CHECK_PASS')
