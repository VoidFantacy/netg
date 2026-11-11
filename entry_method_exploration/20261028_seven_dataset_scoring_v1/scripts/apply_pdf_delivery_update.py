"""Apply the user's later PDF instruction to mutable reports, preserving freezes."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
REL='entry_method_exploration/'+R.name
def main():
    assert (R/'dense_complete.json').exists() and (R/'reviews/interpretation.json').exists()
    auth=json.loads((R/'delivery_authorization_update.json').read_text())
    assert auth['user_request']=='这个弄完做个pdf吧，我明天看'
    rec=json.loads((R/'reviews/report_build.json').read_text())
    rec.update(initial_delivery_plan_no_PDF=rec['no_PDF'],no_PDF=False,PDF_authorized=True,
               delivery_authorization='delivery_authorization_update.json')
    (R/'reviews/report_build.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
    interpretation=json.loads((R/'reviews/interpretation.json').read_text())
    p=R/'report_zh.md';s=p.read_text().replace('本轮不生成PDF。','按用户后续明确授权，完成测试后制作详细中文PDF。')
    heading='## 七集完整结果的详细结论\n\n'+'\n\n'.join(interpretation['conclusions'])
    s=s.replace('## 先读结论的适用范围',heading+'\n\n## 先读结论的适用范围',1)
    s+='\n\n[详细中文PDF（含汇总CSV附件）](E191_七数据集_K1_K100_综合测试报告.pdf)。原冻结no_PDF为后续授权之前的交付计划；科学配置/矩阵/结束条件保持，见[后续授权](delivery_authorization_update.json)。\n'
    p.write_text(s)
    changes={
      'summary.md': [('用户未要求PDF，本轮未生成PDF。','用户随后明确要求完成后制作PDF，本轮交付详细中文PDF；文字、CSV及图表同步保留。')],
      'spec.md': [('当前用户要求无PDF，文字/CSV/PNG/SVG交付；','用户后续明确授权PDF，交付PDF/文字/CSV及图表；原冻结no_PDF属于此前交付计划；')],
      's-target.md': [('默认E99 GT10保持，无PDF。','默认E99 GT10保持，按用户后续授权交付详细中文PDF。')],
      'LOCAL_CODEX_START.md': [('用户明确没有要求就不做PDF，本轮无PDF。','用户明确授权本轮全部完成后制作PDF，现交付详细中文PDF及CSV。')],
      'experiment_history/191_seven_dataset_scoring_v1.md': [('此前明确无要求不做PDF。本轮无PDF。','此前明确无要求不做PDF，随后明确授权本轮完成后制作PDF。本轮按后续授权交付详细中文PDF。')],
    }
    for name,replacements in changes.items():
        p=REPO/name;s=p.read_text()
        for before,after in replacements:
            assert before in s,(name,before);s=s.replace(before,after)
        s+=f'\n[本轮详细PDF]({"../" if name.startswith("experiment_history/") else ""}{REL}/E191_七数据集_K1_K100_综合测试报告.pdf)（用户后续明确授权）。\n'
        p.write_text(s)
    p=REPO/'s-experiment.md';s=p.read_text().replace('七集两K综合证据仍为E183','E183保留旧综合矩阵身份，新七集证据读E191')
    s='\n'.join(line.replace('无PDF','交付PDF') if line.startswith('| E191 |') else line for line in s.splitlines())+'\n';p.write_text(s)
    p=REPO/'experiment_history/README.md';s=p.read_text().replace('七集两K综合证据仍为','旧七集综合矩阵保留为')
    s='\n'.join(line.replace('无PDF','交付PDF') if '191_seven_dataset_scoring_v1.md) |' in line else line for line in s.splitlines())+'\n';p.write_text(s)
    (R/'reviews/PDF_delivery_update.json').write_text(json.dumps(dict(status='PASS_LATER_USER_PDF_DELIVERY_APPLIED',scientific_freeze_unchanged=True,authorization='delivery_authorization_update.json',initial_flags_retained_as_history=True),indent=2)+'\n')
    print('PASS later PDF authorization applied to current reports and root documents',flush=True)
if __name__=='__main__':main()
