<script>
  import { onMount } from 'svelte';
  import { TabsRoot as Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Switch } from "$lib/components/ui/switch/index.js";
  import { Textarea } from "$lib/components/ui/textarea/index.js";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import {
    User,
    Code,
    Plus,
    Trash2,
    Save,
    Settings as SettingsIcon,
    AlertCircle
  } from "@lucide/svelte/icons";
  import { API_BASE_URL } from './config.js';

  let userSettings = $state({
    tanks: {},
    pumps: {
      names: {},
      addresses: {}
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

  let loading = $state(true);
  let saving = $state(false);
  let saveMessage = $state('');

  async function loadSettings() {
    try {
      const [userResponse, devResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/settings/user`),
        fetch(`${API_BASE_URL}/api/settings/developer`)
      ]);
      
      if (userResponse.ok) {
        const userData = await userResponse.json();
        userSettings = { ...userSettings, ...userData };
      }
      if (devResponse.ok) {
        const devData = await devResponse.json();
        devSettings = { ...devSettings, ...devData };
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      saveMessage = 'Error loading settings. Using defaults.';
    } finally {
      loading = false;
    }
  }

  async function saveSettings() {
    saving = true;
    try {
      const [userResponse, devResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/settings/user`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userSettings)
        }),
        fetch(`${API_BASE_URL}/api/settings/developer`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(devSettings)
        })
      ]);

      if (userResponse.ok && devResponse.ok) {
        saveMessage = 'Settings saved successfully!';
      } else {
        saveMessage = 'Error saving settings. Please try again.';
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      saveMessage = 'Error saving settings. Please try again.';
    } finally {
      saving = false;
      setTimeout(() => saveMessage = '', 3000);
    }
  }

  function addTank() {
    const newId = Object.keys(userSettings.tanks || {}).length + 1;
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

  onMount(loadSettings);
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
    <!-- Save Message -->
    {#if saveMessage}
      <Alert variant={saveMessage.includes('Error') ? 'destructive' : 'default'}>
        <AlertCircle class="size-4" />
        <AlertDescription>{saveMessage}</AlertDescription>
      </Alert>
    {/if}

    <!-- Settings Tabs -->
    <Tabs defaultValue="user" class="space-y-6">
      <TabsList class="grid w-full grid-cols-2">
        <TabsTrigger value="user" class="flex items-center gap-2">
          <User class="size-4" />
          User Settings
        </TabsTrigger>
        <TabsTrigger value="developer" class="flex items-center gap-2">
          <Code class="size-4" />
          Developer Settings
        </TabsTrigger>
      </TabsList>

      <!-- User Settings Tab -->
      <TabsContent value="user" class="space-y-6">
        
        <!-- Tank Configuration -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Tank Configuration</CardTitle>
              <Button onclick={addTank} size="sm">
                <Plus class="size-4 mr-2" />
                Add Tank
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {#if userSettings.tanks && Object.keys(userSettings.tanks).length > 0}
              <div class="grid gap-6 md:grid-cols-2">
                {#each Object.entries(userSettings.tanks) as [tankId, tank]}
                  <Card>
                    <CardHeader>
                      <div class="flex items-center justify-between">
                        <h4 class="font-semibold">Tank {tankId}</h4>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onclick={() => removeTank(tankId)}
                        >
                          <Trash2 class="size-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent class="space-y-4">
                      <div class="space-y-2">
                        <Label for="tank-{tankId}-name">Tank Name</Label>
                        <Input 
                          id="tank-{tankId}-name" 
                          bind:value={tank.name}
                          placeholder="Enter tank name"
                        />
                      </div>

                      <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                          <Label for="tank-{tankId}-capacity">Capacity (gal)</Label>
                          <Input 
                            id="tank-{tankId}-capacity" 
                            type="number" 
                            bind:value={tank.capacity_gallons}
                            min="1"
                          />
                        </div>
                        <div class="space-y-2">
                          <Label for="tank-{tankId}-fill">Fill Relay</Label>
                          <Input 
                            id="tank-{tankId}-fill" 
                            type="number" 
                            bind:value={tank.fill_relay}
                            min="0"
                          />
                        </div>
                      </div>

                      <div class="space-y-2">
                        <Label for="tank-{tankId}-send">Send Relay</Label>
                        <Input 
                          id="tank-{tankId}-send" 
                          type="number" 
                          bind:value={tank.send_relay}
                          min="0"
                        />
                      </div>

                      <div class="space-y-2">
                        <div class="flex items-center justify-between">
                          <Label>Mix Relays</Label>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onclick={() => addMixRelay(tankId)}
                          >
                            <Plus class="size-4" />
                          </Button>
                        </div>
                        {#if tank.mix_relays && tank.mix_relays.length > 0}
                          <div class="space-y-2">
                            {#each tank.mix_relays as relay, index}
                              <div class="flex items-center gap-2">
                                <Input 
                                  type="number" 
                                  bind:value={tank.mix_relays[index]}
                                  placeholder="Relay number"
                                  min="0"
                                  class="flex-1"
                                />
                                <Button 
                                  size="sm" 
                                  variant="ghost" 
                                  onclick={() => removeMixRelay(tankId, index)}
                                >
                                  <Trash2 class="size-4" />
                                </Button>
                              </div>
                            {/each}
                          </div>
                        {:else}
                          <p class="text-sm text-muted-foreground">No mix relays configured</p>
                        {/if}
                      </div>
                    </CardContent>
                  </Card>
                {/each}
              </div>
            {:else}
              <div class="text-center py-8">
                <p class="text-muted-foreground">No tanks configured</p>
                <Button onclick={addTank} class="mt-4">
                  <Plus class="size-4 mr-2" />
                  Add Your First Tank
                </Button>
              </div>
            {/if}
          </CardContent>
        </Card>

        <!-- System Limits -->
        <Card>
          <CardHeader>
            <CardTitle>System Limits</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-3 gap-4">
              <div class="space-y-2">
                <Label for="max-pump-volume">Max Pump Volume (ml)</Label>
                <Input 
                  id="max-pump-volume"
                  type="number"
                  bind:value={userSettings.limits.max_pump_volume_ml}
                  min="1"
                />
              </div>
              <div class="space-y-2">
                <Label for="min-pump-volume">Min Pump Volume (ml)</Label>
                <Input 
                  id="min-pump-volume"
                  type="number"
                  bind:value={userSettings.limits.min_pump_volume_ml}
                  min="0.1"
                  step="0.1"
                />
              </div>
              <div class="space-y-2">
                <Label for="max-flow-gallons">Max Flow (gallons)</Label>
                <Input 
                  id="max-flow-gallons"
                  type="number"
                  bind:value={userSettings.limits.max_flow_gallons}
                  min="1"
                />
              </div>
            </div>
          </CardContent>
        </Card>

      </TabsContent>

      <!-- Developer Settings Tab -->
      <TabsContent value="developer" class="space-y-6">
        
        <!-- Hardware Configuration -->
        <Card>
          <CardHeader>
            <CardTitle>Hardware Configuration</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Mock Mode</Label>
                <p class="text-sm text-muted-foreground">
                  Enable mock mode for development without physical hardware
                </p>
              </div>
              <Switch bind:checked={devSettings.mock.mock_mode} />
            </div>

            <Separator />

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="i2c-bus">I2C Bus Number</Label>
                <Input 
                  id="i2c-bus"
                  type="number"
                  bind:value={devSettings.i2c.bus_number}
                  min="0"
                />
              </div>
              <div class="space-y-2">
                <Label for="arduino-baud">Arduino Baud Rate</Label>
                <Input 
                  id="arduino-baud"
                  type="number"
                  bind:value={devSettings.communication.arduino_baudrate}
                />
              </div>
            </div>

            <div class="space-y-2">
              <Label for="command-delay">Command Delay (seconds)</Label>
              <Input 
                id="command-delay"
                type="number"
                bind:value={devSettings.i2c.command_delay}
                min="0"
                step="0.1"
              />
            </div>
          </CardContent>
        </Card>

        <!-- Debug Settings -->
        <Card>
          <CardHeader>
            <CardTitle>Debug Settings</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Enable Debug Logging</Label>
                <p class="text-sm text-muted-foreground">
                  Show detailed debug information in logs
                </p>
              </div>
              <Switch bind:checked={devSettings.debug.debug_mode} />
            </div>

            <div class="flex items-center justify-between">
              <div>
                <Label class="text-base">Verbose Hardware Output</Label>
                <p class="text-sm text-muted-foreground">
                  Log all hardware communication
                </p>
              </div>
              <Switch bind:checked={devSettings.debug.verbose_logging} />
            </div>

            <div class="space-y-2">
              <Label for="log-level">Log Level</Label>
              <Input 
                id="log-level"
                bind:value={devSettings.debug.log_level}
                placeholder="DEBUG, INFO, WARNING, ERROR"
              />
            </div>
          </CardContent>
        </Card>

        <!-- Mock Settings -->
        <Card>
          <CardHeader>
            <CardTitle>Mock Component Settings</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="flex items-center justify-between">
                <Label class="text-base">Mock Pumps</Label>
                <Switch bind:checked={devSettings.mock.mock_pumps} />
              </div>
              <div class="flex items-center justify-between">
                <Label class="text-base">Mock Relays</Label>
                <Switch bind:checked={devSettings.mock.mock_relays} />
              </div>
              <div class="flex items-center justify-between">
                <Label class="text-base">Mock Flow Meters</Label>
                <Switch bind:checked={devSettings.mock.mock_flow_meters} />
              </div>
              <div class="flex items-center justify-between">
                <Label class="text-base">Mock EC/pH</Label>
                <Switch bind:checked={devSettings.mock.mock_ecph} />
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
          Save Settings
        {/if}
      </Button>
    </div>
  </div>
{/if}