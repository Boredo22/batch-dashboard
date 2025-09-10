<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Droplets, Play, Square } from "@lucide/svelte/icons";

  let {
    pumps = [],
    selectedPump = $bindable(""),
    pumpAmount = $bindable(10),
    onDispensePump,
    onStopPump
  } = $props();

  // Ensure pumps is always an array to prevent null reference errors
  let safePumps = $derived(Array.isArray(pumps) ? pumps : []);
  // Convert selectedPump to string to ensure compatibility
  let selectedPumpStr = $derived(selectedPump ? String(selectedPump) : "");
  let selectedPumpData = $derived(selectedPumpStr && selectedPumpStr !== "" ? safePumps.find(p => String(p.id) === selectedPumpStr) : null);
  let isDispensing = $derived(selectedPumpData?.status === 'dispensing');
  let progress = $derived(() => {
    if (!selectedPumpData || !isDispensing) return 0;
    return (selectedPumpData.current_volume / selectedPumpData.target_volume) * 100;
  });

  function handleDispense() {
    if (selectedPump && pumpAmount > 0) {
      onDispensePump?.(selectedPump, pumpAmount);
    }
  }

  function handleStop() {
    if (selectedPump) {
      onStopPump?.(selectedPump);
    }
  }
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Droplets class="size-5" />
      Pump Control
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-4">
    <div class="space-y-2">
      <Label for="pump-select">Select Pump</Label>
      <select
        bind:value={selectedPumpStr}
        onchange={(e) => selectedPump = e.target.value ? parseInt(e.target.value) : ""}
        class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="" disabled>
          {safePumps.length > 0 ? "Choose a pump..." : "No pumps available"}
        </option>
        {#if safePumps.length > 0}
          {#each safePumps as pump}
            <option value={String(pump.id)}>
              Pump {pump.id} - {pump.name || 'Unnamed'}
            </option>
          {/each}
        {/if}
      </select>
    </div>

    {#if selectedPumpData}
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Status</span>
          <Badge variant={selectedPumpData.status === 'idle' ? 'secondary' : 'default'}>
            {selectedPumpData.status.toUpperCase()}
          </Badge>
        </div>

        {#if isDispensing}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Progress</span>
              <span>{selectedPumpData.current_volume || 0}ml / {selectedPumpData.target_volume || 0}ml</span>
            </div>
            <Progress value={progress} class="h-2" />
          </div>
        {/if}

        <div class="flex gap-3">
          <div class="flex-1">
            <Label for="pump-amount">Amount (ml)</Label>
            <Input
              id="pump-amount"
              type="number"
              bind:value={pumpAmount}
              min="1"
              max="1000"
              disabled={isDispensing}
            />
          </div>
          <div class="flex flex-col justify-end gap-2">
            <Button
              onclick={handleDispense}
              disabled={isDispensing || !selectedPump}
              size="sm"
            >
              <Play class="size-4 mr-2" />
              Dispense
            </Button>
            <Button
              onclick={handleStop}
              disabled={!isDispensing}
              variant="destructive"
              size="sm"
            >
              <Square class="size-4 mr-2" />
              Stop
            </Button>
          </div>
        </div>
      </div>
    {/if}
  </CardContent>
</Card>