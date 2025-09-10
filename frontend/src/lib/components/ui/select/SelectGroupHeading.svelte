<script>
	import { Select as SelectPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let headingClass = $derived(
		cn("py-1.5 pl-8 pr-2 text-sm font-semibold text-muted-foreground", className)
	);
</script>

<SelectPrimitive.GroupHeading class={headingClass} {...restProps}>
	{@render children?.()}
</SelectPrimitive.GroupHeading>