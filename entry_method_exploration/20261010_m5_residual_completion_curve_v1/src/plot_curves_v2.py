#!/usr/bin/env python3
"""Plot only future independently audited E176 saved fields; no GT/query reads."""
import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATASETS=('webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1')
LABELS=dict(zip(DATASETS,('WebVid2.5M','YandexT2I')))
L_VALUES=(200,400,800,1000,1200)
PRIMARY=('NSG','GT','M5','M5REG96','M5RES12')
MECHANISM=('M5','M5OPT','REGOPT96','WIDE12','M5RES12')
STYLES={'NSG':('#2563eb','o','NSG'),'GT':('#f59e0b','s','GT10'),'M5':('#dc2626','*','原 M5'),'M5REG96':('#7c3aed','D','M5REG96'),'M5RES12':('#059669','^','M5RES12'),'M5OPT':('#dc2626','o','M5OPT'),'REGOPT96':('#7c3aed','s','REGOPT96'),'WIDE12':('#0891b2','D','WIDE12')}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def load(path):
    p=Path(path);require(p.stat().st_size<64*1024*1024,'bounded saved JSON');return json.loads(p.read_text())
def stat4(path):
    s=Path(path).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def sha(path):
    p=Path(path);require(p.stat().st_size<64*1024*1024,'small source only');return hashlib.sha256(p.read_bytes()).hexdigest()
def pk(p):return p['dataset'],p['K'],p['L'],p['method']
def protect(audit):
    paths=set(audit['source_sha256_and_stat4'])|set(load(ROOT/'reviews/data_preflight.json')['registered_input_files'])
    paths|={str(ROOT/x) for x in ('run_state.json','parameter_lock.json','execution_lock.json','protocol.md','reviews/independent_result_audit/report.json')}
    return {p:stat4(p) for p in paths}
def draw(points,methods,out,title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.lines import Line2D
    font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');require(font.exists(),'local Chinese font')
    font_manager.fontManager.addfont(str(font));plt.rcParams.update({'font.family':font_manager.FontProperties(fname=str(font)).get_name(),'font.size':10,'svg.fonttype':'none','axes.unicode_minus':False})
    fig,axes=plt.subplots(2,2,figsize=(16,11));fig.subplots_adjust(left=.095,right=.975,bottom=.13,top=.815,wspace=.27,hspace=.43)
    plotted=[]
    for row,ds in enumerate(DATASETS):
        for col,K in enumerate((1,100)):
            ax=axes[row,col]
            for mi,name in enumerate(methods):
                curve=[points[(ds,K,L,name)] for L in L_VALUES];color,marker,label=STYLES.get(name,('#64748b','o',name))
                x=[p['recall_pct'] for p in curve];y=[p['qps_median'] for p in curve]
                errors=[[p['qps_median']-p['qps_min'] for p in curve],[p['qps_max']-p['qps_median'] for p in curve]]
                ax.errorbar(x,y,yerr=errors,color=color,marker=marker,markersize=8 if name=='M5' else 6,linewidth=1.25,elinewidth=.8,capsize=3)
                for li,p in enumerate(curve):
                    # Text offsets only; all point coordinates and error endpoints stay exact.
                    dx,dy=(5,7+mi*3) if li%2==0 else (-5,-11-mi*3)
                    ax.annotate(str(p['L']),(p['recall_pct'],p['qps_median']),xytext=(dx,dy),textcoords='offset points',fontsize=7,color=color,ha='left' if dx>0 else 'right')
                    plotted.append({k:p[k] for k in ('role','dataset','K','L','method','n','recall_pct','qps_median','qps_min','qps_max')})
                ax.margins(x=.12,y=.14)
            ax.set_title(f'{LABELS[ds]} · Recall@{K}',pad=12);ax.set_xlabel(f'Recall@{K} (%)');ax.set_ylabel('完整 wall QPS');ax.grid(alpha=.25);ax.ticklabel_format(axis='y',style='plain',useOffset=False)
    fig.suptitle(title,fontsize=17,y=.965)
    fig.text(.5,.915,'公开已曝光 10K 查询；原 raw-IP；串行单线程；QPS 中位数与 3 轮 [min,max]；数字为实测 L',ha='center',fontsize=11)
    handles=[Line2D([],[],color=STYLES.get(m,('#64748b','o',m))[0],marker=STYLES.get(m,('#64748b','o',m))[1],label=STYLES.get(m,('#64748b','o',m))[2]) for m in methods]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.895),ncol=len(methods),frameon=False)
    fig.text(.5,.055,'仅连接五个已测预算点以便阅读；无拟合、无中间 L 性能估计；本图不构成新确认或默认替换。',ha='center',fontsize=10)
    png=out.with_suffix('.png');svg=out.with_suffix('.svg');fig.savefig(png,dpi=160);fig.savefig(svg);plt.close(fig)
    return plotted,[str(png),str(svg)]
def main():
    started=time.monotonic();parser=argparse.ArgumentParser();parser.add_argument('--metrics',type=Path,default=ROOT/'analysis/final_v1/metrics.json');parser.add_argument('--out',type=Path,default=ROOT/'analysis/final_v1/figures');args=parser.parse_args()
    require(args.metrics.is_absolute() and args.out.is_absolute() and not args.out.exists(),'absolute fresh figure directory')
    state=load(ROOT/'run_state.json');require(state['status']=='NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None and len(state['completed'])==2 and all(j['exit_code']==0 for j in state['completed']),'actual all-native completion')
    audit=load(ROOT/'reviews/independent_result_audit/report.json');require(audit['status']=='PASS_E176_INDEPENDENT_DYNAMIC_INTEGER_WALL_TRACE_AUDIT','actual independent audit PASS')
    binding=audit['source_sha256_and_stat4'][str(args.metrics)];require(binding['sha256']==sha(args.metrics) and binding['stat4']==stat4(args.metrics),'exact audited metrics bytes')
    for p,r in audit['source_sha256_and_stat4'].items():require(stat4(p)==r['stat4'],'audited source still current')
    before=protect(audit);data=load(args.metrics);require(data['status']=='COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION' and len(data['points'])==audit['point_count'] and len(data['comparisons'])==audit['comparison_count'],'completed dynamic metrics')
    points={pk(p):p for p in data['points']};require(len(points)==len(data['points']),'unique saved points')
    lock=load(ROOT/'parameter_lock.json');configs=[load(p) for p in lock['jobs']]
    expected={(c['dataset'],K,L,m['name']) for c in configs for K in c['K_values'] for L in c['L'] for m in c['methods']};require(set(points)==expected,'dynamic frozen plot input matrix')
    for p in points.values():require(p['role']=='public_test' and p['n']==10000 and all(math.isfinite(p[k]) for k in ('recall_pct','qps_median','qps_min','qps_max')) and 0<=p['recall_pct']<=100 and 0<p['qps_min']<=p['qps_median']<=p['qps_max'] and len(p['qps_rounds'])==3,'saved point scope')
    names=set(p['method'] for p in points.values());groups=[('recall_qps_budget_curves',[m for m in PRIMARY if m in names],'E176 · 原方法与残差补全'),('mechanism_budget_curves',[m for m in MECHANISM if m in names],'E176 · 缓存、区域扩展与等预算补全对照')]
    args.out.mkdir(parents=True);fields=[];figures=[];counts={}
    for stem,methods,title in groups:
        if not methods:continue
        rows,paths=draw(points,methods,args.out/stem,title);fields.extend(dict(figure=stem,**p) for p in rows);figures.extend(paths);counts[stem]=len(rows)
        with (args.out/f'{stem}.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    require(all(stat4(p)==s for p,s in before.items()),'plot did not mutate registered scientific artifacts')
    for row in fields:
        p=points[pk(row)];require(all(row[k]==p[k] for k in row if k!='figure'),'all plotted fields exactly saved values')
    receipt=dict(status='PASS_E176_PRECOMPUTED_DYNAMIC_BUDGET_CURVES',metrics=str(args.metrics),metrics_audited_sha256_and_stat4=binding,input_point_count=len(points),plotted_point_count=len(fields),figure_point_counts=counts,plotted_saved_fields=fields,saved_point_fields_exactly_equal=True,figures=figures,output_sha256={p:sha(p) for p in figures},source_sha256=sha(__file__),elapsed_seconds=time.monotonic()-started,no_new_GT_query_distance_fit_or_bootstrap=True,axes='x=Recall pct,y=complete-wall QPS median,yerr=[saved min,max]',limits=['Five measured L only; line segments visual guides, no interpolation claim.','Historical exposed public_test10K, no independent confirmation.','Main and mechanism views intentionally share M5RES12 saved points.'])
    receipt_path=ROOT/'reviews/plot_curves_execution.json';require(not receipt_path.exists(),'preserve receipt');receipt_path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:receipt[k] for k in ('status','input_point_count','plotted_point_count','figure_point_counts')}))
if __name__=='__main__':main()
