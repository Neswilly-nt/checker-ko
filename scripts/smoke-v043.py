"""Chrome CDP responsive checks with isolated local API data."""
import asyncio
import json
import urllib.request
import websockets

SIZES = [(1920,1080),(1366,768),(1280,720),(1024,768),(768,1024),(390,844),(360,800)]
ZOOMS = [0.8,1.0,1.25,1.5]
ROUTES = ['/dashboard','/verifier','/sources','/dossiers/4']

async def main():
    request=urllib.request.Request('http://127.0.0.1:9223/json/new?http://127.0.0.1:5181/',method='PUT')
    target=json.load(urllib.request.urlopen(request))
    async with websockets.connect(target['webSocketDebuggerUrl'],max_size=8_000_000) as ws:
        serial=0
        async def command(method,params=None):
            nonlocal serial
            serial+=1; current=serial
            await ws.send(json.dumps({'id':current,'method':method,'params':params or {}}))
            while True:
                msg=json.loads(await ws.recv())
                if msg.get('id')==current:
                    if 'error' in msg:raise RuntimeError(msg['error'])
                    return msg.get('result',{})
        async def evaluate(expression):
            result=await command('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
            if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
            return result['result'].get('value')
        await command('Page.enable');await command('Runtime.enable')
        await asyncio.sleep(1)
        login=await evaluate("fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'journaliste@checker.local',password:'Journaliste2026!'})}).then(r=>r.json())")
        assert login.get('access_token'),login
        await evaluate("localStorage.setItem('checker_ko_demo_token',"+json.dumps(login['access_token'])+")")
        failures=[]; measurements=[]
        for route in ROUTES:
            await evaluate('location.href='+json.dumps(route))
            await asyncio.sleep(1.2)
            rendered=await evaluate("({path:location.pathname,title:document.querySelector('h1')?.textContent,sources:document.querySelectorAll('.source-row').length,caseTitle:document.querySelector('.work-claim h1')?.textContent})")
            if not rendered.get('title'):
                rendered['body']=await evaluate('document.body.innerText.slice(0,600)')
            assert rendered.get('path')==route and rendered.get('title'),rendered
            if route=='/sources':assert rendered['sources']==5,rendered
            if route=='/dossiers/4':assert 'écoles' in rendered['caseTitle'],rendered
            for physical_width,height in SIZES:
                for zoom in ZOOMS:
                    width=round(physical_width/zoom)
                    await command('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':physical_width<=768})
                    await asyncio.sleep(.05)
                    data=await evaluate("(()=>{const brand=document.querySelector('.sidebar .brand');const side=document.querySelector('.sidebar');const b=brand?.getBoundingClientRect(),s=side?.getBoundingClientRect();return {route:location.pathname,scroll:document.documentElement.scrollWidth,inner:window.innerWidth,brandRight:b?.right,sidebarRight:s?.right,title:document.querySelector('h1')?.textContent}})()")
                    measurements.append((route,physical_width,height,zoom,data))
                    if data['scroll']>data['inner']+1:failures.append(('overflow',route,physical_width,zoom,data))
                    if physical_width>900 and data['brandRight'] and data['brandRight']>data['sidebarRight']+1:failures.append(('brand',route,physical_width,zoom,data))
        print('Mesures Chrome:',len(measurements),'échecs:',len(failures))
        for failure in failures[:25]:print(failure)
        assert not failures,failures[:5]
        await evaluate("location.href='/sources?case_id=4'")
        await asyncio.sleep(1.2)
        clicked=await evaluate("(()=>{const button=document.querySelector('.source-row-actions .btn.primary');if(!button)return false;button.click();return true})()")
        assert clicked,'Bouton Ajouter à ma vérification absent'
        await asyncio.sleep(.8)
        notice=await evaluate("document.querySelector('[role=status]')?.textContent")
        assert notice and 'ajouté' in notice,notice
        print('Ajout d’une institution au carnet CK-004 : OK')

asyncio.run(main())
