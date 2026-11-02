"""Optional Chrome DevTools smoke test against local isolated API data."""
import asyncio
import base64
import json
import urllib.request
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT = ROOT / 'backups' / 'browser-v041' / 'workspace-desktop.png'
MOBILE_SCREENSHOT = ROOT / 'backups' / 'browser-v041' / 'workspace-mobile.png'

async def main():
    req = urllib.request.Request('http://127.0.0.1:9222/json/new?http://127.0.0.1:5181/', method='PUT')
    target = json.load(urllib.request.urlopen(req))
    async with websockets.connect(target['webSocketDebuggerUrl'], max_size=8_000_000) as ws:
        serial = 0
        async def command(method, params=None):
            nonlocal serial
            serial += 1
            requested = serial
            await ws.send(json.dumps({'id': requested, 'method': method, 'params': params or {}}))
            while True:
                message = json.loads(await ws.recv())
                if message.get('id') == requested:
                    if 'error' in message: raise RuntimeError(message['error'])
                    return message.get('result', {})
        async def evaluate(expression):
            result = await command('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
            if result.get('exceptionDetails'): raise RuntimeError(result['exceptionDetails'])
            return result['result'].get('value')
        await command('Page.enable')
        await command('Runtime.enable')
        await asyncio.sleep(2)
        login = await evaluate("fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'journaliste@checker.local',password:'Journaliste2026!'})}).then(r=>r.json())")
        assert login.get('access_token'), login
        await evaluate("localStorage.setItem('checker_ko_demo_token'," + json.dumps(login['access_token']) + "); location.href='/dossiers/4'")
        await asyncio.sleep(2)
        summary = await evaluate("({title:document.querySelector('.work-claim h1')?.textContent,actions:[...document.querySelectorAll('.work-actions button')].map(x=>x.textContent.trim()),evidence:document.querySelectorAll('.work-evidence-row').length,report:!!document.querySelector('.report')})")
        assert 'écoles' in summary['title'] and len(summary['actions']) == 3 and not summary['report'], summary
        await command('Emulation.setDeviceMetricsOverride', {'width':1366,'height':768,'deviceScaleFactor':1,'mobile':False})
        shot = await command('Page.captureScreenshot', {'format':'png','captureBeyondViewport':False})
        SCREENSHOT.write_bytes(base64.b64decode(shot['data']))
        await evaluate("[...document.querySelectorAll('.work-actions button')].find(x=>x.textContent.includes('Ajouter une preuve')).click()")
        assert await evaluate("!!document.querySelector('.work-form input')")
        await evaluate("document.querySelector('.work-close').click()")
        await evaluate("[...document.querySelectorAll('.work-actions button')].find(x=>x.textContent.includes('Conclure')).click()")
        assert await evaluate("!!document.querySelector('.work-form select')")
        await evaluate("document.querySelector('.work-close').click()")
        setter = "(el,value)=>{const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(el,value);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}))}"
        await evaluate("[...document.querySelectorAll('.work-actions button')].find(x=>x.textContent.includes('Ajouter une preuve')).click()")
        await evaluate("(" + setter + ")(document.querySelector('.work-form input'),'Document de test UX')")
        await evaluate("(" + setter + ")(document.querySelector('.work-form textarea'),'Observation de test sur la copie isolée.')")
        await evaluate("document.querySelector('.work-form').requestSubmit()")
        await asyncio.sleep(1)
        assert await evaluate("document.querySelector('.work-evidence-row')?.textContent.includes('Document de test UX')")
        await evaluate("document.querySelector('.work-evidence-actions button').click()")
        await evaluate("(" + setter + ")(document.querySelector('.work-form textarea'),'Observation modifiée sur la copie isolée.')")
        await evaluate("document.querySelector('.work-form').requestSubmit()")
        await asyncio.sleep(1)
        assert await evaluate("document.querySelector('.work-evidence-row')?.textContent.includes('Observation modifiée')")
        await evaluate("[...document.querySelectorAll('.work-actions button')].find(x=>x.textContent.includes('Conclure')).click()")
        await evaluate("(" + setter + ")(document.querySelector('.work-form textarea'),'Les informations disponibles ne permettent pas de confirmer cette affirmation.')")
        await evaluate("document.querySelector('.work-form').requestSubmit()")
        await asyncio.sleep(1)
        assert await evaluate("!!document.querySelector('.work-report-link')")
        await evaluate("document.querySelector('.work-report-link').click()")
        await asyncio.sleep(1)
        assert await evaluate("!!document.querySelector('.report .report-verdict')")
        await evaluate("document.querySelector('.work-report-toolbar a').click()")
        await asyncio.sleep(1)
        await command('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
        await asyncio.sleep(1)
        mobile = await evaluate("({overflow:document.documentElement.scrollWidth>window.innerWidth,actions:document.querySelectorAll('.work-actions button').length})")
        assert not mobile['overflow'] and mobile['actions'] == 3, mobile
        shot = await command('Page.captureScreenshot', {'format':'png','captureBeyondViewport':False})
        MOBILE_SCREENSHOT.write_bytes(base64.b64decode(shot['data']))
        print('Chrome : CK-004, trois actions, preuve créée/modifiée, verdict, fiche dédiée et largeur mobile vérifiés sur copie.')
        print('Captures :', SCREENSHOT, MOBILE_SCREENSHOT)

asyncio.run(main())
