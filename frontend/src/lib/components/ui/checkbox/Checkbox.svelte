<script>
	import { Checkbox as CheckboxPrimitive } from "bits-ui";
	import { Check, Minus } from "@lucide/svelte/icons";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		checked = $bindable(false),
		indeterminate = false,
		disabled = false,
		onCheckedChange,
		...restProps
	} = $props();

	let rootClass = $derived(
		cn(
			"peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
			className
		)
	);

	function handleCheckedChange(value) {
		checked = value;
		onCheckedChange?.(value);
	}
</script>

<CheckboxPrimitive.Root
	class={rootClass}
	bind:checked
	{disabled}
	onCheckedChange={handleCheckedChange}
	{...restProps}
>
	<CheckboxPrimitive.Indicator
		class="flex items-center justify-center text-current"
	>
		{#if indeterminate}
			<Minus class="h-3.5 w-3.5" />
		{:else}
			<Check class="h-3.5 w-3.5" />
		{/if}
	</CheckboxPrimitive.Indicator>
</CheckboxPrimitive.Root>
