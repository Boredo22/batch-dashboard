<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let labelClass = $derived(
		cn("py-1.5 pl-8 pr-2 text-sm font-semibold text-muted-foreground", className)
	);
</script>

<div class={labelClass} {...restProps}>
	{@render children?.()}
</div>