from common import RUN,DATASETS,read,dump,check_lock,frozen_check,update_state
from select_alpha import candidates_for


def main():
    check_lock();frozen_check('audit')
    assert read(RUN/'reviews/audit_verification.json')['status']=='PASS'
    assert not (RUN/'reviews/audit_report.json').exists()
    report={}
    for ds in DATASETS:
        _,candidates=candidates_for(ds,'audit');chosen=read(RUN/'models'/ds/'selection.json')['selected']
        record={'selected_on_cal':chosen,'candidates_report_only':candidates,
                'primary':next(c for c in candidates if c['name']==chosen),'reselection':False}
        report[ds]=record
        print(ds,chosen,record['primary']['pooled'],flush=True)
    dump(RUN/'reviews/audit_report.json',{'status':'REPORT_ONLY_COMPLETE','datasets':report,'selected_profiles_unchanged':True})
    frozen_check('audit');update_state(status='AUDIT_REPORT_ONLY_COMPLETE')
    print('AUDIT_REPORTED_WITHOUT_RESELECTION',flush=True)


if __name__=='__main__':main()
