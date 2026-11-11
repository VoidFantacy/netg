#!/usr/bin/env python3
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,json,textwrap
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
R=Path(__file__).resolve().parents[1];A=R/'analysis';DS=['coco','deep10m_l2_v1'];LABEL={'coco':'COCO','deep10m_l2_v1':'Deep10M'};METHODS=['GT10','B32','REG-R','OPT-R','BLOCK-R512','BLOCK-R2048','BLOCK-R8192','BLOCK-C2048']
def rows(name):return list(csv.DictReader((A/f'{name}.csv').open()))
def f(v,n=2):return f'{float(v):.{n}f}' if v not in ['',None] else '—'
def md(head,data):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in data])
def main():
 points=rows('points');paired=rows('paired');comps=rows('discrete_comparisons');selected=rows('selected_validation');summary=json.loads((A/'summary.json').read_text());audit=json.loads((R/'reviews/results_audit.json').read_text());p={(r['dataset'],r['method'],int(r['L'])):r for r in points};pair={(r['dataset'],r['method'],int(r['L'])):r for r in paired}
 blocked=[r for r in comps if r['method'].startswith('BLOCK-')];dom=sum(bool(r['dominated_by_GT_L']) for r in blocked);speed=[r for r in blocked if r['target_speed_delta_pct'] and float(r['target_speed_delta_pct'])>=2 and r['target_speed_three_rounds_positive']=='True'];budget=[r for r in blocked if r['budget_recall_delta_pp'] and float(r['budget_recall_delta_pp'])>=.05]
 lead=f'硬预算区域补全24点中{dom}点被实测GT10覆盖；速度筛选通过{len(speed)}点，预算召回筛选通过{len(budget)}点。默认保留E99 GT10。'
 mainrows=[];equiv=[];rescues=[];budgetrows=[]
 for ds in DS:
  for m in METHODS:
   x=p[ds,m,200];z=pair.get((ds,m,200));mainrows.append([LABEL[ds],m,f(x['recall_pct'],4),f(x['qps']),f(z['recall_delta_pp'],4) if z else '—',f(z['extra_time_pct'])+'%' if z else '—'])
  for L in [100,200,400]:
   a,b=p[ds,'REG-R',L],p[ds,'OPT-R',L];equiv.append([LABEL[ds],L,f(a['recall_pct'],4),f(a['qps']),f(b['qps']),f(100*(float(b['qps'])/float(a['qps'])-1))+'%'])
  for m in METHODS[1:]:
   x=p[ds,m,200];z=pair[ds,m,200];rescues.append([LABEL[ds],m,z['members_rescued'],z['members_damaged'],z['rescued_source_out'],z['original_lt10'],z['lt10_escaped'],z['new_lt10']])
  for m in ['BLOCK-R512','BLOCK-R2048','BLOCK-R8192','BLOCK-C2048']:
   x=p[ds,m,200];z=pair[ds,m,200];budgetrows.append([LABEL[ds],m,f(x['scanned_codes_per_query'],1),x['scan_max'],f(x['extra_exact_scores_per_query'],1),f(z['recall_delta_pp'],4),f(z['extra_mean_us'],1)])
 profile_rows=[]
 for ds in DS:
  q=json.loads((R/f'diagnostics/{ds}/profile.json').read_text())
  for x in q['measurements']:
   s=np.array(x['stage_seconds'])*1e6/x['n'];profile_rows.append([LABEL[ds],x['method'],f(s[0],1),f(s[1],1),f(s[2],1),f(s[4],1),f(s[5]+s[6]+s[7],1)])
 chosen=[[LABEL[s['dataset']],s['main_L'],s['chosen_method'],s['chosen_L'],f(s['test_recall_pct'],4),f(s['test_qps']),f(s['test_recall_delta_pp'],4),f(s['test_time_ratio'],3),s['test_within_budget']] for s in selected]
 costs=[]
 for x in summary['costs']:
  ds=x['dataset'];b=json.loads((R/f'models/{ds}/blocks.json').read_text());l=json.loads((R/f'models/{ds}/labels.json').read_text());tr=json.loads((R/f'models/{ds}/training.json').read_text());env=x['environment'];costs.append([LABEL[ds],f(b['seconds']),f(l['seconds']),f(tr['seconds'],3),f(env['block_backend_bytes']/2**20),f((env['old_backend_bytes']+env['block_backend_bytes'])/2**20),f(x['internal_wall_seconds']),f(x['suite_wall_seconds'])])
 lines=['# E188：补全费用与硬访问预算实验','',lead,'','2026-10-28；COCO与Deep10M，真实K100；正式100点/300完整单线程批次，另100点/300轮校准。每个正式点10K query，校准4K。旧模型/图/GT/metric保持。','',
 '## 固定L200完整结果','',md(['数据','方法','Recall@100 %','完整QPS','ΔRecall pp','平均完整耗时增加'],mainrows),'',
 '耗时由三轮中位QPS倒数派生，不是p95；QPS下降百分比与耗时增加百分比不同。所有方法本轮同一二进制/计时边界，未拼接旧QPS。','',
 '## 保持结果一致的工程省费','',md(['数据','L','共同Recall %','REG-R QPS','OPT-R QPS','QPS变化'],equiv),'',
 'OPT-R缓存模型系数、公共query特征并复用工作空间，精算后再合并；两集三L全部10K实际ID/score/route逐字一致。它与原REG-R的速度差属于工程省费，不直接证明胜过GT10。原主搜已返回的分数继续复用，未加入完整搜索状态缓存。','',
 '## 分段诊断（μs/query）','',md(['数据','路径','粗路由','特征','PQ LUT','扫描/堆','精算+合并'],profile_rows),'',
 '诊断使用合法末4K、L200；旧REG-R诊断复用扫描工作空间，阶段总和不是原版完整wall的严格分解。阶段计时器未进入正式QPS路径。Deep扫描/堆占主要区域费用；COCO粗路由较大。各项互斥，不再与完整wall重复相加。','',
 '## 硬预算与实际救回','',md(['数据','方法L200','平均扫码','最大扫码','平均精算','ΔRecall pp','额外μs'],budgetrows),'',
 '每区域最多B/2码、48精算候选，合计96；按PQ重构向量的空间划分和块中心距离确定访问顺序，整块预算不够时跳过。原REG-R是两区共同PQ96，新块法是每区48；跨两类比较不是纯扫描量消融，三档BLOCK-R内部则保持相同候选配额和选择器。码预算控制了访问量，不保证按比例降低完整wall。','',
 'BLOCK-C2048以预算内最终实际新增命中为标签，预测净救回/区域费用，和同预算BLOCK-R2048比较。单区域监督与双区域合并仍有交互，训练中命中预测和操作费用拟合不是独立的性能证据。','',
 '## 源内外救回与严重失败（L200）','',md(['数据','方法','救回成员','损伤','源外救回','原失败query','脱离失败','新增失败'],rescues),'',
 '失败严格为单query Recall@100<10%（0–9命中）。源外相对于原完整16K训练遗漏并集；成员救回、平均Recall和严重失败修复分别报告，稀少尾部不作普遍规律。','',
 '## 校准选择及正式检验','',md(['数据','主L','校准所选','所选L','test Recall %','test QPS','ΔRecall pp','耗时比','预算内'],chosen),'',
 '原规则因B32包含末4K训练标签而失配，六项均选B32，原结果已保留。正式矩阵前另冻角色修正规则，自动选择排除旧B32，B32仍保留为正式参考；修正配置只由末4K校准结果选择：完整耗时≤同L GT10的1.10倍且Recall至少+0.05pp，选召回最高者；可选择更大L的GT10，无合格者不补全。原选择与角色修正选择文件均先于任何正式矩阵生成，正式结果不反向改变选择。','',
 '**角色限制：末4K仅对新救回/费用模型与前12K分开；旧B32使用完整16K，包含这4K，旧GT10也可能使用合法fit数据。因此校准选择不是所有候选共同未见数据上的公平泛化证明。正式10K不参与本轮选择，但已在历史研究曝光，仍不是新盲确认。**','',
 '## 离散预算对照与范围','',
 f'GT10预定29个L覆盖100至640；每集7个补全方法×3个L。{lead}',
 '所有42个补全点的对照在analysis/discrete_comparisons.csv。速度筛选为达到候选召回阈值的实测GT10对照上+2%且三轮同向；预算筛选为候选完整耗时以内最佳实测GT10上Recall+0.05pp。不同Recall的离散阈值对照不是精确等Recall，连线只作阅读，不作新增测量或插值收益。','',
 '## 成本与核验','',md(['数据','块构建秒','标签秒','训练秒','块数组MiB','共同辅助数组MiB','正式内部wall秒','suite秒'],costs),'',
 '构建/标签/训练本轮均1线程；正式CPU15，实际线程数1，串行运行。suite包含内部wall，不能相加。共同辅助数组是benchmark同时装载旧后端与块后端的载荷，不是峰值RSS；当前实现保留两份布局，不冒称部署时已省掉冗余内存。旧base/图/原PQ首次构建费用继承历史，未清零。','',
 f'核验：{audit["points"]}点/{audit["formal_batches"]}轮packet SHA，{audit["paired_points"]}组成对整数质量，{audit["hard_budget_points"]}个预算点全部query上限，旧包逐字一致{audit["historical_packets_equal"]}点，E187封存{audit["old_E187_seal_files_unchanged"]}文件不变。所有补全从同L真实主包做完整候选排序/合并oracle；另有stdlib集合统计及原base float64分数抽检。第二实现由同一执行者完成，不称独立人员审查。',
 'B32原native计数0为未插桩，真实候选精算数见reviews/results_audit.json。三轮计时不是三份质量样本；paired bootstrap只描述当前query分布，未校正多重比较，不含图/模型重训波动。','',
 '## 当前决定','',
 '保留E99 GT10默认。是否有值得继续的特定数据/L候选，以本轮全部离散对照、冻结校准选择及实际费用共同判断；不由源外救回、标签拟合或单个近阈值点宣布可靠替换。本轮已完成预定矩阵，不继续扩扫或按test调参。尚无K1、其余五集、独立新query确认、完整搜索状态复用或逐query二元门控的新证据。','',
 '[协议](protocol.md) · [冻结](freeze.json) · [原校准选择](selection_freeze.json) · [角色修正](calibration_role_correction.md) · [修正选择](corrected_selection_freeze.json) · [全部点](analysis/points.csv) · [成对救损](analysis/paired.csv) · [预算对照](analysis/discrete_comparisons.csv) · [独立实现核验](reviews/results_audit.json)']
 (R/'report_zh.md').write_text('\n'.join(lines)+'\n')
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font);plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'axes.unicode_minus':False,'pdf.fonttype':3,'font.size':9})
 def page(title,num):
  fig=plt.figure(figsize=(11.7,8.3));fig.text(.05,.95,title,fontsize=18,weight='bold');fig.text(.05,.025,f'E188 · COCO / Deep10M · K100 · 历史曝光测试 · 2026-10-28                         {num}/6',fontsize=8,color='#667788');return fig
 def tablefig(fig,rect,head,data,size=8):
  ax=fig.add_axes(rect);ax.axis('off');tb=ax.table(cellText=data,colLabels=head,cellLoc='center',bbox=[0,0,1,1]);tb.auto_set_font_size(False);tb.set_fontsize(size)
  for (i,j),cell in tb.get_celld().items():cell.set_edgecolor('#d3dce3');cell.set_facecolor('#e6eff5' if i==0 else '#f5f8fa' if i%2 else 'white')
 def txt(fig,y,s,size=10):
  # Wrap by display width, not character count, for mixed CJK/ASCII lines.
  lines=[];buf='';w=0
  for ch in s:
   cw=2 if ord(ch)>255 else 1
   if ch=='\n' or w+cw>128:lines.append(buf);buf='';w=0
   if ch!='\n':buf+=ch;w+=cw
  if buf:lines.append(buf)
  fig.text(.055,y,'\n'.join(lines),fontsize=size,va='top',linespacing=1.5)
 pdf=R/'ACSG_补全成本与硬预算实验_20261028.pdf'
 with PdfPages(pdf) as doc:
  fig=page('费用下降是否换来了可支付的召回？',1);txt(fig,.90,lead,11);tablefig(fig,[.05,.23,.90,.60],['数据','方法 L200','Recall@100 %','完整 QPS','ΔRecall pp','耗时增加'],mainrows,8.2);txt(fig,.19,'正式100点/300轮；两集每点10K query，CPU15实际单线程。另100点/300轮校准。耗时增加按QPS倒数计算；默认保持GT10。',10);doc.savefig(fig);plt.close(fig)
  fig=page('完整 Recall–QPS：全部方法与密集GT10控制',2)
  colors=plt.cm.tab10(np.linspace(0,1,8))
  for k,ds in enumerate(DS):
   ax=fig.add_axes([.07+k*.48,.19,.40,.65])
   for j,m in enumerate(METHODS):
    rr=sorted([x for x in points if x['dataset']==ds and x['method']==m],key=lambda x:int(x['L']));ax.plot([float(x['recall_pct']) for x in rr],[float(x['qps']) for x in rr],marker='o',ms=3,lw=1.2,color=colors[j],label=m)
   ax.set(title=LABEL[ds],xlabel='Recall@100 (%)',ylabel='完整 QPS');ax.grid(alpha=.2)
   if k==0:handles,labels=ax.get_legend_handles_labels()
  fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.07),ncol=4,fontsize=8);txt(fig,.90,'GT10为事前固定29个L；补全固定L100/200/400。连线仅便于阅读，不能作为插值收益或新增测量。',10);doc.savefig(fig);plt.close(fig)
  fig=page('分段费用与保持结果一致的工程省费',3);tablefig(fig,[.05,.62,.90,.22],['数据','路径','粗路由 μs','特征 μs','PQ LUT μs','扫描/堆 μs','精算+合并 μs'],profile_rows,9);tablefig(fig,[.05,.22,.90,.31],['数据','L','共同Recall %','REG-R QPS','OPT-R QPS','QPS变化'],equiv,9);txt(fig,.90,'校准L200分段诊断：Deep扫描/堆较大，COCO粗路由较大。',11);txt(fig,.17,'OPT-R三L全部10K返回逐字一致。legacy诊断复用扫描缓冲，阶段值不是原版wall的严格拆解；阶段计时器不进入正式性能。',9);doc.savefig(fig);plt.close(fig)
  fig=page('访问预算、实际救回与源外覆盖',4);tablefig(fig,[.05,.47,.90,.37],['数据','方法 L200','平均扫码','最大扫码','平均精算','ΔRecall pp','额外 μs'],budgetrows,8.5)
  source_rows=[[a[0],a[1],a[2],a[3],a[4]] for a in rescues if a[1] in ['REG-R','BLOCK-R2048','BLOCK-C2048']];tablefig(fig,[.05,.13,.90,.27],['数据','方法 L200','救回成员','损伤成员','源外救回'],source_rows,9);txt(fig,.90,'硬预算限定每区域扫码B/2和48候选。码数下降必须同时检查完整耗时及召回损失。',10);doc.savefig(fig);plt.close(fig)
  fig=page('校准先选配置，正式样本检验；严重失败单列',5);tablefig(fig,[.05,.58,.90,.27],['数据','主L','所选方法','所选L','test Recall %','test QPS','ΔRecall pp','耗时比','预算内'],chosen,7.5)
  tail=[[r[0],r[1],r[5],r[6],r[7]] for r in rescues if r[1] in ['B32','REG-R','BLOCK-R2048','BLOCK-C2048']];tablefig(fig,[.05,.17,.90,.34],['数据','方法 L200','原失败query','脱离失败','新增失败'],tail,8.5);txt(fig,.12,'失败严格为Recall@100<10%，即0–9命中；成员救回不等于严重失败修复。稀少尾部不推导普遍规律。',9);doc.savefig(fig);plt.close(fig)
  fig=page('成本、核验与结论边界',6);tablefig(fig,[.05,.65,.90,.19],['数据','构块秒','标签秒','训练秒','块 MiB','共同辅助 MiB','内部wall秒','suite秒'],costs,8)
  txt(fig,.59,f'核验通过：100真实点/300轮、42组成对统计、24个预算点的逐query上限；原REG-R与OPT-R返回逐字一致。E187封存{audit["old_E187_seal_files_unchanged"]}文件保持，旧实际包{audit["historical_packets_equal"]}点匹配。另有完整排序/合并oracle、stdlib整数复算和float64原metric分数抽检。',10)
  txt(fig,.43,'校准末4K对新模型留出，旧B32却包含这4K训练标签。原选择六项均为B32，已保留为角色失配诊断；正式前修正自动选择排除B32，正式参考仍保留它。旧GT10也可能使用合法fit数据。正式10K不参与本轮选择，但历史已曝光，不是新盲确认。二实现由同一执行者完成，不称独立人员审查。',10)
  txt(fig,.29,'suite已包含内部wall；共同辅助数组含旧布局与新块布局，不是峰值RSS。原REG-R共同96候选，新块法每区48，跨后端不能归因为纯扫码量变化。无K1/其余五集新验证，无完整主搜状态复用或逐query二元门控。',10)
  txt(fig,.15,lead+' 完整数值和全部负结果见同目录report_zh.md与analysis/。',10);doc.savefig(fig);plt.close(fig)
 print(json.dumps(dict(lead=lead,speed_candidates=speed,budget_candidates=budget,pdf=str(pdf)),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
