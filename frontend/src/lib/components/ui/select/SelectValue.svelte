<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		placeholder = "Select...",
		children,
		...restProps
	} = $props();

	let valueClass = $derived(
		cn("text-sm truncate", className)
	);
</script>

<span class={valueClass} {...restProps}>
	{#if children}
		{@render children()}
	{:else}
		{placeholder}
	{/if}
</span>