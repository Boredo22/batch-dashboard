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