import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    // 3. Add this line here
    tsconfigPaths: true,
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API requests to backend
      '/api': 'http://localhost:8000',
      '/recommend': 'http://localhost:8000',
      '/upload-inventory': 'http://localhost:8000',
      '/upload-profile': 'http://localhost:8000',
      '/inventory': 'http://localhost:8000',
      '/profile-summary': 'http://localhost:8000',
      '/refresh-palate-portrait': 'http://localhost:8000',
      '/style-affinities': 'http://localhost:8000',
      '/refresh-style-affinities': 'http://localhost:8000',
      '/debug': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  }
})
