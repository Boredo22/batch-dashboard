<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let pageClass = $derived(
		cn("font-normal text-foreground", className)
	);
</script>

<span class={pageClass} role="link" aria-disabled="true" aria-current="page" {...restProps}>
	{@render children?.()}
</span>