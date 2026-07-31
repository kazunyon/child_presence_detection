import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/child_presence_detection/',
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'まもるバス',
        short_name: 'まもるバス',
        description: '送迎バス置き去り防止・安全確認',
        theme_color: '#0d9488',
        background_color: '#f8fafc',
        display: 'standalone',
        lang: 'ja',
        icons: [
          { src: 'icons/mamoru-bus-icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/mamoru-bus-icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/mamoru-bus-icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      }
    })
  ]
})
