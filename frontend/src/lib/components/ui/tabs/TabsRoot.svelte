<script>
	import { Tabs as TabsPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		value = $bindable(undefined),
		orientation = "horizontal",
		children,
		...restProps
	} = $props();

	let tabsClass = $derived(cn("", className));
</script>

{#if value !== undefined}
<TabsPrimitive.Root class={tabsClass} bind:value {orientation} {...restProps}>
	{@render children?.()}
</TabsPrimitive.Root>
{:else}
<TabsPrimitive.Root class={tabsClass} {orientation} {...restProps}>
	{@render children?.()}
</TabsPrimitive.Root>
{/if}