<script>
	import { cn } from "$lib/utils.js";
	import { ChevronRight } from "@lucide/svelte";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let separatorClass = $derived(
		cn("flex h-3.5 w-3.5 items-center justify-center", className)
	);
</script>

<li class={separatorClass} role="presentation" aria-hidden="true" {...restProps}>
	{#if children}
		{@render children()}
	{:else}
		<ChevronRight class="h-3.5 w-3.5" />
	{/if}
</li>