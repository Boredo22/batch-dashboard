<script>
	import { cn } from "$lib/utils.js";

	let {
		class: className,
		children,
		...restProps
	} = $props();

	let titleClass = $derived(cn("alert-title", className));
</script>

<h5
	class={titleClass}
	data-alert-title
	{...restProps}
>
	{@render children?.()}
</h5>

<style>
	:global(.alert-title) {
		margin: 0;
		margin-bottom: 0.25rem;
		font-weight: 500;
		font-size: 0.875rem;
		line-height: 1.25rem;
		color: inherit;
		letter-spacing: -0.025em;
		flex: 1;
	}
</style>