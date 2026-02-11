<script>
  import { onMount } from 'svelte';
  import { TabsRoot as Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs/index.js";
  import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Progress } from "$lib/components/ui/progress/index.js";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Separator } from "$lib/components/ui/separator/index.js";
  import { Textarea } from "$lib/components/ui/textarea/index.js";
  import {
    Sprout,
    CalendarDays,
    Droplets,
    FlaskConical,
    Plus,
    Trash2,
    Save,
    CheckCircle,
    Clock,
    Leaf,
    Sun,
    AlertCircle
  } from "@lucide/svelte/icons";

  // ==================== STATE ====================

  let loading = $state(true);
  let saving = $state(false);
  let saveMessage = $state('');
  let saveError = $state('');
  let activeTab = $state('report');

  let cycles = $state({});
  let reports = $state([]);
  let rooms = $state({});
  let nutrientsConfig = $state({});
  let growDefaults = $state({
    veg_days: 28,
    flower_days: 50,
    flush_days: 14,
    feedings_per_day: 2,
    default_watering_volume: 50
  });

  // ==================== DATA LOADING ====================

  onMount(async () => {
    await loadAllData();
  });

  async function loadAllData() {
    loading = true;
    try {
      const [cyclesRes, reportRes, settingsRes, nutrientsRes] = await Promise.all([
        fetch('/api/grow-cycles'),
        fetch('/api/grow-cycles/report'),
        fetch('/api/settings/user'),
        fetch('/api/nutrients')
      ]);

      if (cyclesRes.ok) {
        const data = await cyclesRes.json();
        cycles = data.cycles || {};
      }

      if (reportRes.ok) {
        const data = await reportRes.json();
        reports = data.reports || [];
      }

      if (settingsRes.ok) {
        const data = await settingsRes.json();
        rooms = data.rooms || {};
        if (Object.keys(rooms).length === 0) {
          rooms = { 1: { name: "Grow Room 1", relay: 10 } };
        }
        if (data.growDefaults) {
          growDefaults = { ...growDefaults, ...data.growDefaults };
        }
      }

      if (nutrientsRes.ok) {
        nutrientsConfig = await nutrientsRes.json();
      }

      // Ensure rooms from existing cycles are visible in manage tab
      for (const [roomId, cycle] of Object.entries(cycles)) {
        if (!rooms[roomId]) {
          rooms = { ...rooms, [roomId]: { name: cycle.room_name || `Room ${roomId}` } };
        }
      }
    } catch (err) {
      console.error('Error loading grow cycle data:', err);
    } finally {
      loading = false;
    }
  }

  // ==================== SAVE ====================

  async function saveCycles() {
    saving = true;
    saveMessage = '';
    saveError = '';
    try {
      const response = await fetch('/api/grow-cycles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycles })
      });

      const result = await response.json();
      if (response.ok && result.success) {
        saveMessage = 'Grow cycles saved successfully';
        // Reload reports
        const reportRes = await fetch('/api/grow-cycles/report');
        if (reportRes.ok) {
          const data = await reportRes.json();
          reports = data.reports || [];
        }
      } else {
        saveError = result.error || 'Failed to save grow cycles';
      }
    } catch (err) {
      saveError = 'Network error saving grow cycles';
    } finally {
      saving = false;
      setTimeout(() => { saveMessage = ''; saveError = ''; }, 4000);
    }
  }

  // ==================== CYCLE MANAGEMENT ====================

  function startCycle(roomId) {
    const room = rooms[roomId];
    const today = new Date().toISOString().split('T')[0];
    cycles = {
      ...cycles,
      [roomId]: {
        room_id: String(roomId),
        room_name: room?.name || `Room ${roomId}`,
        strain: '',
        start_date: today,
        veg_days: growDefaults.veg_days,
        flower_days: growDefaults.flower_days,
        flush_days: growDefaults.flush_days,
        watering_volume_gallons: growDefaults.default_watering_volume,
        notes: '',
        active: true
      }
    };
  }

  function endCycle(roomId) {
    const { [roomId]: removed, ...rest } = cycles;
    cycles = rest;
  }

  function updateCycleField(roomId, field, value) {
    cycles = {
      ...cycles,
      [roomId]: {
        ...cycles[roomId],
        [field]: value
      }
    };
  }

  // ==================== STAGE HELPERS ====================

  function getStageInfo(cycle) {
    const start = new Date(cycle.start_date + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffMs = today - start;
    const currentDay = Math.floor(diffMs / 86400000) + 1;

    const vegDays = parseInt(cycle.veg_days) || 0;
    const flowerDays = parseInt(cycle.flower_days) || 0;
    const flushDays = parseInt(cycle.flush_days) || 0;
    const totalDays = vegDays + flowerDays + flushDays;

    let stage, stageDay;
    if (currentDay <= 0) {
      stage = 'not_started';
      stageDay = 0;
    } else if (currentDay <= vegDays) {
      stage = 'veg';
      stageDay = currentDay;
    } else if (currentDay <= vegDays + flowerDays) {
      stage = 'flower';
      stageDay = currentDay - vegDays;
    } else if (currentDay <= totalDays) {
      stage = 'flush';
      stageDay = currentDay - vegDays - flowerDays;
    } else {
      stage = 'complete';
      stageDay = 0;
    }

    const harvestDate = new Date(start);
    harvestDate.setDate(harvestDate.getDate() + totalDays - 1);

    const daysRemaining = stage === 'complete' ? 0 : Math.max(0, Math.ceil((harvestDate - today) / 86400000) + 1);

    return { currentDay: Math.max(0, currentDay), totalDays, stage, stageDay, harvestDate, daysRemaining, vegDays, flowerDays, flushDays };
  }

  function getStageBadgeClass(stage) {
    switch (stage) {
      case 'veg': return 'stage-veg';
      case 'flower': return 'stage-flower';
      case 'flush': return 'stage-flush';
      case 'complete': return 'stage-complete';
      default: return 'stage-pending';
    }
  }

  function getStageLabel(stage) {
    switch (stage) {
      case 'veg': return 'VEG';
      case 'flower': return 'FLOWER';
      case 'flush': return 'FLUSH';
      case 'complete': return 'COMPLETE';
      case 'not_started': return 'NOT STARTED';
      default: return stage.toUpperCase();
    }
  }

  function getProgressVariant(stage) {
    switch (stage) {
      case 'veg': return 'green';
      case 'flower': return 'purple';
      case 'flush': return 'warning';
      default: return 'default';
    }
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  // ==================== DERIVED ====================

  let activeCycleCount = $derived(Object.values(cycles).filter(c => c.active).length);
  let roomIds = $derived(Object.keys(rooms));
</script>

{#if loading}
  <div class="flex items-center justify-center p-12">
    <div class="text-muted-foreground">Loading grow cycle data...</div>
  </div>
{:else}
  <div class="grow-cycles-page">
    <!-- Save Messages -->
    {#if saveMessage}
      <Alert class="mb-4">
        <CheckCircle class="size-4" />
        <AlertDescription>{saveMessage}</AlertDescription>
      </Alert>
    {/if}
    {#if saveError}
      <Alert variant="destructive" class="mb-4">
        <AlertCircle class="size-4" />
        <AlertDescription>{saveError}</AlertDescription>
      </Alert>
    {/if}

    <Tabs value={activeTab} onValueChange={(v) => activeTab = v}>
      <TabsList class="mb-4">
        <TabsTrigger value="report">
          <Sun class="size-4 mr-1.5" />
          Today's Report
        </TabsTrigger>
        <TabsTrigger value="manage">
          <Sprout class="size-4 mr-1.5" />
          Manage Cycles
          {#if activeCycleCount > 0}
            <Badge variant="secondary" class="ml-1.5">{activeCycleCount}</Badge>
          {/if}
        </TabsTrigger>
      </TabsList>

      <!-- ==================== TODAY'S REPORT TAB ==================== -->
      <TabsContent value="report">
        {#if reports.length === 0}
          <Card>
            <CardContent class="flex flex-col items-center justify-center py-12">
              <Sprout class="size-12 text-muted-foreground mb-4" />
              <p class="text-lg font-medium text-muted-foreground mb-2">No Active Grow Cycles</p>
              <p class="text-sm text-muted-foreground mb-4">Start a cycle in the Manage Cycles tab to see daily reports here.</p>
              <Button variant="outline" onclick={() => activeTab = 'manage'}>
                <Plus class="size-4 mr-1.5" />
                Manage Cycles
              </Button>
            </CardContent>
          </Card>
        {:else}
          <div class="grid gap-4">
            {#each reports as report}
              {@const progressPct = report.total_days > 0 ? Math.round((report.current_day / report.total_days) * 100) : 0}
              {@const nutrients = Object.entries(report.recipe_per_gallon || {})}
              <Card>
                <CardHeader class="pb-3">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="flex size-10 items-center justify-center rounded-lg bg-green-500/10">
                        <Sprout class="size-5 text-green-500" />
                      </div>
                      <div>
                        <CardTitle class="text-lg">{report.room_name}</CardTitle>
                        {#if report.strain}
                          <CardDescription>{report.strain}</CardDescription>
                        {/if}
                      </div>
                    </div>
                    <Badge class={getStageBadgeClass(report.current_stage)}>
                      {getStageLabel(report.current_stage)}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <!-- Progress -->
                  <div class="mb-4">
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="text-muted-foreground">
                        Day {report.current_day} of {report.total_days}
                        {#if report.current_stage !== 'complete' && report.current_stage !== 'not_started'}
                          &mdash; {getStageLabel(report.current_stage)} Day {report.stage_day}
                        {/if}
                      </span>
                      <span class="font-medium">{Math.min(progressPct, 100)}%</span>
                    </div>
                    <Progress value={Math.min(report.current_day, report.total_days)} max={report.total_days} variant={getProgressVariant(report.current_stage)} />
                    <div class="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>Veg: {report.veg_days}d</span>
                      <span>Flower: {report.flower_days}d</span>
                      <span>Flush: {report.flush_days}d</span>
                    </div>
                  </div>

                  <Separator class="my-3" />

                  <!-- Targets -->
                  <div class="flex items-center gap-3 mb-3 flex-wrap">
                    <div class="flex items-center gap-1.5">
                      <FlaskConical class="size-4 text-muted-foreground" />
                      <span class="text-sm font-medium">
                        {#if report.current_stage === 'flush'}
                          Flush (Cake)
                        {:else if report.sub_stage === 'flower_veg'}
                          Veg Formula (Early Flower)
                        {:else if report.recipe_name === 'veg_formula'}
                          Veg Formula
                        {:else if report.recipe_name === 'bloom_formula'}
                          Bloom Formula
                        {:else}
                          &mdash;
                        {/if}
                      </span>
                    </div>
                    <Badge variant="outline">EC {report.target_ec[0]}{report.target_ec[1] !== report.target_ec[0] ? `–${report.target_ec[1]}` : ''}</Badge>
                    <Badge variant="outline">pH {report.target_ph}</Badge>
                    <Badge variant="outline">
                      <Droplets class="size-3 mr-1" />
                      {report.watering_volume_gallons} gal &times; {report.feedings_per_day || 2}/day
                    </Badge>
                  </div>

                  <!-- Dosage Table -->
                  {#if nutrients.length > 0}
                    <div class="dosage-table">
                      <div class="dosage-header">
                        <span>Nutrient</span>
                        <span>ml/gal</span>
                        <span>Per Feed</span>
                        <span>Daily ({report.feedings_per_day || 2}x)</span>
                      </div>
                      {#each nutrients as [name, mlPerGal]}
                        <div class="dosage-row">
                          <span class="font-medium">{name}</span>
                          <span>{mlPerGal}</span>
                          <span>{report.recipe_total_ml[name]}</span>
                          <span class="font-medium">{report.recipe_daily_total_ml?.[name] ?? report.recipe_total_ml[name] * 2}</span>
                        </div>
                      {/each}
                    </div>
                  {:else if report.current_stage === 'flush'}
                    <div class="flush-notice">
                      <Droplets class="size-5 text-blue-400" />
                      <div>
                        <p class="font-medium">Flush with Cake</p>
                        <p class="text-sm text-muted-foreground">Cake only during flush period. Target EC 0.0–0.3</p>
                      </div>
                    </div>
                  {/if}

                  <Separator class="my-3" />

                  <!-- Harvest Info -->
                  <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center gap-1.5 text-muted-foreground">
                      <CalendarDays class="size-4" />
                      <span>Harvest: {formatDate(report.harvest_date)}</span>
                    </div>
                    {#if report.days_remaining > 0}
                      <div class="flex items-center gap-1.5">
                        <Clock class="size-4 text-muted-foreground" />
                        <span class="font-medium">{report.days_remaining} days remaining</span>
                      </div>
                    {:else if report.current_stage === 'complete'}
                      <Badge variant="outline" class="text-green-500">
                        <CheckCircle class="size-3 mr-1" />
                        Cycle Complete
                      </Badge>
                    {/if}
                  </div>
                </CardContent>
              </Card>
            {/each}
          </div>
        {/if}
      </TabsContent>

      <!-- ==================== MANAGE CYCLES TAB ==================== -->
      <TabsContent value="manage">
        <div class="grid gap-4">
          {#each roomIds as roomId}
            {@const room = rooms[roomId]}
            {@const cycle = cycles[roomId]}
            <Card>
              <CardHeader class="pb-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="flex size-10 items-center justify-center rounded-lg {cycle ? 'bg-green-500/10' : 'bg-muted'}">
                      {#if cycle}
                        <Sprout class="size-5 text-green-500" />
                      {:else}
                        <Leaf class="size-5 text-muted-foreground" />
                      {/if}
                    </div>
                    <div>
                      <CardTitle class="text-lg">{room?.name || `Room ${roomId}`}</CardTitle>
                      {#if cycle}
                        {@const info = getStageInfo(cycle)}
                        <CardDescription>
                          Day {info.currentDay} &mdash; {getStageLabel(info.stage)}
                          {#if info.stage !== 'not_started' && info.stage !== 'complete'}
                            (Day {info.stageDay})
                          {/if}
                        </CardDescription>
                      {:else}
                        <CardDescription>No active cycle</CardDescription>
                      {/if}
                    </div>
                  </div>
                  {#if cycle}
                    <Badge class={getStageBadgeClass(getStageInfo(cycle).stage)}>
                      {getStageLabel(getStageInfo(cycle).stage)}
                    </Badge>
                  {/if}
                </div>
              </CardHeader>
              <CardContent>
                {#if cycle}
                  <div class="cycle-form">
                    <div class="form-row">
                      <div class="form-field">
                        <Label for="strain-{roomId}">Strain</Label>
                        <Input
                          id="strain-{roomId}"
                          value={cycle.strain}
                          oninput={(e) => updateCycleField(roomId, 'strain', e.target.value)}
                          placeholder="e.g., Wedding Cake"
                        />
                      </div>
                      <div class="form-field">
                        <Label for="start-{roomId}">Start Date</Label>
                        <Input
                          id="start-{roomId}"
                          type="date"
                          value={cycle.start_date}
                          oninput={(e) => updateCycleField(roomId, 'start_date', e.target.value)}
                        />
                      </div>
                    </div>

                    <div class="form-row">
                      <div class="form-field">
                        <Label for="veg-{roomId}">Veg Days</Label>
                        <Input
                          id="veg-{roomId}"
                          type="number"
                          min="0"
                          value={cycle.veg_days}
                          oninput={(e) => updateCycleField(roomId, 'veg_days', parseInt(e.target.value) || 0)}
                        />
                      </div>
                      <div class="form-field">
                        <Label for="flower-{roomId}">Flower Days</Label>
                        <Input
                          id="flower-{roomId}"
                          type="number"
                          min="0"
                          value={cycle.flower_days}
                          oninput={(e) => updateCycleField(roomId, 'flower_days', parseInt(e.target.value) || 0)}
                        />
                      </div>
                      <div class="form-field">
                        <Label for="flush-{roomId}">Flush Days</Label>
                        <Input
                          id="flush-{roomId}"
                          type="number"
                          min="0"
                          value={cycle.flush_days}
                          oninput={(e) => updateCycleField(roomId, 'flush_days', parseInt(e.target.value) || 0)}
                        />
                      </div>
                    </div>

                    <div class="form-row">
                      <div class="form-field">
                        <Label for="volume-{roomId}">Watering Volume (gallons)</Label>
                        <Input
                          id="volume-{roomId}"
                          type="number"
                          min="1"
                          value={cycle.watering_volume_gallons}
                          oninput={(e) => updateCycleField(roomId, 'watering_volume_gallons', parseInt(e.target.value) || 1)}
                        />
                      </div>
                      {#if cycle}
                        {@const harvestInfo = getStageInfo(cycle)}
                        <div class="form-field">
                          <Label>Harvest Date</Label>
                          <div class="harvest-date-display">
                            <CalendarDays class="size-4 text-muted-foreground" />
                            <span>{formatDate(harvestInfo.harvestDate.toISOString().split('T')[0])}</span>
                            {#if harvestInfo.daysRemaining > 0}
                              <Badge variant="outline" class="ml-auto">{harvestInfo.daysRemaining}d left</Badge>
                            {/if}
                          </div>
                        </div>
                      {/if}
                    </div>

                    <div class="form-field">
                      <Label for="notes-{roomId}">Notes</Label>
                      <Textarea
                        id="notes-{roomId}"
                        value={cycle.notes}
                        oninput={(e) => updateCycleField(roomId, 'notes', e.target.value)}
                        placeholder="Optional notes about this cycle..."
                        rows="2"
                      />
                    </div>

                    <div class="flex gap-2 mt-3">
                      <Button onclick={saveCycles} disabled={saving}>
                        <Save class="size-4 mr-1.5" />
                        {saving ? 'Saving...' : 'Save'}
                      </Button>
                      <Button variant="destructive" onclick={() => endCycle(roomId)}>
                        <Trash2 class="size-4 mr-1.5" />
                        End Cycle
                      </Button>
                    </div>
                  </div>
                {:else}
                  <div class="flex flex-col items-center py-6">
                    <p class="text-sm text-muted-foreground mb-3">No active grow cycle for this room.</p>
                    <Button onclick={() => startCycle(roomId)}>
                      <Plus class="size-4 mr-1.5" />
                      Start New Cycle
                    </Button>
                  </div>
                {/if}
              </CardContent>
            </Card>
          {/each}

          {#if roomIds.length === 0}
            <Card>
              <CardContent class="flex flex-col items-center justify-center py-12">
                <AlertCircle class="size-12 text-muted-foreground mb-4" />
                <p class="text-lg font-medium text-muted-foreground mb-2">No Rooms Configured</p>
                <p class="text-sm text-muted-foreground">Add rooms in the Settings page to start tracking grow cycles.</p>
              </CardContent>
            </Card>
          {/if}
        </div>
      </TabsContent>
    </Tabs>
  </div>
{/if}

<style>
  .grow-cycles-page {
    padding: 0;
  }

  .dosage-table {
    border: 1px solid hsl(var(--border));
    border-radius: 0.5rem;
    overflow: hidden;
  }

  .dosage-header {
    display: grid;
    grid-template-columns: 1fr 70px 90px 90px;
    padding: 0.5rem 0.75rem;
    background: hsl(var(--muted));
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: hsl(var(--muted-foreground));
  }

  .dosage-row {
    display: grid;
    grid-template-columns: 1fr 70px 90px 90px;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
    border-top: 1px solid hsl(var(--border));
  }

  .dosage-row:hover {
    background: hsl(var(--muted) / 0.5);
  }

  .flush-notice {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 0.5rem;
    background: hsl(var(--muted) / 0.5);
    border: 1px solid hsl(var(--border));
  }

  .cycle-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.75rem;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .harvest-date-display {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    height: 2.25rem;
    padding: 0 0.75rem;
    border-radius: 0.375rem;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--muted) / 0.3);
    font-size: 0.875rem;
  }

  :global(.stage-veg) {
    background-color: hsl(142 76% 36% / 0.15) !important;
    color: hsl(142 76% 36%) !important;
    border-color: hsl(142 76% 36% / 0.3) !important;
  }

  :global(.stage-flower) {
    background-color: hsl(271 91% 65% / 0.15) !important;
    color: hsl(271 91% 65%) !important;
    border-color: hsl(271 91% 65% / 0.3) !important;
  }

  :global(.stage-flush) {
    background-color: hsl(199 89% 48% / 0.15) !important;
    color: hsl(199 89% 48%) !important;
    border-color: hsl(199 89% 48% / 0.3) !important;
  }

  :global(.stage-complete) {
    background-color: hsl(var(--muted)) !important;
    color: hsl(var(--muted-foreground)) !important;
  }

  :global(.stage-pending) {
    background-color: hsl(var(--muted)) !important;
    color: hsl(var(--muted-foreground)) !important;
  }
</style>
