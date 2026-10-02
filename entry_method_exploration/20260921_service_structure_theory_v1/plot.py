"""Render saved analysis only; no new hypothesis selection."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'results/analysis.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(10,7),sharex=True,sharey=True)
ranks=[1,2,4,8,16,32,64]
for ax,(name,ls) in zip(axes,r['datasets'].items()):
    for a,(L,it) in zip(ax,ls.items()):
        sp=it['spectra']; ns=it['nulls']
        observed=np.array([sp['double_centered']['fraction'][str(k)] for k in ranks])
        null=np.array([[n['spectrum']['fraction'][str(k)] for k in ranks] for n in ns])
        a.plot(ranks,observed*100,'o-',label='Query-entry interaction',color='#176b87')
        a.plot(ranks,null.mean(0)*100,'--',label='Within-query shuffle',color='#a66f38')
        a.fill_between(ranks,null.min(0)*100,null.max(0)*100,color='#a66f38',alpha=.2)
        a.axhline(50,color='.65',lw=.8,ls=':');a.axvline(8,color='.65',lw=.8,ls=':')
        a.set_xscale('log',base=2);a.set_xticks(ranks,labels=ranks)
        a.set_ylim(0,100);a.grid(alpha=.12)
        label='WebVid' if name.startswith('web') else 'Yandex'
        a.set_title(f'{label}, L={L}')
        a.text(.05,.94,f'Raw rank-1 energy: {100*sp["raw"]["fraction"]["1"]:.1f}%\nBlock MSE reduction: {100*it["block"]["mse_reduction"]:.1f}%',transform=a.transAxes,va='top',fontsize=9)
for a in axes[-1]: a.set_xlabel('Rank')
for a in axes[:,0]: a.set_ylabel('Interaction energy explained (%)')
handles,labels=axes[0,0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',ncol=2,bbox_to_anchor=(.5,.025))
fig.suptitle('Shared search responses: historical E20 cache',fontsize=15)
fig.text(.5,.01,'512 queries per dataset; old K=10 single-entry labels; structural analysis, not deployed routing.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.09,1,.95))
fig.savefig(HERE/'results/service_structure.png',dpi=180)
fig.savefig(HERE/'results/service_structure.pdf')
