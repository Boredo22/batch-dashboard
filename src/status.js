// src/status.js - Status page entry point (FIXED)
import Status from './routes/Status.svelte';

const app = new Status({
  target: document.getElementById('app')
});

export default app;