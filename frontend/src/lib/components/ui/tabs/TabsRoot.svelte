<script>
	import { Tabs as TabsPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		value = $bindable(),
		orientation = "horizontal",
		...restProps
	} = $props();

	let tabsClass = $derived(cn("", className));
</script>

<TabsPrimitive.Root class={tabsClass} bind:value {orientation} {...restProps}>
	{@render children?.()}
</TabsPrimitive.Root>