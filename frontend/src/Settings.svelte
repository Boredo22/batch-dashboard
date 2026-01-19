<script>
  import { onMount } from 'svelte';
  import { TabsRoot as Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs/index.js";
  import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Switch } from "$lib/components/ui/switch/index.js";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import {
    Settings as SettingsIcon,
    Droplets,
    Beaker,
    Cpu,
    Info,
    Plus,
    Trash2,
    Save,
    AlertCircle,
    CheckCircle,
    XCircle,
    RefreshCw,
    FlaskConical,
    Gauge,
    Waves,
    Zap
  } from "@lucide/svelte/icons";

  // ==================== STATE ====================

  // Loading and UI state
  let loading = $state(true);
  let saving = $state(false);
  let saveMessage = $state('');
  let loadError = $state('');
  let activeTab = $state('system');

  // System status
  let systemStatus = $state({
    connected: false,
    relays: [],
    pumps: [],
    flowMeters: [],
    ecph: { ec: 0, ph: 0, monitoring: false }
  });
  let statusLoading = $state(false);

  // User Settings
  let userSettings = $state({
    tanks: {},
    rooms: {},
    pumps: {
      names: {},
      addresses: {}
    },
    flowMeters: {
      calibration: {}
    },
    ecphDefaults: {
      ec: { min: 1.0, max: 2.0 },
      ph: { min: 5.5, max: 6.5 }
    },
    timing: {
      status_update_interval: 2.0,
      pump_check_interval: 1.0,
      flow_update_interval: 0.5
    },
    limits: {
      max_pump_volume_ml: 2500.0,
      min_pump_volume_ml: 0.5,
      max_flow_gallons: 100
    }
  });

  // Developer Settings
  let devSettings = $state({
    gpio: {
      relay_pins: {},
      flow_meter_pins: {}
    },
    i2c: {
      bus_number: 1,
      pump_addresses: {},
      command_delay: 0.3
    },
    communication: {
      command_start: "Start",
      command_end: "end",
      arduino_baudrate: 115200
    },
    mock: {
      mock_mode: false,
      mock_pumps: false,
      mock_relays: false,
      mock_flow_meters: false,
      mock_ecph: false
    },
    debug: {
      debug_mode: false,
      verbose_logging: false,
      log_level: "INFO"
    }
  });

  // Nutrients Configuration
  let nutrientsConfig = $state({
    available_nutrients: [],
    veg_formula: {},
    bloom_formula: {},
    pump_name_to_id: {}
  });

  // New recipe being created
  let newRecipeName = $state('');
  let newRecipeNutrients = $state({});
  let showNewRecipeForm = $state(false);

  // ==================== API FUNCTIONS ====================

  async function loadSettings() {
    loading = true;
    loadError = '';
    try {
      const [userResponse, devResponse, nutrientsResponse] = await Promise.all([
        fetch('/api/settings/user'),
        fetch('/api/settings/developer'),
        fetch('/api/nutrients')
      ]);

      if (userResponse.ok) {
        const userData = await userResponse.json();
        userSettings = { ...userSettings, ...userData };
        // Initialize rooms if not present
        if (!userSettings.rooms || Object.keys(userSettings.rooms).length === 0) {
          userSettings.rooms = {
            1: { name: "Grow Room 1", relay: 10 }
          };
        }
        // Initialize flow meter calibration
        if (!userSettings.flowMeters) {
          userSettings.flowMeters = { calibration: { 1: 220, 2: 220 } };
        }
        // Initialize EC/pH defaults
        if (!userSettings.ecphDefaults) {
          userSettings.ecphDefaults = {
            ec: { min: 1.0, max: 2.0 },
            ph: { min: 5.5, max: 6.5 }
          };
        }
      }

      if (devResponse.ok) {
        const devData = await devResponse.json();
        devSettings = { ...devSettings, ...devData };
      }

      if (nutrientsResponse.ok) {
        const nutrientsData = await nutrientsResponse.json();
        nutrientsConfig = { ...nutrientsConfig, ...nutrientsData };
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      loadError = 'Unable to connect to backend. Make sure the server is running.';
    } finally {
      loading = false;
    }
  }

  async function saveSettings() {
    saving = true;
    saveMessage = '';
    try {
      const [userResponse, devResponse, nutrientsResponse] = await Promise.all([
        fetch('/api/settings/user', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userSettings)
        }),
        fetch('/api/settings/developer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(devSettings)
        }),
        fetch('/api/nutrients', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(nutrientsConfig)
        })
      ]);

      if (userResponse.ok && devResponse.ok && nutrientsResponse.ok) {
        saveMessage = 'Settings saved successfully!';
      } else {
        saveMessage = 'Error saving some settings. Please try again.';
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      saveMessage = 'Error connecting to server. Please check connection.';
    } finally {
      saving = false;
      setTimeout(() => saveMessage = '', 4000);
    }
  }

  async function loadSystemStatus() {
    statusLoading = true;
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        systemStatus = {
          connected: true,
          relays: data.relays || [],
          pumps: data.pumps || [],
          flowMeters: data.flow_meters || [],
          ecph: data.ecph || { ec: 0, ph: 0, monitoring: false }
        };
      } else {
        systemStatus.connected = false;
      }
    } catch (error) {
      console.error('Error loading system status:', error);
      systemStatus.connected = false;
    } finally {
      statusLoading = false;
    }
  }

  // ==================== TANK FUNCTIONS ====================

  function addTank() {
    const existingIds = Object.keys(userSettings.tanks || {}).map(Number);
    const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
    userSettings.tanks = {
      ...userSettings.tanks,
      [newId]: {
        name: `Tank ${newId}`,
        capacity_gallons: 100,
        fill_relay: 0,
        send_relay: 0,
        mix_relays: []
      }
    };
  }

  function removeTank(tankId) {
    const { [tankId]: removed, ...rest } = userSettings.tanks;
    userSettings.tanks = rest;
  }

  function addMixRelay(tankId) {
    const tank = userSettings.tanks[tankId];
    if (tank) {
      tank.mix_relays = [...(tank.mix_relays || []), 0];
      userSettings.tanks = { ...userSettings.tanks };
    }
  }

  function removeMixRelay(tankId, index) {
    const tank = userSettings.tanks[tankId];
    if (tank && tank.mix_relays) {
      tank.mix_relays.splice(index, 1);
      userSettings.tanks = { ...userSettings.tanks };
    }
  }

  // ==================== ROOM FUNCTIONS ====================

  function addRoom() {
    const existingIds = Object.keys(userSettings.rooms || {}).map(Number);
    const newId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;
    userSettings.rooms = {
      ...userSettings.rooms,
      [newId]: {
        name: `Room ${newId}`,
        relay: 0
      }
    };
  }

  function removeRoom(roomId) {
    const { [roomId]: removed, ...rest } = userSettings.rooms;
    userSettings.rooms = rest;
  }

  // ==================== RECIPE FUNCTIONS ====================

  function getRecipeNames() {
    return Object.keys(nutrientsConfig)
      .filter(key => !['available_nutrients', 'pump_name_to_id'].includes(key));
  }

  function addNutrientToRecipe(recipeName, nutrientName) {
    if (!nutrientsConfig[recipeName]) return;
    const defaultDosage = nutrientsConfig.available_nutrients?.find(n => n.name === nutrientName)?.defaultDosage || 1;
    nutrientsConfig[recipeName] = {
      ...nutrientsConfig[recipeName],
      [nutrientName]: defaultDosage
    };
    nutrientsConfig = { ...nutrientsConfig };
  }

  function removeNutrientFromRecipe(recipeName, nutrientName) {
    if (!nutrientsConfig[recipeName]) return;
    const { [nutrientName]: removed, ...rest } = nutrientsConfig[recipeName];
    nutrientsConfig[recipeName] = rest;
    nutrientsConfig = { ...nutrientsConfig };
  }

  function updateRecipeDosage(recipeName, nutrientName, value) {
    if (!nutrientsConfig[recipeName]) return;
    nutrientsConfig[recipeName][nutrientName] = parseFloat(value) || 0;
    nutrientsConfig = { ...nutrientsConfig };
  }

  function createNewRecipe() {
    if (!newRecipeName.trim()) return;
    const key = newRecipeName.toLowerCase().replace(/\s+/g, '_');
    nutrientsConfig[key] = { ...newRecipeNutrients };
    nutrientsConfig = { ...nutrientsConfig };
    newRecipeName = '';
    newRecipeNutrients = {};
    showNewRecipeForm = false;
  }

  function deleteRecipe(recipeName) {
    if (['veg_formula', 'bloom_formula'].includes(recipeName)) {
      alert('Cannot delete default recipes');
      return;
    }
    const { [recipeName]: removed, ...rest } = nutrientsConfig;
    nutrientsConfig = rest;
  }

  function formatRecipeName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  // ==================== NUTRIENT FUNCTIONS ====================

  function addNutrient() {
    nutrientsConfig.available_nutrients = [
      ...nutrientsConfig.available_nutrients,
      { name: 'New Nutrient', defaultDosage: 1 }
    ];
  }

  function removeNutrient(index) {
    nutrientsConfig.available_nutrients = nutrientsConfig.available_nutrients.filter((_, i) => i !== index);
  }

  function updatePumpMapping(nutrientName, pumpId) {
    nutrientsConfig.pump_name_to_id = {
      ...nutrientsConfig.pump_name_to_id,
      [nutrientName]: parseInt(pumpId) || 0
    };
  }

  // ==================== LIFECYCLE ====================

  onMount(() => {
    loadSettings();
  });
</script>

{#if loading}
  <div class="flex items-center justify-center py-12">
    <div class="text-center space-y-4">
      <SettingsIcon class="size-8 mx-auto animate-spin text-muted-foreground" />
      <p class="text-muted-foreground">Loading settings...</p>
    </div>
  </div>
{:else}
  <div class="space-y-6">
    <!-- Error Alert -->
    {#if loadError}
      <Alert variant="destructive">
        <AlertCircle class="size-4" />
        <AlertDescription>
          {loadError}
          <Button variant="link" onclick={loadSettings} class="ml-2 p-0 h-auto">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    {/if}

    <!-- Save Message -->
    {#if saveMessage}
      <Alert variant={saveMessage.includes('Error') ? 'destructive' : 'default'}>
        {#if saveMessage.includes('Error')}
          <AlertCircle class="size-4" />
        {:else}
          <CheckCircle class="size-4" />
        {/if}
        <AlertDescription>{saveMessage}</AlertDescription>
      </Alert>
    {/if}

    <!-- Settings Tabs -->
    <Tabs bind:value={activeTab} class="space-y-6">
      <TabsList class="grid w-full grid-cols-4">
        <TabsTrigger value="system" class="flex items-center gap-2">
          <Droplets class="size-4" />
          <span class="hidden sm:inline">System</span>
        </TabsTrigger>
        <TabsTrigger value="recipes" class="flex items-center gap-2">
          <FlaskConical class="size-4" />
          <span class="hidden sm:inline">Recipes</span>
        </TabsTrigger>
        <TabsTrigger value="hardware" class="flex items-center gap-2">
          <Cpu class="size-4" />
          <span class="hidden sm:inline">Hardware</span>
        </TabsTrigger>
        <TabsTrigger value="info" class="flex items-center gap-2">
          <Info class="size-4" />
          <span class="hidden sm:inline">Info</span>
        </TabsTrigger>
      </TabsList>

      <!-- ==================== SYSTEM TAB ==================== -->
      <TabsContent value="system" class="space-y-6">

        <!-- Tank Configuration -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <Droplets class="size-5" />
                  Tank Configuration
                </CardTitle>
                <CardDescription>Configure tanks, their capacities, and relay mappings</CardDescription>
              </div>
              <Button onclick={addTank} size="sm">
                <Plus class="size-4 mr-2" />
                Add Tank
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {#if userSettings.tanks && Object.keys(userSettings.tanks).length > 0}
              <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {#each Object.entries(userSettings.tanks) as [tankId, tank]}
                  <Card class="border-muted">
                    <CardHeader class="pb-3">
                      <div class="flex items-center justify-between">
                        <Badge variant="outline">Tank {tankId}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onclick={() => removeTank(tankId)}
                        >
                          <Trash2 class="size-4 text-destructive" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent class="space-y-3">
                      <div class="space-y-1">
                        <Label class="text-xs">Name</Label>
                        <Input bind:value={tank.name} placeholder="Tank name" />
                      </div>

                      <div class="grid grid-cols-2 gap-2">
                        <div class="space-y-1">
                          <Label class="text-xs">Capacity (gal)</Label>
                          <Input type="number" bind:value={tank.capacity_gallons} min="1" />
                        </div>
                        <div class="space-y-1">
                          <Label class="text-xs">Fill Relay</Label>
                          <Input type="number" bind:value={tank.fill_relay} min="0" />
                        </div>
                      </div>

                      <div class="space-y-1">
                        <Label class="text-xs">Send Relay</Label>
                        <Input type="number" bind:value={tank.send_relay} min="0" />
                      </div>

                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <Label class="text-xs">Mix Relays</Label>
                          <Button size="sm" variant="ghost" onclick={() => addMixRelay(tankId)}>
                            <Plus class="size-3" />
                          </Button>
                        </div>
                        {#if tank.mix_relays && tank.mix_relays.length > 0}
                          <div class="flex flex-wrap gap-2">
                            {#each tank.mix_relays as relay, index}
                              <div class="flex items-center gap-1">
                                <Input
                                  type="number"
                                  bind:value={tank.mix_relays[index]}
                                  min="0"
                                  class="w-16 h-8"
                                />
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onclick={() => removeMixRelay(tankId, index)}
                                  class="h-8 w-8 p-0"
                                >
                                  <Trash2 class="size-3" />
                                </Button>
                              </div>
                            {/each}
                          </div>
                        {:else}
                          <p class="text-xs text-muted-foreground">No mix relays</p>
                        {/if}
                      </div>
                    </CardContent>
                  </Card>
                {/each}
              </div>
            {:else}
              <div class="text-center py-8">
                <Droplets class="size-12 mx-auto text-muted-foreground/50 mb-4" />
                <p class="text-muted-foreground">No tanks configured</p>
                <Button onclick={addTank} class="mt-4">
                  <Plus class="size-4 mr-2" />
                  Add Your First Tank
                </Button>
              </div>
            {/if}
          </CardContent>
        </Card>

        <!-- Room Configuration -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <Zap class="size-5" />
                  Room Configuration
                </CardTitle>
                <CardDescription>Configure grow rooms and their relay mappings for nutrient delivery</CardDescription>
              </div>
              <Button onclick={addRoom} size="sm">
                <Plus class="size-4 mr-2" />
                Add Room
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {#if userSettings.rooms && Object.keys(userSettings.rooms).length > 0}
              <div class="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
                {#each Object.entries(userSettings.rooms) as [roomId, room]}
                  <Card class="border-muted">
                    <CardContent class="pt-4 space-y-3">
                      <div class="flex items-center justify-between">
                        <Badge variant="outline">Room {roomId}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onclick={() => removeRoom(roomId)}
                        >
                          <Trash2 class="size-4 text-destructive" />
                        </Button>
                      </div>
                      <div class="space-y-1">
                        <Label class="text-xs">Name</Label>
                        <Input bind:value={room.name} placeholder="Room name" />
                      </div>
                      <div class="space-y-1">
                        <Label class="text-xs">Relay</Label>
                        <Input type="number" bind:value={room.relay} min="0" />
                      </div>
                    </CardContent>
                  </Card>
                {/each}
              </div>
            {:else}
              <div class="text-center py-6">
                <p class="text-muted-foreground">No rooms configured</p>
              </div>
            {/if}
          </CardContent>
        </Card>

        <!-- Flow Meter Calibration -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Waves class="size-5" />
              Flow Meter Calibration
            </CardTitle>
            <CardDescription>Set pulses per gallon for accurate flow measurement</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-2">
                <Label>Flow Meter 1 (Tank Fill)</Label>
                <div class="flex items-center gap-2">
                  <Input
                    type="number"
                    value={userSettings.flowMeters?.calibration?.[1] || 220}
                    onchange={(e) => {
                      if (!userSettings.flowMeters) userSettings.flowMeters = { calibration: {} };
                      if (!userSettings.flowMeters.calibration) userSettings.flowMeters.calibration = {};
                      userSettings.flowMeters.calibration[1] = parseInt(e.target.value) || 220;
                    }}
                    min="1"
                  />
                  <span class="text-sm text-muted-foreground whitespace-nowrap">pulses/gal</span>
                </div>
              </div>
              <div class="space-y-2">
                <Label>Flow Meter 2 (Tank Send)</Label>
                <div class="flex items-center gap-2">
                  <Input
                    type="number"
                    value={userSettings.flowMeters?.calibration?.[2] || 220}
                    onchange={(e) => {
                      if (!userSettings.flowMeters) userSettings.flowMeters = { calibration: {} };
                      if (!userSettings.flowMeters.calibration) userSettings.flowMeters.calibration = {};
                      userSettings.flowMeters.calibration[2] = parseInt(e.target.value) || 220;
                    }}
                    min="1"
                  />
                  <span class="text-sm text-muted-foreground whitespace-nowrap">pulses/gal</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- EC/pH Default Targets -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Gauge class="size-5" />
              Default EC/pH Targets
            </CardTitle>
            <CardDescription>Default target ranges used in Fill Tank workflow</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-6 sm:grid-cols-2">
              <div class="space-y-3">
                <Label class="text-base font-medium">EC Range (mS/cm)</Label>
                <div class="flex items-center gap-3">
                  <div class="space-y-1 flex-1">
                    <Label class="text-xs">Min</Label>
                    <Input
                      type="number"
                      value={userSettings.ecphDefaults?.ec?.min || 1.0}
                      onchange={(e) => {
                        if (!userSettings.ecphDefaults) userSettings.ecphDefaults = { ec: {}, ph: {} };
                        if (!userSettings.ecphDefaults.ec) userSettings.ecphDefaults.ec = {};
                        userSettings.ecphDefaults.ec.min = parseFloat(e.target.value) || 1.0;
                      }}
                      min="0" max="5" step="0.1"
                    />
                  </div>
                  <span class="mt-5">-</span>
                  <div class="space-y-1 flex-1">
                    <Label class="text-xs">Max</Label>
                    <Input
                      type="number"
                      value={userSettings.ecphDefaults?.ec?.max || 2.0}
                      onchange={(e) => {
                        if (!userSettings.ecphDefaults) userSettings.ecphDefaults = { ec: {}, ph: {} };
                        if (!userSettings.ecphDefaults.ec) userSettings.ecphDefaults.ec = {};
                        userSettings.ecphDefaults.ec.max = parseFloat(e.target.value) || 2.0;
                      }}
                      min="0" max="5" step="0.1"
                    />
                  </div>
                </div>
              </div>
              <div class="space-y-3">
                <Label class="text-base font-medium">pH Range</Label>
                <div class="flex items-center gap-3">
                  <div class="space-y-1 flex-1">
                    <Label class="text-xs">Min</Label>
                    <Input
                      type="number"
                      value={userSettings.ecphDefaults?.ph?.min || 5.5}
                      onchange={(e) => {
                        if (!userSettings.ecphDefaults) userSettings.ecphDefaults = { ec: {}, ph: {} };
                        if (!userSettings.ecphDefaults.ph) userSettings.ecphDefaults.ph = {};
                        userSettings.ecphDefaults.ph.min = parseFloat(e.target.value) || 5.5;
                      }}
                      min="0" max="14" step="0.1"
                    />
                  </div>
                  <span class="mt-5">-</span>
                  <div class="space-y-1 flex-1">
                    <Label class="text-xs">Max</Label>
                    <Input
                      type="number"
                      value={userSettings.ecphDefaults?.ph?.max || 6.5}
                      onchange={(e) => {
                        if (!userSettings.ecphDefaults) userSettings.ecphDefaults = { ec: {}, ph: {} };
                        if (!userSettings.ecphDefaults.ph) userSettings.ecphDefaults.ph = {};
                        userSettings.ecphDefaults.ph.max = parseFloat(e.target.value) || 6.5;
                      }}
                      min="0" max="14" step="0.1"
                    />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- System Limits -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <AlertCircle class="size-5" />
              System Limits
            </CardTitle>
            <CardDescription>Safety limits for pumps and flow meters</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-3">
              <div class="space-y-2">
                <Label>Max Pump Volume (ml)</Label>
                <Input type="number" bind:value={userSettings.limits.max_pump_volume_ml} min="1" />
              </div>
              <div class="space-y-2">
                <Label>Min Pump Volume (ml)</Label>
                <Input type="number" bind:value={userSettings.limits.min_pump_volume_ml} min="0.1" step="0.1" />
              </div>
              <div class="space-y-2">
                <Label>Max Flow (gallons)</Label>
                <Input type="number" bind:value={userSettings.limits.max_flow_gallons} min="1" />
              </div>
            </div>
          </CardContent>
        </Card>

      </TabsContent>

      <!-- ==================== RECIPES TAB ==================== -->
      <TabsContent value="recipes" class="space-y-6">

        <!-- Nutrient Recipes -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <FlaskConical class="size-5" />
                  Nutrient Recipes
                </CardTitle>
                <CardDescription>Configure nutrient formulas with ml per gallon dosages</CardDescription>
              </div>
              <Button onclick={() => showNewRecipeForm = !showNewRecipeForm} size="sm">
                <Plus class="size-4 mr-2" />
                New Recipe
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-4">
            {#if showNewRecipeForm}
              <Card class="border-primary/50 bg-primary/5">
                <CardContent class="pt-4 space-y-4">
                  <div class="flex items-center gap-4">
                    <div class="flex-1 space-y-1">
                      <Label>Recipe Name</Label>
                      <Input
                        bind:value={newRecipeName}
                        placeholder="e.g., Flower Week 3"
                      />
                    </div>
                    <div class="flex gap-2 mt-5">
                      <Button onclick={createNewRecipe} disabled={!newRecipeName.trim()}>
                        Create
                      </Button>
                      <Button variant="outline" onclick={() => showNewRecipeForm = false}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            {/if}

            <div class="grid gap-4 lg:grid-cols-2">
              {#each getRecipeNames() as recipeName}
                <Card>
                  <CardHeader class="pb-3">
                    <div class="flex items-center justify-between">
                      <CardTitle class="text-base">{formatRecipeName(recipeName)}</CardTitle>
                      <div class="flex items-center gap-2">
                        {#if !['veg_formula', 'bloom_formula'].includes(recipeName)}
                          <Button
                            variant="ghost"
                            size="sm"
                            onclick={() => deleteRecipe(recipeName)}
                          >
                            <Trash2 class="size-4 text-destructive" />
                          </Button>
                        {:else}
                          <Badge variant="secondary">Default</Badge>
                        {/if}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent class="space-y-3">
                    {#if nutrientsConfig[recipeName] && Object.keys(nutrientsConfig[recipeName]).length > 0}
                      {#each Object.entries(nutrientsConfig[recipeName]) as [nutrient, dosage]}
                        <div class="flex items-center gap-3">
                          <span class="flex-1 text-sm">{nutrient}</span>
                          <Input
                            type="number"
                            value={dosage}
                            onchange={(e) => updateRecipeDosage(recipeName, nutrient, e.target.value)}
                            min="0"
                            step="0.1"
                            class="w-20 h-8"
                          />
                          <span class="text-xs text-muted-foreground w-12">ml/gal</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onclick={() => removeNutrientFromRecipe(recipeName, nutrient)}
                            class="h-8 w-8 p-0"
                          >
                            <Trash2 class="size-3" />
                          </Button>
                        </div>
                      {/each}
                    {:else}
                      <p class="text-sm text-muted-foreground">No nutrients in this recipe</p>
                    {/if}

                    <Separator />

                    <div class="flex items-center gap-2">
                      <select
                        class="flex-1 h-8 px-2 rounded-md border bg-background text-sm"
                        onchange={(e) => {
                          if (e.target.value) {
                            addNutrientToRecipe(recipeName, e.target.value);
                            e.target.value = '';
                          }
                        }}
                      >
                        <option value="">+ Add nutrient...</option>
                        {#each nutrientsConfig.available_nutrients || [] as nutrient}
                          {#if !nutrientsConfig[recipeName]?.[nutrient.name]}
                            <option value={nutrient.name}>{nutrient.name}</option>
                          {/if}
                        {/each}
                      </select>
                    </div>
                  </CardContent>
                </Card>
              {/each}
            </div>
          </CardContent>
        </Card>

        <!-- Available Nutrients -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  <Beaker class="size-5" />
                  Available Nutrients
                </CardTitle>
                <CardDescription>All nutrients available for recipes with their default dosages</CardDescription>
              </div>
              <Button onclick={addNutrient} size="sm">
                <Plus class="size-4 mr-2" />
                Add Nutrient
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div class="space-y-3">
              {#each nutrientsConfig.available_nutrients || [] as nutrient, index}
                <div class="flex items-center gap-4 p-3 rounded-lg border">
                  <div class="flex-1 space-y-1">
                    <Label class="text-xs">Name</Label>
                    <Input
                      bind:value={nutrient.name}
                      placeholder="Nutrient name"
                    />
                  </div>
                  <div class="w-24 space-y-1">
                    <Label class="text-xs">Default (ml/gal)</Label>
                    <Input
                      type="number"
                      bind:value={nutrient.defaultDosage}
                      min="0"
                      step="0.1"
                    />
                  </div>
                  <div class="w-20 space-y-1">
                    <Label class="text-xs">Pump ID</Label>
                    <Input
                      type="number"
                      value={nutrientsConfig.pump_name_to_id?.[nutrient.name] || 0}
                      onchange={(e) => updatePumpMapping(nutrient.name, e.target.value)}
                      min="0"
                      max="8"
                    />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onclick={() => removeNutrient(index)}
                    class="mt-5"
                  >
                    <Trash2 class="size-4 text-destructive" />
                  </Button>
                </div>
              {/each}
            </div>
          </CardContent>
        </Card>

      </TabsContent>

      <!-- ==================== HARDWARE TAB ==================== -->
      <TabsContent value="hardware" class="space-y-6">

        <!-- Mock Mode Settings -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Cpu class="size-5" />
              Hardware Mode
            </CardTitle>
            <CardDescription>Enable mock mode for testing without physical hardware</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between p-4 rounded-lg border">
              <div>
                <Label class="text-base">Global Mock Mode</Label>
                <p class="text-sm text-muted-foreground">
                  Enable mock mode for all hardware components
                </p>
              </div>
              <Switch
                checked={devSettings.mock.mock_mode}
                onCheckedChange={(checked) => devSettings.mock.mock_mode = checked}
              />
            </div>

            <Separator />

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <Label>Mock Pumps</Label>
                <Switch
                  checked={devSettings.mock.mock_pumps}
                  onCheckedChange={(checked) => devSettings.mock.mock_pumps = checked}
                />
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <Label>Mock Relays</Label>
                <Switch
                  checked={devSettings.mock.mock_relays}
                  onCheckedChange={(checked) => devSettings.mock.mock_relays = checked}
                />
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <Label>Mock Flow Meters</Label>
                <Switch
                  checked={devSettings.mock.mock_flow_meters}
                  onCheckedChange={(checked) => devSettings.mock.mock_flow_meters = checked}
                />
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <Label>Mock EC/pH</Label>
                <Switch
                  checked={devSettings.mock.mock_ecph}
                  onCheckedChange={(checked) => devSettings.mock.mock_ecph = checked}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- GPIO Configuration (Read-only) -->
        <Card>
          <CardHeader>
            <CardTitle>GPIO Pin Mappings</CardTitle>
            <CardDescription>Current GPIO pin assignments (modify in config.py)</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <h4 class="font-medium mb-2">Relay GPIO Pins</h4>
                <div class="space-y-1 text-sm">
                  {#each Object.entries(devSettings.gpio.relay_pins || {}) as [relayId, pin]}
                    <div class="flex justify-between p-2 rounded bg-muted/50">
                      <span>Relay {relayId}</span>
                      <Badge variant="outline">GPIO {pin}</Badge>
                    </div>
                  {/each}
                </div>
              </div>
              <div>
                <h4 class="font-medium mb-2">Flow Meter GPIO Pins</h4>
                <div class="space-y-1 text-sm">
                  {#each Object.entries(devSettings.gpio.flow_meter_pins || {}) as [meterId, pin]}
                    <div class="flex justify-between p-2 rounded bg-muted/50">
                      <span>Flow Meter {meterId}</span>
                      <Badge variant="outline">GPIO {pin}</Badge>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- I2C Configuration -->
        <Card>
          <CardHeader>
            <CardTitle>I2C Configuration</CardTitle>
            <CardDescription>I2C bus settings for pump communication</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-3">
              <div class="space-y-2">
                <Label>I2C Bus Number</Label>
                <Input type="number" bind:value={devSettings.i2c.bus_number} min="0" />
              </div>
              <div class="space-y-2">
                <Label>Command Delay (sec)</Label>
                <Input type="number" bind:value={devSettings.i2c.command_delay} min="0" step="0.1" />
              </div>
              <div class="space-y-2">
                <Label>Arduino Baud Rate</Label>
                <Input type="number" bind:value={devSettings.communication.arduino_baudrate} />
              </div>
            </div>

            <Separator class="my-4" />

            <div>
              <h4 class="font-medium mb-2">Pump I2C Addresses</h4>
              <div class="grid gap-2 sm:grid-cols-4">
                {#each Object.entries(devSettings.i2c.pump_addresses || {}) as [pumpId, address]}
                  <div class="flex justify-between p-2 rounded bg-muted/50 text-sm">
                    <span>Pump {pumpId}</span>
                    <Badge variant="outline">0x{address.toString(16)}</Badge>
                  </div>
                {/each}
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Debug Settings -->
        <Card>
          <CardHeader>
            <CardTitle>Debug Settings</CardTitle>
            <CardDescription>Logging and debug configuration</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <Label>Debug Mode</Label>
                  <p class="text-xs text-muted-foreground">Enable detailed debug info</p>
                </div>
                <Switch
                  checked={devSettings.debug.debug_mode}
                  onCheckedChange={(checked) => devSettings.debug.debug_mode = checked}
                />
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <Label>Verbose Logging</Label>
                  <p class="text-xs text-muted-foreground">Log all hardware comms</p>
                </div>
                <Switch
                  checked={devSettings.debug.verbose_logging}
                  onCheckedChange={(checked) => devSettings.debug.verbose_logging = checked}
                />
              </div>
            </div>
            <div class="space-y-2">
              <Label>Log Level</Label>
              <select
                class="w-full h-10 px-3 rounded-md border bg-background"
                value={devSettings.debug.log_level}
                onchange={(e) => devSettings.debug.log_level = e.target.value}
              >
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </CardContent>
        </Card>

      </TabsContent>

      <!-- ==================== INFO TAB ==================== -->
      <TabsContent value="info" class="space-y-6">

        <!-- System Status -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="flex items-center gap-2">
                  {#if systemStatus.connected}
                    <CheckCircle class="size-5 text-green-500" />
                  {:else}
                    <XCircle class="size-5 text-destructive" />
                  {/if}
                  System Status
                </CardTitle>
                <CardDescription>Real-time hardware connection status</CardDescription>
              </div>
              <Button
                onclick={loadSystemStatus}
                size="sm"
                variant="outline"
                disabled={statusLoading}
              >
                <RefreshCw class="size-4 mr-2 {statusLoading ? 'animate-spin' : ''}" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div class="p-4 rounded-lg border text-center">
                <div class="text-2xl font-bold">{systemStatus.relays?.length || 0}</div>
                <div class="text-sm text-muted-foreground">Relays</div>
                <div class="text-xs mt-1">
                  {systemStatus.relays?.filter(r => r.state)?.length || 0} active
                </div>
              </div>
              <div class="p-4 rounded-lg border text-center">
                <div class="text-2xl font-bold">{systemStatus.pumps?.length || 0}</div>
                <div class="text-sm text-muted-foreground">Pumps</div>
                <div class="text-xs mt-1">
                  {systemStatus.pumps?.filter(p => p.is_dispensing)?.length || 0} dispensing
                </div>
              </div>
              <div class="p-4 rounded-lg border text-center">
                <div class="text-2xl font-bold">{systemStatus.flowMeters?.length || 0}</div>
                <div class="text-sm text-muted-foreground">Flow Meters</div>
                <div class="text-xs mt-1">
                  {systemStatus.flowMeters?.filter(f => f.status === 'running')?.length || 0} running
                </div>
              </div>
              <div class="p-4 rounded-lg border text-center">
                <div class="text-2xl font-bold">
                  {systemStatus.ecph?.monitoring ? 'ON' : 'OFF'}
                </div>
                <div class="text-sm text-muted-foreground">EC/pH Monitor</div>
                <div class="text-xs mt-1">
                  EC: {systemStatus.ecph?.ec?.toFixed(2) || '0.00'} |
                  pH: {systemStatus.ecph?.ph?.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- About -->
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Info class="size-5" />
              About
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-1">
                <Label class="text-muted-foreground">Application</Label>
                <p class="font-medium">Nutrient Mixing System</p>
              </div>
              <div class="space-y-1">
                <Label class="text-muted-foreground">Version</Label>
                <p class="font-medium">1.0.0</p>
              </div>
              <div class="space-y-1">
                <Label class="text-muted-foreground">Backend</Label>
                <p class="font-medium">Flask + Python</p>
              </div>
              <div class="space-y-1">
                <Label class="text-muted-foreground">Frontend</Label>
                <p class="font-medium">Svelte 5 + Vite</p>
              </div>
            </div>

            <Separator />

            <div class="space-y-2">
              <Label class="text-muted-foreground">Hardware Components</Label>
              <div class="grid gap-2 sm:grid-cols-2 text-sm">
                <div class="p-2 rounded bg-muted/50">
                  <span class="font-medium">Pumps:</span> Atlas Scientific EZO-PMP (I2C)
                </div>
                <div class="p-2 rounded bg-muted/50">
                  <span class="font-medium">Relays:</span> ULN2803A Darlington Array
                </div>
                <div class="p-2 rounded bg-muted/50">
                  <span class="font-medium">Flow Meters:</span> VFS1001 via Optocoupler
                </div>
                <div class="p-2 rounded bg-muted/50">
                  <span class="font-medium">EC/pH:</span> Atlas Scientific EZO (I2C)
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Timing Settings -->
        <Card>
          <CardHeader>
            <CardTitle>Update Intervals</CardTitle>
            <CardDescription>Configure status polling intervals</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-4 sm:grid-cols-3">
              <div class="space-y-2">
                <Label>Status Update (sec)</Label>
                <Input
                  type="number"
                  bind:value={userSettings.timing.status_update_interval}
                  min="0.5"
                  step="0.5"
                />
              </div>
              <div class="space-y-2">
                <Label>Pump Check (sec)</Label>
                <Input
                  type="number"
                  bind:value={userSettings.timing.pump_check_interval}
                  min="0.5"
                  step="0.5"
                />
              </div>
              <div class="space-y-2">
                <Label>Flow Update (sec)</Label>
                <Input
                  type="number"
                  bind:value={userSettings.timing.flow_update_interval}
                  min="0.1"
                  step="0.1"
                />
              </div>
            </div>
          </CardContent>
        </Card>

      </TabsContent>
    </Tabs>

    <!-- Save Button -->
    <div class="flex justify-end pt-6 border-t">
      <Button onclick={saveSettings} disabled={saving} size="lg">
        {#if saving}
          <SettingsIcon class="size-4 mr-2 animate-spin" />
          Saving...
        {:else}
          <Save class="size-4 mr-2" />
          Save All Settings
        {/if}
      </Button>
    </div>
  </div>
{/if}
