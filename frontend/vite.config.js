import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Enable Vue DevTools in development
          isCustomElement: () => false,
        },
      },
    }),
  ],
  server: {
    port: 3000,
    host: true,
    open: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  css: {
    devSourcemap: true,
  },
  define: {
    // Enable Vue DevTools in development
    __VUE_PROD_DEVTOOLS__: 'false',
    __VUE_OPTIONS_API__: 'true',
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
  },
})
