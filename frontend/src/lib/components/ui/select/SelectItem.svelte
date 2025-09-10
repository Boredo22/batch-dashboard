<script>
	import { Select as SelectPrimitive } from "bits-ui";
	import { Check } from "@lucide/svelte";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		value,
		selected = false,
		...restProps
	} = $props();

	let itemClass = $derived(
		cn(
			"relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
			className
		)
	);
</script>

<SelectPrimitive.Item class={itemClass} {value} {...restProps}>
	<span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
		{#if selected}
			<Check class="h-4 w-4" />
		{/if}
	</span>
	<span class="block truncate">
		{@render children?.()}
	</span>
</SelectPrimitive.Item>