#!/usr/bin/env python3
"""Snapshot explicitly selected documents and write readable historical views."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CURRENT=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','readme.md','AGENTS.md','experiment_history/README.md']
REPORTS=['实验总结.md','总结.md','研究方向.md','advisor_progress_report.md','recent_ten_days_report_20260911.local.md',
         'finite_beam_reachability_goal.md','aco_router_fast_entry.md','command.md']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    (HERE/'source_before').mkdir(exist_ok=False)
    names=CURRENT+REPORTS;manifest={}
    for name in names:
        p=REPO/name;out=HERE/'source_before'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
        manifest[name]={'sha256':sha(p),'bytes':p.stat().st_size,'lines':len(p.read_text().splitlines())}
    (HERE/'before_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    # Preserve the just-delivered E184 identity, never rewrite its old validation or manifest.
    e184=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
    old=json.loads((e184/'delivery_manifest.json').read_text());protected={}
    for relative,value in old.items():
        p=e184/relative;assert sha(p)==value['sha256'],p;protected[str(p.relative_to(REPO))]=value
    for filename in ['delivery_manifest.json','state.json','delivery_validation.json']:
        p=e184/filename;protected[str(p.relative_to(REPO))]={'sha256':sha(p),'bytes':p.stat().st_size}
    e183=REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
    for filename in ['state.json','protocol.md','analysis/final_v1/points.csv','analysis/final_v1/timings.csv','reviews/independent_results_audit.json']:
        p=e183/filename;protected[str(p.relative_to(REPO))]={'sha256':sha(p),'bytes':p.stat().st_size}
    for p in (REPO/'experiment_history').glob('*.md'):
        if p.name!='README.md':protected[str(p.relative_to(REPO))]={'sha256':sha(p),'bytes':p.stat().st_size}
    (HERE/'protected_evidence.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2)+'\n')
    for name in names:
        original=REPO/name;out=HERE/'archive'/name;out.parent.mkdir(parents=True,exist_ok=True)
        def rebase(m):
            label,target=m.group(1),m.group(2)
            if '://' in target or target.startswith('#') or target.startswith('mailto:'):return m.group(0)
            path,sep,fragment=target.partition('#')
            if not path:return m.group(0)
            resolved=(original.parent/path).resolve()
            try:relative=str(resolved.relative_to(REPO))
            except ValueError:return m.group(0)
            destination=HERE/'archive'/relative if relative in names else resolved
            new=os.path.relpath(destination,out.parent)+(sep+fragment if sep else '')
            return f'[{label}]({new})'
        body=re.sub(r'\[([^\]]*)\]\(([^)]+)\)',rebase,original.read_text())
        if name=='s-target.md':
            # This old inbound name predated the later heading suffix; add a readable-view alias.
            body=body.replace('## 2026-10-03 新对话接续入口',
                '<a id="2026-10-03-新对话接续入口"></a>\n\n## 2026-10-03 新对话接续入口',1)
        banner=('> 历史归档：2026-10-24 清理前的全文。下列“当前/最新/运行中/待执行”仅指原记录时点。'
                '现行状态见 [项目入口]('+os.path.relpath(REPO/'LOCAL_CODEX_START.md',out.parent)+')。\n'
                '> 可读副本只修订Markdown链接；原字节保存在同维护目录的source_before。旧命令不是新执行队列。\n\n')
        out.write_text(banner+body)
    # Existing anchored references must keep resolving after consolidating root docs.
    result=subprocess.run(['rg','-n','-o','--glob','*.md','--glob','!.git/**','--glob','!.venv_cpu/**',
        r'(spec|summary|s-target|s-experiment|LOCAL_CODEX_START|readme)\.md#[^ )>]+',str(REPO)],capture_output=True,text=True)
    assert result.returncode in (0,1)
    (HERE/'inbound_anchors_before.txt').write_text(result.stdout)
    print(json.dumps({'snapshotted_documents':len(names),'protected_evidence_files':len(protected),
        'original_doc_bytes':sum(v['bytes'] for v in manifest.values()),'readable_archives':len(names)},ensure_ascii=False))

if __name__=='__main__':main()
