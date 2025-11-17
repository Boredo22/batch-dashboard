<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { TestTube, Play, Square } from "@lucide/svelte/icons";

  let { 
    ecValue = 0,
    phValue = 0,
    ecPhMonitoring = false,
    onStartMonitoring,
    onStopMonitoring 
  } = $props();

  function getValueColor(value, type) {
    if (type === 'ec') {
      if (value < 800) return 'text-blue-400';
      if (value > 1200) return 'text-red-400';
      return 'text-green-400';
    } else {
      if (value < 5.5) return 'text-blue-400';
      if (value > 6.5) return 'text-red-400';
      return 'text-green-400';
    }
  }
</script>

<Card>
  <CardHeader class="pb-3">
    <CardTitle class="flex items-center justify-between text-base">
      <div class="flex items-center gap-2">
        <TestTube class="size-4" />
        EC/pH Monitor
      </div>
      <Badge
        variant={ecPhMonitoring ? 'default' : 'secondary'}
        class="h-5 px-2 text-xs"
      >
        {ecPhMonitoring ? 'ACTIVE' : 'INACTIVE'}
      </Badge>
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-3 pb-4">
    <div class="grid grid-cols-2 gap-3">
      <div class="text-center space-y-1.5 bg-muted/50 rounded-lg py-3">
        <div class="text-3xl font-bold tabular-nums {getValueColor(ecValue, 'ec')}">
          {ecValue.toFixed(1)}
        </div>
        <div class="text-xs font-medium text-muted-foreground">EC (µS/cm)</div>
        <div class="text-[10px] leading-tight">
          <span class="text-green-400">●</span> 800-1200
        </div>
      </div>

      <div class="text-center space-y-1.5 bg-muted/50 rounded-lg py-3">
        <div class="text-3xl font-bold tabular-nums {getValueColor(phValue, 'ph')}">
          {phValue.toFixed(2)}
        </div>
        <div class="text-xs font-medium text-muted-foreground">pH Level</div>
        <div class="text-[10px] leading-tight">
          <span class="text-green-400">●</span> 5.5-6.5
        </div>
      </div>
    </div>

    <!-- Tablet-optimized: larger touch targets -->
    <div class="flex gap-2">
      <Button
        onclick={onStartMonitoring}
        disabled={ecPhMonitoring}
        class="flex-1 h-11"
      >
        <Play class="size-4 mr-1.5" />
        Start
      </Button>
      <Button
        onclick={onStopMonitoring}
        disabled={!ecPhMonitoring}
        variant="destructive"
        class="flex-1 h-11"
      >
        <Square class="size-4 mr-1.5" />
        Stop
      </Button>
    </div>
  </CardContent>
</Card>