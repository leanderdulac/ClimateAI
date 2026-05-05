import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0', // permite bind em qualquer interface (corrige EPERM em alguns ambientes)
    port: 5173,
    strictPort: true,
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
    exclude: []
  },
  build: {
    sourcemap: false,
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      },
      mangle: {
        toplevel: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/') || id.includes('node_modules/react-router-dom/')) {
            return 'vendor-react'
          }

          if (id.includes('node_modules/@radix-ui/')) {
            return 'vendor-ui'
          }

          if (id.includes('node_modules/recharts/')) {
            return 'vendor-charts'
          }

          if (id.includes('node_modules/react-leaflet/') || id.includes('node_modules/leaflet/')) {
            return 'vendor-maps'
          }

          if (id.includes('node_modules/date-fns/') || id.includes('node_modules/clsx/')) {
            return 'vendor-utils'
          }
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
})
