<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Activity, Play, Square } from "@lucide/svelte/icons";

  let {
    flowMeters = [],
    selectedFlowMeter = $bindable(""),
    flowGallons = $bindable(1.0),
    onStartFlow,
    onStopFlow
  } = $props();

  // Ensure flowMeters is always an array to prevent null reference errors
  let safeFlowMeters = $derived(Array.isArray(flowMeters) ? flowMeters : []);
  let selectedFlowMeterData = $derived(selectedFlowMeter && selectedFlowMeter !== "" ? safeFlowMeters.find(f => f.id === selectedFlowMeter) : null);
  let isFlowing = $derived(selectedFlowMeterData?.status === 'flowing');
  let progress = $derived(() => {
    if (!selectedFlowMeterData || !isFlowing) return 0;
    return (selectedFlowMeterData.current_gallons / selectedFlowMeterData.target_gallons) * 100;
  });

  function handleStartFlow() {
    if (selectedFlowMeter && flowGallons > 0) {
      onStartFlow?.(selectedFlowMeter, flowGallons);
    }
  }

  function handleStopFlow() {
    if (selectedFlowMeter) {
      onStopFlow?.(selectedFlowMeter);
    }
  }
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Activity class="size-5" />
      Flow Meter Control
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-4">
    <div class="space-y-2">
      <Label for="flow-select">Select Flow Meter</Label>
      <Select bind:value={selectedFlowMeter}>
        <SelectTrigger>
          <SelectValue placeholder={safeFlowMeters.length > 0 ? "Choose a flow meter..." : "No flow meters available"} />
        </SelectTrigger>
        <SelectContent>
          {#if safeFlowMeters.length > 0}
            {#each safeFlowMeters as flowMeter}
              <SelectItem value={flowMeter.id}>
                Flow Meter {flowMeter.id} - {flowMeter.name || 'Unnamed'}
              </SelectItem>
            {/each}
          {:else}
            <SelectItem value="" disabled>No flow meters available</SelectItem>
          {/if}
        </SelectContent>
      </Select>
    </div>

    {#if selectedFlowMeterData}
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Status</span>
          <Badge variant={selectedFlowMeterData.status === 'idle' ? 'secondary' : 'default'}>
            {selectedFlowMeterData.status.toUpperCase()}
          </Badge>
        </div>

        {#if isFlowing}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Progress</span>
              <span>{selectedFlowMeterData.current_gallons || 0} gal / {selectedFlowMeterData.target_gallons || 0} gal</span>
            </div>
            <Progress value={progress} class="h-2" />
          </div>
        {/if}

        <div class="flex gap-3">
          <div class="flex-1">
            <Label for="flow-gallons">Volume (gallons)</Label>
            <Input
              id="flow-gallons"
              type="number"
              bind:value={flowGallons}
              min="0.1"
              max="100"
              step="0.1"
              disabled={isFlowing}
            />
          </div>
          <div class="flex flex-col justify-end gap-2">
            <Button
              onclick={handleStartFlow}
              disabled={isFlowing || !selectedFlowMeter}
              size="sm"
            >
              <Play class="size-4 mr-2" />
              Start Flow
            </Button>
            <Button
              onclick={handleStopFlow}
              disabled={!isFlowing}
              variant="destructive"
              size="sm"
            >
              <Square class="size-4 mr-2" />
              Stop Flow
            </Button>
          </div>
        </div>
      </div>
    {/if}
  </CardContent>
</Card>