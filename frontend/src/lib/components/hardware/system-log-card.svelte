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

<Card class="flex flex-col h-full">
  <CardHeader>
    <div class="flex items-center justify-between">
      <CardTitle class="flex items-center gap-2">
        <ScrollText class="size-5" />
        System Log
        <Badge variant="secondary">{logs.length}</Badge>
      </CardTitle>
      <div class="flex gap-2">
        <Button size="sm" variant="outline" onclick={exportLogs} disabled={logs.length === 0}>
          <Download class="size-4" />
        </Button>
        <Button size="sm" variant="outline" onclick={onClearLogs} disabled={logs.length === 0}>
          <Trash2 class="size-4" />
        </Button>
      </div>
    </div>
  </CardHeader>
  <CardContent class="flex-1 min-h-0">
    <div class="space-y-2 h-full overflow-y-auto">
      {#each logs as log}
        <div class="flex items-start gap-2 text-sm p-2 rounded border">
          <Badge 
            variant={getLogLevel(log.message) === 'error' ? 'destructive' : 
                    getLogLevel(log.message) === 'warning' ? 'outline' : 'secondary'}
            class="text-xs shrink-0"
          >
            {log.time}
          </Badge>
          <span class="flex-1 font-mono text-xs break-all">
            {log.message}
          </span>
        </div>
      {:else}
        <div class="text-center text-muted-foreground py-8">
          No log entries yet
        </div>
      {/each}
    </div>
  </CardContent>
</Card>