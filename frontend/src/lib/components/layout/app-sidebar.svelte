<script>
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { getSystemStatus } from "$lib/stores/systemStatus.svelte.js";
  import {
    LayoutDashboard,
    FlaskConical,
    Settings,
    Activity,
    Droplets,
    Zap,
    BookOpen,
    Sprout,
    Waves,
    ClipboardCheck
  } from "@lucide/svelte/icons";

  let { systemStatus = "disconnected", currentPage = "headgrower" } = $props();

  const status = getSystemStatus();

  // Primary operational navigation
  const operationItems = [
    { title: "Dashboard", page: "headgrower", icon: LayoutDashboard },
    { title: "Nutrients", page: "nutrients", icon: FlaskConical },
    { title: "Grow Cycles", page: "grow-cycles", icon: Sprout },
    { title: "Knowledge", page: "knowledge", icon: BookOpen }
  ];

  // Engineering / diagnostics navigation
  const diagnosticItems = [
    { title: "Hardware Testing", page: "stage1", icon: Zap },
    { title: "HW Verification", page: "verify", icon: ClipboardCheck },
    { title: "Batch Fill", page: "stage2", icon: Activity },
    { title: "Settings", page: "settings", icon: Settings }
  ];

  function handleNavigation(page) {
    if (globalThis.navigateTo) {
      globalThis.navigateTo(page);
    }
  }

  // Live hardware tallies from the shared SSE store
  let relaysActive = $derived(status.relays.filter((r) => r.state).length);
  let pumpsActive = $derived(status.pumps.filter((p) => p.is_dispensing).length);
  let flowActive = $derived(
    status.flowMeters.filter((m) => m.is_monitoring || m.status === "active").length
  );

  let hardwareItems = $derived([
    { title: "Pumps", icon: Droplets, count: pumpsActive, total: status.pumps.length },
    { title: "Relays", icon: Zap, count: relaysActive, total: status.relays.length },
    { title: "Flow Meters", icon: Waves, count: flowActive, total: status.flowMeters.length }
  ]);
</script>

<Sidebar.Root variant="inset">
  <Sidebar.Header>
    <div class="flex items-center gap-2.5 px-1.5 py-2">
      <div class="brand-gradient flex size-9 items-center justify-center rounded-lg text-slate-950 shadow-md">
        <FlaskConical class="size-5" />
      </div>
      <div class="grid flex-1 text-left leading-tight">
        <span class="truncate text-sm font-semibold text-foreground">
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
      <Sidebar.GroupLabel>Operations</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each operationItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                active={currentPage === item.page}
                tooltip={item.title}
                onclick={() => handleNavigation(item.page)}
              >
                {@const Icon = item.icon}
                <Icon class="size-4 shrink-0" />
                <span>{item.title}</span>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <Sidebar.Group>
      <Sidebar.GroupLabel>Diagnostics</Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu>
          {#each diagnosticItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                active={currentPage === item.page}
                tooltip={item.title}
                onclick={() => handleNavigation(item.page)}
              >
                {@const Icon = item.icon}
                <Icon class="size-4 shrink-0" />
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
              <Sidebar.MenuButton tooltip={item.title}>
                {@const Icon = item.icon}
                <Icon class="size-4 shrink-0 {item.count > 0 ? 'text-brand' : ''}" />
                <span>{item.title}</span>
                <span class="ml-auto flex items-center gap-1 text-xs tabular-nums">
                  <span class={item.count > 0 ? "font-semibold text-brand" : "text-muted-foreground"}>
                    {item.count}
                  </span>
                  <span class="text-muted-foreground/60">/ {item.total}</span>
                </span>
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer>
    <div class="flex items-center justify-between gap-2 rounded-lg border border-border bg-card/60 px-3 py-2 group-data-[collapsible=icon]:hidden">
      <span class="text-xs font-medium text-muted-foreground">System</span>
      <span class="status-badge status-{String(systemStatus).toLowerCase()}">
        {systemStatus}
      </span>
    </div>
  </Sidebar.Footer>
</Sidebar.Root>
