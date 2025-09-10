<script>
	import { Select as SelectPrimitive } from "bits-ui";

	let {
		children,
		...restProps
	} = $props();
</script>

<SelectPrimitive.Root {...restProps}>
	{@render children?.()}
</SelectPrimitive.Root>