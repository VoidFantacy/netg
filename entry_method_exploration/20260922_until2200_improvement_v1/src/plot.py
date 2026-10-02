import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
R=Path(__file__).resolve().parents[1];(R/'figures').mkdir(exist_ok=True);sources={};outputs=[]
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';fontManager.addfont(fontpath);font=FontProperties(fname=fontpath)
plt.rcParams.update({'font.family':font.get_name(),'font.size':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'svg.fonttype':'none','pdf.fonttype':42})
DS={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
blue='#2855a6';orange='#c56e25';green='#238777';gray='#778495'
def read(p):p=R/p;sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def save(fig,name):
    for ext in ['png','svg','pdf']:
        p=R/'figures'/f'{name}.{ext}';assert not p.exists();fig.savefig(p,dpi=180,bbox_inches='tight');outputs.append(str(p.relative_to(R)))
    plt.close(fig)
S=read('research/profile_direction_stability_v1/results/summary.json');fig,axs=plt.subplots(1,2,figsize=(10.7,4.3))
for ax,(ds,label) in zip(axs,DS.items()):
    families=S[ds]['families'];names=list(families);xx=np.arange(len(names));a=[families[n]['actual_all_hubs']['centered_profile_replicability'] for n in names];b=[families[n]['shuffled_all_hubs']['centered_profile_replicability'] for n in names]
    ax.bar(xx-.18,a,.36,label='真实目标对应',color=blue);ax.bar(xx+.18,b,.36,label='行置换对应',color='#b9c7dc');ax.set_xticks(xx,[n.replace('Hard','-hard').replace('Soft','-soft') for n in names]);ax.set_title(label);ax.set_ylim(0,1.07);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    for x,y in zip(xx-.18,a):ax.text(x,y+.025,f'{y:.3f}',ha='center',fontsize=9)
axs[0].set_ylabel('去公共方向后的两半画像相关 ρ');axs[1].legend(loc='lower right',frameon=False);fig.suptitle('GT10更稳定；正确目标对应还有额外价值',fontsize=15);fig.tight_layout();fig.text(.5,-.025,'固定同20K平分；共同正支持子集结论保持。一次划分的描述量，不是Recall因果保证。',ha='center',fontsize=9);save(fig,'profile_stability')

G=read('research/semantic_decision_geometry_v1/results/summary.json');fig,ax=plt.subplots(figsize=(10.7,4.8));labels=[];proxy=[];residual=[];total=[]
for ds,label in DS.items():
    for K in ['1','100']:
        v=G[ds][K]['19k_minus_3k'];labels.append(f'{label} / K{K}');proxy.append(100*v['privileged_score_regret']['mean']);residual.append(100*v['service_residual_contrast']['mean']);total.append(100*v['actual_u_gap']['mean'])
x=np.arange(4);ax.bar(x-.2,proxy,.4,label='代理决策遗憾变化',color=blue);ax.bar(x+.2,residual,.4,label='服务残差对比变化',color=orange);ax.scatter(x,total,marker='D',s=48,c='#182b43',label='真实效用差变化（两项之和）',zorder=4);ax.axhline(0,color=gray,lw=.8);ax.set_xticks(x,labels);ax.set_ylabel('19K减3K，效用单位 ×100');ax.set_title('更接近特权评分，实际决策仍可能变差',fontsize=15);ax.legend(frameon=False,ncol=1,fontsize=9,loc='upper left',bbox_to_anchor=(0,1));ax.set_ylim(-1.02,1.07);ax.grid(axis='y',alpha=.15);fig.tight_layout();fig.text(.5,-.025,'菱形为正表示学生相对特权策略的实际差距扩大；u不是QPS。固定α也改变α/n，非纯样本数因果实验。',ha='center',fontsize=8.8);save(fig,'proxy_decision_gap')

H=read('research/target_budget_fullH_v1/results/summary.json');fig,ax=plt.subplots(figsize=(11,5));series=[[],[],[],[]];labs=[]
for ds,label in DS.items():
    for K in ['1','100']:
        v=H['datasets'][ds][K];m=v['methods'];labs.append(f'{label} K{K}\n目标L{v["L"]}');series[0].append(v['low_L128_fullH_oracle_gain_pp']);series[1].append(m['FullHOracle']['recall_gain_pp']);series[2].append(m['Top3SingleOracle']['recall_gain_pp']);series[3].append(m['LowL128OracleTransferred']['recall_gain_pp'])
x=np.arange(4)
for j,(a,color,name) in enumerate(zip(series,[gray,blue,orange,green],['L128全H oracle','目标预算全H oracle','目标预算top3 oracle','L128最佳动作迁移'])):
    ax.bar(x+(j-1.5)*.19,a,.19,color=color,label=name)
ax.set_xticks(x,labs);ax.set_ylabel('相对各自同预算默认的Recall增益（pp）');ax.set_ylim(0,20.5);ax.legend(ncol=2,frameon=False,loc='upper right',fontsize=9);ax.set_title('工作预算仍有入口余量，K100跨预算选择明显损失',fontsize=15);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);fig.tight_layout();fig.text(.5,-.025,'每集固定256条历史query；全H仅为现有单入口+默认，oracle免费，不是部署收益。Y K1预算未变。',ha='center',fontsize=9);save(fig,'target_budget_opportunity')

C=read('research/gt_inclusive_build_cost_v1/results/cost_summary.json');fig,axs=plt.subplots(1,2,figsize=(10.7,4.2))
for ax,(ds,label) in zip(axs,DS.items()):
    v=C['datasets'][ds];gt=v['GT_fraction_of_core_stage_sum']*100;ax.barh([0],[gt],color=orange,label='exact GT');ax.barh([0],[100-gt],left=[gt],color=blue,label='其余核心步骤');ax.set_xlim(0,100);ax.set_yticks([]);ax.set_ylim(-.65,.65);ax.set_title(f'{label}：{v["nonoverlapping_core_stage_sum_seconds"]:.1f}秒');ax.text(gt/2,0,f'GT {gt:.2f}%',va='center',ha='center',color='white',fontsize=15);ax.set_xlabel('不重叠核心阶段费用占比（%）')
axs[1].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.25),ncol=2);fig.suptitle('GT10构建费用主要在监督获得阶段',fontsize=15);fig.tight_layout();fig.text(.5,-.105,'单次、未清缓存，CPU0–7；合计不含阶段外I/O和审计、下载/嵌入/公共NSG/历史选型。不是查询QPS。',ha='center',fontsize=8.8);save(fig,'gt_inclusive_cost')

E=read('stages/e125_approximate_target_profiles_v1/results/summary.json');fig,axs=plt.subplots(2,2,figsize=(11.5,8.0))
for col,(ds,label) in enumerate(DS.items()):
    for row,K in enumerate([1,100]):
        ax=axs[row,col];ps=[p for p in E['datasets'][ds]['points'] if p['K']==K]
        for m,(name,color,marker) in enumerate([('原GT10',blue,'o'),('近似目标画像',orange,'s')]):
            xx=np.array([p['methods'][m]['recall']*100 for p in ps]);yy=np.array([p['methods'][m]['QPS'] for p in ps]);lo=np.array([min(p['methods'][m]['QPS_each_round']) for p in ps]);hi=np.array([max(p['methods'][m]['QPS_each_round']) for p in ps]);ax.errorbar(xx,yy,yerr=[yy-lo,hi-yy],fmt=marker+'-',color=color,label=name,ms=5,capsize=3,lw=1.5)
        for p in ps:ax.annotate(f'L{p["L"]}',(p['methods'][0]['recall']*100,p['methods'][0]['QPS']),xytext=(5,8),textcoords='offset points',fontsize=8)
        ax.set_title(f'{label} / Recall@{K}');ax.set_xlabel('实际Recall（%）');ax.set_ylabel('完整单线程QPS');ax.grid(alpha=.16);ax.margins(x=.15,y=.15)
axs[0,0].legend(frameon=False,fontsize=9);fig.suptitle('E125固定三预算与三重复：完整线上费用',fontsize=15);fig.tight_layout();fig.text(.5,-.015,'E105已曝光但训练字节互斥的4096 query/集；误差线为三次QPS范围，非置信区间。此图不构成默认替换。',ha='center',fontsize=9);save(fig,'approx_target_recall_qps')

fig,axs=plt.subplots(1,2,figsize=(10.7,4.3));xx=np.arange(2);base=[E['datasets'][ds]['exact_profile20k_search_seconds_reference'] for ds in DS];cand=[E['datasets'][ds]['candidate_label_job_seconds'] for ds in DS];axs[0].bar(xx-.18,base,.36,label='exact搜索（CPU上限8）',color=blue);axs[0].bar(xx+.18,cand,.36,label='近似标签整作业（单线程）',color=orange);axs[0].set_xticks(xx,list(DS.values()));axs[0].set_yscale('log');axs[0].set_ylabel('20K画像目标获得时间（秒，对数轴）');axs[0].legend(frameon=False,fontsize=8.5)
for x,y,z in zip(xx,base,cand):axs[0].text(x-.18,y*1.07,f'{y:.1f}',ha='center',fontsize=9);axs[0].text(x+.18,z*1.07,f'{z:.1f}',ha='center',fontsize=9)
vals=[E['datasets'][ds]['profile_directions']['median_angle_degrees'] for ds in DS];axs[1].bar(xx,vals,color=green,width=.55);axs[1].set_xticks(xx,list(DS.values()));axs[1].set_ylabel('近似/精确画像方向夹角中位（度）');axs[1].set_ylim(0,max(vals)*1.45)
for x,y in zip(xx,vals):axs[1].text(x,y+.06,f'{y:.2f}°',ha='center')
fig.suptitle('同一画像公式：更便宜的目标与较小的方向扰动',fontsize=15);fig.tight_layout();fig.text(.5,-.025,'QGT5K仍用原exact监督；资源条件不同，非同线程加速比。少量入口偏移更大，中位数不保证最终Recall。',ha='center',fontsize=9);save(fig,'approx_target_build_cost')
(R/'reviews/figures.json').write_text(json.dumps({'status':'PASS','figures':6,'outputs':outputs,'input_sha256':sources,'only_completed_audited_results':True},indent=2)+'\n')
