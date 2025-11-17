<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Zap } from "@lucide/svelte/icons";

  let { relays = [], onRelayControl } = $props();

  // Ensure relays is always an array to prevent null reference errors
  let safeRelays = $derived(Array.isArray(relays) ? relays : []);

  function handleRelayControl(relayId, action) {
    onRelayControl?.(relayId, action);
  }
</script>

<Card>
  <CardHeader class="pb-3">
    <CardTitle class="flex items-center justify-between text-base">
      <div class="flex items-center gap-2">
        <Zap class="size-4" />
        Relay Control
      </div>
      <Button
        size="sm"
        variant="outline"
        onclick={() => handleRelayControl(0, 'off')}
        class="h-8 text-xs"
      >
        All OFF
      </Button>
    </CardTitle>
  </CardHeader>
  <CardContent class="pb-4">
    <!-- Tablet-optimized: 3 columns for better touch targets -->
    <div class="grid grid-cols-3 gap-2">
      {#each safeRelays as relay}
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium">R{relay.id}</span>
            <Badge
              variant={relay.status === 'on' ? 'default' : 'secondary'}
              class="h-4 px-1.5 text-[10px]"
            >
              {relay.status === 'on' ? 'ON' : 'OFF'}
            </Badge>
          </div>
          <!-- Larger touch targets: min 44px height -->
          <div class="flex gap-1">
            <Button
              size="sm"
              variant={relay.status === 'on' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'on')}
              class="flex-1 h-11 text-xs font-semibold"
            >
              ON
            </Button>
            <Button
              size="sm"
              variant={relay.status === 'off' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'off')}
              class="flex-1 h-11 text-xs font-semibold"
            >
              OFF
            </Button>
          </div>
        </div>
      {/each}
    </div>
  </CardContent>
</Card>