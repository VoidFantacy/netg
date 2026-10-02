"""Presentation of frozen E94 tables. No native search, model fitting or reselection."""
from pathlib import Path
import base64, csv, hashlib, html, json, math, statistics, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

O = Path(__file__).resolve().parents[1]
C = O.parent
F = C / 'stage35_final_comparison_v1'
DS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
LS = [64, 128, 256, 400, 800]
LABELS = dict(nsg='原 NSG', fast30k='Fast（GT1 / 30K）', gt10_hard='GT10-hard',
              baseline_soft='GT10-soft（当前 P）', composed10='组合修复（新）', compact10='compact')
COLORS = dict(nsg='#536172', fast30k='#8a969f', gt10_hard='#3276c3', baseline_soft='#087c80',
              composed10='#d76724', compact10='#9761b3')
ORDER = list(LABELS)
font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': font.get_name(), 'font.size': 10, 'axes.unicode_minus': False,
                     'axes.spines.top': False, 'axes.spines.right': False, 'savefig.facecolor':'white'})

def readcsv(p):
    with p.open() as f: return list(csv.DictReader(f))

def identity(p):
    return dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())

inputs = [F/'analysis_v1'/x for x in ['points.csv','paired.csv','timings.csv','cost.json','verification.json']]
inputs += [F/'supplement_v1'/x for x in ['failed_queries_all_L.csv','failure_cases_both_directions.csv','verification.json']]
inputs += [F/'selection.json', F/'protocol.md', F/'report.md', F/'reviews/final_input_access.json',
           F/'reviews/preselection_freeze.json', F/'reviews/prequery_freeze.json',
           C/'session12_report_v1/member_failure_balance.csv', O/'protocol.md', Path(__file__)]
seal = O/'input_freeze.json'
assert not seal.exists(), 'New presentation needs a new output version'
seal.write_text(json.dumps(dict(created_at=time.time(), scope='Existing final tables and reports only',
                                 files=[identity(p) for p in inputs]),ensure_ascii=False,indent=2)+'\n')
t0 = time.perf_counter()
points, pairs, timings = [readcsv(F/'analysis_v1'/x) for x in ['points.csv','paired.csv','timings.csv']]
cases = readcsv(F/'supplement_v1/failure_cases_both_directions.csv')
failures = readcsv(F/'supplement_v1/failed_queries_all_L.csv')
assert len(points)==50 and len(timings)==250 and len(failures)==10730 and len(cases)==8
lookup = {(p['dataset'],p['model'],int(p['L'])):p for p in points}
for key,p in lookup.items():
    ts = [r for r in timings if (r['dataset'],r['model'],int(r['L']))==key]
    assert len(ts)==5 and {int(r['repeat']) for r in ts}==set(range(5))
    qps = [2000/float(r['seconds']) for r in ts]
    for a,b in [(statistics.median(qps),p['QPS']),(min(qps),p['QPS_min']),(max(qps),p['QPS_max'])]:
        assert math.isclose(a,float(b),rel_tol=1e-12)
    assert math.isclose(int(p['failure_count'])/20,float(p['failure_rate_pct']),abs_tol=1e-12)
    assert int(p['queries'])==2000
for r in pairs:
    a=lookup[r['dataset'],r['candidate'],int(r['L'])]; b=lookup[r['dataset'],r['reference'],int(r['L'])]
    assert math.isclose(float(a['recall_pct'])-float(b['recall_pct']),float(r['delta_recall_pp']),abs_tol=1e-12)
    assert int(r['new_failures'])-int(r['rescued'])==int(a['failure_count'])-int(b['failure_count'])
    assert int(r['member_gained'])-int(r['member_lost'])==int(r['gain_hits'])-int(r['loss_hits'])==int(r['net_hits'])

def models(ds): return [m for m in ORDER if (ds,m,64) in lookup]
def series(ds,m,k): return [float(lookup[ds,m,L][k]) for L in LS]
def finish(fig,name):
    fig.savefig(O/'figures'/f'{name}.png',dpi=165,bbox_inches='tight')
    fig.savefig(O/'figures'/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)

for field,xlabel,name in [('recall_pct','Recall@10（%）','recall_qps_zh'),('failure_rate_pct','零命中失败率（%）','failure_qps_zh')]:
    fig,axs=plt.subplots(1,2,figsize=(12,4.9))
    for di,(ds,ax) in enumerate(zip(DS,axs)):
        for m in models(ds):
            ys=series(ds,m,'QPS'); lo=series(ds,m,'QPS_min'); hi=series(ds,m,'QPS_max')
            ax.errorbar(series(ds,m,field),ys,yerr=[[y-l for y,l in zip(ys,lo)],[h-y for h,y in zip(hi,ys)]],
                        fmt='o-',markersize=4,linewidth=1.7,color=COLORS[m],capsize=2,label=LABELS[m],alpha=.95)
        ax.set_title(['WebVid · 每方法 2,000 查询','Yandex · 每方法 2,000 查询'][di],fontweight='bold')
        ax.set_xlabel(xlabel);ax.set_ylabel('QPS（查询 / 秒）');ax.grid(alpha=.18)
        if field=='failure_rate_pct': ax.invert_xaxis()
        ax.legend(fontsize=8,loc='best',framealpha=.92)
    fig.suptitle('同批完整在线计时 · CPU15 / 单线程 · 五轮中位数与最小—最大范围',fontsize=12)
    fig.text(.5,.01,'L = 64 / 128 / 256 / 400 / 800；连线仅连接实测点。历史 validation；未据最终反馈调参。',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.94]);finish(fig,name)

fig,axs=plt.subplots(2,3,figsize=(12,7.3))
for di,ds in enumerate(DS):
    for j,(field,ylabel) in enumerate([('recall_pct','Recall@10（%）'),('QPS','QPS（查询 / 秒）'),('failure_count','零命中查询数 / 2,000')]):
        ax=axs[di,j]
        for m in models(ds):
            ax.plot(range(5),series(ds,m,field),'o-',color=COLORS[m],markersize=4,label=LABELS[m])
        ax.set_xticks(range(5),LS);ax.set_xlabel('搜索 L（等距分类轴）');ax.set_ylabel(ylabel);ax.grid(alpha=.18)
        ax.set_title(('WebVid' if di==0 else 'Yandex')+' · '+ylabel.split('（')[0])
axs[0,0].legend(fontsize=7,loc='lower right');axs[1,0].legend(fontsize=7,loc='lower right')
fig.suptitle('全部五档：召回、吞吐与失败分别报告',fontsize=14,fontweight='bold')
fig.text(.5,.01,'QPS 为五轮中位数，范围见前页及完整原点表；不能由同 L 的召回提升推断前沿收益。',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.04,1,.95]);finish(fig,'metrics_by_L_zh')

fig,axs=plt.subplots(1,2,figsize=(12,5.2))
for di,(ds,ax) in enumerate(zip(DS,axs)):
    rows=[];labs=[]
    for c in [x for x in cases if x['dataset']==ds]:
        for side,field in [('P','baseline_hits'),('新','new_hits')]:
            rows.append([int(v) for v in c[field].split()]);labs.append(f"{'救回' if c['kind']=='rescued' else '新增失败'} {c['source_row']} · {side}")
    im=ax.imshow(rows,vmin=0,vmax=10,cmap='YlGnBu',aspect='auto')
    for i,row in enumerate(rows):
        for j,v in enumerate(row): ax.text(j,i,str(v),ha='center',va='center',color='white' if v>=6 else '#112335',fontsize=11)
    ax.set_yticks(range(8),labs);ax.set_xticks(range(5),LS);ax.set_xlabel('L');ax.set_title(('WebVid：组合修复' if di==0 else 'Yandex：compact')+' vs 当前 P')
    for i in [1.5,3.5,5.5]:ax.axhline(i,color='white',linewidth=2)
fig.suptitle('双向失败案例：每格为实际命中的 GT10 成员数',fontsize=14,fontweight='bold')
fig.text(.5,.01,'沿用已冻结案例：L128 每种方向取源行最小的两条。0 才算失败；全 401 条查询在离线浏览器与 CSV 中保留。',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.04,1,.95]);finish(fig,'failure_cases_zh')

# Pack every existing failure-table cell without re-running retrieval or raw scoring.
groups={}
for r in failures:
    key=(r['dataset'],int(r['source_row']))
    g=groups.setdefault(key,dict(dataset=r['dataset'],row=key[1],namespace=r['namespace'],GT10=[int(v) for v in r['GT10'].split()],cells=[]))
    assert g['GT10']==[int(v) for v in r['GT10'].split()] and g['namespace']=='validation'
    g['cells'].append([int(r['L']),r['model'],int(r['hits']),[int(v) for v in r['entries'].split()],[int(v) for v in r['returned'].split()]])
assert len(groups)==401
for (ds,row),g in groups.items():
    assert len(g['cells'])==5*len(models(ds))
    assert {(c[0],c[1]) for c in g['cells']}=={(L,m) for L in LS for m in models(ds)}
payload=dict(labels=LABELS,points=points,queries=list(groups.values()),L=LS)
(O/'presentation_data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')

mainpairs=[r for r in pairs if (r['dataset']==DS[0] and r['candidate']=='composed10' and r['reference'] in ['compact10','baseline_soft']) or (r['dataset']==DS[1] and r['candidate']=='compact10' and r['reference']=='gt10_hard')]
def pairtable_html():
    rows=''
    for ds,can,ref,label in [(DS[0],'composed10','compact10','Web 组合 / compact'),(DS[0],'composed10','baseline_soft','Web 组合 / 当前 P'),(DS[1],'compact10','gt10_hard','Yandex compact / 当前 P')]:
        xs=[next(x for x in mainpairs if x['dataset']==ds and x['candidate']==can and x['reference']==ref and int(x['L'])==L) for L in LS]
        rec=' / '.join(f"{float(x['delta_recall_pp']):+.3f}" for x in xs)
        fail=' / '.join(f"{int(x['new_failures'])-int(x['rescued']):+d}" for x in xs)
        rows+=f'<tr><td>{label}</td><td>{rec}</td><td>{fail}</td></tr>'
    return '<table><thead><tr><th>方法与参照</th><th>Recall 变化（百分点）</th><th>失败净新增（条）</th></tr></thead><tbody>'+rows+'</tbody></table>'

def baseline_table():
    rows=''
    for ds in DS:
        for m in models(ds):
            p=lookup[ds,m,128]
            rows+=f"<tr><td>{'Web' if ds==DS[0] else 'Yandex'}</td><td>{LABELS[m]}</td><td>{float(p['recall_pct']):.3f}</td><td>{float(p['QPS']):.2f} [{float(p['QPS_min']):.2f}, {float(p['QPS_max']):.2f}]</td><td>{p['failure_count']}</td></tr>"
    return '<table><thead><tr><th>数据</th><th>方法</th><th>Recall %</th><th>QPS 中位 [最小, 最大]</th><th>失败 / 2,000</th></tr></thead><tbody>'+rows+'</tbody></table>'

def img(name,alt):
    b64=base64.b64encode((O/'figures'/f'{name}.png').read_bytes()).decode()
    return f'<img class="chart" alt="{alt}" src="data:image/png;base64,{b64}">'

title='ACSG · 9月13日整日研究汇报'
conclusion='尚未找到稳定优于当前 GT10 起点的新方法，默认保持。'
intro='Web 的组合修复改善了 compact 的部分损失，但相对当前 GT10-soft P 五档召回仍落后。Yandex compact 低 L 小幅正向，高 L 出现损伤。局部修复有价值，尚不足以支持更换默认方法。'
method='Web 组合在 compact 的 1,771 个画像槽 / 815 个真实入口上，保留已冻的 254 条查询监督补边，叠加 5 组、10 行父画像恢复。Yandex 最终候选为 2,067 槽 / 821 个真实入口的 compact。在线均为一次 Micro-HNSW 取七画像槽、去重到三个真实入口，再执行原 NSG。底层大图、base、GT 与 raw-IP 固定；新画像与图的学习只发生在线下。'
selection='开发池共 77 项目录记录，41 项具备同源质量评分（39 个非零新配置 + 两集 P），其余为控制、别名或未原生部署候选。Web 无过门新方法，选组合做反证展示，best_all 保留 P；Yandex 两个选型角色均为 compact。选择和规则先冻结，之后才打开 E34 历史 validation2000。best_all 是开发选型角色，不是部署推荐。'
scope='每集 2,000 查询；Web 六方法、Yandex 四方法；五个 L、五轮，共 50 原点 / 250 整批 wall。CPU15、配置与实际进程及数值库均为单线程，方法串行轮换。计时含完整路由、原 NSG、输出，GT、计数、hash、JSON、构建与加载在外。'
limits='P-fit20K 包含旧 train/monitor；aux、cal、audit 已历史使用，动作选择反馈均计训练。最终集本身也有历史暴露，本次最终反馈未回流训练或选择，held-out 未打开。五轮计时不增加独立 query 样本数；跨 L 也不能当成独立样本。'
cost='E94 新增 700,800 次 NSG、560,000 次 HNSW；原生任务总操作 994.213 秒，250 次纯 wall 合计 695.047 秒。8 个源小图文件，40 次 plain + 40 次 count 加载，0 新拟合 / 普通构图 / GT。当天普通实验累计 6,854,176 NSG、17,820,080 HNSW、360 次普通小图构建。旧开发的 220 点 / 1,100 wall 分属四个批次，与本次最终曲线分开。'
unknown='route-only / graph-only 未单测，完整离线训练及 GT 总成本仍有未知项，不能记零；操作耗时也不能换算 QPS。第13会话只做呈现与交付整理，新增训练、ANN、构图、GT、QPS 均为 0。'
failuretext='失败严格为返回 top10 与 GT10 交集为空；命中 1 个不失败。全方法并集有 401 条独立失败查询（Web 271 / Yandex 130），其中 346 条存在方法间状态变化。完整五 L × 各方法共 10,730 单元。原 812 个 query×L 零命中事件表只有 4,230 单元，两个范围不混用。'
interpret='L128：Web 组合对 compact 新找回 66 / 丢失 12 个 GT 成员，救回 4 / 新增失败 0；对 P 新找回 274 / 丢失 351，救回 14 / 新增失败 13。Yandex compact 对 P 新找回 144 / 丢失 130，救回 8 / 新增失败 6。减少零命中不保证总 Recall 提高；GT 成员增损与逐 query 净命中增损分别统计。'
speed='全部五 L 的配对结果均保留。组合 / compact 与 Yandex compact / P 的五轮 QPS 交叉范围都跨零。组合 / P 的 L128 范围略负，其余跨零，不能宣称稳定整体加速。原报告同 Recall 插值仅为描述性结果，本页曲线没有增加插值测量点。'

md=f'''# {title}\n\n**{conclusion}** {intro}\n\n{method}\n\n{selection}\n\n{scope}\n\n'''
md+='| 对照（L64/128/256/400/800） | Recall 变化 pp | 失败净新增 |\n|---|---|---|\n'
for ds,ref,label in [(DS[0],'compact10','Web 组合 / compact'),(DS[0],'baseline_soft','Web 组合 / 当前 P'),(DS[1],'gt10_hard','Yandex compact / 当前 P')]:
    xs=[next(x for x in mainpairs if x['dataset']==ds and x['reference']==ref and int(x['L'])==L) for L in LS]
    md+=f"| {label} | "+' / '.join(f"{float(x['delta_recall_pp']):+.3f}" for x in xs)+' | '+' / '.join(f"{int(x['new_failures'])-int(x['rescued']):+d}" for x in xs)+' |\n'
md+=f'''\n{speed}\n\n![QPS–Recall](figures/recall_qps_zh.png)\n\n![QPS–失败率](figures/failure_qps_zh.png)\n\n![按L三指标](figures/metrics_by_L_zh.png)\n\n{failuretext}\n\n{interpret}\n\n![双向失败案例](figures/failure_cases_zh.png)\n\n{limits}\n\n{cost}\n\n{unknown}\n\n[离线可交互汇报](report.html) · [打印版 PDF](report.pdf) · [50 原点](../stage35_final_comparison_v1/analysis_v1/points.csv) · [250 轮 wall](../stage35_final_comparison_v1/analysis_v1/timings.csv) · [全部配对损益](../stage35_final_comparison_v1/analysis_v1/paired.csv) · [401 失败查询完整五L表](../stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv) · [原始完整报告及验收](../stage35_final_comparison_v1/report.md)。\n\n第13会话交付材料已整理；整日21:00目标的状态由监督会话接续处理，本会话不将其标完成。最终反馈不再用于调参；没有待恢复实验。\n'''
(O/'report.md').write_text(md)

CSS='''*{box-sizing:border-box}body{margin:0;background:#edf1f3;color:#182a39;font:15px/1.65 "Noto Sans CJK SC",sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px}section{background:#fff;border:1px solid #dae1e5;border-radius:14px;padding:26px 30px;margin-bottom:22px}h1{font-size:32px;line-height:1.35;letter-spacing:-.8px;margin:5px 0 18px}h2{font-size:23px;margin:0 0 12px}h3{font-size:16px;margin:18px 0 6px}.eyebrow{color:#49717f;font-size:13px;letter-spacing:2px}.lead{font-size:19px;font-weight:700;color:#9a481e}.muted,.caption{color:#566b78;font-size:13px}.banner{background:#f4f8fa;padding:14px 18px;border-left:4px solid #0c7b80}.chart{width:100%;height:auto;display:block;margin:12px 0}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.45;font-variant-numeric:tabular-nums}th,td{text-align:left;border-bottom:1px solid #dbe3e8;padding:8px 9px}th{background:#f0f5f7;white-space:nowrap}td{vertical-align:top}button,select,input{font:inherit;border:1px solid #abbfc9;border-radius:6px;padding:6px 10px;background:white;color:inherit}button{cursor:pointer}button:hover{background:#edf6f6}label{display:inline-flex;gap:8px;align-items:center;margin:0 16px 10px 0}.controls{margin:12px 0}.bad{background:#fff0e6;color:#863b1b}.good{background:#dff1ec;color:#1b6159}summary{cursor:pointer;font-weight:bold;padding:8px 0}.ids{font-family:monospace;font-size:12px;overflow-wrap:anywhere}a{color:#076f80}footer{text-align:center;color:#526571;font-size:12px;padding:20px}.no-break{break-inside:avoid}@media(max-width:600px){main{padding:12px}section{padding:18px 14px}h1{font-size:26px}h2{font-size:20px}table{min-width:630px}.chart{min-width:0}label{display:flex}input{min-width:0;width:170px}}@page{size:A4;margin:12mm}@media print{body{background:white;font-size:10px;line-height:1.48}main{max-width:none;padding:0}section{border:0;border-radius:0;padding:0;margin:0;break-after:page}section:last-of-type{break-after:auto}h1{font-size:24px;margin:3px 0 10px}h2{font-size:18px}h3{font-size:12px}.lead{font-size:14px}.muted,.caption{font-size:9px}p{margin:7px 0}table{font-size:9px;line-height:1.3}th,td{padding:5px}.chart{max-height:109mm;object-fit:contain;margin:4px 0}.tall{max-height:155mm}.screen-only{display:none!important}.banner{padding:8px 10px}.eyebrow{font-size:10px}footer{display:none}}'''
body=f'''<main><section><div class="eyebrow">2026.09.13 · 冻结最终比较 · 第13串行会话整理</div><h1>{title}</h1><p class="lead">{conclusion}</p><p>{intro}</p><div class="banner">{scope}</div><h3>五档质量变化</h3><p class="caption">以下顺序均为 L = 64 / 128 / 256 / 400 / 800；失败负值表示减少。</p><div class="scroll">{pairtable_html()}</div><p>{speed}</p><h3>L128 便于逐项核对的原值</h3><div class="scroll">{baseline_table()}</div><p class="caption">完整五 L 的 50 原点与全部轮次可在网页下方查看或下载；此表不是只选 L128 得出结论。</p><p class="muted">{limits}</p></section>
<section><h2>同机、同批的 QPS–Recall 与失败曲线</h2>{img('recall_qps_zh','两数据集完整 QPS–Recall 曲线，含五轮最小最大范围')}{img('failure_qps_zh','两数据集 QPS–零命中失败率曲线')}<p class="caption">失败率轴向左递增，右上表示更快且失败更少。所有曲线来自 E94，同方法五个点；没有拼接开发批次。</p></section>
<section><h2>召回、QPS、失败随 L 的变化</h2>{img('metrics_by_L_zh','两数据集按五个L对比召回、QPS和零命中数量').replace('class="chart"','class="chart tall"')}<h3>实际新方法与冻结选择</h3><p>{method}</p><p>{selection}</p><p class="caption">Fast 从 QGT 查询选择真实 hub，再以 GT1 归属聚合 query 画像，在线由画像小图找到三个真实入口。Fast30K 是历史训练量和构图种子的基线，不能把它与 GT10 的全部差异归因于 GT 目标数。</p></section>
<section><h2>失败查询：救回与新增损伤同时保留</h2><p>{failuretext}</p>{img('failure_cases_zh','八个既定案例的基线和新方法在全部五L的实际命中数')}<p>{interpret}</p><h3>实际成本与结论边界</h3><p>{cost}</p><p>{unknown}</p><p class="caption">此汇报复用已封存的数值和案例；不会从最终坏例生成新训练选择。所有旧实验门、失败结果与局部正信号均保留。</p></section>
<section class="screen-only"><h2>全部 401 条失败查询</h2><p>离线数据完整内嵌。选择数据集和源行，可查看全五 L 的命中数；再选择 L 核对 GT10、真实入口和完整返回。</p><div class="controls"><label>数据集 <select id="dataset"><option value="{DS[0]}">WebVid（271 条）</option><option value="{DS[1]}">Yandex（130 条）</option></select></label><label>源行 <select id="query"></select></label><label>查找源行 <input id="row-search" type="number" min="0" placeholder="例如 162"><button id="find">定位</button></label><span id="message" role="status"></span></div><p id="query-title"></p><div class="scroll" id="hit-table"></div><div class="controls"><label>返回详情 L <select id="L">{''.join(f'<option value="{L}"'+(' selected' if L==128 else '')+f'>{L}</option>' for L in LS)}</select></label></div><p class="ids" id="gt"></p><div class="scroll" id="return-table"></div><p class="caption">着色：橙色为零命中；绿色为当前 P 零命中而该方法有命中。源行命名空间为 validation，不是 router_train。</p><button id="download-failures">下载完整 10,730 单元 CSV</button></section>
<section class="screen-only"><h2>全部原点与证据</h2><details><summary>展开 50 个实测原点</summary><div class="scroll" id="point-table"></div></details><p><button id="download-points">下载 50 原点 CSV</button> <a href="../stage35_final_comparison_v1/analysis_v1/timings.csv">250 轮原始 wall</a> · <a href="../stage35_final_comparison_v1/report.md">原始完整报告与验收</a> · <a href="../stage35_final_comparison_v1/selection.json">冻结选型</a> · <a href="report.pdf">打印版 PDF</a></p><p class="caption">本页图、原点表及失败浏览器可单独离线使用；工作区证据链接需保留项目目录。第13会话材料交付不等于把整日目标状态标完成。</p></section><footer>ACSG · 2026-09-13 · E94 最终同批结果 · 无新增实验</footer></main>'''
script=r'''
const D=JSON.parse(document.getElementById('data').textContent), $=id=>document.getElementById(id);
const ds=$('dataset'),qs=$('query'),lselect=$('L');
function table(headers,rows){return '<table><thead><tr>'+headers.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows.map(x=>'<tr>'+x.join('')+'</tr>').join('')+'</tbody></table>'}
function current(){return D.queries.find(q=>q.dataset===ds.value&&q.row===Number(qs.value))}
function draw(){const q=current();if(!q)return;const ms=D.points.filter(p=>p.dataset===ds.value&&Number(p.L)===64).map(p=>p.model),ref=ds.value.startsWith('web')?'baseline_soft':'gt10_hard';
 $('query-title').textContent='validation 源行 '+q.row+' · 完整五 L × '+ms.length+' 个方法';
 $('hit-table').innerHTML=table(['方法',...D.L.map(L=>'L'+L)],ms.map(m=>['<td>'+D.labels[m]+'</td>',...D.L.map(L=>{const c=q.cells.find(x=>x[0]===L&&x[1]===m),r=q.cells.find(x=>x[0]===L&&x[1]===ref);return '<td class="'+(c[2]===0?'bad':r[2]===0?'good':'')+'">'+c[2]+'</td>'})]));
 $('gt').textContent='GT10：'+q.GT10.join(' · ');
 $('return-table').innerHTML=table(['方法','命中','真实入口','返回 top10'],ms.map(m=>{const c=q.cells.find(x=>x[0]===Number(lselect.value)&&x[1]===m);return ['<td>'+D.labels[m]+'</td>','<td>'+c[2]+'</td>','<td class="ids">'+c[3].filter(x=>x>=0).join(' · ')+'</td>','<td class="ids">'+c[4].join(' · ')+'</td>']}));}
function changeDataset(){qs.innerHTML=D.queries.filter(q=>q.dataset===ds.value).map(q=>'<option value="'+q.row+'">'+q.row+'</option>').join('');$('message').textContent='';draw()}
ds.addEventListener('change',changeDataset);qs.addEventListener('change',draw);lselect.addEventListener('change',draw);
$('find').addEventListener('click',()=>{const v=$('row-search').value;if(v!==''&&D.queries.some(q=>q.dataset===ds.value&&q.row===Number(v))){qs.value=String(Number(v));$('message').textContent='已定位';draw()}else{$('message').textContent='该源行不在此数据集的失败并集中'}});
function download(text,name){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff',text],{type:'text/csv;charset=utf-8'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function csv(rows){return rows.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n')}
$('download-points').addEventListener('click',()=>{const h=Object.keys(D.points[0]);download(csv([h,...D.points.map(p=>h.map(k=>p[k]))]),'E94_50_points.csv')});
$('download-failures').addEventListener('click',()=>{const rows=[['dataset','namespace','source_row','L','model','hits','GT10','entries','returned']];for(const q of D.queries)for(const c of q.cells)rows.push([q.dataset,q.namespace,q.row,c[0],c[1],c[2],q.GT10.join(' '),c[3].join(' '),c[4].join(' ')]);download(csv(rows),'E94_all_401_queries_10730_cells.csv')});
$('point-table').innerHTML=table(['数据','方法','L','Recall %','QPS 中位','QPS 最小','QPS 最大','失败数','失败率 %'],D.points.map(p=>['<td>'+(p.dataset.startsWith('web')?'Web':'Yandex')+'</td>','<td>'+D.labels[p.model]+'</td>','<td>'+p.L+'</td>',...['recall_pct','QPS','QPS_min','QPS_max','failure_count','failure_rate_pct'].map(k=>'<td>'+Number(p[k]).toFixed(k==='failure_count'?0:3)+'</td>')]));changeDataset();
window.reportReady={points:D.points.length,queries:D.queries.length,cells:D.queries.reduce((n,q)=>n+q.cells.length,0)};
'''
doc='<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+CSS+'</style></head><body>'+body+'<script id="data" type="application/json">'+json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\/')+'</script><script>'+script+'</script></body></html>'
(O/'report.html').write_text(doc)
result=dict(status='PASS_TABLE_PRESENTATION',points=50,timings=250,paired_arithmetic_rows=len(pairs),failure_queries=401,failure_cells=10730,fixed_cases=8,
            new_raw_retrieval_scoring=0,new_ANN=0,new_training=0,new_QPS=0,presentation_seconds=time.perf_counter()-t0,
            source_scope='E94 tables previously independently raw-scored and reviewed; this session checks table arithmetic and lossless presentation only')
(O/'reviews/table_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
