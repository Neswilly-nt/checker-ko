import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {BookOpen,ExternalLink} from 'lucide-react';
import {api} from './api';
import {useI18n} from './i18n';
import type {Case,DirectorySource} from './types';

export default function SourceSuggestions({record}:{record:Case}){
 const {t,errorMessage}=useI18n();
 const [sources,setSources]=useState<DirectorySource[]>([]);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');
 useEffect(()=>{let active=true;setLoading(true);api<{items:DirectorySource[]}>('/sources').then(data=>{if(active){setSources(data.items);setError('')}}).catch(reason=>{if(active)setError(errorMessage(reason))}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[errorMessage]);
 const suggestions=sources.filter(source=>!source.archived&&source.sector===record.sector&&(!record.region||!source.region||source.region===record.region||source.geographic_scope?.toLowerCase().includes('madagascar'))).sort((a,b)=>{
  const rank=(source:DirectorySource)=>Number(Boolean(record.region&&source.region===record.region))*4+Number(Boolean(!source.region||source.geographic_scope?.toLowerCase().includes('madagascar')))*2+Number(source.verification_status==='verifiees');
  return rank(b)-rank(a)||a.organization.localeCompare(b.organization);
 }).slice(0,3);
 return <section className="work-source-suggestions" aria-label={t('guidance.title')}><div className="work-section-title"><h2><BookOpen size={18}/>{t('guidance.title')}</h2><Link to={`/sources?case_id=${record.id}`}>{t('guidance.directory')}</Link></div>
  <p>{t('guidance.intro')}</p>
  {loading?<p role="status">{t('common.loading')}</p>:error?<p role="alert">{error}</p>:suggestions.length?<div className="work-source-list">{suggestions.map(source=><article key={source.id}><strong>{source.organization}</strong><span>{record.region&&source.region===record.region?t('guidance.sectorRegion',{region:record.region}):t('guidance.sector')}</span><small>{source.verification_status==='verifiees'?t('source.statusVerified'):source.verification_status==='partiellement_verifiees'?t('source.statusPartial'):t('source.statusRefresh')}{source.last_checked_at?` · ${source.last_checked_at}`:''}</small>{(source.reference_url||source.website_url)&&<a href={source.reference_url||source.website_url||''} target="_blank" rel="noopener noreferrer">{t('guidance.reference')} <ExternalLink size={14}/></a>}</article>)}</div>:<p>{t('guidance.empty')}</p>}
  <small>{t('guidance.warning')}</small>
 </section>;
}
