#!/usr/bin/env python3
"""Plot only saved complete test measurements; never search or interpolate."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]
COLORS={'NSG':'#2474b5','GT':'#e49320','M5':'#cf343e'}
MARKERS={'NSG':'o','GT':'s','M5':'*'}
NAMES={'NSG':'NSG 基线','GT':'GT10','M5':'M5 = GT10 + 补全'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--metrics',type=Path,default=ROOT/'analysis/metrics.json');parser.add_argument('--out',type=Path,default=ROOT/'figures');args=parser.parse_args()
    data=json.loads(args.metrics.read_text());assert data['status']=='COMPLETE_TRUE_PUBLIC_TEST_NSG_GT_M5_60_POINTS' and len(data['points'])==60
    assert not args.out.exists(),'preserve existing figures; choose a new --out';args.out.mkdir()
    font_path=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if font_path.exists():font_manager.fontManager.addfont(str(font_path));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    windows=sorted(data['windows'],key=lambda w:0 if 'webvid' in w['dataset'] else 1)
    panels=[(w,K) for w in windows for K in [1,100]]
    def title(w,K):return f'{"WebVid" if "webvid" in w["dataset"] else "Yandex"} · Recall@{K} · {w["GT_method"]}'
    def rows(w,K,method):return sorted([p for p in data['points'] if p['dataset']==w['dataset'] and p['K']==K and p['method']==method],key=lambda p:p['L'])
    def style(ax):ax.grid(alpha=.22);ax.tick_params(labelsize=10)
    def save(fig,name):
        for ext in ['png','svg','pdf']:fig.savefig(args.out/f'{name}.{ext}',dpi=210)
        plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(15,10));fig.subplots_adjust(left=.075,right=.98,top=.88,bottom=.14,hspace=.32,wspace=.22)
    for ax,(w,K) in zip(axes.flat,panels):
        for method in ['NSG','GT','M5']:
            p=rows(w,K,method);x=np.array([a['recall_pct'] for a in p]);y=np.array([a['qps_median'] for a in p]);lo=np.array([a['qps_min'] for a in p]);hi=np.array([a['qps_max'] for a in p])
            ax.errorbar(x,y,yerr=[y-lo,hi-y],color=COLORS[method],marker=MARKERS[method],markersize=11 if method=='M5' else 6,linewidth=1.6,capsize=3,label=NAMES[method])
            if method=='M5':
                for i,a in enumerate(p):
                    off=(7,9) if a['L']<800 else {800:(7,19),1000:(17,11),1200:(24,1)}[a['L']]
                    ax.annotate(str(a['L']),(x[i],y[i]),xytext=off,textcoords='offset points',fontsize=9,color=COLORS[method])
        ax.margins(x=.12,y=.08);ax.set_title(title(w,K),fontsize=12);ax.set_xlabel(f'Recall@{K}（%）');ax.set_ylabel('完整单线程 QPS');style(ax)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=3,frameon=False)
    fig.suptitle('NSG / GT10 / M5：五个实际搜索预算的 Recall–QPS 对比',fontsize=18,y=.99)
    fig.text(.5,.067,'两集各公共测试前 10000 查询；K=1/100 分别真实搜索；L=200/400/800/1000/1200 对三方法相同',ha='center',fontsize=11)
    fig.text(.5,.035,'越右上越好；红色数字标注 M5 的 L，三方法均为同五档；QPS 为 3 轮中位，误差线为 min–max',ha='center',fontsize=10,color='#555555');save(fig,'recall_qps_nsg_gt_m5')
    fig,axes=plt.subplots(2,4,figsize=(21,10));fig.subplots_adjust(left=.055,right=.985,top=.87,bottom=.14,hspace=.32,wspace=.30)
    for pi,(w,K) in enumerate(panels):
        row=pi//2;start=2*(pi%2)
        for method in ['NSG','GT','M5']:
            p=rows(w,K,method);L=[a['L'] for a in p];rec=[a['recall_pct'] for a in p];qps=np.array([a['qps_median'] for a in p]);low=np.array([a['qps_min'] for a in p]);high=np.array([a['qps_max'] for a in p])
            axes[row,start].plot(L,rec,color=COLORS[method],marker=MARKERS[method],markersize=10 if method=='M5' else 5,label=NAMES[method])
            axes[row,start+1].errorbar(L,qps,yerr=[qps-low,high-qps],color=COLORS[method],marker=MARKERS[method],markersize=10 if method=='M5' else 5,capsize=3,label=NAMES[method])
        for col in [start,start+1]:
            ax=axes[row,col];ax.set_title(title(w,K),fontsize=11);ax.set_xlabel('实际搜索预算 L');ax.set_xticks([200,400,800,1000,1200]);style(ax)
        axes[row,start].set_ylabel(f'Recall@{K}（%）');axes[row,start+1].set_ylabel('完整单线程 QPS')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=3,frameon=False)
    fig.suptitle('同实际 L 比较：Recall 与完整单线程 QPS',fontsize=18,y=.99)
    fig.text(.5,.065,'每场景左图 Recall、右图 QPS；冻结 GT10 / M5 表不训练；两集公共测试窗口均为 [0, 10000)',ha='center',fontsize=11)
    fig.text(.5,.035,'全部五档预算原点；QPS 误差线为三轮范围；不混合不同 K、数据集或查询窗口',ha='center',fontsize=10,color='#555555');save(fig,'recall_qps_vs_L_nsg_gt_m5')
    (args.out/'plot_provenance.json').write_text(json.dumps({'metrics':str(args.metrics),'new_search':False,'interpolation_used_for_conclusion':False,'points':60,'figures':['recall_qps_nsg_gt_m5','recall_qps_vs_L_nsg_gt_m5']},indent=2)+'\n')
    print(json.dumps({'status':'PLOTS_WRITTEN','out':str(args.out)},ensure_ascii=False))

if __name__=='__main__':main()
