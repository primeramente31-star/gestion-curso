import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El navegador del usuario no es el sandbox: todas las llamadas usan rutas
// relativas (/api, /media) y Vite las reenvía al backend Django.
export default defineConfig(({ mode }) => ({
  plugins: [react()],

  // En las pruebas (jsdom) no actúa el plugin de React sobre los .jsx,
  // por eso se activa aquí el transform automático de JSX.
  ...(mode === 'test' ? { esbuild: { jsx: 'automatic' } } : {}),

  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.jsx'],
  },

  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
}))
