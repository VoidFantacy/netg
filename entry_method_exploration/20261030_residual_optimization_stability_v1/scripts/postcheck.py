from common import *
rows=list(csv.DictReader((R/'analysis/points.csv').open()));checks=[]
for ds in DS:
 for window in ['public','confirmation']:
    a=read(R/f'reviews/{ds}.{window}.audit.json');lookup={(x['K'],x['L'],x['method']):x for x in a['rows']}
    pp=[x for x in rows if x['dataset']==ds and x['window']==window]
    for p in pp:
        z=lookup[int(p['K']),int(p['L']),p['method']];assert int(p['hits'])==z['hits']
        if int(p['K'])==100:assert int(p['failed_lt10'])==z['failed_lt10']
        assert int(p['rescued'])-int(p['lost'])==int(p['hits'])-lookup[int(p['K']),int(p['L']),'GT10']['hits']
    q=np.asarray(view(read(R/f'configs/{ds}.{window}.json')['queries']),dtype='<f4')
    checks.append(dict(dataset=ds,window=window,points=len(pp),query_hashes=[hashlib.sha256(x.tobytes()).hexdigest() for x in q]))
for ds in DS:
    a=next(x for x in checks if x['dataset']==ds and x['window']=='public');b=next(x for x in checks if x['dataset']==ds and x['window']=='confirmation')
    assert len(set(b['query_hashes']))==2048 and not(set(a['query_hashes'])&set(b['query_hashes']))
dump(R/'reviews/postcheck.json',dict(status='PASS_ALL_256_INTEGER_METRICS_VS_STDLIB_AND_QUERY_ROLE_HASHES',groups=checks))
print('E194_POSTCHECK_PASS',flush=True)
