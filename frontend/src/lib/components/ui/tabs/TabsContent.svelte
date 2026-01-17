<script>
	import { Tabs as TabsPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		value,
		children,
		...restProps
	} = $props();

	let contentClass = $derived(
		cn(
			"mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
			className
		)
	);
</script>

<TabsPrimitive.Content class={contentClass} {value} {...restProps}>
	{@render children?.()}
</TabsPrimitive.Content>