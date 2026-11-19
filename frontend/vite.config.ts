import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: {
    // Send API calls to Django, so the browser sees one site and the login cookie works.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
