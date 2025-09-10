<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		href,
		children,
		...restProps
	} = $props();

	let linkClass = $derived(
		cn(
			"transition-colors hover:text-foreground",
			className
		)
	);
</script>

<a {href} class={linkClass} {...restProps}>
	{@render children?.()}
</a>