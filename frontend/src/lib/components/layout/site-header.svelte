<script>
  import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";

  let {
    title = "Dashboard",
    subtitle = "",
    systemStatus = "disconnected",
    breadcrumbs = []
  } = $props();
</script>

<header
  class="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-3 border-b border-border bg-background/70 px-4 backdrop-blur-md md:px-6"
>
  <Sidebar.Trigger class="-ml-1 text-muted-foreground hover:text-foreground" />
  <Separator orientation="vertical" class="mr-1 h-6" />

  <div class="flex min-w-0 flex-col justify-center">
    {#if breadcrumbs.length > 1}
      <Breadcrumb.Root>
        <Breadcrumb.List>
          {#each breadcrumbs as crumb, i}
            <Breadcrumb.Item class="hidden sm:block">
              {#if crumb.href}
                <Breadcrumb.Link href={crumb.href} class="text-xs text-muted-foreground">
                  {crumb.title}
                </Breadcrumb.Link>
              {:else}
                <Breadcrumb.Page class="text-xs text-muted-foreground">
                  {crumb.title}
                </Breadcrumb.Page>
              {/if}
            </Breadcrumb.Item>
            {#if i < breadcrumbs.length - 1}
              <Breadcrumb.Separator class="hidden sm:block" />
            {/if}
          {/each}
        </Breadcrumb.List>
      </Breadcrumb.Root>
    {/if}
    <h1 class="truncate text-base font-semibold leading-tight tracking-tight text-foreground">
      {title}
    </h1>
    {#if subtitle}
      <p class="hidden truncate text-xs text-muted-foreground md:block">{subtitle}</p>
    {/if}
  </div>

  <div class="ml-auto flex items-center gap-3">
    <span class="status-badge status-{String(systemStatus).toLowerCase()}">
      {systemStatus}
    </span>
  </div>
</header>
