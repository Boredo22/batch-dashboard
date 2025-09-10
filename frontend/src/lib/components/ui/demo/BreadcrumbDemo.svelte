<script>
	import {
		BreadcrumbRoot,
		BreadcrumbList,
		BreadcrumbItem,
		BreadcrumbLink,
		BreadcrumbPage,
		BreadcrumbSeparator,
		BreadcrumbEllipsis,
		Separator
	} from "$lib/components/ui/index.js";
</script>

<div class="space-y-6 p-6">
	<h2 class="text-2xl font-bold text-foreground">Breadcrumb & Separator Examples</h2>
	
	<div class="space-y-4">
		<h3 class="text-lg font-semibold text-foreground">Basic Breadcrumb</h3>
		<BreadcrumbRoot>
			<BreadcrumbList>
				<BreadcrumbItem>
					<BreadcrumbLink href="/">Home</BreadcrumbLink>
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				<BreadcrumbItem>
					<BreadcrumbLink href="/dashboard">Dashboard</BreadcrumbLink>
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				<BreadcrumbItem>
					<BreadcrumbPage>Settings</BreadcrumbPage>
				</BreadcrumbItem>
			</BreadcrumbList>
		</BreadcrumbRoot>
	</div>

	<Separator />

	<div class="space-y-4">
		<h3 class="text-lg font-semibold text-foreground">Breadcrumb with Ellipsis</h3>
		<BreadcrumbRoot>
			<BreadcrumbList>
				<BreadcrumbItem>
					<BreadcrumbLink href="/">Home</BreadcrumbLink>
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				<BreadcrumbItem>
					<BreadcrumbEllipsis />
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				<BreadcrumbItem>
					<BreadcrumbLink href="/components">Components</BreadcrumbLink>
				</BreadcrumbItem>
				<BreadcrumbSeparator />
				<BreadcrumbItem>
					<BreadcrumbPage>Breadcrumb</BreadcrumbPage>
				</BreadcrumbItem>
			</BreadcrumbList>
		</BreadcrumbRoot>
	</div>

	<Separator />

	<div class="space-y-4">
		<h3 class="text-lg font-semibold text-foreground">Separators</h3>
		<div class="flex items-center space-x-4 text-sm">
			<div>Blog</div>
			<Separator orientation="vertical" class="h-4" />
			<div>Docs</div>
			<Separator orientation="vertical" class="h-4" />
			<div>Source</div>
		</div>
		
		<Separator />
		
		<div class="text-sm text-muted-foreground">
			Horizontal separator above, vertical separators in the navigation.
		</div>
	</div>
</div>