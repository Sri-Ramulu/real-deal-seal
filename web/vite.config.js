import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const api = process.env.RDS_API ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [sveltekit()],
  server: { proxy: { '/api': api, '/mcp': api, '/.well-known': api, '/v1': api } }
});
