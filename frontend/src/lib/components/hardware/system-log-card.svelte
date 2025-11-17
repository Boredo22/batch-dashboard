<script>
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { ScrollText, Download, Trash2 } from "@lucide/svelte/icons";

  let { logs = [], onClearLogs } = $props();

  function getLogLevel(message) {
    if (message.toLowerCase().includes('error')) return 'error';
    if (message.toLowerCase().includes('warning')) return 'warning';
    if (message.toLowerCase().includes('success')) return 'success';
    return 'info';
  }

  function exportLogs() {
    const logText = logs.map(log => `[${log.time}] ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }
</script>

<Card class="flex flex-col">
  <CardHeader class="pb-3">
    <div class="flex items-center justify-between">
      <CardTitle class="flex items-center gap-2 text-base">
        <ScrollText class="size-4" />
        System Log
        <Badge variant="secondary" class="h-5 px-2 text-xs">{logs.length}</Badge>
      </CardTitle>
      <div class="flex gap-1.5">
        <Button size="sm" variant="outline" onclick={exportLogs} disabled={logs.length === 0} class="h-8 w-8 p-0">
          <Download class="size-3.5" />
        </Button>
        <Button size="sm" variant="outline" onclick={onClearLogs} disabled={logs.length === 0} class="h-8 w-8 p-0">
          <Trash2 class="size-3.5" />
        </Button>
      </div>
    </div>
  </CardHeader>
  <CardContent class="pb-4">
    <!-- Tablet-optimized: Fixed height with scroll, compact spacing -->
    <div class="space-y-1.5 h-64 overflow-y-auto pr-2">
      {#each logs as log}
        <div class="flex items-start gap-1.5 text-sm p-2 rounded border bg-muted/30">
          <Badge
            variant={getLogLevel(log.message) === 'error' ? 'destructive' :
                    getLogLevel(log.message) === 'warning' ? 'outline' : 'secondary'}
            class="text-[10px] shrink-0 h-4 px-1.5"
          >
            {log.time}
          </Badge>
          <span class="flex-1 font-mono text-[11px] leading-tight break-all">
            {log.message}
          </span>
        </div>
      {:else}
        <div class="text-center text-muted-foreground py-12 text-sm">
          No log entries yet
        </div>
      {/each}
    </div>
  </CardContent>
</Card>