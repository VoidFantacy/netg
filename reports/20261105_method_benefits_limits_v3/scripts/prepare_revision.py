"""Create a presentation-only revision without modifying prior deliveries."""
from pathlib import Path
import hashlib,json,shutil

W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
OLD=W/'reports/20261105_method_benefits_limits_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['analysis','figures','reviews','source_before']:
    (R/name).mkdir(exist_ok=True)
assert not (R/'source_before/identity.json').exists()
previous=json.loads((OLD/'delivery_validation.json').read_text())
roots={}
for b in previous['root_bridges']:
    p=W/b['path'];h=sha(p)
    assert h==b['after_sha256'],b['path']
    dest=R/'source_before'/b['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dest);roots[b['path']]=h
sources=json.loads((OLD/'source_before/identity.json').read_text())['sources']
for name,h in sources.items():assert sha(W/name)==h,name
for p in [OLD/'delivery_manifest.json',OLD/'delivery_validation.json',
          OLD/'ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf',
          OLD/'scripts/build_pdf.py',OLD/'scripts/render_pdf.py',
          OLD/'analysis/E199_two_family_curves.csv',OLD/'analysis/E183_L200_benefits_and_costs.csv',
          W/'reports/20261024_failure_rescue_residual_lt10_v2/per_query_hits.npz',
          W/'reports/20261024_failure_rescue_residual_lt10_v2/failure_by_L.csv',
          W/'reports/20261105_low_recall_stage_attribution_v1/analysis/low_query_transitions.csv',
          W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs/coco.analysis.json']:
    sources[str(p.relative_to(W))]=sha(p)
cfg=json.loads((W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs/coco.analysis.json').read_text())
gt=Path(cfg['eval_gt']['path']);sources[str(gt.relative_to(W))]=sha(gt)
for L in [100,128,200,400,800,1000,1200]:
    for method in ['NSG','GT10-hard','hard-JOINT32']:
        p=W/f'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/results/coco/k100/{method}_L{L}/raw/ids.i32'
        sources[str(p.relative_to(W))]=sha(p)
prior_manifest=json.loads((OLD/'delivery_manifest.json').read_text())
prior_files={}
for f in prior_manifest['files']:
    p=OLD/f['path'];assert sha(p)==f['sha256'],f['path']
    prior_files[str(p.relative_to(W))]=f['sha256']
for name in ['build_pdf.py','render_pdf.py','finalize.py']:
    shutil.copyfile(OLD/'scripts'/name,R/'scripts'/name)
shutil.copyfile(OLD/'README.md',R/'README.md')
identity=dict(scope='Remove A/B subwindow lines from current performance figures; retain pooled data; audit COCO low-recall increase by stage; no new experiments',
              client_date='2026-11-05',sources=sources,roots_before=roots,prior_delivery='reports/20261105_method_benefits_limits_v2/delivery_validation.json',
              prior_delivery_files=prior_files)
(R/'source_before/identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n')
print('Prepared new revision; six root snapshots; prior delivery and raw COCO sources protected.')
