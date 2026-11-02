import {api} from './api';

export type RegionCatalog={items:string[];national:string;unknown:string;reference_url:string};
export const loadRegions=()=>api<RegionCatalog>('/regions');
