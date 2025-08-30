// src/status.js - Status page entry point
import Status from './routes/Status.svelte';
import NotificationToast from './lib/components/NotificationToast.svelte';

const app = new Status({
  target: document.getElementById('app')
});

// Mount notification toast globally
const toast = new NotificationToast({
  target: document.body
});

export default app;