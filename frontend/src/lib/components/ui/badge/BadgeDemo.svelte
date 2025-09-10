<script>
  import { Badge } from "./index.js";
</script>

<div class="p-6 space-y-4 bg-card rounded-lg border">
  <h3 class="text-lg font-semibold text-card-foreground">Badge Component Demo</h3>
  
  <div class="flex flex-wrap gap-2">
    <Badge>Default Badge</Badge>
    <Badge variant="secondary">Secondary</Badge>
    <Badge variant="destructive">Destructive</Badge>
    <Badge variant="outline">Outline</Badge>
  </div>
  
  <div class="space-y-2">
    <h4 class="text-sm font-medium text-muted-foreground">Status Examples:</h4>
    <div class="flex flex-wrap gap-2">
      <Badge variant="default" class="bg-green-900/20 text-green-400 border-green-900/30 hover:bg-green-900/30">
        Connected
      </Badge>
      <Badge variant="destructive" class="bg-red-900/20 text-red-400 border-red-900/30 hover:bg-red-900/30">
        Disconnected
      </Badge>
      <Badge variant="secondary" class="bg-orange-900/20 text-orange-400 border-orange-900/30 hover:bg-orange-900/30">
        Warning
      </Badge>
      <Badge variant="outline" class="border-purple-600/50 text-purple-400 hover:bg-purple-900/20">
        Processing
      </Badge>
    </div>
  </div>
</div>