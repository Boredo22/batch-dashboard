<script>
  import * as Sidebar from "$lib/components/ui/sidebar/index.js";
  import { SidebarInset } from "$lib/components/ui/sidebar/index.js";
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

<Sidebar.Sidebar>
  <AppSidebar {systemStatus} />
  <SidebarInset>
    <SiteHeader {title} {subtitle} {systemStatus} {breadcrumbs} />
    <div class="flex flex-1 flex-col gap-4 p-4 pt-0">
      {@render children()}
    </div>
  </SidebarInset>
</Sidebar.Sidebar>