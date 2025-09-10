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
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Zap class="size-5" />
      Relay Control
    </CardTitle>
  </CardHeader>
  <CardContent>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      {#each safeRelays as relay}
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">Relay {relay.id}</span>
            <Badge variant={relay.status === 'on' ? 'default' : 'secondary'}>
              {relay.status.toUpperCase()}
            </Badge>
          </div>
          <div class="flex gap-1">
            <Button
              size="sm"
              variant={relay.status === 'on' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'on')}
              class="flex-1"
            >
              ON
            </Button>
            <Button
              size="sm"
              variant={relay.status === 'off' ? 'default' : 'outline'}
              onclick={() => handleRelayControl(relay.id, 'off')}
              class="flex-1"
            >
              OFF
            </Button>
          </div>
        </div>
      {/each}
    </div>
  </CardContent>
</Card>