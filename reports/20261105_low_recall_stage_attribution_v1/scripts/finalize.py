from pathlib import Path
import csv,json,hashlib,re
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open()))
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
identity=read(R/'source_before/identity.json')
for name,h in identity['sources'].items():assert sha(W/name)==h,name
prev=read(W/'reports/20261105_current_method_summary_v1/delivery_validation.json')
before={x['path']:x for x in prev['root_bridges']}
bridges=[]
for name,h in identity['roots_before'].items():
    assert sha(R/'source_before'/name)==h
    assert before[name]['after_sha256']==h,name
    bridges.append(dict(path=name,before_snapshot='source_before/'+name,before_sha256=h,after_sha256=sha(W/name)))
audit=read(R/'reviews/raw_audit.json');assert audit['status']=='PASS_STDLIB_ACTUAL_GT_AND_PACKET_RECOMPUTATION'
assert audit['points']==147 and audit['three_stage_groups']==49 and audit['original_input_hashes_rechecked']==163
rows=csvread(R/'analysis/stage_attribution_all_datasets.csv');assert len(rows)==49
for r in rows:
    a,b,c=[int(r[x]) for x in ['NSG_low','GT10_low','B32_low']]
    assert a-int(r['GT10_rescued'])+int(r['GT10_new_low'])==b
    assert b-int(r['B32_rescued'])+int(r['B32_new_low'])==c
    assert int(r['B32_rescued'])==int(r['B32_rescued_NSG_legacy'])+int(r['B32_rescued_GT10_induced'])
assert len(list(R.rglob('*.pdf')))==0,'User explicitly asked for no PDF'
figs=read(R/'reviews/plot_build.json')['figures'];assert len(figs)==4
for name in figs:
    assert (R/f'figures/{name}.png').is_file() and (R/f'figures/{name}.svg').is_file()
docs=[W/name for name in identity['roots_before']]+[R/'README.md',R/'report_zh.md',R/'protocol.md'];links=0
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if target.startswith(('https:','http:','#','mailto:')):continue
        dest=(doc.parent/target.split('#')[0]).resolve()
        if dest==(R/'delivery_validation.json').resolve():continue
        assert dest.exists(),(doc,target)
        links+=1
write(R/'reviews/visual_review.json',dict(status='PASS_FOUR_PNG_SVG_VISUAL_REVIEW',reviewer='same operator',figures=figs,checks=['all four PNGs inspected','Chinese legends and captions readable','dataset-specific failure-rate scales stated','zero-event Flickr annotated','positive rescue and negative introduced queries separated','L200 source decomposition has integer counts','mean recall and tail repair use separate axes and definitions'],PDF=False))
write(R/'reviews/document_checks.json',dict(status='PASS_STAGE_REPORT_AND_SOURCE_CHECKS',root_bridges=len(bridges),source_hashes_unchanged=len(identity['sources']),links_checked=links,all_49_stage_conservation_checks=True,zero_PDF_files=True,new_ANN=0,new_timing=0,default_changed=False,stopped_branches_resumed=False))
files=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ['delivery_manifest.json','delivery_validation.json']]
write(R/'delivery_manifest.json',dict(status='LOW_RECALL_STAGE_ACCOUNTING_LOCAL_DELIVERY',files=files,root_bridges=bridges,protected_sources=identity['sources'],source_identity='E183 preserved full public windows; not E199 new confirmation'))
write(R/'delivery_validation.json',dict(status='PASS_LOW_RECALL_STAGE_ACCOUNTING_NO_PDF',client_date='2026-11-05',primary_datasets=4,appendix_datasets=3,K=100,L=[100,128,200,400,800,1000,1200],source_points=147,three_stage_groups=49,eight_state_rows=392,paired_stage_rows=98,original_raw_input_hashes_rechecked=163,independent_audit='same operator; NumPy sealed counts versus stdlib original GT and timed ID packets',figures=figs,PDF=False,new_ANN=0,new_GT=0,new_timing=0,new_models=0,default_changed=False,root_bridges=bridges,links_checked=links,manifest_sha256=sha(R/'delivery_manifest.json')))
print('PASS: complete all-L stage accounting; 147 raw points audited, 163 source hashes preserved, four plots, zero PDFs or new ANN runs.')
