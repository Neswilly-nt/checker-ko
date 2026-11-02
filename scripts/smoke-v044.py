"""Capture and measure the dashboard in isolated local Chrome."""
import asyncio
import base64
import json
import sys
import urllib.request
from pathlib import Path
import websockets

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'backups/dashboard-v044'
SIZES=[(1920,1080),(1366,768),(1280,720),(1024,768),(390,844)]

async def main():
    label=sys.argv[1] if len(sys.argv)>1 else 'after'
    req=urllib.request.Request('http://127.0.0.1:9224/json/new?http://127.0.0.1:5182/',method='PUT')
    target=json.load(urllib.request.urlopen(req))
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
        await evaluate("localStorage.setItem('checker_ko_demo_token',"+json.dumps(login['access_token'])+");location.href='/dashboard'")
        await asyncio.sleep(1.5)
        results=[]
        for width,height in SIZES:
            for zoom in ([1] if label=='before' else [1,1.25]):
                await command('Emulation.setDeviceMetricsOverride',{'width':round(width/zoom),'height':round(height/zoom),'deviceScaleFactor':1,'mobile':width<=390})
                await asyncio.sleep(.2)
                result=await evaluate("(()=>{const recent=document.querySelector('.dashboard-recent,.panel:last-child');const first=recent?.querySelector('.dashboard-row,.case-row');const header=document.querySelector('.dashboard-heading,.page-heading');const rect=e=>e?({top:Math.round(e.getBoundingClientRect().top),bottom:Math.round(e.getBoundingClientRect().bottom)}):null;const controls=[...document.querySelectorAll('.dashboard a,.menu-toggle')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height});return {path:location.pathname,title:document.querySelector('h1')?.textContent,viewport:{width:innerWidth,height:innerHeight},page:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight},header:rect(header),recent:rect(recent),first:rect(first),rows:recent?.querySelectorAll('.dashboard-row,.case-row').length,nav:document.querySelectorAll('.sidebar nav a').length,offscreenControls:controls.filter(e=>{const r=e.getBoundingClientRect();return r.left<-1||r.right>innerWidth+1}).map(e=>e.textContent?.trim().slice(0,40))}})()")
                results.append({'size':[width,height],'zoomEquivalent':zoom,**result})
                if label=='after':
                    assert result['title']=='Accueil' and result['nav']==5 and result['page']['width']<=result['viewport']['width']+1,result
                    assert not result['offscreenControls'],result
                    assert result['recent'] and result['first'] and result['rows']==4,result
                if zoom==1 and width in (1366,390):
                    shot=await command('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
                    (OUTPUT/f'{label}-{width}x{height}.png').write_bytes(base64.b64decode(shot['data']))
        (OUTPUT/f'{label}-measurements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        if label=='after':
            await command('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            await evaluate("document.querySelector('.menu-toggle').click()")
            assert await evaluate("document.querySelector('.sidebar').classList.contains('show')")
            await evaluate("document.querySelector('.sidebar nav a[href=\"/sources\"]').click()")
            await asyncio.sleep(.5)
            assert await evaluate("location.pathname=='/sources'")
            await evaluate("location.href='/dashboard'")
            await asyncio.sleep(1.3)
            assert await evaluate("!!document.querySelector('.dashboard-row')"),'Liste récente absente après navigation'
            await evaluate("document.querySelector('.dashboard-row').click()")
            await asyncio.sleep(.5)
            assert await evaluate("location.pathname.startsWith('/dossiers/')")
        print(json.dumps(results,ensure_ascii=False,indent=2))

asyncio.run(main())
