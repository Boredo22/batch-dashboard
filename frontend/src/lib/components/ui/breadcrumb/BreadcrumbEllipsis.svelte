<script>
	import { cn } from "$lib/utils.js";
	import { MoreHorizontal } from "@lucide/svelte";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let ellipsisClass = $derived(
		cn("flex h-9 w-9 items-center justify-center", className)
	);
</script>

<span class={ellipsisClass} role="presentation" aria-hidden="true" aria-label="More pages" {...restProps}>
	{#if children}
		{@render children()}
	{:else}
		<MoreHorizontal class="h-4 w-4" />
	{/if}
</span>