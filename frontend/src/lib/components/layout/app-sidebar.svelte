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
      title: "Head Grower",
      page: "headgrower",
      icon: LayoutDashboard,
      description: "Complete growing operations"
    },
    {
      title: "Nutrients",
      page: "nutrients", 
      icon: FlaskConical,
      description: "Manual dispensing & recipes"
    },
    {
      title: "Stage 1: Hardware Testing",
      page: "stage1",
      icon: Zap,
      description: "Individual component testing"
    },
    {
      title: "Stage 2: Job Testing",
      page: "stage2", 
      icon: Activity,
      description: "Complete job processes"
    },
    {
      title: "Settings",
      page: "settings",
      icon: Settings,
      description: "System configuration"
    }
  ];

  function handleNavigation(page) {
    if (globalThis.navigateTo) {
      globalThis.navigateTo(page);
    }
  }

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
              <Sidebar.MenuButton onclick={() => handleNavigation(item.page)}>
                {@const Icon = item.icon}
                <Icon class="size-4" />
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
                {@const Icon = item.icon}
                <Icon class="size-4" />
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