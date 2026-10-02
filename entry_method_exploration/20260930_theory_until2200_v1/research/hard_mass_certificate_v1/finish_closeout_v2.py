"""Finish document indexing after v1's incorrect three-column table marker; no numerical rerun."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def put(p,x):
    with Path(p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    assert json.loads((R/'independent_audit.json').read_text())['status']=='PASS'
    assert '[161完整hard质量条件]' in (ROOT/'summary.md').read_text()
    put(R/'closeout_correction.json',{'original_script':'closeout.py','exit_code':1,'reason':'Three-column Markdown table marker was used for the two-column history index','already_written':['report.md','decision.json','history161','summary.md','spec.md','s-target.md'],'numerical_rerun':False})
    p=ROOT/'s-experiment.md';text=p.read_text();marker='## 最新记录\n\n| 记录 | 内容与边界 |\n|---|---|\n'
    assert marker in text and '[161 hard质量区间证书]' not in text
    p.write_text(text.replace(marker,marker+'| [161 hard质量区间证书](experiment_history/161_hard_mass_interval_certificate.md) | 独立盒内充要条件/两种tie穷举核验；0真实搜索，界与费用未知 |\n',1))
    p=ROOT/'experiment_history/README.md';text=p.read_text();title='# ACSG 历史实验详细复盘\n\n';assert title in text
    p.write_text(text.replace(title,title+'2026-09-30最新[161完整hard质量区间条件](161_hard_mass_interval_certificate.md)完成数学核验，0真实搜索/模型，实际费用未知。\n\n',1))
    state=json.loads((CAMP/'state.json').read_text());assert R.name not in state['completed_stages'];state['completed_stages'].append(R.name)
    state.update(stage='box_certificate_verified_real_cost_unknown',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<240*1024
    put(R/'seal.json',{'status':'AUDITED_COMPLETE_MATHEMATICAL_ONLY','unix':time.time(),'files':{str(p.relative_to(R)):ident(p) for p in sorted(R.rglob('*')) if p.is_file()}})
    print('BOX_CERTIFICATE_VERIFIED_REAL_COST_UNKNOWN',flush=True)
if __name__=='__main__':main()
