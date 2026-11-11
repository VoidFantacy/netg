"""Publish only reviewed ACSG research documents, sources and compact evidence."""
from pathlib import Path
from collections import Counter
import base64,hashlib,json,os,re,shutil,subprocess

SOURCE=Path('/data/netg/ACSG')
PUB=Path('/data/netg/ACSG-publish-20261111')
TMP=Path(__file__).resolve().parent
SNAP=Path('research_snapshots/20261111_residual_reports')
PARENT='9fd0788a81b2f58e6f86539e080f629de7199344'
REPO='VoidFantacy/netg'
def git(*args):return subprocess.check_output(['git','-C',str(PUB),*args])
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(data):
    return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
def objects(tree):
    ans={}
    for row in git('ls-tree','-r','-z',tree).split(b'\0'):
        if row:
            meta,path=row.split(b'\t',1);mode,kind,sha=meta.decode().split()
            ans[path.decode()]=dict(mode=mode,type=kind,sha=sha)
    return ans

def select():
    paths={'AGENTS.md','LOCAL_CODEX_START.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','论文写作约定.md'}
    for p in (SOURCE/'experiment_history').glob('*.md'):
        if p.name[:3].isdigit() and 183<=int(p.name[:3])<=200:paths.add(str(p.relative_to(SOURCE)))
    bases=[]
    for root in ['entry_method_exploration','reports']:
        for p in sorted((SOURCE/root).iterdir()):
            if p.is_dir() and not p.is_symlink() and '20261024'<=p.name[:8]<='20261110':bases.append(p)
    maint=SOURCE/'experiment_history/_maintenance'
    bases += [p for p in sorted(maint.iterdir()) if p.is_dir() and '20261024'<=p.name[:8]<='20261110']
    skip_dirs={'storage','models','inputs','results','bin','build','__pycache__','.git','.venv','pdf_pages','review_pages','review_pdf_pages','pdf_renderer','fonts','calibration','qualification','dense_control','development','staging','recovery_boot1'}
    allowed={'.md','.py','.cpp','.h','.hpp','.inc','.json','.csv','.svg','.png','.pdf','.txt','.sh'}
    excluded=Counter();big=[]
    for base in bases:
        for directory,dirs,files in os.walk(base,followlinks=False):
            dirs[:]=[n for n in dirs if n not in skip_dirs and not (Path(directory)/n).is_symlink()]
            for name in files:
                p=Path(directory)/name
                if p.is_symlink() or not p.is_file():continue
                if p.suffix.lower() not in allowed:excluded[p.suffix.lower()]+=1;continue
                if p.name in ['query_metrics.csv','node_geometry.csv','loss_cases.csv']:
                    excluded['dense_per_query_csv']+=1;continue
                size=p.stat().st_size
                if size>8_000_000:
                    big.append(dict(path=str(p.relative_to(SOURCE)),bytes=size));continue
                paths.add(str(p.relative_to(SOURCE)))
    return sorted(paths),dict(excluded),big

def prepare():
    assert git('rev-parse','HEAD').decode().strip()==PARENT
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    paths,excluded,big=select()
    old=objects(PARENT)
    entries=[]
    for rel in paths:
        src=SOURCE/rel;assert src.is_file() and not src.is_symlink(),rel
        data=src.read_bytes();dest=PUB/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        mode=old.get(rel,{}).get('mode','100755' if src.stat().st_mode&0o111 else '100644')
        os.chmod(dest,0o755 if mode=='100755' else 0o644)
        entries.append(dict(path=rel,mode=mode,**digest(data)))
    (PUB/SNAP).mkdir(parents=True,exist_ok=True)
    reader='''# 2026-11-11 研究同步\n\n本次同步包含截至2026-11-10的现行根文档、E184–E200相关协议/实现/汇总结果/审计，以及2026-11-05的PDF与COCO失败查询修订。默认仍为E99 GT10，没有新增实验。\n\n先读[当前接续入口](../../LOCAL_CODEX_START.md)、[当前结论](../../summary.md)、[实现合同](../../spec.md)。\n\n- 最新实测：[E200报告](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)、[640点](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/points.csv)、[两轮完整计时](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/rounds.csv)。\n- 本对话修订：[8页PDF](../../reports/20261105_method_benefits_limits_v3/ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf)、[修订说明](../../reports/20261105_method_benefits_limits_v3/README.md)。收益图去掉A/B浅线，合并数字保持原样。\n- COCO严重失败：L200原NSG→GT10→B32为0→1→1；同一查询命中97→3→3。新增发生于GT10阶段，B32未新增也未救回。[逐查询复核](../../reports/20261105_method_benefits_limits_v3/reviews/coco_raw_audit.json)。\n- 方法定位：[论文写作约定](../../论文写作约定.md)；当前流程为GT10加直接B32，双塔/导航/残差门的停止边界保持。\n\n2026-11-05的PDF是E199/E183既有证据整理，最新性能应读E200，不混拼不同轮次的绝对QPS。\n\n[文件清单](manifest.json)逐项绑定发布内容与服务器源SHA；[外部资产边界](external_assets.md)说明未纳入Git的大资产。\n'''
    external='''# 外部资产与复跑边界\n\n本次是有范围的研究同步，发布现行文档、实现/绘图/分析源码、配置、冻结身份、汇总CSV、曲线、PDF与审计收据。全部原件保持字节，历史收据的验收范围不扩大。\n\nbase/query/GT向量、主图、训练响应、模型checkpoint与优化器状态、平台静态库/ELF、原始逐查询返回包、密集trace/日志、部分逐query诊断数组及重复PDF渲染页继续保留服务器，不属于本Git交付。目录中的原manifest可能引用这些外部文件；不把源码同步称作开箱复跑。服务器路径与输入SHA沿原协议/配置/收据保留。\n\nGit中已有历史资产不删除，工作区其他改动不混入。主工作区HEAD与index保持；使用独立发布worktree，以已核对远端父提交新增提交，非强制更新既有研究分支。\n'''
    for name,text in [('README.md',reader),('external_assets.md',external)]:
        p=PUB/SNAP/name;p.write_text(text);entries.append(dict(path=str(SNAP/name),mode='100644',**digest(p.read_bytes())))
    shutil.copyfile(Path(__file__),PUB/SNAP/'prepare_publication.py')
    p=PUB/SNAP/'prepare_publication.py';entries.append(dict(path=str(p.relative_to(PUB)),mode='100644',**digest(p.read_bytes())))
    manifest=dict(schema='scoped-research-publication-v2',repository=REPO,branch='research/state-20261002',publication_date='2026-11-11',publication_parent=PARENT,
                  source_head=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD']).decode().strip(),files=sorted(entries,key=lambda x:x['path']),file_count=len(entries),
                  total_bytes=sum(x['bytes'] for x in entries),excluded_extension_counts=excluded,oversized_excluded=big,external_assets=str(SNAP/'external_assets.md'),self_excluded=str(SNAP/'manifest.json'),
                  new_experiments=0,default_changed=False)
    dump(PUB/SNAP/'manifest.json',manifest)
    paths=[x['path'] for x in entries]+[str(SNAP/'manifest.json')]
    (TMP/'paths.nul').write_bytes(b'\0'.join(s.encode() for s in sorted(paths))+b'\0')
    git('add','-f','--pathspec-from-file='+str(TMP/'paths.nul'),'--pathspec-file-nul')
    tree=git('write-tree').decode().strip();now=objects(tree)
    changes=[x.decode() for x in git('diff','--cached','--name-only','-z').split(b'\0') if x]
    assert set(changes)<=set(paths)
    for e in entries:
        assert now[e['path']]['sha']==e['git_blob_sha'] and now[e['path']]['mode']==e['mode'],e['path']
        if e['path'] in paths and not e['path'].startswith(str(SNAP)):
            assert digest((SOURCE/e['path']).read_bytes())['sha256']==e['sha256'],e['path']
    receipt=dict(status='PASS_SCOPED_PUBLICATION_PREFLIGHT',parent=PARENT,base_tree_sha=git('rev-parse',PARENT+'^{tree}').decode().strip(),tree_sha=tree,selected_files=len(paths),changed_files=len(changes),bytes=manifest['total_bytes'],manifest_sha256=digest((PUB/SNAP/'manifest.json').read_bytes())['sha256'])
    dump(TMP/'preflight.json',receipt);print(json.dumps(receipt))

def export():
    pre=json.loads((TMP/'preflight.json').read_text());old=objects(PARENT);new=objects(pre['tree_sha'])
    old_shas={v['sha'] for v in old.values()};blobs=[];seen=set();elements=[]
    paths=[x.decode() for x in git('diff','--cached','--name-only','-z').split(b'\0') if x]
    for path in sorted(paths):
        entry=dict(path=path,**new[path]);data=(PUB/path).read_bytes()
        try:
            text=data.decode('utf-8');assert '\0' not in text
            binary=False
        except (UnicodeDecodeError,AssertionError):binary=True
        if entry['sha'] not in old_shas and (binary or len(data)>100_000):
            if entry['sha'] not in seen:
                payload=dict(repository_full_name=REPO,encoding='base64' if binary else 'utf-8',content=base64.b64encode(data).decode() if binary else text)
                loc=TMP/'blobs'/f"{entry['sha']}.json";dump(loc,payload)
                blobs.append(dict(sha=entry['sha'],path=path,payload=str(loc),bytes=len(data)))
                seen.add(entry['sha'])
        elif entry['sha'] not in old_shas:
            del entry['sha'];entry['content']=text
        elements.append(entry)
    batches=[];current=[];size=0
    for e in elements:
        n=len(json.dumps(e,ensure_ascii=False).encode())
        if current and (len(current)>=40 or size+n>220_000):batches.append(current);current=[];size=0
        current.append(e);size+=n
    if current:batches.append(current)
    records=[]
    for i,batch in enumerate(batches):
        p=TMP/'trees'/f'{i:03}.json';dump(p,dict(repository_full_name=REPO,tree_elements=batch))
        records.append(dict(payload=str(p),entries=len(batch),bytes=p.stat().st_size))
    plan=dict(**pre,blobs=blobs,batches=records)
    dump(TMP/'plan.json',plan)
    print(json.dumps(dict(binary_or_large_blobs=len(blobs),blob_bytes=sum(x['bytes'] for x in blobs),tree_batches=len(records),changed_files=len(paths))))

if __name__=='__main__':
    import sys
    {'prepare':prepare,'export':export}[sys.argv[1]]()
