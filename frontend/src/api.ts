export class ApiError extends Error {constructor(public status:number,message:string){super(message)}}

const configuredApiUrl=(import.meta.env.VITE_CHECKER_API_URL||'').trim().replace(/\/+$/,'');
const apiBase=configuredApiUrl||'/api';

export function apiUrl(path:string):string{
  const endpoint=path.replace(/^\/api(?=\/|$)/,'');
  return `${apiBase}${endpoint.startsWith('/')?endpoint:`/${endpoint}`}`;
}

export async function api<T>(url:string, options:RequestInit={}):Promise<T>{
  const headers=new Headers(options.headers||{});
  headers.set('X-Checker-CSRF','1');
  if(options.body&&!(options.body instanceof FormData))headers.set('Content-Type','application/json');
  let response:Response;
  const requestUrl=apiUrl(url);
  const credentials=new URL(requestUrl,window.location.href).origin===window.location.origin?'same-origin':'include';
  try{response=await fetch(requestUrl,{...options,headers,credentials,cache:'no-store'})}
  catch{throw new ApiError(0,'Serveur indisponible. Vérifiez que FastAPI est lancé sur le port 8000.')}
  let payload:unknown;
  try{payload=await response.json()}catch{payload=null}
  if(!response.ok){const obj=payload as {detail?:unknown}|null;const detail=obj?.detail;
    const msg=typeof detail==='string'?detail:detail?JSON.stringify(detail):`Erreur HTTP ${response.status}`;
    throw new ApiError(response.status,msg);
  }
  return payload as T;
}

export const jsonRequest=(method:string,body:object):RequestInit=>({method,body:JSON.stringify(body)});
