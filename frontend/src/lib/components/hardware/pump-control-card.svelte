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
    selectedPump = $bindable(),
    pumpAmount = $bindable(10),
    onDispensePump,
    onStopPump 
  } = $props();

  let selectedPumpData = $derived(pumps.find(p => p.id === selectedPump));
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
      <Select bind:selected={selectedPump}>
        <SelectTrigger>
          <SelectValue placeholder="Choose a pump..." />
        </SelectTrigger>
        <SelectContent>
          {#each pumps as pump}
            <SelectItem value={pump.id}>
              Pump {pump.id} - {pump.name || 'Unnamed'}
            </SelectItem>
          {/each}
        </SelectContent>
      </Select>
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