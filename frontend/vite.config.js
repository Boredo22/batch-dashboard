import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve } from 'path';

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    alias: {
      '$lib': resolve('./src/lib')
    }
  },
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/main.js'
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
});