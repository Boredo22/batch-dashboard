<script>
	import { Button as ButtonPrimitive } from "bits-ui";
	import { buttonVariants } from "./index.js";
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		variant = "default",
		size = "default",
		children,
		...restProps
	} = $props();

	let buttonClass = $derived(cn(buttonVariants({ variant, size, className })));
</script>

<ButtonPrimitive.Root class={buttonClass} {...restProps}>
	{@render children?.()}
</ButtonPrimitive.Root>