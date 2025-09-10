<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let listClass = $derived(
		cn("flex items-center gap-1.5", className)
	);
</script>

<ol class={listClass} {...restProps}>
	{@render children?.()}
</ol>