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
  <CardHeader class="pb-3">
    <CardTitle class="flex items-center gap-2 text-base">
      <Activity class="size-4" />
      Flow Meter Control
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-3 pb-4">
    <div class="space-y-1.5">
      <Label for="flow-select" class="text-xs">Select Flow Meter</Label>
      <Select bind:value={selectedFlowMeter}>
        <SelectTrigger class="h-11">
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
          <span class="text-xs font-medium">Status</span>
          <Badge
            variant={selectedFlowMeterData.status === 'idle' ? 'secondary' : 'default'}
            class="h-5 px-2 text-xs"
          >
            {selectedFlowMeterData.status.toUpperCase()}
          </Badge>
        </div>

        {#if isFlowing}
          <div class="space-y-1.5">
            <div class="flex justify-between text-xs">
              <span class="font-medium">Progress</span>
              <span class="font-mono">{selectedFlowMeterData.current_gallons || 0} / {selectedFlowMeterData.target_gallons || 0} gal</span>
            </div>
            <Progress value={progress} class="h-2.5" />
          </div>
        {/if}

        <!-- Tablet-optimized layout: horizontal control panel -->
        <div class="flex gap-2 items-end">
          <div class="flex-1">
            <Label for="flow-gallons" class="text-xs">Volume (gallons)</Label>
            <Input
              id="flow-gallons"
              type="number"
              bind:value={flowGallons}
              min="0.1"
              max="100"
              step="0.1"
              disabled={isFlowing}
              class="h-11 text-base"
            />
          </div>
          <Button
            onclick={handleStartFlow}
            disabled={isFlowing || !selectedFlowMeter}
            class="h-11 px-4"
          >
            <Play class="size-4 mr-1.5" />
            Start
          </Button>
          <Button
            onclick={handleStopFlow}
            disabled={!isFlowing}
            variant="destructive"
            class="h-11 px-4"
          >
            <Square class="size-4 mr-1.5" />
            Stop
          </Button>
        </div>
      </div>
    {/if}
  </CardContent>
</Card>