<script>
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Badge } from '$lib/components/ui/badge';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Separator } from '$lib/components/ui/separator';

  // Lucide icons (import via CDN or as components)
  // For simplicity, using text labels with styled indicators

  // State variables using Svelte 5 runes
  let selectedMeter = $state(1);
  let testDuration = $state(10);
  let logs = $state([]);
  let autoScroll = $state(true);
  let isTestRunning = $state(false);
  let testStartTime = $state(null);
  let testTimer = $state(null);
  let remainingTime = $state(0);

  // Diagnostic data
  let gpioInfo = $state(null);
  let currentStatus = $state(null);
  let pulseCount = $state(0);
  let flowRate = $state(0);
  let totalGallons = $state(0);

  // Polling intervals
  let statusInterval = null;
  let gpioInterval = null;

  // Log scroll container reference
  let logContainer = null;

  // Derived values
  let meterStatusBadge = $derived((() => {
    if (!currentStatus) return { text: 'Unknown', variant: 'secondary' };
    if (currentStatus.status === 1) return { text: 'Active', variant: 'default' };
    return { text: 'Idle', variant: 'secondary' };
  })());

  let gpioLevelBadge = $derived((() => {
    if (!gpioInfo?.diagnostics?.gpio_level) return { text: 'N/A', variant: 'secondary' };
    const level = gpioInfo.diagnostics.gpio_level;
    if (level === 'HIGH') return { text: 'HIGH (~3.3V)', variant: 'default', color: 'text-green-400' };
    if (level === 'LOW') return { text: 'LOW (~0V)', variant: 'destructive', color: 'text-purple-400' };
    return { text: level, variant: 'secondary' };
  })());

  // Format timestamp for logs
  function formatTimestamp() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
  }

  // Add log entry with color coding
  function addLog(message, type = 'info') {
    const logEntry = {
      id: Date.now() + Math.random(),
      timestamp: formatTimestamp(),
      message,
      type // 'info', 'success', 'warning', 'error'
    };
    logs = [...logs, logEntry];

    // Auto-scroll to bottom
    if (autoScroll && logContainer) {
      setTimeout(() => {
        logContainer.scrollTop = logContainer.scrollHeight;
      }, 10);
    }
  }

  // Clear logs
  function clearLogs() {
    logs = [];
    addLog('Logs cleared', 'info');
  }

  // Export logs to text file
  function exportLogs() {
    const logText = logs.map(log => `[${log.timestamp}] [${log.type.toUpperCase()}] ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flow-meter-${selectedMeter}-logs-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addLog('Logs exported to file', 'success');
  }

  // Fetch GPIO diagnostics
  async function fetchGPIODiagnostics() {
    try {
      const response = await fetch(`/api/flow/${selectedMeter}/diagnostics/gpio`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          gpioInfo = data;
        } else {
          addLog(`Failed to fetch GPIO diagnostics: ${data.error}`, 'error');
        }
      }
    } catch (error) {
      addLog(`Error fetching GPIO diagnostics: ${error.message}`, 'error');
    }
  }

  // Fetch flow meter status
  async function fetchFlowStatus() {
    try {
      const response = await fetch(`/api/flow/${selectedMeter}/status`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          currentStatus = data.status;

          // Update pulse count and calculated values
          const newPulseCount = currentStatus.pulse_count || 0;
          if (newPulseCount !== pulseCount && isTestRunning) {
            const pulseDiff = newPulseCount - pulseCount;
            addLog(`PULSE DETECTED: Count ${newPulseCount} (+${pulseDiff})`, 'success');
          }
          pulseCount = newPulseCount;

          const ppg = currentStatus.pulses_per_gallon || 220;
          totalGallons = pulseCount / ppg;

          // Calculate flow rate (gallons per minute)
          if (isTestRunning && testStartTime) {
            const elapsed = (Date.now() - testStartTime) / 1000; // seconds
            flowRate = elapsed > 0 ? (totalGallons / elapsed) * 60 : 0;
          }
        }
      }
    } catch (error) {
      addLog(`Error fetching flow status: ${error.message}`, 'error');
    }
  }

  // Reset pulse counter
  async function resetCounter() {
    try {
      const response = await fetch(`/api/flow/${selectedMeter}/diagnostics/reset`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          addLog('Flow meter counter reset', 'success');
          pulseCount = 0;
          totalGallons = 0;
          flowRate = 0;
          await fetchFlowStatus();
        } else {
          addLog(`Failed to reset counter: ${data.error}`, 'error');
        }
      }
    } catch (error) {
      addLog(`Error resetting counter: ${error.message}`, 'error');
    }
  }

  // Start pulse test
  async function startPulseTest() {
    if (isTestRunning) {
      addLog('Test already running', 'warning');
      return;
    }

    try {
      // Reset counter first
      await resetCounter();

      const response = await fetch(`/api/flow/${selectedMeter}/diagnostics/pulse-test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: testDuration })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          isTestRunning = true;
          testStartTime = Date.now();
          remainingTime = testDuration;

          addLog(`Pulse test started for ${testDuration} seconds`, 'info');
          addLog('Turn on water flow and watch for pulse detection...', 'info');

          // Start countdown timer
          testTimer = setInterval(() => {
            remainingTime = Math.max(0, testDuration - Math.floor((Date.now() - testStartTime) / 1000));

            if (remainingTime <= 0) {
              stopPulseTest();
            }
          }, 100);

        } else {
          addLog(`Failed to start pulse test: ${data.error}`, 'error');
        }
      }
    } catch (error) {
      addLog(`Error starting pulse test: ${error.message}`, 'error');
    }
  }

  // Stop pulse test
  async function stopPulseTest() {
    if (!isTestRunning) return;

    isTestRunning = false;

    if (testTimer) {
      clearInterval(testTimer);
      testTimer = null;
    }

    const elapsed = (Date.now() - testStartTime) / 1000;

    addLog('Pulse test stopped', 'info');
    addLog(`Total pulses detected: ${pulseCount}`, pulseCount > 0 ? 'success' : 'warning');
    addLog(`Total gallons: ${totalGallons.toFixed(3)} gal`, 'info');
    addLog(`Average flow rate: ${flowRate.toFixed(2)} GPM`, 'info');
    addLog(`Test duration: ${elapsed.toFixed(1)} seconds`, 'info');

    if (pulseCount === 0) {
      addLog('No pulses detected! Check wiring and water flow.', 'error');
      addLog('Troubleshooting: Verify voltage at GPIO pin, check optocoupler connections, ensure water is flowing', 'warning');
    }

    testStartTime = null;
    remainingTime = 0;
  }

  // Run GPIO level check
  async function runGPIOCheck() {
    addLog('Running GPIO pin status check...', 'info');
    await fetchGPIODiagnostics();

    if (gpioInfo?.diagnostics) {
      const diag = gpioInfo.diagnostics;
      addLog(`GPIO Pin: ${diag.gpio_pin}`, 'info');
      addLog(`Current Level: ${diag.gpio_level || 'N/A'} (${diag.gpio_voltage || 'N/A'})`, 'info');
      addLog(`Pull Resistor: ${diag.pull_resistor}`, 'info');
      addLog(`Interrupt Edge: ${diag.interrupt_edge}`, 'info');
      addLog(`Calibration: ${diag.calibration_ppg} pulses/gallon`, 'info');
      addLog('GPIO check complete', 'success');
    } else {
      addLog('Failed to retrieve GPIO diagnostics', 'error');
    }
  }

  // Handle meter selection change
  function changeMeter(meterId) {
    if (isTestRunning) {
      addLog('Cannot change meter while test is running', 'warning');
      return;
    }

    selectedMeter = meterId;
    addLog(`Switched to Flow Meter ${meterId}`, 'info');

    // Reset data
    gpioInfo = null;
    currentStatus = null;
    pulseCount = 0;
    flowRate = 0;
    totalGallons = 0;

    // Fetch new data
    fetchGPIODiagnostics();
    fetchFlowStatus();
  }

  // Component lifecycle
  onMount(() => {
    addLog('Flow Meter Diagnostics initialized', 'info');
    addLog(`Selected: Flow Meter ${selectedMeter}`, 'info');

    // Initial data fetch
    fetchGPIODiagnostics();
    fetchFlowStatus();

    // Start polling intervals
    statusInterval = setInterval(fetchFlowStatus, 500); // 500ms for real-time pulse detection
    gpioInterval = setInterval(fetchGPIODiagnostics, 2000); // 2s for GPIO level updates
  });

  onDestroy(() => {
    // Clean up intervals
    if (statusInterval) clearInterval(statusInterval);
    if (gpioInterval) clearInterval(gpioInterval);
    if (testTimer) clearInterval(testTimer);

    // Stop any running tests
    if (isTestRunning) {
      stopPulseTest();
    }
  });
</script>

<div class="p-4 md:p-6">
  <!-- Note: Header is provided by DashboardLayout -->

  <!-- Flow Meter Selection -->
  <Card class="mb-6 bg-gray-800/50 border-gray-700">
    <CardHeader>
      <CardTitle class="text-white">Select Flow Meter</CardTitle>
      <CardDescription class="text-gray-400">Choose which flow meter to diagnose</CardDescription>
    </CardHeader>
    <CardContent>
      <div class="flex gap-3">
        <Button
          variant={selectedMeter === 1 ? "default" : "outline"}
          onclick={() => changeMeter(1)}
          disabled={isTestRunning}
          class={selectedMeter === 1 ? "bg-purple-600 hover:bg-purple-700" : "border-gray-600 text-gray-300 hover:bg-gray-700"}
        >
          Flow Meter 1 - GPIO 23 (Tank Fill)
        </Button>
        <Button
          variant={selectedMeter === 2 ? "default" : "outline"}
          onclick={() => changeMeter(2)}
          disabled={isTestRunning}
          class={selectedMeter === 2 ? "bg-purple-600 hover:bg-purple-700" : "border-gray-600 text-gray-300 hover:bg-gray-700"}
        >
          Flow Meter 2 - GPIO 24 (Send to Room)
        </Button>
      </div>
    </CardContent>
  </Card>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Left Column - Status and Diagnostics -->
    <div class="lg:col-span-1 space-y-6">
      <!-- GPIO Status Card -->
      <Card class="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle class="text-white flex items-center justify-between">
            GPIO Status
            <Badge variant={meterStatusBadge.variant} class="ml-2">
              {meterStatusBadge.text}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-3">
          {#if gpioInfo?.diagnostics}
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-400">GPIO Pin:</span>
                <span class="text-white font-mono">{gpioInfo.diagnostics.gpio_pin}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Current Level:</span>
                <span class={gpioLevelBadge.color + " font-mono font-bold"}>
                  {gpioInfo.diagnostics.gpio_level || 'N/A'}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Voltage:</span>
                <span class="text-white font-mono">{gpioInfo.diagnostics.gpio_voltage || 'N/A'}</span>
              </div>
              <Separator class="bg-gray-600" />
              <div class="flex justify-between">
                <span class="text-gray-400">Interrupt Edge:</span>
                <span class="text-white">{gpioInfo.diagnostics.interrupt_edge}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Pull Resistor:</span>
                <span class="text-white">{gpioInfo.diagnostics.pull_resistor}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-400">Calibration:</span>
                <span class="text-white">{gpioInfo.diagnostics.calibration_ppg} PPG</span>
              </div>
            </div>
          {:else}
            <div class="text-center text-gray-400 py-4">
              Loading GPIO information...
            </div>
          {/if}
        </CardContent>
      </Card>

      <!-- Pulse Counter Card -->
      <Card class="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle class="text-white">Pulse Counter</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="text-center">
            <div class="text-5xl font-bold text-purple-400 font-mono">
              {pulseCount}
            </div>
            <div class="text-sm text-gray-400 mt-1">Total Pulses</div>
          </div>

          <Separator class="bg-gray-600" />

          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Gallons:</span>
              <span class="text-green-400 font-mono font-bold">{totalGallons.toFixed(3)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Flow Rate:</span>
              <span class="text-green-400 font-mono font-bold">{flowRate.toFixed(2)} GPM</span>
            </div>
            {#if isTestRunning}
              <div class="flex justify-between">
                <span class="text-gray-400">Time Remaining:</span>
                <span class="text-yellow-400 font-mono font-bold">{remainingTime}s</span>
              </div>
            {/if}
          </div>
        </CardContent>
      </Card>

      <!-- Control Buttons -->
      <Card class="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle class="text-white">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent class="space-y-3">
          <Button
            onclick={runGPIOCheck}
            disabled={isTestRunning}
            class="w-full bg-blue-600 hover:bg-blue-700 text-white"
          >
            Check GPIO Status
          </Button>

          <Button
            onclick={resetCounter}
            disabled={isTestRunning}
            variant="outline"
            class="w-full border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            Reset Counter
          </Button>
        </CardContent>
      </Card>
    </div>

    <!-- Right Column - Testing and Logs -->
    <div class="lg:col-span-2 space-y-6">
      <!-- Pulse Test Card -->
      <Card class="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle class="text-white">Pulse Detection Test</CardTitle>
          <CardDescription class="text-gray-400">
            Monitor real-time pulse detection from the flow meter sensor
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="md:col-span-2">
              <Label for="duration" class="text-gray-300">Test Duration (seconds)</Label>
              <Input
                id="duration"
                type="number"
                bind:value={testDuration}
                min="5"
                max="300"
                disabled={isTestRunning}
                class="bg-gray-700 border-gray-600 text-white mt-1"
              />
            </div>
            <div class="flex items-end">
              {#if !isTestRunning}
                <Button
                  onclick={startPulseTest}
                  class="w-full bg-green-600 hover:bg-green-700 text-white"
                >
                  Start Test
                </Button>
              {:else}
                <Button
                  onclick={stopPulseTest}
                  variant="destructive"
                  class="w-full"
                >
                  Stop Test
                </Button>
              {/if}
            </div>
          </div>

          {#if isTestRunning}
            <div class="bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-4">
              <div class="flex items-center gap-2 text-yellow-400">
                <div class="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
                <span class="font-semibold">Test Running - {remainingTime}s remaining</span>
              </div>
              <p class="text-sm text-gray-300 mt-2">
                Turn on water flow or manually trigger the sensor to detect pulses.
                Watch the log panel below for real-time pulse detection.
              </p>
            </div>
          {/if}

          <!-- Instructions -->
          <div class="bg-blue-900/20 border border-blue-600/50 rounded-lg p-4">
            <h4 class="text-blue-400 font-semibold mb-2">Expected Behavior:</h4>
            <ul class="text-sm text-gray-300 space-y-1 ml-4 list-disc">
              <li>Idle state: GPIO reads HIGH (~3.3V)</li>
              <li>Pulse detected: GPIO transitions LOW (~0V)</li>
              <li>Each pulse increments the counter</li>
              <li>Flow rate calculated from pulse frequency</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <!-- Log Display Card -->
      <Card class="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <div class="flex items-center justify-between">
            <div>
              <CardTitle class="text-white">Activity Log</CardTitle>
              <CardDescription class="text-gray-400">Real-time diagnostic output</CardDescription>
            </div>
            <div class="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onclick={() => autoScroll = !autoScroll}
                class="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                {autoScroll ? 'Auto-scroll: ON' : 'Auto-scroll: OFF'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onclick={exportLogs}
                class="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                Export
              </Button>
              <Button
                variant="outline"
                size="sm"
                onclick={clearLogs}
                class="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div
            bind:this={logContainer}
            class="bg-gray-900 border border-gray-700 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm"
          >
            {#if logs.length === 0}
              <div class="text-gray-500 text-center py-8">No log entries yet...</div>
            {:else}
              {#each logs as log (log.id)}
                <div class="mb-1 flex gap-2">
                  <span class="text-gray-500">[{log.timestamp}]</span>
                  <span class={
                    log.type === 'success' ? 'text-green-400' :
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'warning' ? 'text-yellow-400' :
                    'text-gray-300'
                  }>
                    {log.message}
                  </span>
                </div>
              {/each}
            {/if}
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</div>

<style>
  /* Custom scrollbar for log container */
  :global(.overflow-y-auto::-webkit-scrollbar) {
    width: 8px;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-track) {
    background: #1f2937;
    border-radius: 4px;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-thumb) {
    background: #4b5563;
    border-radius: 4px;
  }

  :global(.overflow-y-auto::-webkit-scrollbar-thumb:hover) {
    background: #6b7280;
  }
</style>
