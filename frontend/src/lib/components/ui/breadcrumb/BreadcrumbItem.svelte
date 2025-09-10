<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let itemClass = $derived(
		cn("flex items-center gap-1.5", className)
	);
</script>

<li class={itemClass} {...restProps}>
	{@render children?.()}
</li>