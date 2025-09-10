<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let breadcrumbClass = $derived(
		cn("flex items-center gap-1.5 break-words text-sm text-muted-foreground", className)
	);
</script>

<nav class={breadcrumbClass} aria-label="breadcrumb" {...restProps}>
	{@render children?.()}
</nav>