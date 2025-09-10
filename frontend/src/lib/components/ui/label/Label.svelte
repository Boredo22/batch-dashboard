<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		for: htmlFor,
		children,
		...restProps
	} = $props();

	let labelClass = $derived(
		cn(
			"text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
			className
		)
	);
</script>

<label class={labelClass} for={htmlFor} {...restProps}>
	{@render children?.()}
</label>