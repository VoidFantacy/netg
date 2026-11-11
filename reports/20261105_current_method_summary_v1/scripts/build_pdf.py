from pathlib import Path
import json, hashlib, unicodedata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages

W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
for name in ['Regular','Bold']:
    font_manager.fontManager.addfont(str(E/f'storage/fonts/NotoSansSC-{name}.ttf'))
family=font_manager.FontProperties(fname=str(E/'storage/fonts/NotoSansSC-Regular.ttf')).get_name()
plt.rcParams.update({'font.family':family,'font.size':10,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False})
NAVY,BLUE,GREEN,GRAY='#203B50','#2C6B9E','#147D69','#607380'
PDF=R/'ACSG_当前方法总结_GT10与直接残差补点_20261105.pdf'
artists=[];titles=[];figures=[]
def wrap(s,width):
    out=[];line='';n=0
    for ch in s:
        if ch=='\n':out.append(line);line='';n=0;continue
        w=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if n+w>width:out.append(line);line='';n=0
        line+=ch;n+=w
    if line:out.append(line)
    return '\n'.join(out)
def txt(fig,x,y,s,size=11,color=NAVY,bold=False,width=None):
    a=fig.text(x,y,wrap(s,width) if width else s,va='top',fontsize=size,color=color,weight='bold' if bold else 'normal',linespacing=1.55)
    artists.append(a);return a
def new(title,subtitle):
    titles.append(title);fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    txt(fig,.055,.953,title,22,bold=True)
    txt(fig,.055,.891,subtitle,10,color=GRAY)
    txt(fig,.055,.028,'ACSG · 当前方法说明 · 2026-11-05 · 依据已实现流程整理',8,color=GRAY)
    txt(fig,.928,.028,f'{len(titles):02}',8,color=GRAY)
    return fig,ax
def box(ax,x,y,w,h,label,color=BLUE,fill='#EFF5FA',size=11):
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.012',lw=1.1,edgecolor=color,facecolor=fill)
    ax.add_patch(p)
    t=ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=size,color=color,linespacing=1.6)
    artists.append(t);return p
def arrow(ax,x1,y1,x2,y2,color=GRAY,dashed=False):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=13,lw=1.4,color=color,linestyle='--' if dashed else '-'))
def table(fig,headers,rows,rect,widths=None,size=11):
    ax=fig.add_axes(rect);ax.axis('off')
    t=ax.table(cellText=rows,colLabels=headers,cellLoc='center',bbox=[0,0,1,1],colWidths=widths)
    t.auto_set_font_size(False);t.set_fontsize(size)
    for (i,j),cell in t.get_celld().items():
        cell.set_edgecolor('#D7E3E9');cell.set_linewidth(.7);cell.PAD=.045
        if i==0:cell.set_facecolor(NAVY);cell.get_text().set_color('white');cell.get_text().set_weight('bold')
        else:cell.set_facecolor('#F1F7F5' if i%2==0 else 'white')
    return t
def save(pdf,fig,name):
    fig.canvas.draw();w,h=fig.canvas.get_width_height()
    for a in artists:
        if a.figure is fig:
            b=a.get_window_extent(fig.canvas.get_renderer());assert b.x0>=0 and b.y0>=0 and b.x1<=w+1 and b.y1<=h+1,(name,a.get_text(),b)
            if hasattr(a,'_max_right'):assert b.x1<=w*a._max_right,(name,'column overflow',a.get_text())
    pdf.savefig(fig);fig.savefig(R/f'figures/{name}.png',dpi=180);fig.savefig(R/f'figures/{name}.svg')
    figures.append(name);plt.close(fig)

with PdfPages(PDF,metadata={'Title':'ACSG 当前方法总结：GT10与直接残差补点','Author':'ACSG research','Subject':'Method-only summary of implemented GT10 baseline and B32 direct completion'}) as pdf:
    fig,ax=new('当前方法：GT10基线＋B32直接残差补点',
        'GT10负责选择图搜索入口；直接残差补点在主搜索完成后补充候选，并合并最终答案。')
    positions=[.06,.29,.52,.75]
    for x,label,c,fill in zip(positions,['GT10画像路由\n三个真实入口ID','原图搜索\n主返回 R_K','直接残差补点\n候选 C(q)','按原任务度量\n合并最终Top-K'],[BLUE,BLUE,GREEN,GREEN],['#EFF5FA','#EFF5FA','#EEF7F3','#EEF7F3']):
        box(ax,x,.60,.17,.115,label,c,fill)
    for x in [.23,.46,.69]:arrow(ax,x+.007,.6575,x+.052,.6575)
    box(ax,.52,.78,.17,.06,'离线残差表 T',GREEN,'#EEF7F3',11)
    arrow(ax,.605,.775,.605,.721,GREEN)
    txt(fig,.06,.769,'在线输入：查询向量 q',12,bold=True)
    txt(fig,.06,.535,'同一次GT10路由产生的三个入口ID，也用于读取对应的三行残差表。',11)
    txt(fig,.06,.487,'默认主链仍为GT10；直接补点是保留的残差研究方案，按配置附加启用。',11,bold=True)
    txt(fig,.06,.410,'GT10在这里提供什么',13,color=BLUE,bold=True)
    left_text=txt(fig,.06,.365,'画像小图检索得到路由结果，再映射到真实数据ID，由原NSG图搜索返回Top-K。画像用于路由，真实ID用作主图入口。',10.5,width=60)
    left_text._max_right=.49
    txt(fig,.53,.410,'直接补点增加什么',13,color=GREEN,bold=True)
    right_text=txt(fig,.53,.365,'根据路由读取离线候选表，计算候选与查询的真实相似度或距离，将候选作为答案参与Top-K合并。',10.5,width=60)
    right_text._max_right=.94
    table(fig,['标记','含义','与线上候选数的关系'],[
        ['16K表 / 8K表','用16,000 / 8,000条训练查询造表','表示监督查询数量'],
        ['B32','每个路由行最多保留32个真实ID','三个路由行去重前最多96个'],
        ['K=1 / K=100','最终返回1个 / 100个答案','与GT10名字中的“10”独立']
    ],[.06,.105,.86,.17],[.19,.45,.36],10.5)
    txt(fig,.06,.070,'图中的“直接补点（16K表）”对应完整B32表；8K表采用相同补点流程，造表监督来源不同。',9.5)
    save(pdf,fig,'01_method_overview')

    fig,ax=new('离线：把训练查询的遗漏编成B32表',
        '残差指主搜索没有返回的真实近邻ID；每个“训练查询—遗漏目标”构成一个单位覆盖事件。')
    labels=['合法训练查询\n及其真实GT100','运行GT10\nK100 / L200','逐查询比较\n记录遗漏ID','按路由覆盖挑选\n每行最多32个ID']
    for x,label in zip(positions,labels):box(ax,x,.705,.17,.105,label,GREEN,'#EEF7F3',10.8)
    for x in [.23,.46,.69]:arrow(ax,x+.007,.7575,x+.052,.7575,GREEN)
    txt(fig,.06,.642,'先确定每条训练查询的遗漏集合：',11,bold=True)
    txt(fig,.12,.596,r'$M_i = G_{100}(q_i)\;\setminus\;R_{100}^{L=200}(q_i)$',17,color=GREEN)
    txt(fig,.06,.505,'① 将遗漏关联到该查询实际命中的三个路由行',12,bold=True)
    txt(fig,.06,.461,'例如查询 q_i 漏掉目标 x，且路由到 h1、h2、h3，则在这三行中放入 x 都可能覆盖同一个遗漏事件。',11,width=137)
    txt(fig,.06,.365,'② 优先选择新增覆盖最多的“路由行—目标ID”',12,bold=True)
    txt(fig,.06,.321,'实现采用全局覆盖贪心，按8→16→32逐级扩容并保留已有前缀。每步计算尚未覆盖的遗漏事件数；同一事件被多行命中只计一次。',11,width=137)
    txt(fig,.06,.220,'③ 冻结路由ID到候选ID列表的查找表',12,bold=True)
    txt(fig,.06,.176,'线上读取的是已选好的真实数据ID。K1与K100共用这张以K100/L200遗漏生成的表；8K表沿用相同选表机制。',11,width=137)
    txt(fig,.06,.092,'GT用于离线生成遗漏监督；线上补点不读取GT。造表实现：E183 residual_tools.cpp 的 teacher / compile_tables / extend。',9.2,width=153)
    save(pdf,fig,'02_offline_table')

    fig,ax=new('在线：查三行表，精确打分，合并答案',
        '全部剩余候选使用原向量、原任务metric评分。这里的精确评分不含额外的学习排序器。')
    txt(fig,.06,.812,'一次查询的实际处理顺序',13,bold=True)
    steps=[('1','得到GT10的主返回 R_K，并复用该查询的三个路由入口。'),
           ('2','读取三个入口对应的B32表，合并最多96个候选ID。'),
           ('3','去除重复ID，以及已经出现在主返回中的ID，得到 C(q)。'),
           ('4','对全部 C(q) 计算原向量相似度或距离。'),
           ('5','将主返回和补点候选按原metric合并，输出最终Top-K。')]
    for i,(n,s) in enumerate(steps):
        y=.748-i*.112
        box(ax,.06,y-.032,.035,.042,n,GREEN,'#EEF7F3',11)
        txt(fig,.11,y,s,11,width=72)
    txt(fig,.57,.812,'K1示例（人为示意数值）',13,bold=True)
    table(fig,['路由行','候选ID列表'],[['h1','a, c'],['h2','c, d'],['h3','b, d']], [.57,.585,.35,.18],[.3,.7],11)
    txt(fig,.57,.550,'主返回：{a}；查表并去重后：{a,b,c,d}',10.5)
    txt(fig,.57,.510,'排除已有 a，补算候选：{b,c,d}',10.5,color=GREEN,bold=True)
    table(fig,['ID','IP相似度','来源'],[['a','0.80','主返回'],['b','0.76','补点'],['c','0.91','补点'],['d','0.83','补点']], [.57,.245,.35,.215],[.2,.4,.4],10.5)
    txt(fig,.57,.209,'相似度越大越好，最终K1返回 c。',11,color=GREEN,bold=True)
    txt(fig,.06,.168,'合并规则与返回数量',12,bold=True)
    txt(fig,.06,.122,'K1保留最优1个，K100保留最优100个。同分遵循现有到达次序与严格替换规则；IP保持原内积，L2保持原平方欧氏距离。',10.5,width=143)
    txt(fig,.06,.066,'实现：E194 benchmark.cpp 的 fast_plan / fast_apply。图中示例只解释操作，不是新增测试或性能结果。',9.2)
    save(pdf,fig,'03_online_completion')

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='BUILT_PENDING_ACTUAL_PDF_RENDER_AND_VISUAL_REVIEW',pdf=PDF.name,pdf_sha256=sha(PDF),pages=len(titles),titles=titles,figures=figures,scope='Current method only: GT10 interface and B32 direct completion; no two-tower branch, problem analysis, new experiment or default change')
(R/'reviews/pdf_build.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('Built',len(titles),'pages:',PDF)
