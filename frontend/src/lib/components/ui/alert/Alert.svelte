<script>
	import { cn } from "$lib/utils.js";
	import { alertVariants } from "./index.js";

	let {
		class: className,
		variant = "default",
		children,
		...restProps
	} = $props();

	let alertClass = $derived(cn(alertVariants({ variant }), className));
</script>

<div
	role="alert"
	class={alertClass}
	{...restProps}
>
	{@render children?.()}
</div>

<style>
	:global(.alert) {
		position: relative;
		width: 100%;
		border-radius: 0.375rem;
		border: 1px solid;
		padding: 1rem;
		font-size: 0.875rem;
		line-height: 1.25rem;
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		transition: all 0.2s ease-in-out;
	}

	:global(.alert-default) {
		background-color: hsl(var(--background));
		color: hsl(var(--foreground));
		border-color: hsl(var(--border));
	}

	:global(.alert-destructive) {
		border-color: hsl(var(--destructive) / 0.5);
		color: hsl(var(--destructive));
		background-color: hsl(var(--destructive) / 0.1);
	}

	:global(.alert-destructive) [data-alert-title] {
		color: hsl(var(--destructive));
	}

	:global(.alert-success) {
		border-color: hsl(var(--success, 34 197 94) / 0.5);
		color: hsl(var(--success, 34 197 94));
		background-color: hsl(var(--success, 34 197 94) / 0.1);
	}

	:global(.alert-success) [data-alert-title] {
		color: hsl(var(--success, 34 197 94));
	}

	:global(.alert-warning) {
		border-color: hsl(var(--warning, 251 191 36) / 0.5);
		color: hsl(var(--warning, 251 191 36));
		background-color: hsl(var(--warning, 251 191 36) / 0.1);
	}

	:global(.alert-warning) [data-alert-title] {
		color: hsl(var(--warning, 251 191 36));
	}

	:global(.alert-info) {
		border-color: hsl(var(--info, 59 130 246) / 0.5);
		color: hsl(var(--info, 59 130 246));
		background-color: hsl(var(--info, 59 130 246) / 0.1);
	}

	:global(.alert-info) [data-alert-title] {
		color: hsl(var(--info, 59 130 246));
	}

	:global(.alert-purple) {
		border-color: hsl(var(--purple, 139 92 246) / 0.5);
		color: hsl(var(--purple, 139 92 246));
		background-color: hsl(var(--purple, 139 92 246) / 0.1);
	}

	:global(.alert-purple) [data-alert-title] {
		color: hsl(var(--purple, 139 92 246));
	}

	:global(.alert-green) {
		border-color: hsl(var(--green, 16 185 129) / 0.5);
		color: hsl(var(--green, 16 185 129));
		background-color: hsl(var(--green, 16 185 129) / 0.1);
	}

	:global(.alert-green) [data-alert-title] {
		color: hsl(var(--green, 16 185 129));
	}

	/* Icon styling */
	:global(.alert > svg) {
		width: 1rem;
		height: 1rem;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}
</style>