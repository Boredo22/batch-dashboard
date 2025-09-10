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
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <TestTube class="size-5" />
      EC/pH Monitor
      <Badge variant={ecPhMonitoring ? 'default' : 'secondary'} class="ml-auto">
        {ecPhMonitoring ? 'ACTIVE' : 'INACTIVE'}
      </Badge>
    </CardTitle>
  </CardHeader>
  <CardContent class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div class="text-center space-y-2">
        <div class="text-2xl font-bold {getValueColor(ecValue, 'ec')}">
          {ecValue.toFixed(1)}
        </div>
        <div class="text-sm text-muted-foreground">EC (µS/cm)</div>
        <div class="text-xs">
          <span class="text-green-400">●</span> 800-1200 Optimal
        </div>
      </div>
      
      <div class="text-center space-y-2">
        <div class="text-2xl font-bold {getValueColor(phValue, 'ph')}">
          {phValue.toFixed(2)}
        </div>
        <div class="text-sm text-muted-foreground">pH Level</div>
        <div class="text-xs">
          <span class="text-green-400">●</span> 5.5-6.5 Optimal
        </div>
      </div>
    </div>

    <div class="flex gap-2">
      <Button
        onclick={onStartMonitoring}
        disabled={ecPhMonitoring}
        class="flex-1"
        size="sm"
      >
        <Play class="size-4 mr-2" />
        Start Monitoring
      </Button>
      <Button
        onclick={onStopMonitoring}
        disabled={!ecPhMonitoring}
        variant="destructive"
        class="flex-1"
        size="sm"
      >
        <Square class="size-4 mr-2" />
        Stop Monitoring
      </Button>
    </div>
  </CardContent>
</Card>