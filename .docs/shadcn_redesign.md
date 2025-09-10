# Complete shadcn-svelte Migration Guide for Nutrient Mixing System

## 🎯 **Project Overview**

Transform the existing Nutrient Mixing System frontend from custom CSS/components to a modern shadcn-svelte implementation while maintaining all current functionality and improving the user experience.

**Current State:**
- Svelte 5 with runes (`$state`, `$derived`, `$effect`)
- Custom CSS styling with dark theme
- Three main pages: Dashboard, Stage2Testing, Settings
- Hardware control components (pumps, relays, flow meters, EC/pH)
- Real-time data updates via REST API

**Target State:**
- Professional shadcn-svelte UI components
- Consistent design system with Tailwind CSS
- Improved responsive design
- Modern dashboard layout with sidebar navigation
- Enhanced accessibility and user experience

---

## 📋 **Phase 1: Project Setup & Configuration**

### 1.1 Install shadcn-svelte Dependencies

```bash
cd frontend

# Install shadcn-svelte
npx shadcn-svelte@latest init
# Select: TypeScript: No (keep current JS setup)
# Select: Tailwind: Yes
# Select: Style: default
# Select: Base color: slate

# Install Svelte 5 compatible dependencies
npm install bits-ui@latest svelte-sonner@latest @lucide/svelte@latest mode-watcher@latest tailwindcss-animate
```

### 1.2 Update Configuration Files

**Create `frontend/components.json`:**
```json
{
  "$schema": "https://shadcn-svelte.com/schema.json",
  "style": "default",
  "tailwind": {
    "css": "src/app.css",
    "baseColor": "slate"
  },
  "aliases": {
    "components": "$lib/components",
    "utils": "$lib/utils",
    "ui": "$lib/components/ui",
    "hooks": "$lib/hooks",
    "lib": "$lib"
  },
  "typescript": false,
  "registry": "https://shadcn-svelte.com/registry"
}
```

**Update `frontend/tailwind.config.js`:**
```js
import tailwindcssAnimate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      colors: {
        // Custom brand colors (keep existing cyan/teal theme)
        brand: {
          primary: "#06b6d4", // cyan-500
          secondary: "#22d3ee", // cyan-400
          accent: "#0891b2", // cyan-600
        },
        // shadcn color system
        border: "hsl(var(--border) / <alpha-value>)",
        input: "hsl(var(--input) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        background: "hsl(var(--background) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        primary: {
          DEFAULT: "hsl(var(--primary) / <alpha-value>)",
          foreground: "hsl(var(--primary-foreground) / <alpha-value>)"
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary) / <alpha-value>)",
          foreground: "hsl(var(--secondary-foreground) / <alpha-value>)"
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive) / <alpha-value>)",
          foreground: "hsl(var(--destructive-foreground) / <alpha-value>)"
        },
        muted: {
          DEFAULT: "hsl(var(--muted) / <alpha-value>)",
          foreground: "hsl(var(--muted-foreground) / <alpha-value>)"
        },
        accent: {
          DEFAULT: "hsl(var(--accent) / <alpha-value>)",
          foreground: "hsl(var(--accent-foreground) / <alpha-value>)"
        },
        popover: {
          DEFAULT: "hsl(var(--popover) / <alpha-value>)",
          foreground: "hsl(var(--popover-foreground) / <alpha-value>)"
        },
        card: {
          DEFAULT: "hsl(var(--card) / <alpha-value>)",
          foreground: "hsl(var(--card-foreground) / <alpha-value>)"
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)"
      }
    }
  },
  plugins: [tailwindcssAnimate]
};
```

**Create/Update `frontend/src/app.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 84% 4.9%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
    --radius: 0.5rem;
  }
}

/* Custom brand styles */
.brand-gradient {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.status-badge {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.status-connected {
  @apply bg-green-900/20 text-green-400 border border-green-900/30;
}

.status-disconnected {
  @apply bg-red-900/20 text-red-400 border border-red-900/30;
}

.status-error {
  @apply bg-orange-900/20 text-orange-400 border border-orange-900/30;
}
```

### 1.3 Install Core shadcn Components

```bash
# Layout & Navigation
npx shadcn-svelte@latest add sidebar
npx shadcn-svelte@latest add breadcrumb
npx shadcn-svelte@latest add separator

# Content Components
npx shadcn-svelte@latest add card
npx shadcn-svelte@latest add badge
npx shadcn-svelte@latest add button
npx shadcn-svelte@latest add alert

# Form Components
npx shadcn-svelte@latest add input
npx shadcn-svelte@latest add label
npx shadcn-svelte@latest add switch
npx shadcn-svelte@latest add select
npx shadcn-svelte@latest add textarea

# Data Display
npx shadcn-svelte@latest add data-table
npx shadcn-svelte@latest add progress
npx shadcn-svelte@latest add tabs

# Overlays
npx shadcn-svelte@latest add dialog
npx shadcn-svelte@latest add toast
```

---

## 📁 **Phase 2: New File Structure**

### 2.1 Create New Directory Structure

```
frontend/src/
├── lib/
│   ├── components/
│   │   ├── ui/ (shadcn components - auto-generated)
│   │   ├── layout/
│   │   │   ├── app-sidebar.svelte
│   │   │   ├── site-header.svelte
│   │   │   └── dashboard-layout.svelte
│   │   ├── hardware/
│   │   │   ├── relay-control-card.svelte
│   │   │   ├── pump-control-card.svelte
│   │   │   ├── flow-meter-card.svelte
│   │   │   ├── ecph-monitor-card.svelte
│   │   │   └── system-log-card.svelte
│   │   └── settings/
│   │       ├── tank-configuration-card.svelte
│   │       ├── nutrient-settings-card.svelte
│   │       └── developer-settings-card.svelte
│   └── utils.js
├── routes/ (or keep as root-level pages)
│   ├── dashboard.svelte
│   ├── stage2.svelte
│   └── settings.svelte
├── App.svelte (updated with new layout)
└── main.js
```

---

## 🎨 **Phase 3: Layout Components**

### 3.1 Create App Sidebar Component

**Create `frontend/src/lib/components/layout/app-sidebar.svelte`:**
```svelte
<script>
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { 
    LayoutDashboard,
    FlaskConical,
    Settings,
    Activity,
    Droplets,
    Zap
  } from "@lucide/svelte/icons";

  let { systemStatus = "disconnected" } = $props();

  const menuItems = [
    {
      title: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      description: "Hardware testing & control"
    },
    {
      title: "Stage 2 Testing",
      href: "/stage2", 
      icon: FlaskConical,
      description: "Complete job processes"
    },
    {
      title: "Settings",
      href: "/settings",
      icon: Settings,
      description: "System configuration"
    }
  ];

  const hardwareItems = [
    { title: "Pumps", icon: Droplets, count: 0 },
    { title: "Relays", icon: Zap, count: 0 },
    { title: "Flow Meters", icon: Activity, count: 0 }
  ];
</script>

<Sidebar.Root variant="inset">
  <Sidebar.Header>
    <div class="flex items-center gap-2 px-2 py-2">
      <div class="flex size-8 items-center justify-center rounded-md bg-brand-primary text-white">
        <FlaskConical class="size-4" />
      </div>
      <div class="grid flex-1 text-left text-sm leading-tight">
        <span class="truncate font-semibold text-foreground">
          Nutrient System
        </span>
        <span class="truncate text-xs text-muted-foreground">
          Control Panel
        </span>
      </div>
    </div>
  </Sidebar.Header>

  <Sidebar.Content>
    <Sidebar.Group>
      <Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each menuItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton>
                <svelte:component this={item.icon} class="size-4" />
                <span>{item.title}</span>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <Sidebar.Group class="group-data-[collapsible=icon]:hidden">
      <Sidebar.GroupLabel>Hardware Status</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each hardwareItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton>
                <svelte:component this={item.icon} class="size-4" />
                <span>{item.title}</span>
                <Badge variant="secondary" class="ml-auto">
                  {item.count}
                </Badge>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer>
    <div class="flex items-center gap-2 p-2">
      <div class="flex-1">
        <div class="text-sm font-medium">System Status</div>
        <Badge class="status-badge status-{systemStatus.toLowerCase()}">
          {systemStatus}
        </Badge>
      </div>
    </div>
  </Sidebar.Footer>
</Sidebar.Root>
```

### 3.2 Create Site Header Component

**Create `frontend/src/lib/components/layout/site-header.svelte`:**
```svelte
<script>
  import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";

  let { 
    title = "Dashboard",
    subtitle = "",
    systemStatus = "disconnected",
    breadcrumbs = []
  } = $props();
</script>

<header class="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
  <div class="flex items-center gap-2 px-4">
    <Sidebar.Trigger class="-ml-1" />
    <Separator orientation="vertical" class="mr-2 h-4" />
    
    {#if breadcrumbs.length > 0}
      <Breadcrumb.Root>
        <Breadcrumb.List>
          {#each breadcrumbs as crumb, i}
            <Breadcrumb.Item class="hidden md:block">
              {#if crumb.href}
                <Breadcrumb.Link href={crumb.href}>{crumb.title}</Breadcrumb.Link>
              {:else}
                <Breadcrumb.Page>{crumb.title}</Breadcrumb.Page>
              {/if}
            </Breadcrumb.Item>
            {#if i < breadcrumbs.length - 1}
              <Breadcrumb.Separator class="hidden md:block" />
            {/if}
          {/each}
        </Breadcrumb.List>
      </Breadcrumb.Root>
    {:else}
      <div class="flex flex-col">
        <h1 class="text-lg font-semibold">{title}</h1>
        {#if subtitle}
          <p class="text-sm text-muted-foreground">{subtitle}</p>
        {/if}
      </div>
    {/if}
  </div>

  <div class="ml-auto px-4">
    <Badge class="status-badge status-{systemStatus.toLowerCase()}">
      {systemStatus}
    </Badge>
  </div>
</header>
```

### 3.3 Create Dashboard Layout Component

**Create `frontend/src/lib/components/layout/dashboard-layout.svelte`:**
```svelte
<script>
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import AppSidebar from "./app-sidebar.svelte";
  import SiteHeader from "./site-header.svelte";

  let { 
    children,
    title = "Dashboard",
    subtitle = "",
    systemStatus = "disconnected",
    breadcrumbs = []
  } = $props();
</script>

<Sidebar.Provider>
  <AppSidebar {systemStatus} />
  <Sidebar.Inset>
    <SiteHeader {title} {subtitle} {systemStatus} {breadcrumbs} />
    <div class="flex flex-1 flex-col gap-4 p-4 pt-0">
      {@render children()}
    </div>
  </Sidebar.Inset>
</Sidebar.Provider>
```

---

## 🔧 **Phase 4: Hardware Control Components**

### 4.1 Relay Control Card

**Create `frontend/src/lib/components/hardware/relay-control-card.svelte`:**
```svelte
<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Zap } from "@lucide/svelte/icons";

  let { relays = [], onRelayControl } = $props();

  function handleRelayControl(relayId, action) {
    onRelayControl?.(relayId, action);
  }
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Zap class="size-5" />
      Relay Control
    </CardTitle>
  </CardHeader>
  <CardContent>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      {#each relays as relay}
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">Relay {relay.id}</span>
            <Badge variant={relay.status === 'on' ? 'default' : 'secondary'}>
              {relay.status.toUpperCase()}
            </Badge>
          </div>
          <div class="flex gap-1">
            <Button
              size="sm"
              variant={relay.status === 'on' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'on')}
              class="flex-1"
            >
              ON
            </Button>
            <Button
              size="sm"
              variant={relay.status === 'off' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'off')}
              class="flex-1"
            >
              OFF
            </Button>
          </div>
        </div>
      {/each}
    </div>
  </CardContent>
</Card>
```

### 4.2 Pump Control Card

**Create `frontend/src/lib/components/hardware/pump-control-card.svelte`:**
```svelte
<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Droplets, Play, Square } from "@lucide/svelte/icons";

  let { 
    pumps = [], 
    selectedPump = null,
    pumpAmount = 10,
    onDispensePump,
    onStopPump 
  } = $props();

  let selectedPumpData = $derived(pumps.find(p => p.id === selectedPump));
  let isDispensing = $derived(selectedPumpData?.status === 'dispensing');
  let progress = $derived(() => {
    if (!selectedPumpData || !isDispensing) return 0;
    return (selectedPumpData.current_volume / selectedPumpData.target_volume) * 100;
  });

  function handleDispense() {
    if (selectedPump && pumpAmount > 0) {
      onDispensePump?.(selectedPump, pumpAmount);
    }
  }

  function handleStop() {
    if (selectedPump) {
      onStopPump?.(selectedPump);
    }
  }
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Droplets class="size-5" />
      Pump Control
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-4">
    <div class="space-y-2">
      <Label for="pump-select">Select Pump</Label>
      <Select bind:selected={selectedPump}>
        <SelectTrigger>
          <SelectValue placeholder="Choose a pump..." />
        </SelectTrigger>
        <SelectContent>
          {#each pumps as pump}
            <SelectItem value={pump.id}>
              Pump {pump.id} - {pump.name || 'Unnamed'}
            </SelectItem>
          {/each}
        </SelectContent>
      </Select>
    </div>

    {#if selectedPumpData}
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Status</span>
          <Badge variant={selectedPumpData.status === 'idle' ? 'secondary' : 'default'}>
            {selectedPumpData.status.toUpperCase()}
          </Badge>
        </div>

        {#if isDispensing}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Progress</span>
              <span>{selectedPumpData.current_volume || 0}ml / {selectedPumpData.target_volume || 0}ml</span>
            </div>
            <Progress value={progress} class="h-2" />
          </div>
        {/if}

        <div class="flex gap-3">
          <div class="flex-1">
            <Label for="pump-amount">Amount (ml)</Label>
            <Input
              id="pump-amount"
              type="number"
              bind:value={pumpAmount}
              min="1"
              max="1000"
              disabled={isDispensing}
            />
          </div>
          <div class="flex flex-col justify-end gap-2">
            <Button
              onclick={handleDispense}
              disabled={isDispensing || !selectedPump}
              size="sm"
            >
              <Play class="size-4 mr-2" />
              Dispense
            </Button>
            <Button
              onclick={handleStop}
              disabled={!isDispensing}
              variant="destructive"
              size="sm"
            >
              <Square class="size-4 mr-2" />
              Stop
            </Button>
          </div>
        </div>
      </div>
    {/if}
  </CardContent>
</Card>
```

### 4.3 EC/pH Monitor Card

**Create `frontend/src/lib/components/hardware/ecph-monitor-card.svelte`:**
```svelte
<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { TestTube, Play, Square } from "@lucide/svelte/icons";

  let { 
    ecValue = 0,
    phValue = 0,
    ecPhMonitoring = false,
    onStartMonitoring,
    onStopMonitoring 
  } = $props();

  function getValueColor(value, type) {
    if (type === 'ec') {
      if (value < 800) return 'text-blue-400';
      if (value > 1200) return 'text-red-400';
      return 'text-green-400';
    } else {
      if (value < 5.5) return 'text-blue-400';
      if (value > 6.5) return 'text-red-400';
      return 'text-green-400';
    }
  }
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <TestTube class="size-5" />
      EC/pH Monitor
      <Badge variant={ecPhMonitoring ? 'default' : 'secondary'} class="ml-auto">
        {ecPhMonitoring ? 'ACTIVE' : 'INACTIVE'}
      </Badge>
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div class="text-center space-y-2">
        <div class="text-2xl font-bold {getValueColor(ecValue, 'ec')}">
          {ecValue.toFixed(1)}
        </div>
        <div class="text-sm text-muted-foreground">EC (µS/cm)</div>
        <div class="text-xs">
          <span class="text-green-400">●</span> 800-1200 Optimal
        </div>
      </div>
      
      <div class="text-center space-y-2">
        <div class="text-2xl font-bold {getValueColor(phValue, 'ph')}">
          {phValue.toFixed(2)}
        </div>
        <div class="text-sm text-muted-foreground">pH Level</div>
        <div class="text-xs">
          <span class="text-green-400">●</span> 5.5-6.5 Optimal
        </div>
      </div>
    </div>

    <div class="flex gap-2">
      <Button
        onclick={onStartMonitoring}
        disabled={ecPhMonitoring}
        class="flex-1"
        size="sm"
      >
        <Play class="size-4 mr-2" />
        Start Monitoring
      </Button>
      <Button
        onclick={onStopMonitoring}
        disabled={!ecPhMonitoring}
        variant="destructive"
        class="flex-1"
        size="sm"
      >
        <Square class="size-4 mr-2" />
        Stop Monitoring
      </Button>
    </div>
  </CardContent>
</Card>
```

### 4.4 System Log Card

**Create `frontend/src/lib/components/hardware/system-log-card.svelte`:**
```svelte
<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { ScrollText, Download, Trash2 } from "@lucide/svelte/icons";

  let { logs = [], onClearLogs } = $props();

  function getLogLevel(message) {
    if (message.toLowerCase().includes('error')) return 'error';
    if (message.toLowerCase().includes('warning')) return 'warning';
    if (message.toLowerCase().includes('success')) return 'success';
    return 'info';
  }

  function exportLogs() {
    const logText = logs.map(log => `[${log.time}] ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<Card class="flex flex-col h-full">
  <CardHeader>
    <div class="flex items-center justify-between">
      <CardTitle class="flex items-center gap-2">
        <ScrollText class="size-5" />
        System Log
        <Badge variant="secondary">{logs.length}</Badge>
      </CardTitle>
      <div class="flex gap-2">
        <Button size="sm" variant="outline" onclick={exportLogs} disabled={logs.length === 0}>
          <Download class="size-4" />
        </Button>
        <Button size="sm" variant="outline" onclick={onClearLogs} disabled={logs.length === 0}>
          <Trash2 class="size-4" />
        </Button>
      </div>
    </div>
  </CardHeader>
  <CardContent class="flex-1 min-h-0">
    <div class="space-y-2 h-full overflow-y-auto">
      {#each logs as log}
        <div class="flex items-start gap-2 text-sm p-2 rounded border">
          <Badge 
            variant={getLogLevel(log.message) === 'error' ? 'destructive' : 
                    getLogLevel(log.message) === 'warning' ? 'outline' : 'secondary'}
            class="text-xs shrink-0"
          >
            {log.time}
          </Badge>
          <span class="flex-1 font-mono text-xs break-all">
            {log.message}
          </span>
        </div>
      {:else}
        <div class="text-center text-muted-foreground py-8">
          No log entries yet
        </div>
      {/each}
    </div>
  </CardContent>
</Card>
```

---

## 📄 **Phase 5: Updated Main Pages**

### 5.1 Update App.svelte

**Update `frontend/src/App.svelte`:**
```svelte
<script>
  import { onMount } from 'svelte';
  import DashboardLayout from '$lib/components/layout/dashboard-layout.svelte';
  import Dashboard from './Dashboard.svelte';
  import Stage2Testing from './Stage2Testing.svelte';
  import Settings from './Settings.svelte';

  let currentPage = $state('dashboard');
  let systemStatus = $state('disconnected');

  async function fetchSystemStatus() {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        systemStatus = data.status || 'disconnected';
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      systemStatus = 'error';
    }
  }

  onMount(() => {
    fetchSystemStatus();
    // Poll system status every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  });

  function getPageConfig() {
    switch (currentPage) {
      case 'dashboard':
        return {
          title: 'Hardware Testing Dashboard',
          subtitle: 'Individual component testing and control',
          breadcrumbs: [{ title: 'Dashboard' }]
        };
      case 'stage2':
        return {
          title: 'Stage 2 Testing',
          subtitle: 'Complete job process testing',
          breadcrumbs: [{ title: 'Stage 2 Testing' }]
        };
      case 'settings':
        return {
          title: 'System Settings',
          subtitle: 'Configuration and preferences',
          breadcrumbs: [{ title: 'Settings' }]
        };
      default:
        return {
          title: 'Nutrient Mixing System',
          subtitle: '',
          breadcrumbs: []
        };
    }
  }

  let pageConfig = $derived(getPageConfig());
</script>

<div class="min-h-screen bg-background text-foreground">
  <DashboardLayout 
    title={pageConfig.title}
    subtitle={pageConfig.subtitle}
    {systemStatus}
    breadcrumbs={pageConfig.breadcrumbs}
  >
    {#snippet children()}
      {#if currentPage === 'dashboard'}
        <Dashboard />
      {:else if currentPage === 'stage2'}
        <Stage2Testing />
      {:else if currentPage === 'settings'}
        <Settings />
      {/if}
    {/snippet}
  </DashboardLayout>
</div>
```

### 5.2 Update Dashboard.svelte

**Update `frontend/src/Dashboard.svelte`:**
```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import RelayControlCard from '$lib/components/hardware/relay-control-card.svelte';
  import PumpControlCard from '$lib/components/hardware/pump-control-card.svelte';
  import FlowMeterCard from '$lib/components/hardware/flow-meter-card.svelte';
  import ECPHMonitorCard from '$lib/components/hardware/ecph-monitor-card.svelte';
  import SystemLogCard from '$lib/components/hardware/system-log-card.svelte';

  // State using Svelte 5 runes
  let relays = $state([]);
  let pumps = $state([]);
  let flowMeters = $state([]);
  let logs = $state([]);
  let selectedPump = $state(null);
  let selectedFlowMeter = $state(null);
  let pumpAmount = $state(10);
  let flowGallons = $state(1.0);
  let ecValue = $state(0);
  let phValue = $state(0);
  let ecPhMonitoring = $state(false);

  let statusInterval;

  // API functions (keep existing logic)
  async function fetchHardwareData() {
    // ... existing fetch logic
  }

  async function controlRelay(relayId, action) {
    // ... existing control logic
  }

  async function dispensePump(pumpId, amount) {
    // ... existing dispense logic
  }

  async function stopPump(pumpId) {
    // ... existing stop logic
  }

  async function startFlow(flowMeterId, gallons) {
    // ... existing flow logic
  }

  async function stopFlow(flowMeterId) {
    // ... existing stop logic
  }

  async function startEcPhMonitoring() {
    // ... existing monitoring logic
  }

  async function stopEcPhMonitoring() {
    // ... existing stop logic
  }

  function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    logs = [{ time: timestamp, message }, ...logs].slice(0, 100);
  }

  function clearLogs() {
    logs = [];
  }

  onMount(async () => {
    addLog('System starting...');
    await fetchHardwareData();
    
    statusInterval = setInterval(async () => {
      // Poll for hardware updates
    }, 2000);
    
    if (pumps.length > 0) selectedPump = pumps[0].id;
    if (flowMeters.length > 0) selectedFlowMeter = flowMeters[0].id;
  });

  onDestroy(() => {
    if (statusInterval) clearInterval(statusInterval);
  });
</script>

<!-- Main dashboard grid -->
<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  <!-- Hardware Controls - Takes up 2 columns on large screens -->
  <div class="lg:col-span-2 space-y-4">
    <RelayControlCard {relays} onRelayControl={controlRelay} />
    
    <div class="grid gap-4 md:grid-cols-2">
      <PumpControlCard 
        {pumps} 
        bind:selectedPump 
        bind:pumpAmount 
        onDispensePump={dispensePump} 
        onStopPump={stopPump} 
      />
      
      <FlowMeterCard
        {flowMeters}
        bind:selectedFlowMeter
        bind:flowGallons
        onStartFlow={startFlow}
        onStopFlow={stopFlow}
      />
    </div>
    
    <ECPHMonitorCard
      {ecValue}
      {phValue}
      {ecPhMonitoring}
      onStartMonitoring={startEcPhMonitoring}
      onStopMonitoring={stopEcPhMonitoring}
    />
  </div>

  <!-- System Log - Takes up 1 column -->
  <div class="lg:col-span-1">
    <SystemLogCard {logs} onClearLogs={clearLogs} />
  </div>
</div>
```

---

## ⚙️ **Phase 6: Settings Page Redesign**

### 6.1 Update Settings.svelte

**Update `frontend/src/Settings.svelte`:**
```svelte
<script>
  import { onMount } from 'svelte';
  import { Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Switch } from "$lib/components/ui/switch/index.js";
  import { Textarea } from "$lib/components/ui/textarea/index.js";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import { 
    User, 
    Code, 
    Plus, 
    Trash2, 
    Save,
    Settings as SettingsIcon,
    AlertCircle 
  } from "@lucide/svelte/icons";

  let userSettings = $state({});
  let devSettings = $state({});
  let loading = $state(true);
  let saving = $state(false);
  let saveMessage = $state('');

  async function loadSettings() {
    try {
      const [userResponse, devResponse] = await Promise.all([
        fetch('/api/settings/user'),
        fetch('/api/settings/developer')
      ]);
      
      if (userResponse.ok) {
        userSettings = await userResponse.json();
      }
      if (devResponse.ok) {
        devSettings = await devResponse.json();
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      loading = false;
    }
  }

  async function saveSettings() {
    saving = true;
    try {
      const [userResponse, devResponse] = await Promise.all([
        fetch('/api/settings/user', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userSettings)
        }),
        fetch('/api/settings/developer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(devSettings)
        })
      ]);

      if (userResponse.ok && devResponse.ok) {
        saveMessage = 'Settings saved successfully!';
      } else {
        saveMessage = 'Error saving settings. Please try again.';
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      saveMessage = 'Error saving settings. Please try again.';
    } finally {
      saving = false;
      setTimeout(() => saveMessage = '', 3000);
    }
  }

  function addTank() {
    const newId = Object.keys(userSettings.tanks || {}).length + 1;
    userSettings.tanks = {
      ...userSettings.tanks,
      [newId]: {
        name: `Tank ${newId}`,
        capacity_gallons: 100,
        fill_relay: 0,
        send_relay: 0,
        mix_relays: []
      }
    };
  }

  function removeTank(tankId) {
    const { [tankId]: removed, ...rest } = userSettings.tanks;
    userSettings.tanks = rest;
  }

  function addMixRelay(tankId) {
    const tank = userSettings.tanks[tankId];
    if (tank) {
      tank.mix_relays = [...(tank.mix_relays || []), 0];
      userSettings.tanks = { ...userSettings.tanks };
    }
  }

  function removeMixRelay(tankId, index) {
    const tank = userSettings.tanks[tankId];
    if (tank && tank.mix_relays) {
      tank.mix_relays.splice(index, 1);
      userSettings.tanks = { ...userSettings.tanks };
    }
  }

  onMount(loadSettings);
</script>

{#if loading}
  <div class="flex items-center justify-center py-12">
    <div class="text-center space-y-4">
      <SettingsIcon class="size-8 mx-auto animate-spin text-muted-foreground" />
      <p class="text-muted-foreground">Loading settings...</p>
    </div>
  </div>
{:else}
  <div class="space-y-6">
    <!-- Header -->
    <div class="space-y-2">
      <h1 class="text-3xl font-bold tracking-tight">System Settings</h1>
      <p class="text-muted-foreground">
        Configure your nutrient mixing system settings and preferences.
      </p>
    </div>

    <!-- Save Message -->
    {#if saveMessage}
      <Alert>
        <AlertCircle class="size-4" />
        <AlertDescription>{saveMessage}</AlertDescription>
      </Alert>
    {/if}

    <!-- Settings Tabs -->
    <Tabs defaultValue="user" class="space-y-6">
      <TabsList class="grid w-full grid-cols-2">
        <TabsTrigger value="user" class="flex items-center gap-2">
          <User class="size-4" />
          User Settings
        </TabsTrigger>
        <TabsTrigger value="developer" class="flex items-center gap-2">
          <Code class="size-4" />
          Developer Settings
        </TabsTrigger>
      </TabsList>

      <!-- User Settings Tab -->
      <TabsContent value="user" class="space-y-6">
        
        <!-- Tank Configuration -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Tank Configuration</CardTitle>
              <Button onclick={addTank} size="sm">
                <Plus class="size-4 mr-2" />
                Add Tank
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {#if userSettings.tanks && Object.keys(userSettings.tanks).length > 0}
              <div class="grid gap-6 md:grid-cols-2">
                {#each Object.entries(userSettings.tanks) as [tankId, tank]}
                  <Card>
                    <CardHeader>
                      <div class="flex items-center justify-between">
                        <h4 class="font-semibold">Tank {tankId}</h4>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onclick={() => removeTank(tankId)}
                        >
                          <Trash2 class="size-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent class="space-y-4">
                      <div class="space-y-2">
                        <Label for="tank-{tankId}-name">Tank Name</Label>
                        <Input 
                          id="tank-{tankId}-name" 
                          bind:value={tank.name}
                          placeholder="Enter tank name"
                        />
                      </div>

                      <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                          <Label for="tank-{tankId}-capacity">Capacity (gal)</Label>
                          <Input 
                            id="tank-{tankId}-capacity" 
                            type="number" 
                            bind:value={tank.capacity_gallons}
                            min="1"
                          />
                        </div>
                        <div class="space-y-2">
                          <Label for="tank-{tankId}-fill">Fill Relay</Label>
                          <Input 
                            id="tank-{tankId}-fill" 
                            type="number" 
                            bind:value={tank.fill_relay}
                            min="0"
                          />
                        </div>
                      </div>

                      <div class="space-y-2">
                        <Label for="tank-{tankId}-send">Send Relay</Label>
                        <Input 
                          id="tank-{tankId}-send" 
                          type="number" 
                          bind:value={tank.send_relay}
                          min="0"
                        />
                      </div>

                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <Label>Mix Relays</Label>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onclick={() => addMixRelay(tankId)}
                          >
                            <Plus class="size-4" />
                          </Button>
                        </div>
                        {#if tank.mix_relays && tank.mix_relays.length > 0}
                          <div class="space-y-2">
                            {#each tank.mix_relays as relay, index}
                              <div class="flex items-center gap-2">
                                <Input 
                                  type="number" 
                                  bind:value={tank.mix_relays[index]}
                                  placeholder="Relay number"
                                  min="0"
                                  class="flex-1"
                                />
                                <Button 
                                  size="sm" 
                                  variant="ghost" 
                                  onclick={() => removeMixRelay(tankId, index)}
                                >
                                  <Trash2 class="size-4" />
                                </Button>
                              </div>
                            {/each}
                          </div>
                        {:else}
                          <p class="text-sm text-muted-foreground">No mix relays configured</p>
                        {/if}
                      </div>
                    </CardContent>
                  </Card>
                {/each}
              </div>
            {:else}
              <div class="text-center py-8">
                <p class="text-muted-foreground">No tanks configured</p>
                <Button onclick={addTank} class="mt-4">
                  <Plus class="size-4 mr-2" />
                  Add Your First Tank
                </Button>
              </div>
            {/if}
          </CardContent>
        </Card>

        <!-- Add more user setting cards here -->

      </TabsContent>

      <!-- Developer Settings Tab -->
      <TabsContent value="developer" class="space-y-6">
        
        <!-- Hardware Configuration -->
        <Card>
          <CardHeader>
            <CardTitle>Hardware Configuration</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Mock Mode</Label>
                <p class="text-sm text-muted-foreground">
                  Enable mock mode for development without physical hardware
                </p>
              </div>
              <Switch bind:checked={devSettings.mock_mode} />
            </div>

            <Separator />

            <div class="space-y-2">
              <Label for="serial-port">Serial Port</Label>
              <Input 
                id="serial-port" 
                bind:value={devSettings.serial_port}
                placeholder="/dev/ttyUSB0"
              />
            </div>

            <div class="space-y-2">
              <Label for="baud-rate">Baud Rate</Label>
              <Input 
                id="baud-rate" 
                type="number" 
                bind:value={devSettings.baud_rate}
                placeholder="9600"
              />
            </div>
          </CardContent>
        </Card>

        <!-- Debug Settings -->
        <Card>
          <CardHeader>
            <CardTitle>Debug Settings</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Enable Debug Logging</Label>
                <p class="text-sm text-muted-foreground">
                  Show detailed debug information in logs
                </p>
              </div>
              <Switch bind:checked={devSettings.debug_logging} />
            </div>

            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Verbose Hardware Output</Label>
                <p class="text-sm text-muted-foreground">
                  Log all hardware communication
                </p>
              </div>
              <Switch bind:checked={devSettings.verbose_hardware} />
            </div>
          </CardContent>
        </Card>

      </TabsContent>
    </Tabs>

    <!-- Save Button -->
    <div class="flex justify-end pt-6 border-t">
      <Button onclick={saveSettings} disabled={saving} size="lg">
        {#if saving}
          <SettingsIcon class="size-4 mr-2 animate-spin" />
          Saving...
        {:else}
          <Save class="size-4 mr-2" />
          Save Settings
        {/if}
      </Button>
    </div>
  </div>
{/if}
```

---

## 🚀 **Phase 7: Implementation Checklist**

### 7.1 Pre-Implementation Steps

1. **Backup Current Frontend:**
   ```bash
   cp -r frontend frontend_backup_$(date +%Y%m%d)
   ```

2. **Create Feature Branch:**
   ```bash
   git checkout -b feature/shadcn-svelte-migration
   git add .
   git commit -m "Backup before shadcn-svelte migration"
   ```

### 7.2 Implementation Order

**Week 1: Foundation Setup**
- [ ] Install shadcn-svelte and dependencies
- [ ] Update configuration files (tailwind.config.js, components.json, app.css)
- [ ] Install core shadcn components
- [ ] Create new directory structure
- [ ] Build and test basic setup

**Week 2: Layout Implementation**
- [ ] Create app-sidebar.svelte component
- [ ] Create site-header.svelte component  
- [ ] Create dashboard-layout.svelte component
- [ ] Update App.svelte with new layout
- [ ] Test navigation and responsive behavior

**Week 3: Component Migration**
- [ ] Create relay-control-card.svelte
- [ ] Create pump-control-card.svelte
- [ ] Create flow-meter-card.svelte (create this following the pattern)
- [ ] Create ecph-monitor-card.svelte
- [ ] Create system-log-card.svelte
- [ ] Update Dashboard.svelte to use new components

**Week 4: Settings & Polish**
- [ ] Update Settings.svelte with new design
- [ ] Update Stage2Testing.svelte (following similar patterns)
- [ ] Test all hardware control functionality
- [ ] Refine responsive design
- [ ] Add loading states and error handling
- [ ] Performance optimization

### 7.3 Testing Checklist

**Functionality Testing:**
- [ ] All relay controls work as before
- [ ] Pump dispensing with progress tracking works
- [ ] Flow meter controls function properly
- [ ] EC/pH monitoring displays correctly
- [ ] System logs show properly
- [ ] Settings save and load correctly
- [ ] Navigation between pages works
- [ ] Real-time data updates continue working

**UI/UX Testing:**
- [ ] Dark theme displays correctly
- [ ] Components are responsive on different screen sizes
- [ ] All interactive elements have proper hover/focus states
- [ ] Loading states display during API calls
- [ ] Error states show appropriate messages
- [ ] Typography and spacing are consistent
- [ ] Accessibility (keyboard navigation, screen readers)

**Cross-Browser Testing:**
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Mobile browsers

### 7.4 Migration Notes

**Preserving Functionality:**
- All existing API calls and data handling logic should remain unchanged
- Svelte 5 runes syntax must be used throughout
- Real-time polling intervals should continue working
- Hardware control commands should function identically

**Design System:**
- Maintain dark theme as primary
- Use cyan/teal accent colors consistently  
- Apply consistent spacing using Tailwind classes
- Ensure proper contrast ratios for accessibility
- Use shadcn component variants appropriately

**Performance Considerations:**
- Minimize bundle size by only importing needed components
- Optimize API polling to prevent unnecessary requests
- Use proper Svelte reactivity to avoid unnecessary re-renders
- Implement proper loading states to improve perceived performance

---

## 🔧 **Phase 8: Advanced Enhancements (Optional)**

### 8.1 Data Visualization
Add charts for system metrics:
```bash
npx shadcn-svelte@latest add chart
```

### 8.2 Toast Notifications
Implement system-wide notifications:
```bash
npx shadcn-svelte@latest add sonner
```

### 8.3 Dark/Light Mode Toggle
Add theme switching capability:
```bash
npx shadcn-svelte@latest add mode-toggle
```

### 8.4 Advanced Data Tables
For settings and hardware management:
```bash
npx shadcn-svelte@latest add data-table
```

---

## 📚 **Reference Links & Documentation**

- **shadcn-svelte Documentation:** https://www.shadcn-svelte.com/
- **shadcn-svelte Components:** https://www.shadcn-svelte.com/components
- **Tailwind CSS Documentation:** https://tailwindcss.com/docs
- **Svelte 5 Documentation:** https://svelte-5-preview.vercel.app/docs/introduction
- **Lucide Icons:** https://lucide.dev/icons/

---

## ⚠️ **Important Notes for Claude Code**

1. **Preserve Existing API Logic:** All fetch calls and hardware control logic should remain unchanged
2. **Use Svelte 5 Runes:** Always use `$state()`, `$derived()`, `$effect()` syntax
3. **Maintain Dark Theme:** Keep the existing dark color scheme with cyan accents
4. **Test Hardware Controls:** Ensure all hardware functionality continues to work after migration
5. **Responsive Design:** Test on multiple screen sizes during development
6. **Component Props:** Use Svelte 5's `$props()` destructuring syntax
7. **Event Handlers:** Use `onclick` instead of `on:click` for consistency
8. **CSS Classes:** Prefer Tailwind utility classes over custom CSS
9. **Loading States:** Add proper loading states for all async operations
10. **Error Handling:** Include proper error boundaries and user feedback

This migration will significantly improve the user experience while maintaining all existing functionality. The new design will be more professional, accessible, and maintainable.