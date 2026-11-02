import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig(({mode})=>{const env=loadEnv(mode,'.','CHECKER_');return {plugins:[react(), tailwindcss()],server:{port:Number(env.CHECKER_FRONTEND_PORT||5173),strictPort:true,proxy:{'/api':env.CHECKER_API_TARGET||'http://127.0.0.1:8000'}}}});
