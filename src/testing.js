import { mount } from 'svelte';
import HardwareTesting from './routes/HardwareTesting.svelte';

// Mount the Hardware Testing component
const app = mount(HardwareTesting, {
  target: document.getElementById('app')
});

export default app;