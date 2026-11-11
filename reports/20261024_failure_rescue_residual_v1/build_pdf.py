#!/usr/bin/env python3
"""Six-page visual explanation using sealed E183/E184 CSVs only; no ANN calls."""
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='1'
from pathlib import Path
import csv
import hashlib
import json
import sys
import time
import unicodedata
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
E184=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
E183=REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
PDF=HERE/'ACSG_失败率_救回率与残差作用_20261024.pdf'
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BOLD=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
for p in [FONT,BOLD]:font_manager.fontManager.addfont(str(p))
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=str(FONT)).get_name(),
    'font.size':10,'pdf.fonttype':3,'ps.fonttype':3,'axes.unicode_minus':False,
    'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
    'axes.edgecolor':'#ccd6e0','axes.labelcolor':'#536b7c','xtick.color':'#536b7c','ytick.color':'#294659',
    'text.color':'#172f40','savefig.facecolor':'white'})
C={'ink':'#172f40','muted':'#536b7c','nsg':'#a5b3c3','gt':'#416e9f','res':'#168d80',
   'res_light':'#9fd3c7','res_dark':'#086c61','gold':'#dfad64','red':'#bf5d64','grid':'#e7edf3','pale':'#f3f7fa'}
INPUTS={}
ARTISTS=[]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p);INPUTS[str(p)]={'bytes':p.stat().st_size,'sha256':sha(p)}
    return list(csv.DictReader(p.open()))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def writecsv(p,rr):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def n(r,k):return int(r[k])
def f(r,k):return float(r[k])
def percent(a,b):return 100*a/b if b else 0.
def wrap(s,max_units):
    out=[];line='';units=0
    for ch in s:
        if ch=='\n':out.append(line);line='';units=0;continue
        size=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if units+size>max_units:out.append(line);line='';units=0
        line+=ch;units+=size
    if line:out.append(line)
    return '\n'.join(out)
def txt(fig,x,y,text,size=10.5,color=None,weight='normal',va='top',**kwargs):
    artist=fig.text(x,y,text,fontsize=size,color=color or C['ink'],weight=weight,va=va,**kwargs)
    ARTISTS.append(artist)
    return artist
def para(fig,x,y,s,width=.89,size=10.3,**kw):
    units=width*11.69*72/(size*.54)
    return txt(fig,x,y,wrap(s,units),size=size,linespacing=1.5,**kw)

def page(number,title,subtitle):
    fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
    txt(fig,.055,.955,f'{number:02d}',size=12,color=C['res'],weight='bold')
    txt(fig,.105,.958,title,size=22,weight='bold')
    para(fig,.055,.897,subtitle,size=10.5)
    fig.add_artist(plt.Line2D([.055,.945],[.075,.075],transform=fig.transFigure,color=C['grid'],lw=1))
    txt(fig,.055,.046,'ACSG  /  2026-10-24  /  E183实测 + E184离线诊断  /  本PDF仅作图表整理',size=8.5,color=C['muted'])
    txt(fig,.945,.046,f'{number} / 6',size=9,color=C['muted'],ha='right')
    return fig
def axis(fig,rect,title=None):
    ax=fig.add_axes(rect);ax.set_axisbelow(True)
    ax.grid(axis='x',color=C['grid'],lw=.8);ax.tick_params(axis='y',length=0,pad=6,labelsize=9.7)
    ax.tick_params(axis='x',length=3,labelsize=9)
    if title:ax.set_title(title,loc='left',pad=13,fontsize=12,weight='bold')
    return ax
def horiz(ax,labels):
    ax.set_yticks(np.arange(len(labels)));ax.set_yticklabels(labels);ax.set_ylim(len(labels)-.5,-.5)
def legend(fig,items,x=.055,y=.843):
    return fig.legend(handles=[Patch(facecolor=c,label=s) for s,c in items],loc='upper left',bbox_to_anchor=(x,y),
        ncol=len(items),frameon=False,borderaxespad=0,fontsize=10,columnspacing=2.)
def note(fig,s,y=.14,color=None):return para(fig,.055,y,s,size=10.2,color=color or C['muted'])
def save(fig,pdf,number,checks):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=[]
    # Figure-level titles/notes are bounded explicitly; axes labels are reviewed on rendered PDF.
    for a in list(ARTISTS):
        if a.figure is not fig:continue
        b=a.get_window_extent(renderer);fb=fig.bbox
        if b.x0<-1 or b.y0<-1 or b.x1>fb.width+1 or b.y1>fb.height+1:bounds.append(a.get_text())
    assert not bounds,('figure text outside page',number,bounds)
    pdf.savefig(fig)
    fig.savefig(HERE/f'figures/page_{number:02d}.png',dpi=145)
    fig.savefig(HERE/f'figures/page_{number:02d}.svg')
    checks.append({'page':number,'figure_text_in_page':True,'title':fig.texts[1].get_text()})
    plt.close(fig)

def main():
    t=time.time();old_draft_sha=None
    if PDF.exists():
        assert '--revise-draft' in sys.argv and not (HERE/'delivery_validation.json').exists(),'new version required after delivery'
        old_draft_sha=sha(PDF)
    (HERE/'figures').mkdir(exist_ok=True)
    ss=read(E184/'analysis/dataset_summary.csv');cc=read(E184/'analysis/coverage_chain.csv')
    pp=read(E183/'analysis/final_v1/points.csv');dd=read(E183/'analysis/final_v1/same_L_deltas.csv')
    ww=read(E184/'analysis/within_dataset_spearman.csv');cross=read(E184/'analysis/cross_dataset_associations.csv')
    assert len(ss)==7 and sum(n(s,'n') for s in ss)==56000
    order=[s['dataset'] for s in ss];labels=[s['label'] for s in ss];y=np.arange(7);metrics=[];comparisons=[]
    for s in ss:
        ds=s['dataset'];rt=s['router'];gt='GT10-soft-t1' if rt=='soft' else 'GT10-hard';res=rt+'-JOINT32'
        pairs={}
        for k in [1,100]:
            for m in [gt,res]:
                r=next(r for r in dd if r['dataset']==ds and r['method']==m and n(r,'K')==k and n(r,'L')==200)
                pairs[k,m]=r;comparisons.append(r)
        g1,r1,g100,r100=pairs[1,gt],pairs[1,res],pairs[100,gt],pairs[100,res]
        q=n(s,'n');assert n(r1,'reference_missing_members')==n(s,'GT_K1_failed')
        assert n(r100,'reference_missing_members')==n(s,'K100_missing_members')
        assert n(r100,'net_improved_queries')==n(s,'K100_improved_queries')
        assert n(r100,'rescued_members')==n(s,'K100_rescued_members')
        assert n(r100,'failed_queries_become_full_success')==n(s,'K100_full_repairs')
        assert n(g100,'n')==q and q-n(g100,'actual_full_success_queries')==n(s,'GT_K100_incomplete')
        b1=n(r1,'reference_missing_members')-n(r1,'rescued_members')+n(r1,'damaged_members')
        assert b1==q-n(r1,'actual_full_success_queries')
        gp=next(p for p in pp if p['dataset']==ds and p['method']==gt and n(p,'K')==100 and n(p,'L')==200)
        rp=next(p for p in pp if p['dataset']==ds and p['method']==res and n(p,'K')==100 and n(p,'L')==200)
        row={'dataset':ds,'label':s['label'],'router':rt,'n':q,'GT10_method':gt,'B32_method':res,
            'NSG_K1_failure_pct':percent(n(g1,'reference_missing_members'),q),
            'GT_K1_failure_pct':percent(n(r1,'reference_missing_members'),q),'B32_K1_failure_pct':percent(b1,q),
            'NSG_K100_incomplete_pct':percent(n(g100,'reference_incomplete_queries'),q),
            'GT_K100_incomplete_pct':f(s,'GT_K100_incomplete_pct'),
            'B32_K100_incomplete_pct':percent(q-n(r100,'actual_full_success_queries'),q),
            'GT10_K1_rescued':n(g1,'rescued_members'),'GT10_K1_reference_failed':n(g1,'reference_missing_members'),
            'GT10_K1_damage':n(g1,'damaged_members'),'GT10_K1_rescue_pct':100*f(g1,'rescue_rate_on_missing'),
            'B32_K1_rescued':n(r1,'rescued_members'),'B32_K1_reference_failed':n(r1,'reference_missing_members'),
            'B32_K1_rescue_pct':f(s,'K1_rescue_of_failed_pct'),
            'K100_incomplete':n(s,'GT_K100_incomplete'),'K100_improved':n(s,'K100_improved_queries'),
            'K100_full_repairs':n(s,'K100_full_repairs'),'K100_improved_pct':f(s,'K100_improved_incomplete_pct'),
            'K100_full_repair_pct':f(s,'K100_full_repairs_of_incomplete_pct'),
            'K100_member_repair_pct':f(s,'K100_member_repair_pct'),'K100_missing_members':n(s,'K100_missing_members'),
            'K100_rescued_members':n(s,'K100_rescued_members'),'K100_missing_per_query':n(s,'K100_missing_members')/q,
            'K100_rescued_per_query':n(s,'K100_rescued_members')/q,'recall_gain_pp':f(s,'K100_net_recall_pp'),
            'qps_delta_pct':f(s,'K100_QPS_delta_pct'),'GT_recall_pct':f(gp,'recall_pct'),'B32_recall_pct':f(rp,'recall_pct'),
            'GT_qps':f(gp,'qps'),'B32_qps':f(rp,'qps'),'training_residual_repeat_factor':f(s,'train_residual_repeat_factor')}
        assert abs(row['GT_qps'] and 100*(row['B32_qps']/row['GT_qps']-1)-row['qps_delta_pct'])<1e-9
        assert abs(row['K100_missing_per_query']*row['K100_member_repair_pct']/100-row['recall_gain_pp'])<1e-9
        metrics.append(row)
    writecsv(HERE/'chart_data.csv',metrics);writecsv(HERE/'L200_source_comparisons.csv',comparisons)
    curves=[p for p in pp if p['dataset'] in order and n(p,'K')==100 and p['method'] in
            [next(m['GT10_method'] for m in metrics if m['dataset']==p['dataset']),
             next(m['B32_method'] for m in metrics if m['dataset']==p['dataset']),'NSG']]
    assert len(curves)==147
    writecsv(HERE/'K100_measured_curves.csv',curves)
    checks=[]
    with PdfPages(PDF,metadata={'Title':'ACSG 失败率、救回率与残差作用','Author':'ACSG research',
        'Subject':'E183 measured results and E184 diagnostics, seven datasets; presentation only'}) as pdf:
        # 1. Net failure rates across the three actual methods.
        fig=page(1,'失败率：三种方法分别留下多少失败',
            '七集共56,000条已有查询；统一L200。Deep / SIFT / WebVid用soft，其余hard；残差固定同家族B32。')
        legend(fig,[('NSG',C['nsg']),('GT10',C['gt']),('GT10＋残差',C['res'])],y=.842)
        for idx,(key,title,xlim,ticks) in enumerate([
            ('K1_failure_pct','K1：第一名没有找对',27,[0,5,10,15,20,25]),
            ('K100_incomplete_pct','K100：100个成员尚未找齐',108,[0,20,40,60,80,100])]):
            ax=axis(fig,[.115+.485*idx,.255,.345,.485],title)
            for j,(prefix,color) in enumerate([('NSG',C['nsg']),('GT',C['gt']),('B32',C['res'])]):
                vals=[m[prefix+'_'+key] for m in metrics]
                ax.barh(y+(j-1)*.23,vals,height=.19,color=color,zorder=3)
                for yi,val in zip(y+(j-1)*.23,vals):
                    ax.text(val+xlim*.012,yi,f'{val:.2f}%',va='center',fontsize=8.5,color=color if prefix!='NSG' else C['muted'])
            horiz(ax,labels);ax.set_xlim(0,xlim);ax.set_xticks(ticks);ax.xaxis.set_major_formatter(ticker.PercentFormatter(100,decimals=0))
            ax.set_xlabel('失败查询数 / 全部测试查询')
        para(fig,.055,.183,'K100只差1个成员也计为“未找齐”，因此它的查询失败率可很高；这不等于平均Recall很低。',size=11)
        note(fig,'固定L200只展示这一工作点。GT10改入口可能救回旧失败，也可能新增失败；第5页保留全部K100预算曲线。',y=.132)
        save(fig,pdf,1,checks)

        # 2. The denominators of rescue rates, including complete-query recovery.
        fig=page(2,'救回率：先看分母，再看修复到什么程度',
            'A的基线是NSG；B/C/D的基线是GT10。K1救回一条就是命中GT1；K100改善一条，不代表100/100。')
        panels=[(.115,.535,'A  GT10的K1救回率','GT10_K1_rescue_pct',C['gt'],62),
                (.605,.535,'B  残差的K1救回率','B32_K1_rescue_pct',C['res'],94),
                (.115,.205,'C  残差的K100查询修复','K100_improved_pct',C['res_light'],132),
                (.605,.205,'D  残差的K100成员修复','K100_member_repair_pct',C['res'],59)]
        for x,bottom,title,key,color,limit in panels:
            ax=axis(fig,[x,bottom,.345,.225],title);vals=[m[key] for m in metrics]
            ax.barh(y,vals,.62,color=color,zorder=3)
            if key=='K100_improved_pct':
                ax.barh(y,[m['K100_full_repair_pct'] for m in metrics],.62,color=C['res_dark'],zorder=4)
            for i,(val,m) in enumerate(zip(vals,metrics)):
                if key=='GT10_K1_rescue_pct':text=f"{val:.2f}%  {m['GT10_K1_rescued']}/{m['GT10_K1_reference_failed']}"
                elif key=='B32_K1_rescue_pct':text=f"{val:.2f}%  {m['B32_K1_rescued']}/{m['B32_K1_reference_failed']}"
                elif key=='K100_improved_pct':text=f"改{val:.2f}% / 全{m['K100_full_repair_pct']:.2f}%"
                else:text=f"{val:.3f}%  {m['K100_rescued_members']}/{m['K100_missing_members']}"
                ax.text(val+limit*.012,i,text,va='center',fontsize=8.1)
            horiz(ax,labels);ax.set_xlim(0,limit)
            if key=='GT10_K1_rescue_pct':xl='救回查询 / 原NSG失败查询';ticks=[0,10,20,30,40]
            elif key=='B32_K1_rescue_pct':xl='救回查询 / 原GT10失败查询';ticks=[0,20,40,60]
            elif key=='K100_improved_pct':xl='原GT10未满100查询中：浅色改善，深色找齐100';ticks=[0,25,50,75,100]
            else:xl='补回GT成员 / 原GT10遗漏GT成员';ticks=[0,10,20,30,40]
            ax.set_xticks(ticks);ax.xaxis.set_major_formatter(ticker.PercentFormatter(100,decimals=0));ax.set_xlabel(xl,fontsize=8.7)
        note(fig,'GT10的K1新增失败（按图中数据集顺序）：5 / 0 / 1 / 155 / 134 / 10 / 1条；残差在本L200两K损伤均为0。',y=.12)
        save(fig,pdf,2,checks)

        # 3. Mechanism and coverage loss partition.
        fig=page(3,'残差的作用：补最终结果，机会逐层受限',
            '残差是GT_K减去主搜索返回的遗漏目标。在线只查冻结表、对新增候选评分并合并；主图遍历保持原样。')
        flow=fig.add_axes([.055,.665,.89,.16]);flow.set_axis_off()
        boxes=[(.00,.50,.19,.42,'GT10路由\n三个真实hub',C['gt']),(.255,.50,.22,.42,'原NSG主搜索\n返回R',C['gt']),
               (.255,.00,.22,.39,'冻结残差表\n每hub最多32槽',C['gold']),(.58,.29,.23,.52,'去重＋原metric评分\n与R合并Top-K',C['res']),
               (.87,.29,.12,.52,'最终返回\nR′',C['res_dark'])]
        for x0,y0,w,h,s,col in boxes:
            box=FancyBboxPatch((x0,y0),w,h,boxstyle='round,pad=.008,rounding_size=.025',fc=col,ec='none',transform=flow.transAxes)
            flow.add_patch(box);flow.text(x0+w/2,y0+h/2,s,ha='center',va='center',fontsize=10.5,color='white' if col!=C['gold'] else C['ink'])
        for a,b in [((.195,.71),(.25,.71)),((.195,.57),(.25,.22)),((.48,.71),(.575,.62)),((.48,.20),(.575,.44)),((.815,.55),(.865,.55))]:
            flow.add_patch(FancyArrowPatch(a,b,transform=flow.transAxes,arrowstyle='-|>',mutation_scale=13,color=C['muted'],lw=1.3))
        ax=axis(fig,[.14,.28,.72,.325],'K100 / L200：原遗漏成员最后落在哪里')
        left=np.zeros(7)
        for field,label,color in [('unseen_source','训练残差源外',C['nsg']),('route_lost','源内、当前路由未覆盖','#7ca8c5'),
                                  ('capacity_lost','路由内、B32未保留',C['gold']),('rescued','实际补回',C['res'])]:
            vals=np.array([100*n(c,field)/n(c,'missing') for c in cc]);ax.barh(y,vals,left=left,height=.66,color=color,label=label,zorder=3);left+=vals
        assert np.allclose(left,100)
        for i,m in enumerate(metrics):ax.text(101.2,i,f"救回 {m['K100_member_repair_pct']:.3f}%",va='center',fontsize=9,color=C['res_dark'])
        horiz(ax,labels);ax.set_xlim(0,113);ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('分母：GT10原遗漏的全部GT成员事件')
        ax.legend(frameon=False,ncol=4,loc='upper left',bbox_to_anchor=(-.015,-.23),fontsize=8.7,columnspacing=1.3)
        para(fig,.055,.165,'Deep/SIFT：超过99%的遗漏在固定训练残差源外。GIST：10886个遗漏 → 源内4242 → 路由内1117 → 补回66。',size=10.7)
        note(fig,'B32三路由去重前最多96个候选，不是96个正确答案。主L200候选覆盖的遗漏均进入结果；其他L的边界损伤保留。',y=.115)
        save(fig,pdf,3,checks)

        # 4. Same-L gain and complete-wall cost with actual numbers.
        fig=page(4,'收益与费用：补回多少，完整查询慢多少',
            '统一K100 / L200；以下Recall和QPS均为E183实际测量。pp是百分点；两边横轴不同，按标注读数。')
        ax=axis(fig,[.14,.50,.31,.26],'残差带来的净Recall增量')
        vals=[m['recall_gain_pp'] for m in metrics]
        ax.scatter(vals,y,c=C['res'],s=54,zorder=4)
        for yi,val in zip(y,vals):ax.text(val*1.14,yi,f'+{val:.4f} pp',va='center',fontsize=9)
        horiz(ax,labels);ax.set_xscale('log');ax.set_xlim(.001,7);ax.set_xticks([.001,.01,.1,1]);ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v,pos:f'{v:g}'));ax.set_xlabel('净Recall增量（pp；横轴为对数尺度）',fontsize=9)
        ax=axis(fig,[.625,.50,.27,.26],'对应完整QPS变化')
        vals=[m['qps_delta_pct'] for m in metrics];ax.barh(y,vals,.59,color=C['red'],zorder=3)
        for yi,val in zip(y,vals):ax.text(val-.12,yi,f'{val:.2f}%',ha='right',va='center',fontsize=9)
        horiz(ax,labels);ax.set_xlim(-8.4,.2);ax.set_xticks([-8,-6,-4,-2,0]);ax.xaxis.set_major_formatter(ticker.PercentFormatter(100,decimals=0));ax.set_xlabel('相对自身GT10；完整单线程wall',fontsize=9)
        tax=fig.add_axes([.07,.175,.86,.235]);tax.set_axis_off()
        headers=['数据集','GT10 Recall / QPS','GT10＋残差 Recall / QPS','补回成员 / 原遗漏']
        cells=[[m['label'],f"{m['GT_recall_pct']:.4f}% / {m['GT_qps']:.2f}",f"{m['B32_recall_pct']:.4f}% / {m['B32_qps']:.2f}",
                f"{m['K100_rescued_members']} / {m['K100_missing_members']}"] for m in metrics]
        table=tax.table(cellText=cells,colLabels=headers,cellLoc='center',colLoc='center',loc='center',colWidths=[.15,.29,.34,.22])
        table.auto_set_font_size(False);table.set_fontsize(9.1);table.scale(1,1.2)
        for (r,c),cell in table.get_celld().items():
            cell.set_edgecolor('white');cell.set_facecolor(C['gt'] if r==0 else ('#f0f5f8' if r%2 else 'white'))
            if r==0:cell.get_text().set_color('white')
        note(fig,'同L付出额外补算费用；是否划算还要看完整曲线。Web/COCO既有同Recall折线受益，不能由同L变慢直接否定。',y=.12)
        save(fig,pdf,4,checks)

        # 5. Full measured K100 curves; no new interpolation or envelope fitting.
        fig=page(5,'完整K100曲线：同L费用与同Recall取舍一起看',
            '每点是既有真实L；依原L顺序连线，竖线为三轮QPS最小–最大。线段不代表额外测量，不外推未测L。')
        legend(fig,[('NSG',C['nsg']),('GT10',C['gt']),('GT10＋残差',C['res'])],y=.847)
        for i,m in enumerate(metrics):
            col=i%4;row=i//4
            ax=fig.add_axes([.07+col*.232,.505-row*.335,.19,.25]);ax.grid(color=C['grid'],lw=.6)
            for method,color in [('NSG',C['nsg']),(m['GT10_method'],C['gt']),(m['B32_method'],C['res'])]:
                rs=sorted([r for r in curves if r['dataset']==m['dataset'] and r['method']==method],key=lambda r:n(r,'L'))
                assert len(rs)==7
                x=np.array([f(r,'recall_pct') for r in rs]);z=np.array([f(r,'qps') for r in rs])
                err=np.array([[f(r,'qps')-f(r,'qps_min') for r in rs],[f(r,'qps_max')-f(r,'qps') for r in rs]])
                ax.errorbar(x,z,yerr=err,color=color,lw=1.3,marker='o',ms=2.6,capsize=1,elinewidth=.6)
            ax.set_title(m['label'],fontsize=11.5,weight='bold',loc='left');ax.set_yscale('log')
            ax.yaxis.set_major_locator(ticker.LogLocator(base=10,subs=(1,2,5),numticks=5));ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v,pos:f'{v:g}'))
            ax.yaxis.set_minor_locator(ticker.NullLocator());ax.xaxis.set_major_locator(ticker.MaxNLocator(3));ax.tick_params(labelsize=7.8,length=2)
            ax.set_xlabel('Recall@100（%）',fontsize=8.3);ax.set_ylabel('完整QPS',fontsize=8.3)
        box=fig.add_axes([.77,.17,.175,.25]);box.set_axis_off()
        box.text(0,.94,'如何看这一页',fontsize=12,weight='bold',va='top')
        box.text(0,.72,'Web / COCO：\n补全曲线在共同区间受益。\n\nFlickr / GIST：有交叉。\nDeep / SIFT / Yandex：\nK100补全曲线较低。',fontsize=10,linespacing=1.55,va='top')
        note(fig,'各面板横纵范围独立，只比较同数据集的三条线。跨库规模、metric或不同内核的绝对QPS不拼接；默认仍保留GT10。',y=.12)
        save(fig,pdf,5,checks)

        # 6. Relationship with target recurrence and geometry, with explicit observational limits.
        fig=page(6,'为什么差异这么大：几何难度与可复用遗漏',
            '来自E184的离线诊断。空间结构影响主搜难度；静态表能否补回，还取决于遗漏目标是否重现及其路由集中程度。')
        ax=axis(fig,[.115,.36,.35,.405],'七集描述：训练残差重复程度与修复率')
        x=np.array([m['training_residual_repeat_factor'] for m in metrics]);v=np.array([m['K100_member_repair_pct'] for m in metrics])
        ax.scatter(x,v,c=C['res'],s=48,zorder=4)
        offsets=[(6,-13),(6,6),(6,5),(6,-12),(-2,8),(7,4),(-64,7)]
        for xx,yy,label,offset in zip(x,v,labels,offsets):ax.annotate(label,(xx,yy),xytext=offset,textcoords='offset points',fontsize=9.5)
        ax.set_yscale('log');ax.set_xlim(.88,3.85);ax.set_ylim(.035,65);ax.set_yticks([.1,1,10,50]);ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda z,pos:f'{z:g}%'))
        ax.set_xlabel('训练遗漏token数 / 不同目标ID数',fontsize=9.5);ax.set_ylabel('K100遗漏成员修复率（对数尺度）',fontsize=9.5)
        rr=next(r for r in cross if r['feature']=='train_residual_repeat_factor')
        ax.text(.05,.94,f"Spearman ρ = {float(rr['spearman']):.3f}\n仅7个异质数据集；不是因果证明",transform=ax.transAxes,va='top',fontsize=10,color=C['muted'])
        ax=axis(fig,[.625,.36,.29,.405],'同一数据集内：几何分离度的关联')
        for key,col,dy in [('K100_missing_count',C['gt'],-.12),('K100_net_improved',C['gold'],.12)]:
            vals=[float(next(r['spearman'] for r in ww if r['dataset']==ds and r['feature']=='background_separation_z' and r['outcome']==key)) for ds in order]
            ax.scatter(vals,y+dy,c=col,s=38,zorder=4)
        horiz(ax,labels);ax.axvline(0,color=C['muted'],lw=.9);ax.set_xlim(-.8,.18);ax.set_xticks([-.8,-.6,-.4,-.2,0]);ax.set_xlabel('Spearman ρ；z越大表示背景分离更明显',fontsize=9)
        ax.legend(handles=[plt.Line2D([],[],marker='o',ls='',color=C['gt'],label='与GT10遗漏数'),plt.Line2D([],[],marker='o',ls='',color=C['gold'],label='与残差是否改善')],
            loc='upper left',bbox_to_anchor=(-.12,-.15),frameon=False,fontsize=9,ncol=2,columnspacing=1.)
        para(fig,.055,.245,'几何不能被排除：粗略按遗漏量分层后，Web/COCO的高分离组改善概率仍高8.17/11.50pp；该分层仍有混杂。',size=10.7)
        para(fig,.055,.182,'证据边界：单图/单模型、已曝光查询；GIST仅1K。几何含GT信息，不能当免费线上特征；本报告没有新实验或默认替换。',size=10.2,color=C['muted'])
        note(fig,'来源：E183 points.csv / same_L_deltas.csv；E184 dataset_summary.csv / coverage_chain.csv / within_dataset_spearman.csv。',y=.12)
        save(fig,pdf,6,checks)
    for path,v in INPUTS.items():assert Path(path).stat().st_size==v['bytes'] and sha(path)==v['sha256'],path
    dump(HERE/'inputs_manifest.json',INPUTS)
    dump(HERE/'build_checks.json',{'status':'PASS_NUMERIC_SOURCE_BINDINGS_AND_FIGURE_LAYOUT','source_datasets':7,'source_queries':56000,
        'selected_L200_comparisons':len(comparisons),'selected_K100_curve_points':len(curves),'pages':checks,
        'new_ANN_calls':0,'new_GT':0,'new_training':0,'new_timing':0,'default_changed':False,
        'pdf':PDF.name,'pdf_bytes':PDF.stat().st_size,'pdf_sha256':sha(PDF),'build_seconds':time.time()-t,
        'builder_sha256':sha(__file__),'font':str(FONT),'font_sha256':sha(FONT),
        'superseded_draft_pdf_sha256':old_draft_sha,'draft_revision':'page 6 legend separated from interpretation text; numeric source unchanged',
        'actual_PDF_visual_review':'PENDING_RENDER_AND_VIEW'})
    print(json.dumps({'pdf':str(PDF),'bytes':PDF.stat().st_size,'pages':6,'build_seconds':time.time()-t},ensure_ascii=False))

if __name__=='__main__':main()
