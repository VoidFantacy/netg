"""Direct local scientific PDF export; browser is unavailable under current sandbox."""
from pathlib import Path
import ast,csv,json,time,unicodedata,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

O=Path(__file__).resolve().parents[1]
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'pdf.fonttype':42,'axes.unicode_minus':False})
strings={}
for node in ast.parse((O/'src/build_report.py').read_text()).body:
    if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
        for t in node.targets:
            if isinstance(t,ast.Name):strings[t.id]=node.value.value

def wrap(text,width=86):
    result=[];line='';n=0
    for c in text:
        w=2 if unicodedata.east_asian_width(c) in ('W','F') else 1
        if n+w>width:result.append(line);line='';n=0
        line+=c;n+=w
    if line:result.append(line)
    return result

def page(title,blocks):
    fig=plt.figure(figsize=(8.27,11.69),facecolor='white')
    fig.text(.08,.944,title,fontsize=17,fontweight='bold',color='#173443',va='top')
    fig.text(.08,.911,'2026-09-13 · E94 冻结最终同批结果 · 第13串行会话整理',fontsize=8.5,color='#52717c')
    y=.875
    for heading,text in blocks:
        if heading:
            fig.text(.08,y,heading,fontsize=11,fontweight='bold',color='#087c80',va='top');y-=.030
        for line in wrap(text):
            fig.text(.08,y,line,fontsize=9.2,va='top',color='#243745');y-=.020
        y-=.014
    assert y>.06,('text page overflow',y)
    return fig

t0=time.perf_counter();pdf=O/'report.pdf';assert not pdf.exists()
with PdfPages(pdf,metadata={'Title':strings['title'],'Author':'ACSG','Subject':'Frozen E94 Recall-QPS and failure-query report'}) as book:
    fig=page('尚未找到稳定优于当前 GT10 起点的新方法',[
        ('当前判断',strings['intro']),
        ('完整比较',strings['scope']),
        ('五档变化：L64 / 128 / 256 / 400 / 800',
         'Web 组合 / compact：Recall +0.095 / +0.270 / +0.080 / +0.085 / +0.030 pp；失败净新增 −3 / −4 / −1 / −1 / −1。'),
        ('','Web 组合 / 当前 P：Recall −0.340 / −0.385 / −0.410 / −0.125 / −0.105 pp；失败净新增 −7 / −1 / +4 / +2 / +1。'),
        ('','Yandex compact / 当前 P：Recall +0.090 / +0.070 / +0.120 / −0.030 / −0.125 pp；失败净新增 +3 / −2 / −4 / −1 / +2。'),
        ('速度与适用范围',strings['speed']),
        ('数据角色',strings['limits'])])
    fig.savefig(O/'reviews/pdf_page1_preview.png',dpi=115);book.savefig(fig);plt.close(fig)
    fig=page('方法、失败查询与实际成本',[
        ('本次最终候选',strings['method']),('先冻结，再打开最终数据',strings['selection']),
        ('零命中失败',strings['failuretext']),('',strings['interpret']),
        ('成本',strings['cost']),('',strings['unknown']),
        ('交付入口','同目录 report.html 内嵌全部 50 原点和 401 条失败查询，可按源行查看全五 L 的 GT10、入口与完整返回。report.md 保留原始结果、计时与验收的工作区链接。')])
    fig.savefig(O/'reviews/pdf_page2_preview.png',dpi=115);book.savefig(fig);plt.close(fig)
    for name in ['recall_qps_zh','failure_qps_zh','metrics_by_L_zh','failure_cases_zh']:
        im=plt.imread(O/'figures'/f'{name}.png')
        fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
        ax=fig.add_axes([.025,.06,.95,.88]);ax.imshow(im);ax.axis('off')
        fig.text(.5,.027,'E94 · 两集各 2,000 条历史 validation 查询 · CPU15 / 单线程 · 最终反馈未回流训练或选择',ha='center',fontsize=8)
        book.savefig(fig);plt.close(fig)
    assert book.get_pagecount()==6
record=dict(status='PASS_DIRECT_PDF_EXPORT',pages=6,seconds=time.perf_counter()-t0,pdf_bytes=pdf.stat().st_size,
            pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),backend='Matplotlib PdfPages with embedded CJK font',
            note='Text-page previews and original four plot images inspected; not a browser print or independent PDF renderer test.')
(O/'reviews/pdf_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False))
