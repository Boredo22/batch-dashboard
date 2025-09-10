<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let descriptionClass = $derived(cn("alert-description", className));
</script>

<div
	class={descriptionClass}
	{...restProps}
>
	{@render children?.()}
</div>

<style>
	:global(.alert-description) {
		font-size: 0.875rem;
		line-height: 1.5rem;
		color: inherit;
		opacity: 0.9;
		flex: 1;
	}

	:global(.alert-description p) {
		margin: 0;
	}

	:global(.alert-description p + p) {
		margin-top: 0.5rem;
	}
</style>