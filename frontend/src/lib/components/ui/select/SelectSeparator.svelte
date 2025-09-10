<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		...restProps
	} = $props();

	let separatorClass = $derived(
		cn("-mx-1 my-1 h-px bg-muted", className)
	);
</script>

<div class={separatorClass} {...restProps}></div>