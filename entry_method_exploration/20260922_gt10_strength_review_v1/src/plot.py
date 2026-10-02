import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
R=Path(__file__).resolve().parents[1]
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                     'svg.fonttype':'none','pdf.fonttype':42,'axes.unicode_minus':False})
def read(name):return json.loads((R/'results'/name).read_text())
def save(fig,name):
    for suffix in ('png','svg','pdf'):
        p=R/'figures'/f'{name}.{suffix}';assert not p.exists();fig.savefig(p,dpi=180,bbox_inches='tight')
    plt.close(fig)
short={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
colors={1:'#2855a6',100:'#c86926'}
a=read('finite_responses.json')
fig,axs=plt.subplots(2,2,figsize=(11,7.4),sharex='col')
for j,(ds,label) in enumerate(short.items()):
    for K in (1,100):
        p=sorted([x for x in a if x['dataset']==ds and x['K']==K],key=lambda x:x['L'])
        xs=[x['L'] for x in p]
        axs[0,j].plot(xs,[x['all_seven_equal_hitcount_pct'] for x in p],'o-',color=colors[K],label=f'K={K}')
        axs[1,j].plot(xs,[x['oracle_gain_pp'] for x in p],'o-',color=colors[K],label=f'K={K}')
    axs[0,j].set_title(label);axs[0,j].set_ylim(35,101)
    axs[1,j].set_ylim(0,8.2);axs[1,j].set_xlabel('主搜索预算 L（对数轴）')
    for ax in axs[:,j]:ax.set_xscale('log',base=2);ax.grid(alpha=.18);ax.legend()
axs[0,0].set_ylabel('七策略命中数全部相同的查询（%）')
axs[1,0].set_ylabel('七策略事后 oracle 对默认的增益（pp）')
fig.suptitle('预算增加后，已有入口策略的结果逐渐趋同',fontsize=16,y=1.02)
fig.text(.5,-.015,'E107/E120 已曝光 4096 query/集；七策略不含 NSG 固定入口。命中数相同不代表返回成员或时间相同。',ha='center',fontsize=10)
fig.tight_layout();save(fig,'response_plateau')

c=read('same_cohort_candidate_coverage.json')
fig,ax=plt.subplots(figsize=(10,5.8))
labels=[f"{short[r['dataset']]}\nK={r['K']}" for r in c]
x=np.arange(4);small=np.array([r['default_plus_actual_three_singles_oracle_gain_pp'] for r in c]);rest=np.array([r['additional_all_H_beyond_three_oracle_gain_pp'] for r in c])
ax.bar(x,small,color='#2855a6',label='默认 + 实际 top3 各自单入口')
ax.bar(x,rest,bottom=small,color='#b9c8e5',label='全 H 单入口额外可达的 oracle 增益')
for i,r in enumerate(c):
    ax.text(i,small[i]+rest[i]+.25,f"{small[i]+rest[i]:.2f} pp",ha='center')
    ax.text(i,small[i]/2,f"{small[i]:.2f}\n占 {r['actual_three_captured_oracle_gain_fraction']*100:.1f}%",ha='center',va='center',color='white',fontsize=10)
ax.set_xticks(x,labels);ax.set_ylabel('对默认 GT10 的 Recall 增益（pp）');ax.set_ylim(0,20)
ax.set_title('原 top3 内选 1/3 入口，只覆盖全 H oracle 增益的一小部分',pad=16)
ax.legend(loc='upper right',frameon=False);ax.grid(axis='y',alpha=.15)
fig.text(.5,-.01,'同一批 E118 fit 4096 query/集、L128；两个 K 分别事后择优，选择免费。不是可部署收益或全动作上界。',ha='center',fontsize=10)
fig.tight_layout();save(fig,'candidate_coverage')

fig,axs=plt.subplots(1,2,figsize=(10,4.8))
for j,(ds,label) in enumerate(short.items()):
    r=next(v for v in c if v['dataset']==ds and v['K']==100)
    p=r['positive_pairs'];n=r['negative_pairs'];total=4096*r['H']
    axs[j].bar(['有收益的动作对','有损伤的动作对'],[p/total*100,n/total*100],color=['#2f8467','#b8544e'])
    for i,(fraction,mag) in enumerate([(p/total,r['mean_positive_action_gain_in_recall_pp']),(n/total,r['mean_negative_action_loss_in_recall_pp'])]):
        axs[j].text(i,fraction*100+.3,f'{fraction*100:.2f}%\n条件平均幅度 {mag:.2f} pp',ha='center',fontsize=10)
    axs[j].set_title(label);axs[j].set_ylim(0,32);axs[j].grid(axis='y',alpha=.15)
axs[0].set_ylabel('全 H query × 单入口动作对中的比例（%）')
fig.suptitle('K100：损伤的平均幅度约为收益的两倍',fontsize=15,y=1.03)
fig.text(.5,-.02,'E118 fit，L128；条件幅度是单个 query 的 Recall 变化，非总体增益。未画命中数不变的动作对。',ha='center',fontsize=10)
fig.tight_layout();save(fig,'gain_damage')

# An explicit factor contrast; no cost inference from exact-routing cached results.
pairs=list(csv.DictReader((R/'results/finite_pairs.csv').open()))
fig,axs=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
methods=['NSGFixed1','UnitHub1','UnitHub3','GT11','GT13','GT101','GT103','DefaultANN']
labels=['NSG固定1','Unit 1','Unit 3','GT1 1','GT1 3','GT10 1','GT10 3','默认ANN 3']
for j,(ds,label) in enumerate(short.items()):
    for off,K in [(-.18,1),(.18,100)]:
        ref=next(v for v in a if v['dataset']==ds and v['K']==K and v['L']==128)
        d={v['method']:float(v['delta_pp']) for v in pairs if v['dataset']==ds and int(v['K'])==K and int(v['L'])==128}
        vals=[d.get(m,0)+ref['default_minus_NSG_pp'] for m in methods]
        axs[j].bar(np.arange(8)+off,vals,.35,color=colors[K],label=f'K={K}')
    axs[j].axhline(0,color='#777',lw=.7);axs[j].set_xticks(np.arange(8),labels,rotation=40,ha='right');axs[j].set_title(label);axs[j].legend();axs[j].grid(axis='y',alpha=.15)
axs[0].set_ylabel('相对 NSG 固定入口的 Recall 变化（pp）')
fig.suptitle('系统收益不能全部归给“十目标画像”',fontsize=16,y=1.04)
fig.text(.5,-.055,'E107/E120 同批 L128；Unit/GT1/GT10 1/3 为精确路由，默认为真实 ANN；Unit 仍使用 QGT 已选出的 H。',ha='center',fontsize=10)
fig.tight_layout();save(fig,'initialization_controls')

print('4 figures × PNG/SVG/PDF; historical data only')
