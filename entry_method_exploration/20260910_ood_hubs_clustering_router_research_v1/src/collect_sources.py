"""Download public primary documents only; no dataset/model/index operations."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json
import urllib.request

RUN = Path(__file__).resolve().parents[1]
PREVIOUS = RUN.parent / '20260910_optimizer_research_v1'

DOCUMENTS = [
    ('roargraph', 'https://arxiv.org/html/2408.08933v1', 'html', None),
    ('ood_diskann', 'https://arxiv.org/html/2211.12850v1', 'html', None),
    ('leanvec', 'https://arxiv.org/html/2312.16335v2', 'html', None),
    ('gleanvec', 'https://arxiv.org/html/2410.22347v1', 'html', None),
    ('lira', 'https://arxiv.org/html/2503.23409v1', 'html', None),
    ('gate', 'https://arxiv.org/html/2506.15986v1', 'html', PREVIOUS/'sources/gate.html'),
    ('lora', 'https://arxiv.org/html/2106.09685v2', 'html', PREVIOUS/'sources/lora.html'),
    ('adalora', 'https://arxiv.org/html/2303.10512v2', 'html', None),
    ('hnsw', 'https://arxiv.org/pdf/1603.09320', 'pdf', None),
    ('vmf', 'https://jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf', 'pdf', None),
    ('partition_trees_2026', 'https://arxiv.org/html/2607.09909v1', 'html', None),
    ('neural_lsh', 'https://www.microsoft.com/en-us/research/uploads/prod/2019/10/1901.08544.pdf', 'pdf', None),
    ('quodar_abstract', 'https://link.springer.com/chapter/10.1007/978-981-95-8318-8_1', 'html', None),
]

class Plain(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden += 1
        if tag in ('p','div','section','h1','h2','h3','h4','h5','li','tr','br'): self.parts.append('\n')
        if tag == 'math':
            alt = dict(attrs).get('alttext')
            if alt: self.parts.append(' [LATEX: '+alt+'] ')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
        if tag in ('p','div','section','h1','h2','h3','h4','h5','li','tr'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)
    def text(self):
        return '\n'.join(' '.join(x.split()) for x in ''.join(self.parts).splitlines() if x.strip())+'\n'

def fetch(item):
    key,url,kind,reuse=item
    record={'id':key,'url':url,'kind':kind,'access_utc':datetime.now(timezone.utc).isoformat()}
    try:
        if reuse:
            data=reuse.read_bytes(); final=url; record['reused_from']=str(reuse)
        else:
            request=urllib.request.Request(url,headers={'User-Agent':'ACSG research bibliography review'})
            with urllib.request.urlopen(request,timeout=35) as response:
                data=response.read(); final=response.geturl()
        if kind=='pdf' and not data.startswith(b'%PDF'): raise ValueError('response is not a PDF')
        path=RUN/'sources'/f'{key}.{kind}'
        with path.open('xb') as f: f.write(data)
        record.update(status='AVAILABLE',final_url=final,path=str(path.relative_to(RUN)),bytes=len(data),sha256=sha256(data).hexdigest())
        if kind=='html':
            parser=Plain();parser.feed(data.decode('utf-8',errors='replace'))
            txt=path.with_suffix('.txt');txt.write_text(parser.text())
            record['text_path']=str(txt.relative_to(RUN))
    except Exception as error:
        record.update(status='FETCH_FAILED',reason=str(error))
    print(key,record['status'],record.get('bytes',record.get('reason')),flush=True)
    return record

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(fetch,DOCUMENTS))
    (RUN/'sources/manifest.json').write_text(json.dumps(records,indent=2)+'\n')
