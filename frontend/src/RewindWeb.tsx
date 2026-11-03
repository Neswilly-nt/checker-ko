/** REWIND WEB: investigation assistée, jamais une recherche automatique ni un verdict algorithmique. */
import {useState, type FormEvent} from 'react';
import {Download, ExternalLink, Globe2, Info, Link2, LockKeyhole, Plus, Search, ShieldCheck} from 'lucide-react';
import {api, getToken, jsonRequest} from './api';
import {Tx,useI18n} from './i18n';
import type {Case,Media} from './types';

type Observation = 'identique'|'ressemblante'|'contexte'|'aucun';
type Relation = 'appuie'|'contredit'|'contexte';
const KIND:Record<Observation,string> = {
  identique:'Image jugée identique par le journaliste (non validée automatiquement)',
  ressemblante:'Image ressemblante, sans identité confirmée',
  contexte:'Page fournissant uniquement du contexte',
  aucun:'Aucun résultat probant signalé pour cette recherche'
};
const SOURCES = [
  {name:'Google Lens',url:'https://lens.google.com/'},
  {name:'TinEye',url:'https://tineye.com/'}
] as const;
const DEFAULTS = {title:'',url:'',date_of_source:'',note:'',kind:'ressemblante' as Observation,service:'Google Lens',relation_type:'contexte' as Relation};

export default function RewindWeb({record,mine,action}:{record:Case&{media:Media};mine:boolean;action:(fn:()=>Promise<unknown>,message:string)=>Promise<boolean>}){
 const {t,errorMessage}=useI18n();
 const [form,setForm]=useState(DEFAULTS);
 const [error,setError]=useState('');
 const [downloading,setDownloading]=useState(false);
 const [recentlySaved,setRecentlySaved]=useState(false);
 const [saving,setSaving]=useState(false);
 const download = async()=>{
   setError('');setDownloading(true);
   try {
     // La copie JPEG est un aperçu privé fourni par l'API, sans EXIF/GPS.
     // Ne jamais envoyer le jeton d'authentification à un service externe.
     if(!/^\/api\/media\/\d+\/preview$/.test(record.media.preview_url)){setError(t('rewind.previewUnavailable'));return;}
     const response=await fetch(record.media.preview_url,{headers:{Authorization:`Bearer ${getToken()||''}`},cache:'no-store'});
     if(!response.ok){setError(errorMessage({status:response.status}));return;}
     const blob=await response.blob();
     if(!blob.type.startsWith('image/')){setError(t('errors.unsupported'));return;}
     const url=URL.createObjectURL(blob);
     const link=document.createElement('a');
     link.href=url;link.download=`checker-ko_CK-${String(record.id).padStart(3,'0')}_recherche.jpg`;
     document.body.appendChild(link);link.click();link.remove();
     window.setTimeout(()=>URL.revokeObjectURL(url),1000);
   } catch(e){setError(errorMessage(e))} finally{setDownloading(false)}
 };
 const submit=async(e:FormEvent)=>{
   e.preventDefault();setError('');setRecentlySaved(false);
   const trimmed=form.url.trim();
   if(trimmed){
     try { const u=new URL(trimmed);if(!['https:','http:'].includes(u.protocol))throw new Error();}
     catch{setError(t('rewind.invalidUrlError'));return}
   }
   if(!form.note.trim() || form.note.trim().length<12){setError(t('rewind.insufficientNoteError'));return}
   const title=form.title.trim() || `${form.service} — ${form.kind==='aucun'?'aucun résultat probant':'résultat à vérifier'}`;
   // Le statut de correspondance est une OBSERVATION HUMAINE conservée dans la note.
   const note=`REWIND WEB — Recherche manuelle via ${form.service}. Observation déclarée par le journaliste : ${KIND[form.kind]}. ${form.note.trim()}`;
   setSaving(true);
   const saved=await action(()=>api(`/cases/${record.id}/evidence`,jsonRequest('POST',{
     title,url:trimmed||null,date_of_source:form.date_of_source||null,
     note,relation_type:form.relation_type,archived_media_id:null
   })),t('messages.resultAdded'));
   setSaving(false);
   if(saved){setRecentlySaved(true);setForm(DEFAULTS)}
 };
 return <section className="panel rewind-web" aria-labelledby="rewind-web-title">
   <div className="panel-head"><div><div className="rewind-web-heading"><Globe2 size={22}/><h2 id="rewind-web-title"><Tx id="rewind.fullTitle"/></h2></div>
     <p><Tx id="rewind.prompt"/></p></div><span className="pill blue"><Tx id="rewind.manual"/></span></div>
   <div className="web-main-action"><label><Tx id="rewind.service"/><select value={form.service} onChange={e=>setForm({...form,service:e.target.value})}><option>Google Lens</option><option>TinEye</option></select></label><button className="btn primary" type="button" disabled={downloading} onClick={()=>{window.open(form.service==='TinEye'?'https://tineye.com/':'https://lens.google.com/','_blank','noopener,noreferrer');void download()}}><Search size={17}/> <Tx id="rewind.searchOriginExact"/></button><p><Tx id="rewind.copyNoteStraight"/></p></div>
   <div className="web-steps">
     <div className="web-step"><div className="step-heading"><span className="step-number">1</span><strong><Tx id="rewind.prepare"/></strong></div>
       <p><Tx id="rewind.prepareDetailed"/></p>
       <button className="btn secondary" onClick={download} disabled={downloading} type="button"><Download size={17}/>{downloading?t('rewind.preparingBusy'):t('rewind.download')}</button>
     </div>
     <div className="web-step"><div className="step-heading"><span className="step-number">2</span><strong><Tx id="rewind.searchOutside"/></strong></div>
       <p><Tx id="rewind.import"/></p>
       <div className="web-service-buttons">{SOURCES.map(s=><a key={s.name} className="btn secondary" href={s.url} target="_blank" rel="noopener noreferrer"><Search size={16}/>{t('rewind.openService',{name:s.name})}<ExternalLink size={14}/></a>)}</div>
     </div>
     <div className="web-step"><div className="step-heading"><span className="step-number">3</span><strong><Tx id="rewind.record"/></strong></div>
       <p><Tx id="rewind.recordGuidance"/></p>
       <div className="web-privacy"><LockKeyhole size={15}/> <Tx id="rewind.privacy"/></div>
     </div>
   </div>
   <div className="web-warning"><Info size={18}/><span><Tx id="rewind.warning"/></span></div>
   {mine?t('workspace.busy'):<div className="form-info"><ShieldCheck size={18}/> <Tx id="rewind.readOnly"/></div>}
 </section>;
}
