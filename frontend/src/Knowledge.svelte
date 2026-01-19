<script>
  import { TabsRoot as Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs/index.js";
  import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "$lib/components/ui/card/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import {
    Thermometer,
    Droplets,
    Sun,
    TrendingUp,
    Bug,
    Wrench,
    Calculator,
    Leaf,
    FlaskConical,
    Clock,
    AlertTriangle,
    CheckCircle,
    Info
  } from "@lucide/svelte/icons";

  // Import knowledge data
  import environmentData from '$lib/data/knowledge/environment.json';
  import nutrientsData from '$lib/data/knowledge/nutrients.json';
  import lightingData from '$lib/data/knowledge/lighting.json';
  import cropSteeringData from '$lib/data/knowledge/crop-steering.json';
  import ipmData from '$lib/data/knowledge/ipm.json';
  import operationsData from '$lib/data/knowledge/operations.json';

  let activeTab = $state('environment');

  // VPD Calculator state
  let vpdTemp = $state(78);
  let vpdHumidity = $state(55);
  let calculatedVpd = $derived(calculateVPD(vpdTemp, vpdHumidity));
  let vpdRecommendation = $derived(getVPDRecommendation(calculatedVpd));

  // DLI Calculator state
  let dliPpfd = $state(600);
  let dliHours = $state(12);
  let calculatedDli = $derived(calculateDLI(dliPpfd, dliHours));
  let dliRecommendation = $derived(getDLIRecommendation(calculatedDli));

  // Dryback Calculator state
  let drybackWetWeight = $state(10);
  let drybackCurrentWeight = $state(8.5);
  let drybackDryWeight = $state(2);
  let calculatedDryback = $derived(calculateDryback(drybackWetWeight, drybackCurrentWeight, drybackDryWeight));
  let drybackRecommendation = $derived(getDrybackRecommendation(calculatedDryback));

  // VPD Calculation (Magnus formula approximation)
  function calculateVPD(tempF, rh) {
    const tempC = (tempF - 32) * 5/9;
    // Saturation vapor pressure (kPa)
    const svp = 0.6108 * Math.exp((17.27 * tempC) / (tempC + 237.3));
    // Actual vapor pressure
    const avp = svp * (rh / 100);
    // VPD
    const vpd = svp - avp;
    return Math.round(vpd * 100) / 100;
  }

  function getVPDRecommendation(vpd) {
    if (vpd < 0.4) return { status: 'low', message: 'Too low - risk of mold/slow growth', color: 'text-blue-400' };
    if (vpd <= 0.8) return { status: 'clone', message: 'Ideal for clones/seedlings', color: 'text-green-400' };
    if (vpd <= 1.0) return { status: 'early-veg', message: 'Ideal for early veg', color: 'text-green-400' };
    if (vpd <= 1.2) return { status: 'late-veg', message: 'Ideal for late veg', color: 'text-green-400' };
    if (vpd <= 1.5) return { status: 'flower', message: 'Ideal for flower', color: 'text-green-400' };
    if (vpd <= 1.6) return { status: 'late-flower', message: 'Ideal for late flower/ripen', color: 'text-green-400' };
    return { status: 'high', message: 'Too high - risk of stress/wilting', color: 'text-red-400' };
  }

  // DLI Calculation
  function calculateDLI(ppfd, hours) {
    return Math.round((ppfd * hours * 3600) / 1000000 * 10) / 10;
  }

  function getDLIRecommendation(dli) {
    if (dli < 8) return { status: 'low', message: 'Too low for cannabis', color: 'text-red-400' };
    if (dli <= 12) return { status: 'clone', message: 'Good for clones', color: 'text-green-400' };
    if (dli <= 18) return { status: 'seedling', message: 'Good for seedlings', color: 'text-green-400' };
    if (dli <= 25) return { status: 'early-veg', message: 'Good for early veg', color: 'text-green-400' };
    if (dli <= 35) return { status: 'late-veg', message: 'Good for late veg', color: 'text-green-400' };
    if (dli <= 45) return { status: 'early-flower', message: 'Good for flower', color: 'text-green-400' };
    if (dli <= 55) return { status: 'peak-flower', message: 'Peak flower intensity', color: 'text-green-400' };
    return { status: 'high', message: 'Very high - watch for light stress', color: 'text-yellow-400' };
  }

  // Dryback Calculation
  function calculateDryback(wet, current, dry) {
    if (wet <= dry) return 0;
    const totalWaterCapacity = wet - dry;
    const waterLost = wet - current;
    return Math.round((waterLost / totalWaterCapacity) * 100);
  }

  function getDrybackRecommendation(dryback) {
    if (dryback < 5) return { status: 'saturated', message: 'Very wet - minimal dryback', color: 'text-blue-400' };
    if (dryback <= 15) return { status: 'vegetative', message: 'Vegetative steering range', color: 'text-green-400' };
    if (dryback <= 25) return { status: 'balanced', message: 'Balanced steering range', color: 'text-green-400' };
    if (dryback <= 35) return { status: 'generative', message: 'Generative steering range', color: 'text-green-400' };
    if (dryback <= 50) return { status: 'dry', message: 'Getting dry - irrigate soon', color: 'text-yellow-400' };
    return { status: 'critical', message: 'Too dry - irrigate immediately', color: 'text-red-400' };
  }

  // Helper to get VPD stage color for table
  function getVPDColor(vpd) {
    if (vpd <= 0.8) return 'bg-cyan-500/20 text-cyan-300';
    if (vpd <= 1.2) return 'bg-green-500/20 text-green-300';
    if (vpd <= 1.5) return 'bg-yellow-500/20 text-yellow-300';
    return 'bg-orange-500/20 text-orange-300';
  }
</script>

<div class="space-y-6 p-1">
  <Tabs bind:value={activeTab} class="space-y-6">
    <TabsList class="grid w-full grid-cols-6 h-auto">
      <TabsTrigger value="environment" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <Thermometer class="size-4" />
        <span>Environment</span>
      </TabsTrigger>
      <TabsTrigger value="nutrients" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <FlaskConical class="size-4" />
        <span>Nutrients</span>
      </TabsTrigger>
      <TabsTrigger value="lighting" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <Sun class="size-4" />
        <span>Lighting</span>
      </TabsTrigger>
      <TabsTrigger value="steering" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <TrendingUp class="size-4" />
        <span>Steering</span>
      </TabsTrigger>
      <TabsTrigger value="ipm" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <Bug class="size-4" />
        <span>IPM</span>
      </TabsTrigger>
      <TabsTrigger value="operations" class="flex flex-col items-center gap-1 py-2 px-1 text-xs">
        <Wrench class="size-4" />
        <span>Operations</span>
      </TabsTrigger>
    </TabsList>

    <!-- ENVIRONMENT TAB -->
    <TabsContent value="environment" class="space-y-4">
      <div class="grid gap-4 md:grid-cols-2">
        <!-- VPD Calculator -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-base">
              <Calculator class="size-4 text-cyan-400" />
              VPD Calculator
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="vpd-temp">Temperature (°F)</Label>
                <Input id="vpd-temp" type="number" bind:value={vpdTemp} min="60" max="100" />
              </div>
              <div class="space-y-2">
                <Label for="vpd-humidity">Humidity (%)</Label>
                <Input id="vpd-humidity" type="number" bind:value={vpdHumidity} min="20" max="90" />
              </div>
            </div>
            <div class="rounded-lg bg-muted p-4 text-center">
              <div class="text-3xl font-bold text-cyan-400">{calculatedVpd} kPa</div>
              <div class="text-sm {vpdRecommendation.color}">{vpdRecommendation.message}</div>
            </div>
          </CardContent>
        </Card>

        <!-- Temperature Guide -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-base">
              <Thermometer class="size-4 text-orange-400" />
              Temperature Targets
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-3">
            <div class="flex justify-between items-center py-2 border-b border-border">
              <span class="text-muted-foreground">Day</span>
              <Badge variant="secondary">{environmentData.temperature.day_range_f[0]}-{environmentData.temperature.day_range_f[1]}°F</Badge>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-border">
              <span class="text-muted-foreground">Night</span>
              <Badge variant="secondary">{environmentData.temperature.night_range_f[0]}-{environmentData.temperature.night_range_f[1]}°F</Badge>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-border">
              <span class="text-muted-foreground">Day/Night Diff</span>
              <Badge variant="secondary">{environmentData.temperature.day_night_differential.min}-{environmentData.temperature.day_night_differential.max}°F</Badge>
            </div>
            <div class="text-xs text-muted-foreground mt-2">
              <Info class="size-3 inline mr-1" />
              Drop night temps to 65-70°F in final 2 weeks for terpenes
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- VPD Chart -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Droplets class="size-4 text-blue-400" />
            VPD Targets by Growth Stage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Stage</th>
                  <th class="text-center py-2 px-2">VPD (kPa)</th>
                  <th class="text-center py-2 px-2">Temp (°F)</th>
                  <th class="text-center py-2 px-2">RH (%)</th>
                  <th class="text-left py-2 px-2 hidden md:table-cell">Notes</th>
                </tr>
              </thead>
              <tbody>
                {#each Object.entries(environmentData.vpd_stages) as [key, stage]}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{stage.label}</td>
                    <td class="text-center py-2 px-2">
                      <Badge class={getVPDColor(stage.optimal_vpd)}>{stage.vpd_kpa[0]}-{stage.vpd_kpa[1]}</Badge>
                    </td>
                    <td class="text-center py-2 px-2">{stage.temp_f[0]}-{stage.temp_f[1]}</td>
                    <td class="text-center py-2 px-2">{stage.rh[0]}-{stage.rh[1]}</td>
                    <td class="py-2 px-2 text-muted-foreground text-xs hidden md:table-cell">{stage.notes}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <!-- CO2 Card -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Leaf class="size-4 text-green-400" />
            CO2 Guidelines
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Ambient</div>
              <div class="text-lg font-bold">{environmentData.co2.ambient_ppm[0]}-{environmentData.co2.ambient_ppm[1]} ppm</div>
            </div>
            <div class="p-3 rounded-lg bg-green-500/10">
              <div class="text-xs text-muted-foreground">Elevated</div>
              <div class="text-lg font-bold text-green-400">{environmentData.co2.elevated_ppm[0]}-{environmentData.co2.elevated_ppm[1]} ppm</div>
            </div>
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Max Benefit</div>
              <div class="text-lg font-bold">{environmentData.co2.maximum_benefit_ppm} ppm</div>
            </div>
          </div>
          <p class="text-xs text-muted-foreground mt-3">{environmentData.co2.notes}</p>
        </CardContent>
      </Card>
    </TabsContent>

    <!-- NUTRIENTS TAB -->
    <TabsContent value="nutrients" class="space-y-4">
      <!-- Protocol Summary -->
      <Card class="border-cyan-500/50">
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <CheckCircle class="size-4 text-cyan-400" />
            Your Protocol (Crop Salt + Coco)
          </CardTitle>
          <CardDescription>{nutrientsData.protocol_summary.philosophy}</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-3 rounded-lg bg-cyan-500/10">
              <div class="text-xs text-muted-foreground">Target pH</div>
              <div class="text-2xl font-bold text-cyan-400">{nutrientsData.protocol_summary.target_ph}</div>
            </div>
            <div class="p-3 rounded-lg bg-green-500/10">
              <div class="text-xs text-muted-foreground">Target EC</div>
              <div class="text-2xl font-bold text-green-400">{nutrientsData.protocol_summary.target_ec}</div>
            </div>
            <div class="p-3 rounded-lg bg-yellow-500/10">
              <div class="text-xs text-muted-foreground">Heavy Flower EC</div>
              <div class="text-2xl font-bold text-yellow-400">{nutrientsData.protocol_summary.heavy_flower_ec}</div>
            </div>
          </div>
          <p class="text-xs text-muted-foreground mt-3 flex items-start gap-1">
            <Info class="size-3 mt-0.5 flex-shrink-0" />
            {nutrientsData.protocol_summary.notes}
          </p>
        </CardContent>
      </Card>

      <!-- EC/pH by Stage -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <FlaskConical class="size-4 text-purple-400" />
            EC/pH by Stage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Stage</th>
                  <th class="text-center py-2 px-2">EC</th>
                  <th class="text-center py-2 px-2">pH</th>
                  <th class="text-left py-2 px-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {#each nutrientsData.ec_ph_by_stage as row}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{row.stage}</td>
                    <td class="text-center py-2 px-2">
                      <Badge variant="secondary">{row.ec[0]}{row.ec[1] !== row.ec[0] ? `-${row.ec[1]}` : ''}</Badge>
                    </td>
                    <td class="text-center py-2 px-2">{row.ph}</td>
                    <td class="py-2 px-2 text-muted-foreground text-xs">{row.notes}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <!-- Crop Salt Products -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Droplets class="size-4 text-blue-400" />
            Crop Salt Products
          </CardTitle>
          <CardDescription>Liquid Concentrate - Label rate: 30ml/gal</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid gap-2">
            {#each nutrientsData.crop_salt.products as product}
              <div class="flex items-center justify-between py-2 px-3 rounded-lg bg-muted/50">
                <div>
                  <span class="font-medium">{product.name}</span>
                  <span class="text-xs text-muted-foreground ml-2">{product.usage}</span>
                </div>
                {#if product.label_rate_ml_gal}
                  <Badge variant="outline">{product.label_rate_ml_gal} ml/gal</Badge>
                {:else if product.default_ml_gal}
                  <Badge variant="outline">{product.default_ml_gal} ml/gal</Badge>
                {/if}
              </div>
            {/each}
          </div>
        </CardContent>
      </Card>

      <!-- Additives -->
      <div class="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm">Power Si Bloom</CardTitle>
          </CardHeader>
          <CardContent class="text-xs text-muted-foreground">
            <p>{nutrientsData.additives.power_si_bloom.notes}</p>
            <div class="mt-2 flex flex-wrap gap-1">
              {#each nutrientsData.additives.power_si_bloom.benefits as benefit}
                <Badge variant="secondary" class="text-xs">{benefit}</Badge>
              {/each}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm">Clonex Solution</CardTitle>
          </CardHeader>
          <CardContent class="text-xs text-muted-foreground">
            <p>EC Target: {nutrientsData.additives.clonex_solution.ec_target[0]}-{nutrientsData.additives.clonex_solution.ec_target[1]}</p>
            <p class="mt-1">{nutrientsData.additives.clonex_solution.notes}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm">Clonex Mist</CardTitle>
          </CardHeader>
          <CardContent class="text-xs text-muted-foreground">
            <p>Frequency: {nutrientsData.additives.clonex_mist.frequency}</p>
            <p class="mt-1">{nutrientsData.additives.clonex_mist.notes}</p>
          </CardContent>
        </Card>
      </div>

      <!-- Flush Protocol -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Clock class="size-4 text-yellow-400" />
            Flush Protocol
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-3 gap-4 text-center mb-4">
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Duration</div>
              <div class="text-lg font-bold">{nutrientsData.flush_protocol.duration_days[0]}-{nutrientsData.flush_protocol.duration_days[1]} days</div>
            </div>
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">EC Target</div>
              <div class="text-lg font-bold">{nutrientsData.flush_protocol.ec_target[0]}-{nutrientsData.flush_protocol.ec_target[1]}</div>
            </div>
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Method</div>
              <div class="text-lg font-bold">{nutrientsData.flush_protocol.method}</div>
            </div>
          </div>
          <div class="text-sm">
            <div class="font-medium mb-2">Timing Indicators:</div>
            <ul class="space-y-1 text-muted-foreground text-xs">
              {#each nutrientsData.flush_protocol.indicators as indicator}
                <li class="flex items-center gap-2">
                  <CheckCircle class="size-3 text-green-400" />
                  {indicator}
                </li>
              {/each}
            </ul>
          </div>
        </CardContent>
      </Card>
    </TabsContent>

    <!-- LIGHTING TAB -->
    <TabsContent value="lighting" class="space-y-4">
      <div class="grid gap-4 md:grid-cols-2">
        <!-- DLI Calculator -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-base">
              <Calculator class="size-4 text-yellow-400" />
              DLI Calculator
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="dli-ppfd">PPFD (μmol/m²/s)</Label>
                <Input id="dli-ppfd" type="number" bind:value={dliPpfd} min="100" max="1500" />
              </div>
              <div class="space-y-2">
                <Label for="dli-hours">Photoperiod (hrs)</Label>
                <Input id="dli-hours" type="number" bind:value={dliHours} min="1" max="24" />
              </div>
            </div>
            <div class="rounded-lg bg-muted p-4 text-center">
              <div class="text-3xl font-bold text-yellow-400">{calculatedDli} mol/m²/day</div>
              <div class="text-sm {dliRecommendation.color}">{dliRecommendation.message}</div>
            </div>
          </CardContent>
        </Card>

        <!-- Photoperiods -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="flex items-center gap-2 text-base">
              <Clock class="size-4 text-purple-400" />
              Photoperiod Schedules
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-3">
            {#each Object.entries(lightingData.photoperiods) as [key, period]}
              <div class="flex justify-between items-center py-2 border-b border-border/50">
                <span class="capitalize">{key.replace('_', ' ')}</span>
                <div class="text-right">
                  <Badge variant="secondary">{period.light_hours}/{period.dark_hours}</Badge>
                  <div class="text-xs text-muted-foreground">{period.notes}</div>
                </div>
              </div>
            {/each}
          </CardContent>
        </Card>
      </div>

      <!-- DLI Chart -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Sun class="size-4 text-yellow-400" />
            DLI & PPFD Targets by Stage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Stage</th>
                  <th class="text-center py-2 px-2">DLI (mol/m²/day)</th>
                  <th class="text-center py-2 px-2">PPFD (μmol)</th>
                  <th class="text-center py-2 px-2">Hours</th>
                  <th class="text-left py-2 px-2 hidden md:table-cell">Notes</th>
                </tr>
              </thead>
              <tbody>
                {#each lightingData.dli_targets as row}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{row.stage}</td>
                    <td class="text-center py-2 px-2">
                      <Badge variant="secondary">{row.dli_mol[0]}-{row.dli_mol[1]}</Badge>
                    </td>
                    <td class="text-center py-2 px-2">{row.ppfd_umol[0]}-{row.ppfd_umol[1]}</td>
                    <td class="text-center py-2 px-2">{row.photoperiod_hours}</td>
                    <td class="py-2 px-2 text-muted-foreground text-xs hidden md:table-cell">{row.notes}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <!-- Light Distance -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Info class="size-4 text-blue-400" />
            Light Height Guidelines (LED Bar Style)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Clone/Seedling</div>
              <div class="text-lg font-bold">{lightingData.light_distance_guidelines.led_bar_style.clone_seedling_inches[0]}-{lightingData.light_distance_guidelines.led_bar_style.clone_seedling_inches[1]}"</div>
            </div>
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Veg</div>
              <div class="text-lg font-bold">{lightingData.light_distance_guidelines.led_bar_style.veg_inches[0]}-{lightingData.light_distance_guidelines.led_bar_style.veg_inches[1]}"</div>
            </div>
            <div class="p-3 rounded-lg bg-muted">
              <div class="text-xs text-muted-foreground">Flower</div>
              <div class="text-lg font-bold">{lightingData.light_distance_guidelines.led_bar_style.flower_inches[0]}-{lightingData.light_distance_guidelines.led_bar_style.flower_inches[1]}"</div>
            </div>
          </div>
          <p class="text-xs text-muted-foreground mt-3">{lightingData.light_distance_guidelines.general_rule}</p>
        </CardContent>
      </Card>
    </TabsContent>

    <!-- CROP STEERING TAB -->
    <TabsContent value="steering" class="space-y-4">
      <!-- Dryback Calculator -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Calculator class="size-4 text-green-400" />
            Dry-back Calculator
          </CardTitle>
          <CardDescription>Weigh your pot to determine dry-back percentage</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-3 gap-4">
            <div class="space-y-2">
              <Label for="db-wet">Wet Weight (lbs)</Label>
              <Input id="db-wet" type="number" step="0.1" bind:value={drybackWetWeight} min="0" />
            </div>
            <div class="space-y-2">
              <Label for="db-current">Current Weight (lbs)</Label>
              <Input id="db-current" type="number" step="0.1" bind:value={drybackCurrentWeight} min="0" />
            </div>
            <div class="space-y-2">
              <Label for="db-dry">Dry Weight (lbs)</Label>
              <Input id="db-dry" type="number" step="0.1" bind:value={drybackDryWeight} min="0" />
            </div>
          </div>
          <div class="rounded-lg bg-muted p-4 text-center">
            <div class="text-3xl font-bold text-green-400">{calculatedDryback}%</div>
            <div class="text-sm {drybackRecommendation.color}">{drybackRecommendation.message}</div>
          </div>
        </CardContent>
      </Card>

      <!-- Steering Strategies -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <TrendingUp class="size-4 text-cyan-400" />
            Crop Steering Strategies (100% Coco)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Strategy</th>
                  <th class="text-center py-2 px-2">Dry-back</th>
                  <th class="text-center py-2 px-2">EC</th>
                  <th class="text-center py-2 px-2">VPD (kPa)</th>
                  <th class="text-left py-2 px-2">Best For</th>
                </tr>
              </thead>
              <tbody>
                {#each Object.entries(cropSteeringData.strategies) as [key, strategy]}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{strategy.label}</td>
                    <td class="text-center py-2 px-2">
                      <Badge variant="secondary">{strategy.dryback_percent[0]}-{strategy.dryback_percent[1]}%</Badge>
                    </td>
                    <td class="text-center py-2 px-2">{strategy.ec_range[0]}-{strategy.ec_range[1]}</td>
                    <td class="text-center py-2 px-2">{strategy.vpd_range_kpa[0]}-{strategy.vpd_range_kpa[1]}</td>
                    <td class="py-2 px-2 text-xs text-muted-foreground">
                      {strategy.best_for.join(', ')}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <!-- Irrigation Timing -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Clock class="size-4 text-blue-400" />
            Irrigation Timing Protocol
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div class="flex items-start gap-3 p-3 rounded-lg bg-green-500/10">
              <Badge class="bg-green-500/20 text-green-300">First</Badge>
              <div>
                <div class="font-medium">{cropSteeringData.irrigation_timing.first_irrigation.timing}</div>
                <div class="text-xs text-muted-foreground">{cropSteeringData.irrigation_timing.first_irrigation.notes}</div>
              </div>
            </div>
            <div class="flex items-start gap-3 p-3 rounded-lg bg-cyan-500/10">
              <Badge class="bg-cyan-500/20 text-cyan-300">P1</Badge>
              <div>
                <div class="font-medium">{cropSteeringData.irrigation_timing.p1_shot.description}</div>
                <div class="text-xs text-muted-foreground">{cropSteeringData.irrigation_timing.p1_shot.purpose}</div>
              </div>
            </div>
            <div class="flex items-start gap-3 p-3 rounded-lg bg-muted">
              <Badge variant="secondary">P2-P4</Badge>
              <div>
                <div class="font-medium">{cropSteeringData.irrigation_timing.maintenance_shots.description}</div>
                <div class="text-xs text-muted-foreground">{cropSteeringData.irrigation_timing.maintenance_shots.purpose}</div>
              </div>
            </div>
            <div class="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/10">
              <Badge class="bg-yellow-500/20 text-yellow-300">Last</Badge>
              <div>
                <div class="font-medium">{cropSteeringData.irrigation_timing.last_irrigation.timing}</div>
                <div class="text-xs text-muted-foreground">{cropSteeringData.irrigation_timing.last_irrigation.notes}</div>
              </div>
            </div>
            <div class="flex items-start gap-3 p-3 rounded-lg bg-purple-500/10">
              <Badge class="bg-purple-500/20 text-purple-300">Night</Badge>
              <div>
                <div class="font-medium">No irrigation</div>
                <div class="text-xs text-muted-foreground">{cropSteeringData.irrigation_timing.night.notes}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Coco Notes -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Info class="size-4 text-orange-400" />
            Coco-Specific Notes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul class="space-y-2 text-sm">
            {#each cropSteeringData.coco_specific.notes as note}
              <li class="flex items-start gap-2">
                <CheckCircle class="size-4 text-green-400 mt-0.5 flex-shrink-0" />
                <span class="text-muted-foreground">{note}</span>
              </li>
            {/each}
          </ul>
        </CardContent>
      </Card>
    </TabsContent>

    <!-- IPM TAB -->
    <TabsContent value="ipm" class="space-y-4">
      <!-- Weekly Schedule -->
      <Card class="border-green-500/50">
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Bug class="size-4 text-green-400" />
            Weekly Prevention Schedule
          </CardTitle>
          <CardDescription>{ipmData.philosophy}</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            {#each Object.entries(ipmData.weekly_schedule) as [day, schedule]}
              <div class="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Badge variant="secondary" class="capitalize min-w-[80px] justify-center">{day}</Badge>
                <div class="flex-1">
                  <div class="font-medium">{schedule.product}</div>
                  <div class="text-xs text-muted-foreground">{schedule.application} - {schedule.target}</div>
                  <div class="text-xs text-muted-foreground">Timing: {schedule.timing}</div>
                </div>
              </div>
            {/each}
          </div>
        </CardContent>
      </Card>

      <!-- Products Reference -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <FlaskConical class="size-4 text-purple-400" />
            Your IPM Products
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Product</th>
                  <th class="text-left py-2 px-2">Type</th>
                  <th class="text-left py-2 px-2">Targets</th>
                  <th class="text-center py-2 px-2">Flower Safe</th>
                </tr>
              </thead>
              <tbody>
                {#each ipmData.products as product}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{product.name}</td>
                    <td class="py-2 px-2 text-xs text-muted-foreground">{product.type}</td>
                    <td class="py-2 px-2 text-xs">{product.target_pests.slice(0, 3).join(', ')}</td>
                    <td class="text-center py-2 px-2">
                      {#if product.flower_safe === true}
                        <Badge class="bg-green-500/20 text-green-300">Yes</Badge>
                      {:else}
                        <Badge class="bg-yellow-500/20 text-yellow-300">Caution</Badge>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <!-- Pest Identification -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <AlertTriangle class="size-4 text-yellow-400" />
            Pest Identification & Treatment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            {#each Object.entries(ipmData.pest_identification) as [pest, info]}
              <div class="p-3 rounded-lg border border-border">
                <div class="font-medium capitalize mb-2">{pest.replace('_', ' ')}</div>
                <div class="text-xs space-y-2">
                  <div>
                    <span class="text-muted-foreground">Signs: </span>
                    {info.signs.join(', ')}
                  </div>
                  <div>
                    <span class="text-green-400">Treatment: </span>
                    {info.treatment.join(', ')}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </CardContent>
      </Card>

      <!-- Predatory Insects -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Bug class="size-4 text-cyan-400" />
            Predatory Insects
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-left py-2 px-2">Predator</th>
                  <th class="text-left py-2 px-2">Target</th>
                  <th class="text-left py-2 px-2">Release Rate</th>
                  <th class="text-left py-2 px-2 hidden md:table-cell">Notes</th>
                </tr>
              </thead>
              <tbody>
                {#each ipmData.predatory_insects as predator}
                  <tr class="border-b border-border/50 hover:bg-muted/50">
                    <td class="py-2 px-2 font-medium">{predator.name}</td>
                    <td class="py-2 px-2 text-xs">{predator.target}</td>
                    <td class="py-2 px-2 text-xs text-muted-foreground">{predator.release_rate}</td>
                    <td class="py-2 px-2 text-xs text-muted-foreground hidden md:table-cell">{predator.notes}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </TabsContent>

    <!-- OPERATIONS TAB -->
    <TabsContent value="operations" class="space-y-4">
      <!-- Maintenance Schedule -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Wrench class="size-4 text-orange-400" />
            Maintenance Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            {#each Object.entries(operationsData.maintenance_schedule) as [period, tasks]}
              <div class="p-3 rounded-lg border border-border">
                <div class="font-medium capitalize mb-2 flex items-center gap-2">
                  {#if period === 'daily'}
                    <Badge class="bg-green-500/20 text-green-300">Daily</Badge>
                  {:else if period === 'weekly'}
                    <Badge class="bg-cyan-500/20 text-cyan-300">Weekly</Badge>
                  {:else if period === 'monthly'}
                    <Badge class="bg-yellow-500/20 text-yellow-300">Monthly</Badge>
                  {:else}
                    <Badge class="bg-purple-500/20 text-purple-300">Quarterly</Badge>
                  {/if}
                </div>
                <ul class="space-y-1 text-xs text-muted-foreground">
                  {#each tasks as task}
                    <li class="flex items-start gap-2">
                      <CheckCircle class="size-3 text-muted-foreground mt-0.5 flex-shrink-0" />
                      {task}
                    </li>
                  {/each}
                </ul>
              </div>
            {/each}
          </div>
        </CardContent>
      </Card>

      <!-- Harvest Timing -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Leaf class="size-4 text-green-400" />
            Harvest Timing Indicators
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-3">
              <div class="font-medium">Trichome Colors</div>
              <div class="space-y-2 text-sm">
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full bg-white/80"></div>
                  <span class="text-muted-foreground">Clear - Too early</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full bg-gray-300"></div>
                  <span class="text-muted-foreground">Cloudy - Peak THC</span>
                </div>
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span class="text-muted-foreground">Amber - Sedative effect</span>
                </div>
              </div>
              <div class="p-2 rounded-lg bg-green-500/10 text-xs">
                <strong>Target:</strong> {operationsData.harvest_timing.trichome_indicators.target}
              </div>
            </div>
            <div class="space-y-3">
              <div class="font-medium">Visual Indicators</div>
              <ul class="space-y-1 text-xs text-muted-foreground">
                {#each operationsData.harvest_timing.visual_indicators as indicator}
                  <li class="flex items-start gap-2">
                    <CheckCircle class="size-3 text-green-400 mt-0.5 flex-shrink-0" />
                    {indicator}
                  </li>
                {/each}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- System Reference -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <Info class="size-4 text-blue-400" />
            System Reference
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <div class="font-medium mb-2">Tanks</div>
              <div class="space-y-2 text-sm">
                {#each Object.entries(operationsData.system_reference.tanks) as [key, tank]}
                  <div class="flex justify-between items-center py-1 border-b border-border/50">
                    <span class="text-muted-foreground">{tank.name}</span>
                    <Badge variant="secondary">{tank.capacity_gallons} gal</Badge>
                  </div>
                {/each}
              </div>
            </div>
            <div>
              <div class="font-medium mb-2">Timing Defaults</div>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between items-center py-1 border-b border-border/50">
                  <span class="text-muted-foreground">Fill Timeout</span>
                  <span>{operationsData.system_reference.timing_defaults.fill_timeout_minutes} min</span>
                </div>
                <div class="flex justify-between items-center py-1 border-b border-border/50">
                  <span class="text-muted-foreground">Mix Duration</span>
                  <span>{operationsData.system_reference.timing_defaults.mix_duration_minutes} min</span>
                </div>
                <div class="flex justify-between items-center py-1 border-b border-border/50">
                  <span class="text-muted-foreground">EC/pH Tolerance</span>
                  <span>±{operationsData.system_reference.timing_defaults.ec_tolerance}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Calibration Reference -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <FlaskConical class="size-4 text-purple-400" />
            Calibration Reference
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            <div>
              <div class="font-medium mb-2">EC Solutions</div>
              <div class="space-y-1 text-sm">
                <div class="flex justify-between"><span class="text-muted-foreground">Low</span><span>{operationsData.calibration_reference.ec_solutions.low} μS/cm</span></div>
                <div class="flex justify-between"><span class="text-muted-foreground">Standard</span><span>{operationsData.calibration_reference.ec_solutions.single} μS/cm</span></div>
              </div>
            </div>
            <div>
              <div class="font-medium mb-2">pH Solutions</div>
              <div class="space-y-1 text-sm">
                <div class="flex justify-between"><span class="text-muted-foreground">Low</span><span>{operationsData.calibration_reference.ph_solutions.low}</span></div>
                <div class="flex justify-between"><span class="text-muted-foreground">Mid</span><span>{operationsData.calibration_reference.ph_solutions.mid}</span></div>
                <div class="flex justify-between"><span class="text-muted-foreground">High</span><span>{operationsData.calibration_reference.ph_solutions.high}</span></div>
              </div>
            </div>
          </div>
          <div class="mt-4">
            <div class="font-medium mb-2 text-sm">Tips</div>
            <ul class="space-y-1 text-xs text-muted-foreground">
              {#each operationsData.calibration_reference.calibration_tips as tip}
                <li class="flex items-start gap-2">
                  <Info class="size-3 text-blue-400 mt-0.5 flex-shrink-0" />
                  {tip}
                </li>
              {/each}
            </ul>
          </div>
        </CardContent>
      </Card>

      <!-- Troubleshooting -->
      <Card>
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <AlertTriangle class="size-4 text-yellow-400" />
            Troubleshooting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid gap-4 md:grid-cols-2">
            {#each Object.entries(operationsData.troubleshooting) as [issue, solutions]}
              <div class="p-3 rounded-lg border border-border">
                <div class="font-medium capitalize mb-2">{issue.replace(/_/g, ' ')}</div>
                <ul class="space-y-1 text-xs text-muted-foreground">
                  {#each solutions as solution}
                    <li class="flex items-start gap-2">
                      <CheckCircle class="size-3 text-green-400 mt-0.5 flex-shrink-0" />
                      {solution}
                    </li>
                  {/each}
                </ul>
              </div>
            {/each}
          </div>
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
</div>
