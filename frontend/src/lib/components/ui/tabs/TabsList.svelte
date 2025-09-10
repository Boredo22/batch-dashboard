<script>
	import { Tabs as TabsPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		...restProps
	} = $props();

	let listClass = $derived(
		cn(
			"inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
			className
		)
	);
</script>

<TabsPrimitive.List class={listClass} {...restProps}>
	{@render children?.()}
</TabsPrimitive.List>