// src/dashboard.js - Dashboard page entry point (FIXED)
import Dashboard from './routes/Dashboard.svelte';

const app = new Dashboard({
  target: document.getElementById('app')
});

export default app;