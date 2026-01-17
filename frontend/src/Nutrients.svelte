<script>
  import { Beaker, Play, Square, Settings, Droplets, AlertTriangle, CheckCircle, XCircle, Loader2, RotateCcw, Trash2 } from '@lucide/svelte/icons';
  import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Badge } from '$lib/components/ui/badge';
  import { Progress } from '$lib/components/ui/progress';
  import { TabsRoot, TabsList, TabsTrigger, TabsContent } from '$lib/components/ui/tabs';
  import { Select, SelectTrigger, SelectContent, SelectItem } from '$lib/components/ui/select';
  import { Label } from '$lib/components/ui/label';
  import { subscribe, getSystemStatus } from '$lib/stores/systemStatus.svelte.js';

  // Get reactive system status from SSE store
  const sseStatus = getSystemStatus();

  // Available nutrients for assignment
  const availableNutrients = [
    { value: 'veg_a', label: 'Veg A' },
    { value: 'veg_b', label: 'Veg B' },
    { value: 'bloom_a', label: 'Bloom A' },
    { value: 'bloom_b', label: 'Bloom B' },
    { value: 'cake', label: 'Cake' },
    { value: 'pk_synergy', label: 'PK Synergy' },
    { value: 'runclean', label: 'Runclean' },
    { value: 'ph_down', label: 'pH Down' },
    { value: 'cal_mag', label: 'Cal-Mag' },
    { value: 'silica', label: 'Silica' },
    { value: 'roots', label: 'Roots' },
    { value: 'custom', label: 'Custom' }
  ];

  // Default pump configuration
  const defaultPumpConfig = {
    1: { nutrient: 'veg_a', label: 'Veg A' },
    2: { nutrient: 'veg_b', label: 'Veg B' },
    3: { nutrient: 'bloom_a', label: 'Bloom A' },
    4: { nutrient: 'bloom_b', label: 'Bloom B' },
    5: { nutrient: 'cake', label: 'Cake' },
    6: { nutrient: 'pk_synergy', label: 'PK Synergy' },
    7: { nutrient: 'runclean', label: 'Runclean' },
    8: { nutrient: 'ph_down', label: 'pH Down' }
  };

  // State
  let pumps = $state([]);
  let pumpConfig = $state({ ...defaultPumpConfig });
  let testAmounts = $state({ 1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10 });
  let dispensingPumps = $state(new Set());
  let calibratingPump = $state(null);
  let calibrationStep = $state('idle'); // idle, dispensing, measuring, saving
  let calibrationTarget = $state(10);
  let actualVolume = $state('');
  let statusMessage = $state('');
  let activeTab = $state('pumps');
  let lastUpdate = $state(new Date());

  // Derived states
  let isConnected = $derived(sseStatus.isConnected);
  let lastProcessedTimestamp = '';

  // SSE subscription
  let unsubscribe = null;

  // React to SSE status updates
  $effect(() => {
    const data = sseStatus.data;
    if (!data || !data.success) return;
    if (data.timestamp === lastProcessedTimestamp) return;
    lastProcessedTimestamp = data.timestamp;

    let newPumps = data.pumps || [];
    pumps = newPumps.map(pump => ({
      ...pump,
      is_dispensing: pump.is_dispensing || pump.status === 'running',
      current_volume: pump.current_volume || 0,
      target_volume: pump.target_volume || 0,
      voltage: pump.voltage || 0,
      calibrated: pump.calibrated || false,
      calibration_status: pump.calibration_status || 'unknown'
    }));

    lastUpdate = new Date();

    // Check if any dispensing pump has completed
    for (const pumpId of dispensingPumps) {
      const pump = pumps.find(p => p.id === pumpId);
      if (pump && pump.status !== 'running') {
        dispensingPumps.delete(pumpId);
        dispensingPumps = new Set(dispensingPumps);
      }
    }
  });

  // Initialize
  $effect(() => {
    loadPumpConfig();
    unsubscribe = subscribe();

    return () => {
      if (unsubscribe) unsubscribe();
    };
  });

  // API functions
  async function loadPumpConfig() {
    try {
      const response = await fetch('/api/nutrients');
      if (response.ok) {
        const data = await response.json();
        if (data.pump_assignments) {
          pumpConfig = { ...defaultPumpConfig, ...data.pump_assignments };
        }
      }
    } catch (error) {
      console.error('Failed to load pump config:', error);
    }
  }

  async function savePumpConfig() {
    try {
      const response = await fetch('/api/nutrients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pump_assignments: pumpConfig })
      });
      if (response.ok) {
        statusMessage = 'Configuration saved';
        setTimeout(() => statusMessage = '', 2000);
      }
    } catch (error) {
      console.error('Failed to save pump config:', error);
      statusMessage = 'Failed to save configuration';
    }
  }

  async function testDispense(pumpId) {
    const amount = testAmounts[pumpId];
    if (!amount || amount <= 0) return;

    dispensingPumps.add(pumpId);
    dispensingPumps = new Set(dispensingPumps);

    try {
      const response = await fetch(`/api/pumps/${pumpId}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount })
      });

      if (!response.ok) {
        throw new Error('Failed to start dispense');
      }
    } catch (error) {
      console.error(`Error dispensing from pump ${pumpId}:`, error);
      dispensingPumps.delete(pumpId);
      dispensingPumps = new Set(dispensingPumps);
    }
  }

  async function stopPump(pumpId) {
    try {
      await fetch(`/api/pumps/${pumpId}/stop`, { method: 'POST' });
      dispensingPumps.delete(pumpId);
      dispensingPumps = new Set(dispensingPumps);
    } catch (error) {
      console.error(`Error stopping pump ${pumpId}:`, error);
    }
  }

  async function emergencyStop() {
    try {
      await fetch('/api/emergency/stop', { method: 'POST' });
      dispensingPumps.clear();
      dispensingPumps = new Set(dispensingPumps);
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  }

  // Calibration functions
  async function startCalibration(pumpId) {
    calibratingPump = pumpId;
    calibrationStep = 'dispensing';
    actualVolume = '';

    try {
      const response = await fetch(`/api/pumps/${pumpId}/dispense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: calibrationTarget })
      });

      if (response.ok) {
        // Wait for dispense to complete, then move to measuring
        setTimeout(() => {
          calibrationStep = 'measuring';
        }, 3000);
      } else {
        throw new Error('Failed to start calibration dispense');
      }
    } catch (error) {
      console.error('Calibration error:', error);
      calibrationStep = 'idle';
      calibratingPump = null;
    }
  }

  async function completeCalibration() {
    if (!actualVolume || parseFloat(actualVolume) <= 0) return;

    calibrationStep = 'saving';

    try {
      const response = await fetch(`/api/pumps/${calibratingPump}/calibrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_volume: calibrationTarget,
          actual_volume: parseFloat(actualVolume)
        })
      });

      if (response.ok) {
        statusMessage = `Pump ${calibratingPump} calibrated successfully`;
        setTimeout(() => statusMessage = '', 3000);
      } else {
        throw new Error('Calibration failed');
      }
    } catch (error) {
      console.error('Calibration error:', error);
      statusMessage = 'Calibration failed';
    }

    calibrationStep = 'idle';
    calibratingPump = null;
    actualVolume = '';
  }

  async function clearCalibration(pumpId) {
    try {
      const response = await fetch(`/api/pumps/${pumpId}/calibration/clear`, {
        method: 'POST'
      });

      if (response.ok) {
        statusMessage = `Pump ${pumpId} calibration cleared`;
        setTimeout(() => statusMessage = '', 2000);
      }
    } catch (error) {
      console.error('Clear calibration error:', error);
    }
  }

  function cancelCalibration() {
    calibrationStep = 'idle';
    calibratingPump = null;
    actualVolume = '';
  }

  function updatePumpNutrient(pumpId, nutrientValue) {
    const nutrient = availableNutrients.find(n => n.value === nutrientValue);
    if (nutrient) {
      pumpConfig[pumpId] = { nutrient: nutrientValue, label: nutrient.label };
      pumpConfig = { ...pumpConfig };
    }
  }

  function getPumpData(pumpId) {
    return pumps.find(p => p.id === pumpId) || {
      id: pumpId,
      voltage: 0,
      calibrated: false,
      calibration_status: 'unknown',
      status: 'stopped',
      current_volume: 0,
      target_volume: 0
    };
  }

  function getCalibrationBadgeVariant(status) {
    if (status === 'calibrated' || status === 'single_point' || status === 'volume_calibrated') {
      return 'default';
    }
    return 'destructive';
  }

  function formatCalibrationStatus(status) {
    const statusMap = {
      'calibrated': 'Calibrated',
      'single_point': 'Calibrated',
      'volume_calibrated': 'Calibrated',
      'uncalibrated': 'Uncalibrated',
      'unknown': 'Unknown'
    };
    return statusMap[status] || status;
  }
</script>

<div class="p-6 max-w-7xl mx-auto space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="space-y-1">
      <h1 class="text-2xl font-bold text-foreground flex items-center gap-2">
        <Beaker class="h-6 w-6 text-primary" />
        Nutrient Management
      </h1>
      <p class="text-sm text-muted-foreground flex items-center gap-2">
        {#if isConnected}
          <span class="flex items-center gap-1 text-green-500">
            <CheckCircle class="h-4 w-4" />
            Connected
          </span>
        {:else}
          <span class="flex items-center gap-1 text-destructive">
            <XCircle class="h-4 w-4" />
            Disconnected
          </span>
        {/if}
        <span class="text-muted-foreground">· Updated {lastUpdate.toLocaleTimeString()}</span>
      </p>
    </div>

    <Button variant="destructive" size="lg" onclick={emergencyStop} class="gap-2">
      <AlertTriangle class="h-5 w-5" />
      Emergency Stop
    </Button>
  </div>

  <!-- Status Message -->
  {#if statusMessage}
    <div class="bg-primary/10 border border-primary/20 text-primary px-4 py-2 rounded-md text-sm">
      {statusMessage}
    </div>
  {/if}

  <!-- Tabs -->
  <TabsRoot bind:value={activeTab} class="w-full">
    <TabsList class="grid w-full grid-cols-3">
      <TabsTrigger value="pumps">
        <Droplets class="h-4 w-4 mr-2" />
        Pump Setup
      </TabsTrigger>
      <TabsTrigger value="test">
        <Play class="h-4 w-4 mr-2" />
        Test Dispense
      </TabsTrigger>
      <TabsTrigger value="calibration">
        <Settings class="h-4 w-4 mr-2" />
        Calibration
      </TabsTrigger>
    </TabsList>

    <!-- Pump Setup Tab -->
    <TabsContent value="pumps">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        {#each [1, 2, 3, 4, 5, 6, 7, 8] as pumpId}
          {@const pump = getPumpData(pumpId)}
          {@const config = pumpConfig[pumpId]}
          <Card class="relative">
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between">
                <CardTitle class="text-lg">Pump {pumpId}</CardTitle>
                <Badge variant={getCalibrationBadgeVariant(pump.calibration_status)}>
                  {formatCalibrationStatus(pump.calibration_status)}
                </Badge>
              </div>
              <CardDescription class="flex items-center gap-2">
                <span class="text-xs px-2 py-0.5 rounded bg-muted">
                  {pump.voltage?.toFixed(1) || '0.0'}V
                </span>
                <span class={pump.status === 'running' ? 'text-green-500' : 'text-muted-foreground'}>
                  {pump.status === 'running' ? 'Running' : 'Idle'}
                </span>
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-3">
              <div class="space-y-2">
                <Label class="text-xs text-muted-foreground">Assigned Nutrient</Label>
                <Select
                  type="single"
                  value={config?.nutrient}
                  onValueChange={(value) => updatePumpNutrient(pumpId, value)}
                >
                  <SelectTrigger class="w-full">
                    <span class="truncate">{config?.label || 'Select nutrient'}</span>
                  </SelectTrigger>
                  <SelectContent>
                    {#each availableNutrients as nutrient}
                      <SelectItem value={nutrient.value}>
                        {nutrient.label}
                      </SelectItem>
                    {/each}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        {/each}
      </div>

      <div class="flex justify-end mt-4">
        <Button onclick={savePumpConfig} class="gap-2">
          <CheckCircle class="h-4 w-4" />
          Save Configuration
        </Button>
      </div>
    </TabsContent>

    <!-- Test Dispense Tab -->
    <TabsContent value="test">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        {#each [1, 2, 3, 4, 5, 6, 7, 8] as pumpId}
          {@const pump = getPumpData(pumpId)}
          {@const config = pumpConfig[pumpId]}
          {@const isDispensing = dispensingPumps.has(pumpId)}
          <Card class={isDispensing ? 'ring-2 ring-green-500' : ''}>
            <CardHeader class="pb-3">
              <div class="flex items-center justify-between">
                <CardTitle class="text-lg">{config?.label || `Pump ${pumpId}`}</CardTitle>
                <span class="text-xs text-muted-foreground">Pump {pumpId}</span>
              </div>
              <CardDescription>
                {pump.voltage?.toFixed(1) || '0.0'}V · {pump.calibrated ? 'Calibrated' : 'Uncalibrated'}
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-2">
                <Label class="text-xs text-muted-foreground">Amount (ml)</Label>
                <Input
                  type="number"
                  min="0.5"
                  max="500"
                  step="0.5"
                  bind:value={testAmounts[pumpId]}
                  disabled={isDispensing}
                  class="text-center"
                />
              </div>

              {#if isDispensing && pump.target_volume > 0}
                <div class="space-y-2">
                  <div class="flex justify-between text-xs text-muted-foreground">
                    <span>Progress</span>
                    <span>{pump.current_volume?.toFixed(1) || 0} / {pump.target_volume?.toFixed(1)} ml</span>
                  </div>
                  <Progress
                    value={pump.current_volume || 0}
                    max={pump.target_volume || 100}
                    variant="success"
                  />
                </div>
              {/if}
            </CardContent>
            <CardFooter class="pt-0">
              {#if isDispensing}
                <Button
                  variant="destructive"
                  class="w-full gap-2"
                  onclick={() => stopPump(pumpId)}
                >
                  <Square class="h-4 w-4" />
                  Stop
                </Button>
              {:else}
                <Button
                  class="w-full gap-2"
                  onclick={() => testDispense(pumpId)}
                  disabled={!testAmounts[pumpId] || testAmounts[pumpId] <= 0}
                >
                  <Play class="h-4 w-4" />
                  Dispense
                </Button>
              {/if}
            </CardFooter>
          </Card>
        {/each}
      </div>
    </TabsContent>

    <!-- Calibration Tab -->
    <TabsContent value="calibration">
      <Card class="mt-4">
        <CardHeader>
          <CardTitle>Pump Calibration</CardTitle>
          <CardDescription>
            Calibrate pumps for accurate dispensing. Use water for calibration, not chemicals.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <!-- Calibration Target -->
          <div class="space-y-4 mb-6">
            <div class="flex items-center gap-4">
              <Label class="min-w-32">Target Volume (ml)</Label>
              <Input
                type="number"
                min="5"
                max="100"
                step="1"
                bind:value={calibrationTarget}
                disabled={calibrationStep !== 'idle'}
                class="w-32"
              />
            </div>
          </div>

          <!-- Pump Grid for Calibration -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {#each [1, 2, 3, 4, 5, 6, 7, 8] as pumpId}
              {@const pump = getPumpData(pumpId)}
              {@const config = pumpConfig[pumpId]}
              {@const isCalibrating = calibratingPump === pumpId}
              <Card class={isCalibrating ? 'ring-2 ring-primary' : ''}>
                <CardHeader class="pb-2">
                  <div class="flex items-center justify-between">
                    <CardTitle class="text-base">{config?.label || `Pump ${pumpId}`}</CardTitle>
                    <Badge variant={getCalibrationBadgeVariant(pump.calibration_status)} class="text-xs">
                      {formatCalibrationStatus(pump.calibration_status)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent class="space-y-3">
                  {#if isCalibrating}
                    <!-- Calibration in progress -->
                    {#if calibrationStep === 'dispensing'}
                      <div class="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 class="h-4 w-4 animate-spin" />
                        Dispensing {calibrationTarget}ml...
                      </div>
                    {:else if calibrationStep === 'measuring'}
                      <div class="space-y-3">
                        <p class="text-sm text-muted-foreground">
                          Measure the actual volume dispensed:
                        </p>
                        <div class="flex gap-2">
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            placeholder="Actual ml"
                            bind:value={actualVolume}
                            class="flex-1"
                          />
                          <span class="flex items-center text-sm text-muted-foreground">ml</span>
                        </div>
                        <div class="flex gap-2">
                          <Button
                            size="sm"
                            class="flex-1"
                            onclick={completeCalibration}
                            disabled={!actualVolume || parseFloat(actualVolume) <= 0}
                          >
                            <CheckCircle class="h-4 w-4 mr-1" />
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onclick={cancelCalibration}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    {:else if calibrationStep === 'saving'}
                      <div class="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 class="h-4 w-4 animate-spin" />
                        Saving calibration...
                      </div>
                    {/if}
                  {:else}
                    <!-- Calibration actions -->
                    <div class="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        class="flex-1"
                        onclick={() => startCalibration(pumpId)}
                        disabled={calibratingPump !== null}
                      >
                        <RotateCcw class="h-4 w-4 mr-1" />
                        Calibrate
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onclick={() => clearCalibration(pumpId)}
                        disabled={calibratingPump !== null}
                      >
                        <Trash2 class="h-4 w-4" />
                      </Button>
                    </div>
                  {/if}
                </CardContent>
              </Card>
            {/each}
          </div>

          <!-- Calibration Tips -->
          <div class="mt-6 p-4 bg-muted/50 rounded-lg">
            <h4 class="font-medium text-sm mb-2 flex items-center gap-2">
              <AlertTriangle class="h-4 w-4 text-yellow-500" />
              Calibration Tips
            </h4>
            <ul class="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Always use water for calibration, never chemicals</li>
              <li>Ensure tubing is full of water with no air bubbles</li>
              <li>Use a graduated cylinder or precise scale for measurement</li>
              <li>Recommended calibration volume: 10ml for best accuracy</li>
              <li>Recalibrate periodically to maintain accuracy</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  </TabsRoot>
</div>
