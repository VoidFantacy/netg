from pathlib import Path
import sys,hashlib,json,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();check(O/'reviews/final_artifact_freeze.json');S=Path(__file__).resolve().parent
paths=[O/'results'/ds/'fit/action_statistics.json' for ds in DS]+[O/'results'/ds/'merged_interaction.json' for ds in DS]+[O/'results'/ds/'fit/restore10.npz' for ds in DS]+[O/'results'/ds/'fit/compact_baseline.npz' for ds in DS]+[Path(__file__).resolve()];freeze(S/'input_freeze.json',paths);tick=time.monotonic();records=[]
fig,axes=plt.subplots(2,2,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 a=read(O/'results'/ds/'fit/action_statistics.json');base=dict(np.load(O/'results'/ds/'fit/compact_baseline.npz'));gain=loss=mixed=0
 for j,r in enumerate(a):
  z=dict(np.load(O/'results'/ds/'fit'/f'action_{j:03}.npz'));delta=z['hits'].astype(int)-base['hits'][z['rows']];g=int(np.maximum(delta,0).sum());l=int(np.maximum(-delta,0).sum());assert g==r['gain_hits'] and l==r['loss_hits'];gain+=g;loss+=l;mixed+=int(g>0 and l>0)
 x=np.arange(32);ax=axes[di,0];ax.bar(x,[r['gain_hits'] for r in a],color='#258a75',label='Gained query hits');ax.bar(x,[-r['loss_hits'] for r in a],color='#c76357',label='Lost query hits');ax.scatter([j for j,r in enumerate(a) if r['accepted']],[0 for r in a if r['accepted']],s=25,color='black',marker='*',label='Accepted');ax.set_xlabel('Frozen proposal order (0–31)');ax.set_ylabel('Query-hit gain / loss');ax.set_title(('WebVid' if di==0 else 'Yandex')+f': {mixed}/32 mixed; +{gain} / −{loss}');ax.axhline(0,color='black',lw=.7)
 if di==0:ax.legend(fontsize=8)
 inter=read(O/'results'/ds/'merged_interaction.json');union=dict(np.load(O/'results'/ds/'fit/restore10.npz'));assert int(union['hits'].sum(dtype=np.int64)-base['hits'].sum(dtype=np.int64))==inter['actual_merged'];assert sum(r['net_hits'] for r in a if r['accepted'])==inter['independent_sum'];ax=axes[di,1];bars=ax.bar(['Sum of accepted\nsingle-action changes','Actual merged model'],[inter['independent_sum'],inter['actual_merged']],color=['#c29647','#267f96']);ax.bar_label(bars,fmt='%+.0f',padding=5);ax.set_ylim(0,max(inter.values())*1.3);ax.set_ylabel('Net GT10 hits vs compact');ax.set_title(f"{inter['nonadditive_queries']} queries have nonadditive merged outcomes");records.append(dict(dataset=ds,actions=32,mixed_actions=mixed,gain_hit_events=gain,loss_hit_events=loss,**inter))
fig.suptitle('E89 P-fit 20,000 training responses | action-event totals are not unique query counts\nActual fixed-topology parent restoration; all data historically exposed; no QPS')
fig.savefig(S/'training_gain_loss.png',dpi=170);fig.savefig(S/'training_gain_loss.svg');plt.close(fig);dump(S/'derivation.json',dict(status='PASS',records=records,new_ANN=0,new_fits=0,seconds=time.monotonic()-tick,scope='Post-query training-plot supplement; original E89 final seal remains unchanged.'))
(S/'report.md').write_text('# E89 训练损益图补充\n\n本补充仅从已封存响应导出训练图，0新增ANN/拟合。原报告和最终seal不改。Web31/32、Y26/32动作同时产生收益和损伤；1334/1274与610/625为query-action命中事件正负部，不是独立query数。筛选后单项净和297/125，实际合并224/114，训练收益不能代替迁移或QPS。\n\n![训练损益](training_gain_loss.png)\n\n[原报告](../report.md) · [可核验派生](derivation.json)\n')
check(O/'reviews/final_artifact_freeze.json');freeze(S/'final_freeze.json',[p for p in S.rglob('*') if p.is_file()]);print('E89_TRAINING_SUPPLEMENT_COMPLETE')
