"""Add navigation to the completed PDF without changing measured content."""
import hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,'/tmp/acsg_e187_pdf_tool')
import fitz
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta_path=R/'reviews/pdf_build.json';build=json.loads(meta_path.read_text());path=Path(build['path'])
assert sha(path)==build['pdf_sha256'];before=build['pdf_sha256']
pdf=fitz.open(path);toc=[[1,title,i+1] for i,title in enumerate(build['page_titles'])]
pdf.set_toc(toc);assert pdf.get_toc()==toc
tmp=R/'reviews/pdf_navigation.pdf';pdf.save(tmp,garbage=4,deflate=True);pdf.close();os.replace(tmp,path)
after=sha(path);source=dict(path=str(Path(__file__).resolve()),sha256=sha(Path(__file__)),before_pdf_sha256=before,after_pdf_sha256=after,bookmarks=len(toc))
build['navigation']=source;build['pdf_sha256']=after;meta_path.write_text(json.dumps(build,ensure_ascii=False,indent=2)+'\n')
(R/'reviews/pdf_navigation.json').write_text(json.dumps(dict(status='PASS_PDF_CHAPTER_BOOKMARKS',**source),indent=2)+'\n')
print('PASS PDF page bookmarks added',flush=True)
