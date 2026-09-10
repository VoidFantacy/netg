#!/usr/bin/env python3
"""Collect public literature and snapshot small local evidence; no ANN/training."""
import concurrent.futures
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import urllib.request

ROOT = Path('/data/netg/ACSG')
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'entry_method_exploration/20260909_ab_readonly_research_v1/sources'

SOURCES = [
    ('gate', 'GATE', 'https://arxiv.org/html/2506.15986v1', 'html'),
    ('lora', 'LoRA', 'https://arxiv.org/html/2106.09685v2', 'html'),
    ('loraplus', 'LoRA+', 'https://arxiv.org/html/2402.12354v2', 'html'),
    ('lorapro', 'LoRA-Pro', 'https://arxiv.org/html/2407.18242v3', 'html'),
    ('perturbed', 'Learning with Differentiable Perturbed Optimizers', 'https://arxiv.org/html/2002.08676v2', 'html'),
    ('soft_topk', 'Differentiable Top-k with Optimal Transport', 'https://papers.nips.cc/paper_files/paper/2020/file/ec24a54d62ce57ba93a531b460fa8d18-Paper.pdf', 'pdf'),
    ('gumbel_topk', 'Stochastic Beams and Where To Find Them', 'https://proceedings.mlr.press/v97/kool19a/kool19a.pdf', 'pdf'),
    ('reinforce', 'Simple statistical gradient-following algorithms', 'https://link.springer.com/content/pdf/10.1007/BF00992696.pdf', 'pdf'),
    ('op_lora', 'OP-LoRA', 'https://openaccess.thecvf.com/content/CVPR2026W/ECV/papers/Teterwak_OP-LoRA_The_Blessing_of_Dimensionality_with_Overparameterized_Low-Rank_Adaptation_CVPRW_2026_paper.pdf', 'pdf'),
]

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip += 1
        if tag in ('p','div','section','h1','h2','h3','h4','li','tr'): self.items.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip -= 1
    def handle_data(self, data):
        if not self.skip: self.items.append(data)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def fetch(item):
    key,title,url,kind=item
    record={'id':key,'title':title,'url':url,'access_date':'2026-09-10','kind':kind}
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (literature research)'})
        with urllib.request.urlopen(request,timeout=30) as response:
            data=response.read(); record['final_url']=response.url
        if kind=='pdf' and not data.startswith(b'%PDF'): raise ValueError('Response is not a PDF')
        path=OUT/'sources'/f'{key}.{kind}'
        path.write_bytes(data)
        record.update(status='DOWNLOADED',path=str(path.relative_to(OUT)),bytes=len(data),sha256=sha(path))
        if kind=='html':
            parser=Extract(); parser.feed(data.decode('utf-8'))
            txt=path.with_suffix('.txt'); txt.write_text(''.join(parser.items))
            record['text_path']=str(txt.relative_to(OUT))
        else:
            record['text_extraction']='Not attempted: PDF method sections read through web tool; local parser unavailable'
    except Exception as error:
        record.update(status='DOWNLOAD_UNAVAILABLE',error=str(error))
    return record

def main():
    (OUT/'sources').mkdir(exist_ok=True)
    before=OUT/'source_before'; before.mkdir(exist_ok=True)
    names=['AGENTS.md','spec.md','summary.md','s-target.md','s-experiment.md',
           'experiment_history/11_ab_fixed_slot_exploration.md',
           'entry_method_exploration/20260909_ab_experiment_v1/src/train.py',
           'entry_method_exploration/20260909_ab_experiment_v1/src/benchmark.cpp',
           'entry_method_exploration/20260909_ab_experiment_v1/config.locked.json',
           'entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/src/quick.cpp',
           'ACSG/ACSG.cpp','benches/test.cpp']
    local=[]
    for name in names:
        src=ROOT/name; dest=before/name; dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists(): raise FileExistsError(dest)
        shutil.copy2(src,dest); local.append({'path':name,'sha256':sha(src),'bytes':src.stat().st_size})
    dump(OUT/'local_source_manifest.json',local)
    reused=[]
    for name in ['gate.pdf','gate.txt','gate_train.py','gate_online.cpp','gate_labels.py',
                 'lrsg.pdf','lrsg.txt','lrsg_agent.py','lrsg_trainer.py']:
        src=OLD/name; dest=OUT/'sources'/('gate.previous.txt' if name=='gate.txt' else name)
        shutil.copy2(src,dest)
        reused.append({'path':str(dest.relative_to(OUT)),'source_path':str(src),'sha256':sha(src),
                       'scope':'Existing paper/author-source snapshot; selected sections re-read, no author code executed'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        downloaded=list(pool.map(fetch,SOURCES))
    dump(OUT/'sources/manifest.json',{'downloaded':downloaded,'reused':reused})
    print(json.dumps([{'id':x['id'],'status':x['status'],'error':x.get('error')} for x in downloaded]))

if __name__=='__main__': main()
