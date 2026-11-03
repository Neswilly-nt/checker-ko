import {createContext,useCallback,useContext,useMemo,useRef,useState,type ReactNode} from 'react';
import fr from './locales/fr.json';
import mg from './locales/mg.json';
import en from './locales/en.json';

export type Locale='fr'|'mg'|'en';
const resources:Record<Locale,Record<string,string>>={fr,mg,en};
const localeName:Record<Locale,string>={fr:'Français',mg:'Malagasy',en:'English'};
const preferenceKey='checker-ko.locale';
function initialLocale():Locale{
 try{const value=localStorage.getItem(preferenceKey);if(value==='fr'||value==='mg'||value==='en')return value}catch{/* local storage can be disabled */}
 return 'fr';
}
type I18nValue={locale:Locale;setLocale:(locale:Locale)=>void;t:(key:string,values?:Record<string,string|number>)=>string;formatDate:(value:string|null|undefined,withTime?:boolean)=>string;localeName:Record<Locale,string>;errorMessage:(error:unknown)=>string};
const I18nContext=createContext<I18nValue|null>(null);

export function I18nProvider({children}:{children:ReactNode}){
 const [locale,setCurrentLocale]=useState<Locale>(initialLocale);
 const localeRef=useRef(locale);localeRef.current=locale;
 const change=(next:Locale)=>{setCurrentLocale(next);try{localStorage.setItem(preferenceKey,next)}catch{/* the active session still changes */}};
 const errorMessage=useCallback((error:unknown)=>{
  const activeLocale=localeRef.current;
  const status=typeof error==='object'&&error!==null&&'status' in error?Number((error as {status:unknown}).status):0;
  const key=status===0?'errors.offline':status===401?'errors.unauthorized':status===403?'errors.forbidden':status===404?'errors.notFound':status===413?'errors.tooLarge':status===415?'errors.unsupported':status===422?'errors.invalid':status===503?'errors.toolUnavailable':'errors.generic';
  return resources[activeLocale][key]??resources.fr[key];
 },[]);
 const value=useMemo<I18nValue>(()=>{
  const t=(key:string,values:Record<string,string|number>={})=>{
   let phrase=resources[locale][key]??resources.fr[key]??'Texte indisponible';
   for(const [name,replacement] of Object.entries(values))phrase=phrase.replaceAll(`{{${name}}}`,String(replacement));
   return phrase;
  };
  const formatDate=(value:string|null|undefined,withTime=false)=>{
   if(!value)return t('common.unknownDate');
   const date=new Date(value);
   if(Number.isNaN(date.getTime()))return value;
   return new Intl.DateTimeFormat(locale==='mg'?'mg-MG':locale==='en'?'en-GB':'fr-FR',withTime?{dateStyle:'medium',timeStyle:'short'}:{day:'2-digit',month:'short',year:'numeric'}).format(date);
  };
  return {locale,setLocale:change,t,formatDate,localeName,errorMessage};
 },[locale,errorMessage]);
 return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
export function useI18n(){const value=useContext(I18nContext);if(!value)throw new Error('I18nProvider is required');return value;}

export function Tx({id,values}:{id:string;values?:Record<string,string|number>}){const {t}=useI18n();return <>{t(id,values)}</>}
