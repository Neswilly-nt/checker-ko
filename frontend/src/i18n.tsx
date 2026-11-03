import {cloneElement,createContext,isValidElement,useContext,useMemo,useState,type ReactNode} from 'react';
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
type I18nValue={locale:Locale;setLocale:(locale:Locale)=>void;t:(key:string,values?:Record<string,string|number>)=>string;localize:(text:string)=>string;formatDate:(value:string|null|undefined,withTime?:boolean)=>string;localeName:Record<Locale,string>;errorMessage:(error:unknown)=>string};
const I18nContext=createContext<I18nValue|null>(null);

export function I18nProvider({children}:{children:ReactNode}){
 const [locale,setCurrentLocale]=useState<Locale>(initialLocale);
 const change=(next:Locale)=>{setCurrentLocale(next);try{localStorage.setItem(preferenceKey,next)}catch{/* the active session still changes */}};
 const value=useMemo<I18nValue>(()=>{
  const t=(key:string,values:Record<string,string|number>={})=>{
   let phrase=resources[locale][key]??resources.fr[key]??'Texte indisponible';
   for(const [name,replacement] of Object.entries(values))phrase=phrase.replaceAll(`{{${name}}}`,String(replacement));
   return phrase;
  };
  const reverse=new Map<string,string>();
  for(const [key,french] of Object.entries(resources.fr))if(!reverse.has(french))reverse.set(french,resources[locale][key]??french);
  const localize=(text:string)=>reverse.get(text)??text;
  const formatDate=(value:string|null|undefined,withTime=false)=>{
   if(!value)return t('common.unknownDate');
   const date=new Date(value);
   if(Number.isNaN(date.getTime()))return value;
   return new Intl.DateTimeFormat(locale==='mg'?'mg-MG':locale==='en'?'en-GB':'fr-FR',withTime?{dateStyle:'medium',timeStyle:'short'}:{day:'2-digit',month:'short',year:'numeric'}).format(date);
  };
  const errorMessage=(error:unknown)=>{
   const status=typeof error==='object'&&error!==null&&'status' in error?Number((error as {status:unknown}).status):0;
   if(status===0)return t('errors.offline');
   if(status===401)return t('errors.unauthorized');
   if(status===403)return t('errors.forbidden');
   if(status===404)return t('errors.notFound');
   if(status===413)return t('errors.tooLarge');
   if(status===415)return t('errors.unsupported');
   if(status===422)return t('errors.invalid');
   if(status===503)return t('errors.toolUnavailable');
   return t('errors.generic');
  };
  return {locale,setLocale:change,t,localize,formatDate,localeName,errorMessage};
 },[locale]);
 return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
export function useI18n(){const value=useContext(I18nContext);if(!value)throw new Error('I18nProvider is required');return value;}

/** Bridges older views while their visible labels migrate to explicit t() calls. */
export function LocalizedTree({children}:{children:ReactNode}){
 const {localize,t}=useI18n();
 const translate=(node:ReactNode,inError=false):ReactNode=>{
  if(typeof node==='string'){
   const match=node.match(/^(\s*)([\s\S]*?)(\s*)$/);
   if(!match)return node;
   const known=localize(match[2]);
   return `${match[1]}${inError&&known===match[2]?t('errors.generic'):known}${match[3]}`;
  }
  if(Array.isArray(node))return node.map(child=>translate(child,inError));
  if(isValidElement(node)){
   const childProps=node.props as Record<string,unknown>;
   const isError=inError||childProps.role==='alert'||(typeof childProps.className==='string'&&childProps.className.split(/\s+/).includes('error'));
   const props:Record<string,unknown>={};
   for(const attr of ['aria-label','title','placeholder']){const value=childProps[attr];if(typeof value==='string')props[attr]=localize(value)}
   props.children=translate((childProps as {children?:ReactNode}).children,isError);
   return cloneElement(node,props);
  }
  return node;
 };
 return <>{translate(children)}</>;
}
