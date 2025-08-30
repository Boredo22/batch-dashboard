// src/main.js - Main entry point (FIXED)
import Dashboard from './routes/Dashboard.svelte';

const app = new Dashboard({
  target: document.getElementById('app')
});

export default app;