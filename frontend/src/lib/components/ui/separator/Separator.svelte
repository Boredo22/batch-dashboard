<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		orientation = "horizontal",
		decorative = true,
		...restProps
	} = $props();

	let separatorClass = $derived(
		cn(
			"shrink-0 bg-border",
			orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
			className
		)
	);
</script>

<div
	class={separatorClass}
	data-orientation={orientation}
	role={decorative ? "none" : "separator"}
	aria-orientation={decorative ? undefined : orientation}
	{...restProps}
></div>