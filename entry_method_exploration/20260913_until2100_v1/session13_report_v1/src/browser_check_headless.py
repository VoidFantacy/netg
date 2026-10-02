"""Use installed Chromium's local pipe. No server, network, package install or ANN."""
from pathlib import Path
import base64, hashlib, json, os, selectors, subprocess, tempfile, time

O=Path(__file__).resolve().parents[1]
chrome=Path('/root/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell')
profile=tempfile.mkdtemp(prefix='acsg_session13_chrome_',dir='/tmp')
log=(O/'reviews/browser_stderr.log').open('w')
args=[str(chrome),'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
      '--no-first-run','--no-default-browser-check','--disable-background-networking',
      '--disable-component-update','--disable-sync','--disable-extensions',
      '--disk-cache-size=1048576','--disable-gpu-shader-disk-cache',
      '--remote-debugging-pipe','--user-data-dir='+profile,'about:blank']
# The shell only maps constant pipe descriptors; argv is passed without interpolation.
p=subprocess.Popen(['bash','-c','exec "$@" 3<&0 4>&1','chromium-pipe',*args],
                   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log)
sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
buf=b'';seq=0;events=[];results={};session=None
def call(method,params=None,session_id=None,timeout=25):
    global buf,seq
    seq+=1;cmd=dict(id=seq,method=method,params=params or {})
    if session_id:cmd['sessionId']=session_id
    p.stdin.write(json.dumps(cmd).encode()+b'\0');p.stdin.flush();end=time.monotonic()+timeout
    while time.monotonic()<end:
        while b'\0' in buf:
            raw,buf=buf.split(b'\0',1)
            if not raw:continue
            r=json.loads(raw)
            if 'id' in r:
                if r['id']==seq:
                    assert 'error' not in r,r
                    return r.get('result',{})
                results[r['id']]=r
            else:events.append(r)
        if seq in results:
            r=results.pop(seq);assert 'error' not in r,r;return r.get('result',{})
        if sel.select(.25):
            block=os.read(p.stdout.fileno(),1<<20)
            if not block:raise RuntimeError('Chrome pipe closed')
            buf+=block
        elif p.poll() is not None:raise RuntimeError('Chrome exited '+str(p.returncode))
    raise TimeoutError(method)

def evaluate(expression):
    r=call('Runtime.evaluate',dict(expression=expression,returnByValue=True,awaitPromise=True),session)
    assert 'exceptionDetails' not in r,r
    return r['result'].get('value')

record=dict(started_at=time.time(),chrome=str(chrome),profile=profile,ann=0)
try:
    target=call('Target.createTarget',dict(url='about:blank'))['targetId']
    session=call('Target.attachToTarget',dict(targetId=target,flatten=True))['sessionId']
    for method in ['Page.enable','Runtime.enable','Network.enable']:call(method,session_id=session)
    call('Network.setBlockedURLs',dict(urls=['http://*','https://*']),session)
    call('Emulation.setDeviceMetricsOverride',dict(width=1280,height=960,deviceScaleFactor=1,mobile=False),session)
    call('Page.navigate',dict(url=(O/'report.html').as_uri()),session)
    ready=None
    for _ in range(30):
        ready=evaluate('window.reportReady || null')
        if ready:break
        time.sleep(.1)
    assert ready==dict(points=50,queries=401,cells=10730),ready
    record['ready']=ready
    assert evaluate('document.images.length')==4
    assert evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
    assert evaluate('document.querySelectorAll("#point-table tbody tr").length')==50
    assert evaluate('document.getElementById("query").options.length')==271
    # Inspect a rescued Web query and a newly failed Yandex query against frozen examples.
    q=evaluate("document.getElementById('row-search').value='162';document.getElementById('find').click();({row:current().row,hits:current().cells.filter(c=>c[1]==='composed10').map(c=>c[2])})")
    assert q==dict(row=162,hits=[5,5,5,7,7]),q
    record['web_rescued']=q
    y=evaluate("document.getElementById('dataset').value='yandex_t2i_official10M_ip_v1';document.getElementById('dataset').dispatchEvent(new Event('change'));document.getElementById('row-search').value='154';document.getElementById('find').click();({row:current().row,hits:current().cells.filter(c=>c[1]==='compact10').map(c=>c[2]),options:document.getElementById('query').options.length})")
    assert y==dict(row=154,hits=[0,0,4,5,8],options=130),y
    record['yandex_new_failure']=y
    assert evaluate("document.getElementById('L').value='800';document.getElementById('L').dispatchEvent(new Event('change'));document.querySelectorAll('#return-table tbody tr')[3].children[1].textContent")=='8'
    assert evaluate("document.getElementById('row-search').value='9999999';document.getElementById('find').click();document.getElementById('message').textContent").startswith('该源行不在')
    # Exercise CSV download buttons while capturing generated data, without writing duplicate CSVs.
    downloads=evaluate("""window.captured=[];download=(text,name)=>captured.push({name,rows:text.split('\\r\\n').length,first:text.split('\\r\\n')[0]});document.getElementById('download-points').click();document.getElementById('download-failures').click();captured""")
    assert [x['rows'] for x in downloads]==[51,10731],downloads
    record['downloads']=downloads
    evaluate("document.getElementById('dataset').value='webvid2_5m_light_v1';document.getElementById('dataset').dispatchEvent(new Event('change'));document.getElementById('row-search').value='162';document.getElementById('find').click();window.scrollTo(0,0)")
    png=call('Page.captureScreenshot',dict(format='png'),session)['data']
    (O/'reviews/desktop.png').write_bytes(base64.b64decode(png))
    pdf=call('Page.printToPDF',dict(printBackground=True,preferCSSPageSize=True,displayHeaderFooter=False),session,timeout=35)['data']
    (O/'report.pdf').write_bytes(base64.b64decode(pdf))
    call('Emulation.setDeviceMetricsOverride',dict(width=390,height=844,deviceScaleFactor=1,mobile=True),session)
    assert evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'mobile page overflow'
    (O/'reviews/mobile.png').write_bytes(base64.b64decode(call('Page.captureScreenshot',dict(format='png'),session)['data']))
    evaluate("document.getElementById('hit-table').scrollIntoView({block:'center'})")
    (O/'reviews/mobile_failure.png').write_bytes(base64.b64decode(call('Page.captureScreenshot',dict(format='png'),session)['data']))
    errors=[x for x in events if x.get('method')=='Runtime.exceptionThrown']
    requests=[x['params']['request']['url'] for x in events if x.get('method')=='Network.requestWillBeSent']
    assert not errors,errors
    assert not [u for u in requests if u.startswith(('http://','https://'))],requests
    record.update(status='PASS',JS_exceptions=errors,external_requests=0,images=4,mobile_page_overflow=False,
                  checked_controls=['dataset','source row','search hit/miss','L detail','both CSV downloads'],
                  report_html_sha256=hashlib.sha256((O/'report.html').read_bytes()).hexdigest(),
                  report_pdf_sha256=hashlib.sha256((O/'report.pdf').read_bytes()).hexdigest())
finally:
    if p.poll() is None:
        try:call('Browser.close',timeout=5)
        except (RuntimeError,TimeoutError):pass
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
    record.update(completed_at=time.time(),browser_returncode=p.returncode)
    (O/'reviews/browser_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    log.close()
print(json.dumps(record,ensure_ascii=False))
