<script>
	import { Progress as ProgressPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import { progressVariants } from "./index.js";

	let {
		class: className,
		value = 0,
		max = 100,
		size = "default",
		variant = "default",
		...restProps
	} = $props();

	let progressClass = $derived(cn(progressVariants({ variant, size }), className));
	let percentage = $derived(Math.min(Math.max((value / max) * 100, 0), 100));
</script>

<ProgressPrimitive.Root
	class={progressClass}
	{value}
	{max}
	aria-label="Progress"
	{...restProps}
>
	<div class="progress-indicator" style="transform: translateX(-{100 - percentage}%)"></div>
</ProgressPrimitive.Root>

<style>
	:global(.progress-root) {
		position: relative;
		height: 0.5rem;
		width: 100%;
		overflow: hidden;
		border-radius: 9999px;
		background-color: hsl(var(--muted));
		transition: all 0.2s ease-in-out;
	}

	:global(.progress-root.progress-sm) {
		height: 0.375rem;
	}

	:global(.progress-root.progress-lg) {
		height: 0.625rem;
	}

	.progress-indicator {
		height: 100%;
		width: 100%;
		flex: 1;
		background-color: hsl(var(--primary));
		transition: transform 0.3s ease-in-out;
		border-radius: inherit;
	}

	:global(.progress-root.progress-destructive) .progress-indicator {
		background-color: hsl(var(--destructive));
	}

	:global(.progress-root.progress-success) .progress-indicator {
		background-color: hsl(var(--success, 34 197 94));
	}

	:global(.progress-root.progress-warning) .progress-indicator {
		background-color: hsl(var(--warning, 251 191 36));
	}

	:global(.progress-root.progress-purple) .progress-indicator {
		background-color: hsl(var(--purple, 139 92 246));
	}

	:global(.progress-root.progress-green) .progress-indicator {
		background-color: hsl(var(--green, 16 185 129));
	}
</style>