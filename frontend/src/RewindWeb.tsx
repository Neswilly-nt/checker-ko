/** REWIND WEB: investigation assistée, jamais une recherche automatique ni un verdict algorithmique. */
import {useState, type FormEvent} from 'react';
import {Download, ExternalLink, Globe2, Info, Link2, LockKeyhole, Plus, Search, ShieldCheck} from 'lucide-react';
import {api, getToken, jsonRequest} from './api';
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
  {name:'Google Lens',url:'https://lens.google.com/',label:'Ouvrir Google Lens'},
  {name:'TinEye',url:'https://tineye.com/',label:'Ouvrir TinEye'}
] as const;
const DEFAULTS = {title:'',url:'',date_of_source:'',note:'',kind:'ressemblante' as Observation,service:'Google Lens',relation_type:'contexte' as Relation};

export default function RewindWeb({record,mine,action}:{record:Case&{media:Media};mine:boolean;action:(fn:()=>Promise<unknown>,message:string)=>Promise<boolean>}){
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
     if(!/^\/api\/media\/\d+\/preview$/.test(record.media.preview_url))throw new Error('Adresse d’aperçu non reconnue');
     const response=await fetch(record.media.preview_url,{headers:{Authorization:`Bearer ${getToken()||''}`},cache:'no-store'});
     if(!response.ok)throw new Error('Accès à l’image refusé : reconnectez-vous puis réessayez.');
     const blob=await response.blob();
     if(!blob.type.startsWith('image/'))throw new Error('Le serveur n’a pas renvoyé une image.');
     const url=URL.createObjectURL(blob);
     const link=document.createElement('a');
     link.href=url;link.download=`checker-ko_CK-${String(record.id).padStart(3,'0')}_recherche.jpg`;
     document.body.appendChild(link);link.click();link.remove();
     window.setTimeout(()=>URL.revokeObjectURL(url),1000);
   } catch(e){setError((e as Error).message)} finally{setDownloading(false)}
 };
 const submit=async(e:FormEvent)=>{
   e.preventDefault();setError('');setRecentlySaved(false);
   const trimmed=form.url.trim();
   if(trimmed){
     try { const u=new URL(trimmed);if(!['https:','http:'].includes(u.protocol))throw new Error();}
     catch{setError('Utilisez une URL http:// ou https:// valide.');return}
   }
   if(!form.note.trim() || form.note.trim().length<12){setError('Décrivez ce que la recherche montre et ce qui demeure incertain (12 caractères minimum).');return}
   const title=form.title.trim() || `${form.service} — ${form.kind==='aucun'?'aucun résultat probant':'résultat à vérifier'}`;
   // Le statut de correspondance est une OBSERVATION HUMAINE conservée dans la note.
   const note=`REWIND WEB — Recherche manuelle via ${form.service}. Observation déclarée par le journaliste : ${KIND[form.kind]}. ${form.note.trim()}`;
   setSaving(true);
   const saved=await action(()=>api(`/cases/${record.id}/evidence`,jsonRequest('POST',{
     title,url:trimmed||null,date_of_source:form.date_of_source||null,
     note,relation_type:form.relation_type,archived_media_id:null
   })),'Résultat de recherche externe ajouté au carnet de preuves');
   setSaving(false);
   if(saved){setRecentlySaved(true);setForm(DEFAULTS)}
 };
 return <section className="panel rewind-web" aria-labelledby="rewind-web-title">
   <div className="panel-head"><div><div className="rewind-web-heading"><Globe2 size={22}/><h2 id="rewind-web-title">REWIND WEB — Recherche inversée assistée</h2></div>
     <p>Complétez les archives locales par une recherche sur des sites externes, puis documentez vous-même les résultats.</p></div><span className="pill blue">ASSISTANCE MANUELLE</span></div>
   <div className="web-main-action"><label>Service<select value={form.service} onChange={e=>setForm({...form,service:e.target.value})}><option>Google Lens</option><option>TinEye</option></select></label><button className="btn primary" type="button" disabled={downloading} onClick={()=>{window.open(form.service==='TinEye'?'https://tineye.com/':'https://lens.google.com/','_blank','noopener,noreferrer');void download()}}><Search size={17}/> Rechercher l'origine de cette image</button><p>Une copie sans EXIF/GPS est téléchargée. Importez-la dans l'onglet du service ouvert.</p></div>
   <div className="web-steps">
     <div className="web-step"><div className="step-heading"><span className="step-number">1</span><strong>Préparer la photo</strong></div>
       <p>Enregistrez une copie JPEG de recherche. Cette copie est redimensionnée si nécessaire et ses métadonnées EXIF/GPS ne sont pas incluses.</p>
       <button className="btn secondary" onClick={download} disabled={downloading} type="button"><Download size={17}/>{downloading?'Préparation...':'Télécharger une copie pour recherche'}</button>
     </div>
     <div className="web-step"><div className="step-heading"><span className="step-number">2</span><strong>Rechercher à l’extérieur</strong></div>
       <p>Ouvrez un service, importez manuellement la copie téléchargée et examinez les pages trouvées.</p>
       <div className="web-service-buttons">{SOURCES.map(s=><a key={s.name} className="btn secondary" href={s.url} target="_blank" rel="noopener noreferrer"><Search size={16}/>{s.label}<ExternalLink size={14}/></a>)}</div>
     </div>
     <div className="web-step"><div className="step-heading"><span className="step-number">3</span><strong>Consigner vos constatations</strong></div>
       <p>Indiquez si l’image est identique, simplement ressemblante ou si la page apporte du contexte.</p>
       <div className="web-privacy"><LockKeyhole size={15}/> Aucune image n’est transmise automatiquement à Google Lens ou TinEye.</div>
     </div>
   </div>
   <div className="web-warning"><Info size={18}/><span>Une ressemblance ne prouve ni la date, ni le lieu, ni la véracité d’une affirmation. Les sites externes ont leurs propres règles de confidentialité ; n’y envoyez pas de contenu sensible sans autorisation.</span></div>
   {mine?<div className="web-proof-form"><div className="web-proof-title"><Link2 size={19}/><div><h3>Enregistrer le résultat dans le dossier CK-{String(record.id).padStart(3,'0')}</h3><p>Le carnet de preuves et la fiche PDF incluront votre observation après enregistrement.</p></div></div>
     <form className="form-stack" onSubmit={submit}>
      <div className="web-form-grid">
       <label>Service de recherche<select value={form.service} onChange={e=>setForm({...form,service:e.target.value})}><option>Google Lens</option><option>TinEye</option><option>Autre moteur ou site</option></select></label>
       <label>Type de résultat observé<select value={form.kind} onChange={e=>setForm({...form,kind:e.target.value as Observation})}>
         <option value="identique">Image jugée identique (à confirmer)</option><option value="ressemblante">Image visuellement ressemblante</option><option value="contexte">Page de contexte uniquement</option><option value="aucun">Aucun résultat probant</option>
       </select></label>
       <label>Titre ou organisme<input minLength={2} maxLength={250} value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="Ex. : Viator — Baobabs (piste de contexte)"/></label>
       <label>URL exacte du résultat (facultatif)<input type="url" maxLength={2000} value={form.url} onChange={e=>setForm({...form,url:e.target.value})} placeholder="https://..."/></label>
       <label>Date publiée, si vérifiée<input type="date" value={form.date_of_source} onChange={e=>setForm({...form,date_of_source:e.target.value})}/></label>
       <label>Lien avec l’affirmation<select value={form.relation_type} onChange={e=>setForm({...form,relation_type:e.target.value as Relation})}><option value="contexte">Apporte du contexte</option><option value="appuie">Appuie (justification requise)</option><option value="contredit">Contredit (justification requise)</option></select></label>
      </div>
      <label>Constatations et incertitudes<textarea required minLength={12} maxLength={4500} rows={4} value={form.note} onChange={e=>setForm({...form,note:e.target.value})} placeholder="Même photographie ou scène seulement similaire ? Quel site ? Quelle date vérifiable ? Qu'est-ce qui reste incertain ?"/></label>
      {error&&<div className="error" role="alert"><Info size={17}/>{error}</div>}
      {recentlySaved&&<div className="form-info"><ShieldCheck size={17}/> Preuve ajoutée : ouvrez « Sources et preuves » pour la consulter ou la modifier.</div>}
      <button className="btn primary" type="submit" disabled={saving||form.note.trim().length<12}><Plus size={17}/>{saving?'Enregistrement...':'Enregistrer comme preuve (validation humaine)'}</button>
     </form>
   </div>:<div className="form-info"><ShieldCheck size={18}/> Lecture seule : seul l’auteur du dossier peut ajouter une preuve externe.</div>}
 </section>;
}
