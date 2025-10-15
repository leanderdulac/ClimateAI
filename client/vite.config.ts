import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: 'localhost',
    port: 3000,
    strictPort: false,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom']
  },
  build: {
    sourcemap: false,
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@radix-ui/react-popover', '@radix-ui/react-select', '@radix-ui/react-slot']
        }
      }
    }
  }
})
