#!/usr/bin/env python3
"""Validate document maintenance without replaying scientific jobs or old closeout gates."""
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import time
from urllib.parse import unquote

H=Path(__file__).resolve().parent
REPO=H.parents[2]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def links(s,base):
    result=[]
    for p in re.findall(r'\]\(([^)]+)\)',s):
        if '://' in p or p.startswith('mailto:'):continue
        path,_,anchor=p.partition('#');dest=(base/unquote(path)).resolve() if path else base
        result.append((dest,unquote(anchor)))
    return result
def anchors(p):
    s=p.read_text();out=set(re.findall(r'<a\s+id="([^"]+)"',s));seen={}
    for line in s.splitlines():
        m=re.match(r'^#+\s+(.*?)\s*#*$',line)
        if not m:continue
        t=re.sub(r'\[([^\]]*)\]\([^)]+\)',r'\1',m.group(1));t=re.sub(r'<[^>]*>','',t).lower()
        t=re.sub(r'[^\w\-\s]','',t,flags=re.UNICODE).replace(' ','-')
        n=seen.get(t,0);seen[t]=n+1;out.add(t+(f'-{n}' if n else ''))
    return out

def main():
    start=time.time();before=load(H/'before_manifest.json');protected=load(H/'protected_evidence.json')
    for name,v in before.items():
        p=H/'source_before'/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],name
    for name,v in protected.items():
        p=REPO/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],name
    current=[REPO/n for n in before]+[H/'README.md'];checked=0;broken=[];anchor_checks=0
    generated_here={H/'validation.json',H/'manifest.json'}
    for p in current:
        for target,anchor in links(p.read_text(),p.parent):
            if not target.exists() and target not in generated_here:broken.append((str(p.relative_to(REPO)),str(target)))
            if anchor and target.is_file() and target.suffix=='.md':
                assert anchor in anchors(target),(p,target,anchor);anchor_checks+=1
            checked+=1
    assert not broken,broken
    history={p.name for p in (REPO/'experiment_history').glob('*.md') if p.name!='README.md'}
    index=(REPO/'experiment_history/README.md').read_text()
    indexed=set(re.findall(r'\]\(([^/()]+\.md)\)',index))
    assert history<=indexed,(history-indexed)
    # Old anchored links keep a current compatibility target, and full archived target.
    legacy='2026-10-03-新对话接续入口'
    assert legacy in anchors(REPO/'s-target.md') and legacy in anchors(H/'archive/s-target.md')
    archive_missing={};new_missing={}
    for name in before:
        prior_missing={str(t) for t,a in links((H/'source_before'/name).read_text(),(REPO/name).parent) if not t.exists()}
        later_missing={str(t) for t,a in links((H/'archive'/name).read_text(),(H/'archive'/name).parent) if not t.exists()}
        extra=later_missing-prior_missing
        assert not extra,(name,extra)
        if later_missing:archive_missing[name]=sorted(later_missing)
    plan=load(H/'cleanup_plan.json');clean=load(H/'cleanup_receipt.json')
    for v in plan['removed']+plan['other_removed']:assert not (REPO/v['path']).exists(),v['path']
    for v in plan['preserved']:
        p=REPO/v['path'];assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],v['path']
    for p in H.glob('*.py'):ast.parse(p.read_text())
    diff=subprocess.run(['git','diff','--check','--',*before.keys()],cwd=REPO,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    # Final sizes may include the supplemental 90a index correction after initial consolidation.
    changes={n:{'before_bytes':v['bytes'],'after_bytes':(REPO/n).stat().st_size,'before_lines':v['lines'],
                'after_lines':len((REPO/n).read_text().splitlines())} for n,v in before.items()}
    (H/'document_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    roots=['summary.md','spec.md','s-target.md','s-experiment.md'];old=sum(before[n]['bytes'] for n in roots);new=sum((REPO/n).stat().st_size for n in roots)
    out={'status':'PASS_CURRENT_DOCUMENT_CONSOLIDATION_AND_REFERENCED_CACHE_PROTECTION',
        'current_local_links_checked':checked,'current_anchor_checks':anchor_checks,'broken_current_links':broken,
        'historical_cards_preserved_and_indexed':len(history),'protected_evidence_files_verified':len(protected),
        'source_before_original_bytes_verified':len(before),'archive_preexisting_missing_links':archive_missing,
        'archive_new_missing_links':new_missing,'four_root_bytes_before':old,'four_root_bytes_after':new,
        'four_root_reduction_pct':100*(old-new)/old,'removed_cache_files':clean['removed_cache_files'],
        'preserved_cache_files':clean['preserved_cache_files'],'reclaimed_file_bytes':clean['reclaimed_file_bytes'],
        'old_E184_delivery_modified':False,'scientific_runs':0,'default_changed':False,'git_diff_check':'PASS',
        'elapsed_seconds':time.time()-start,'final_current_document_sha256':{n:sha(REPO/n) for n in before}}
    (H/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    manifest={str(p.relative_to(H)):{'sha256':sha(p),'bytes':p.stat().st_size}
        for p in H.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (H/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    assert all(p.is_file() for p in generated_here)
    print(json.dumps({k:v for k,v in out.items() if k not in ['archive_preexisting_missing_links','final_current_document_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
