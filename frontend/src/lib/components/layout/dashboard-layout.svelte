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
    breadcrumbs = [],
    currentPage = "headgrower"
  } = $props();
</script>

<Sidebar.Sidebar>
  <AppSidebar {systemStatus} {currentPage} />
  <SidebarInset>
    <SiteHeader {title} {subtitle} {systemStatus} {breadcrumbs} />
    <!-- Tablet-optimized: reduced padding for more screen space -->
    <div class="flex flex-1 flex-col gap-4 p-4 pt-2 md:p-6 md:pt-3">
      {@render children()}
    </div>
  </SidebarInset>
</Sidebar.Sidebar>