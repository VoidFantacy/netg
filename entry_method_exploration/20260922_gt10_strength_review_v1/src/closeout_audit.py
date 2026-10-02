"""Read-only source identity and delivery consistency checks, no benchmark calls."""
import datetime, hashlib, json, re
from pathlib import Path

R=Path(__file__).resolve().parents[1];repo=R.parent.parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def save(name,obj):
    p=R/'reviews'/name
    assert not p.exists(),p
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

inputs={}
for name in ['consumed_inputs.json','opportunity_inputs.json','verification_inputs.json']:
    for path,identity in read(R/'reviews'/name).items():
        if path in inputs:assert inputs[path]==identity,path
        inputs[path]=identity
for path,identity in inputs.items():
    p=Path(path)
    assert p.stat().st_size==identity['size'],path
    assert sha(p)==identity['sha256'],path

before=read(R/'reviews/source_before.json');root_checks={}
for name,saved in before.items():
    p=repo/name;original=R/'source_before'/name
    assert sha(original)==saved,name
    if name=='AGENTS.md':assert sha(p)==saved,name
    else:
        # This review only inserted a new leading entry; all prior prose remains.
        first,tail=original.read_text().split('\n',1)
        assert p.read_text().startswith(first+'\n'),name
        assert p.read_text().endswith(tail),name
    root_checks[name]={'before_sha256':saved,'after_sha256':sha(p),'prior_content_preserved':True}

docs=[R/'report.md',R/'theory.md',R/'directions.md',R/'literature/review.md',
      repo/'experiment_history/127_gt10_strength_review.md']
links=[];references={}
for p in docs:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https://','http://','#')):continue
        dest=(p.parent/target.split('#')[0]).resolve()
        assert dest.is_file(),(p,target)
        links.append({'source':str(p.relative_to(repo)),'target':str(dest.relative_to(repo))})
        if R not in dest.parents:
            references[str(dest)]={'size':dest.stat().st_size,'sha256':sha(dest),
                                  'identity_captured':'closeout; not an initial protection hash'}

pdf=read(R/'reviews/pdf_verification.json')
assert pdf['status']=='PASS' and pdf['pages']==11
assert sha(R/'GT10现状与改进方向.pdf')==pdf['pdf_sha256']
for source,identity in pdf['sources'].items():assert sha(R/source)==identity,source
assert len(list((R/'figures').glob('*.png')))==4
assert len(list((R/'figures').glob('*.svg')))==4
assert len(list((R/'figures').glob('*.pdf')))==4
assert read(R/'reviews/numeric_audit.json')['all_action_masks_and_K1_labels_verified']==6709248
assert read(R/'state.json')['default_changed'] is False

save('reference_file_identities.json',references)
save('completion_audit.json',{
 'status':'PASS','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'historical_input_files_unchanged':len(inputs),'root_checks':root_checks,
 'local_links_checked':len(links),'local_links':links,
 'reference_files_identified_at_closeout':len(references),
 'pdf_pages':11,'pdf_sources_match':True,'plots':4,
 'source_protection_limit':'Checks cover the listed consumed inputs and root snapshots, not all repository files.',
 'new_training':0,'new_searches':0,'new_graphs':0,'new_GT':0,'new_performance_timing':0,
 'default_changed':False,'independent_person_or_agent_review':False,
 'research_deadline_state':'Final close time is recorded separately in state.json.'})
print(json.dumps({'status':'PASS','unchanged_inputs':len(inputs),'links':len(links),'pdf_pages':11}))
