<script>
  import { cn } from "$lib/utils.js";
  import { badgeVariants } from "./index.js";

  let {
    class: className = "",
    variant = "default",
    children,
    ...restProps
  } = $props();
</script>

<span 
  class={cn(badgeVariants({ variant }), className)} 
  {...restProps}
>
  {@render children?.()}
</span>