<script>
	import { Select as SelectPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let groupClass = $derived(
		cn("", className)
	);
</script>

<SelectPrimitive.Group class={groupClass} {...restProps}>
	{@render children?.()}
</SelectPrimitive.Group>