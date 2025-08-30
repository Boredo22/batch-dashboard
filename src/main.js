// src/main.js - Main dashboard entry point
import Dashboard from './routes/Dashboard.svelte';
import NotificationToast from './lib/components/NotificationToast.svelte';

const app = new Dashboard({
  target: document.getElementById('app')
});

// Mount notification toast globally
const toast = new NotificationToast({
  target: document.body
});

export default app;