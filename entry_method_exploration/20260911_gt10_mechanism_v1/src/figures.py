import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import *

def csvread(p):return list(csv.DictReader(Path(p).open()))
def save(fig,name):
    for ext in ['png','svg']:fig.savefig(RUN/'figures'/f'{name}.{ext}',dpi=180)
    plt.close(fig)

def main():
    metrics=csvread(RUN/'results/all_metrics.csv');pairs=csvread(RUN/'results/all_pairs.csv')
    reps=csvread(RUN/'results/repetition.csv');new=csvread(RUN/'supplement/results/repeat_wall.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    labels={'nsg_medoid':'NSG','gt1_hard':'GT1 hard / matched Fast20K','gt10_hard':'GT10 hard','fast30k_3':'Fast30K (context)'}
    colors={'nsg_medoid':'#8d96a0','gt1_hard':'#223a52','gt10_hard':'#bc652b','fast30k_3':'#8d74a0'}
    fig,axes=plt.subplots(2,2,figsize=(12.5,8),constrained_layout=True)
    for col,ds in enumerate(DATASETS):
        ax=axes[0,col]
        for family in labels:
            mm=sorted([x for x in metrics if x['dataset']==ds and x['stage']=='validation' and x['model']==family],key=lambda x:int(x['L']))
            ax.scatter([float(x['recall_percent']) for x in mm],[float(x['qps']) for x in mm],color=colors[family],label=labels[family],s=30)
            if family=='gt10_hard':
                for x in mm:ax.annotate('L'+x['L'],(float(x['recall_percent']),float(x['qps'])),xytext=(4,5),textcoords='offset points',fontsize=8)
        ax.set(title=('WebVid' if col==0 else 'Yandex-IP')+' | E24 observed points',xlabel='Recall@10 (%)',ylabel='End-to-end QPS')
        ax.grid(alpha=.2);ax.legend(fontsize=8)
        ax=axes[1,col];xx=np.arange(5)
        mm=sorted([x for x in pairs if x['dataset']==ds and x['stage']=='validation' and x['model']=='gt10_hard'],key=lambda x:int(x['L']))
        ax.scatter(xx-.15,[float(x['delta_qps_percent']) for x in mm],color='#999999',marker='x',label='E24: one timing',s=45)
        versions=[('E27',new)] if col==0 else [('E25',[x for x in reps if x['version']=='25']),('E26',[x for x in reps if x['version']=='26'])]
        for j,(version,values) in enumerate(versions):
            color=['#176e90','#9575ab'][j]
            for i,L in enumerate(LS):
                rr=[float(x['delta_qps_percent']) for x in values if x['dataset']==ds and int(x['L'])==L]
                ax.scatter(np.repeat(i+.06+.14*j,len(rr)),rr,color=color,s=25,alpha=.8,label=version+': three timings' if i==0 else None)
        ax.axhline(0,color='black',lw=.8);ax.set(xticks=xx,xticklabels=LS,xlabel='NSG L',ylabel='GT10 hard / GT1 hard QPS change (%)')
        ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Separate quality gains from timing stability\nOne frozen build; reused historical validation; no curve interpolation',fontsize=13)
    save(fig,'quality_and_timing')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    for ax,ds in zip(axes,DATASETS):
        mm=sorted([x for x in pairs if x['dataset']==ds and x['stage']=='validation' and x['model']=='gt10_hard'],key=lambda x:int(x['L']))
        xx=np.arange(5);g=np.array([int(x['gain_hits']) for x in mm]);loss=np.array([int(x['lost_hits']) for x in mm])
        ax.bar(xx,g,color='#287f70',label='Gained GT hits');ax.bar(xx,-loss,color='#b55a60',label='Lost GT hits')
        ax.scatter(xx,g-loss,color='#203345',marker='D',s=30,label='Net hits',zorder=3)
        for i,v in enumerate(g-loss):ax.annotate(f'{v:+d}',(i,v),xytext=(5,5 if v>=0 else -14),textcoords='offset points',fontsize=9)
        ax.axhline(0,color='black',lw=.7);ax.set(xticks=xx,xticklabels=LS,title='WebVid' if ds==DATASETS[0] else 'Yandex-IP',
             xlabel='NSG L',ylabel='GT hits across all 2,000 queries')
        ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('GT10 hard versus GT1 hard: positive and negative contributions retained')
    save(fig,'gain_loss_all_L')
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    sh=csvread(RUN/'supplement/results/shuffle_comparisons.csv')
    for ax,ds in zip(axes,DATASETS):
        xx=np.arange(4);names=['cal HNSW','cal exact','audit HNSW','audit exact'];true=[];shuffle=[]
        for stage,backend in [('cal','HNSW'),('cal','exact'),('audit','HNSW'),('audit','exact')]:
            true.append(float(next(x for x in pairs if x['dataset']==ds and x['stage']==stage and x['model']=='gt10_hard' and x['exact']==str(backend=='exact'))['delta_recall_pp']))
            shuffle.append(float(next(x for x in sh if x['dataset']==ds and x['stage']==stage and x['backend']==backend and x['baseline']=='gt1_hard')['delta_recall_pp']))
        ax.bar(xx-.18,true,width=.35,label='True GT10 hard',color='#287f70');ax.bar(xx+.18,shuffle,width=.35,label='One fixed tail shuffle',color='#b55a60')
        ax.axhline(0,color='black',lw=.7);ax.set(xticks=xx,xticklabels=names,title='WebVid' if ds==DATASETS[0] else 'Yandex-IP',ylabel='Recall change vs GT1 hard (pp)')
        ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Query-target correspondence control | L128, historical cal/audit\nHub mass preserved; ESS and profile directions are not matched',fontsize=12)
    save(fig,'correspondence_control')
    print('FIGURES_COMPLETE')

if __name__=='__main__':main()
