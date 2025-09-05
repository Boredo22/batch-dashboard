<script>
  // Tank and room definitions from config
  const TANKS = {
    1: { name: "Tank 1 - Grow 1", capacity: 100, fillRelay: 1, tankRelay: 4, mixRelays: [4, 7], sendRelay: 10 },
    2: { name: "Tank 2 - Grow 2", capacity: 100, fillRelay: 2, tankRelay: 5, mixRelays: [5, 8], sendRelay: 11 },
    3: { name: "Tank 3 - Nursery", capacity: 35, fillRelay: 3, tankRelay: 6, mixRelays: [6, 9], sendRelay: 12 }
  };

  const ROOMS = {
    1: { name: "Grow Room 1", relay: 10 },
    2: { name: "Nursery", relay: 12 }
  };

  // Nutrient recipes (simplified for head grower use)
  const RECIPES = {
    "Veg Formula": { "Veg A": 2.5, "Veg B": 2.5, "Cake": 1.0 },
    "Bloom Formula": { "Bloom A": 3.0, "Bloom B": 3.0, "PK Synergy": 1.5 },
    "Light Feed": { "Veg A": 1.5, "Veg B": 1.5, "Cake": 0.5 },
    "Heavy Feed": { "Bloom A": 4.0, "Bloom B": 4.0, "PK Synergy": 2.0, "Cake": 1.5 }
  };

  // Pump definitions from config
  const PUMPS = {
    1: "Veg A",
    2: "Veg B", 
    3: "Bloom A",
    4: "Bloom B",
    5: "Cake",
    6: "PK Synergy",
    7: "Runclean",
    8: "pH Down"
  };

  // State
  let feedback = $state('');
  let feedbackClass = $state('info');
  let isProcessing = $state(false);

  // Form states for each operation
  let fillForm = $state({ tank: 1, gallons: 50 });
  let sendForm = $state({ tank: 1, room: 1, gallons: 30 });
  let mixForm = $state({ tank: 1, recipe: 'Veg Formula', gallons: 50, mode: 'recipe' });
  let drainForm = $state({ tank: 1 });
  
  // Manual dosage state - initialize with 0 for all pumps
  let manualDosages = $state({
    1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0
  });

  // Show feedback message
  function showFeedback(message, type = 'info', duration = 5000) {
    feedback = message;
    feedbackClass = type;
    setTimeout(() => { feedback = ''; }, duration);
  }

  // API call helper
  async function apiCall(url, method = 'POST', data = null) {
    try {
      const options = { 
        method,
        headers: { 'Content-Type': 'application/json' }
      };
      if (data) options.body = JSON.stringify(data);
      
      const response = await fetch(url, options);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'API call failed');
      }
      
      return result;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Fill Tank Operation
  async function fillTank() {
    if (isProcessing) return;
    
    const tank = TANKS[fillForm.tank];
    isProcessing = true;
    
    try {
      showFeedback(`Starting fill for ${tank.name} - ${fillForm.gallons} gallons. Turn ON water supply manually, then turn OFF when complete.`, 'info');
      
      // Turn on fill relay
      await apiCall(`/api/relays/${tank.fillRelay}/control`, 'POST', { state: true });
      
      showFeedback(`${tank.name} fill relay activated! Manually control water supply and turn off relay when ${fillForm.gallons} gallons reached.`, 'success', 8000);
      
    } catch (error) {
      showFeedback(`Error starting fill: ${error.message}`, 'error');
    } finally {
      isProcessing = false;
    }
  }

  // Send Tank to Room Operation
  async function sendTankToRoom() {
    if (isProcessing) return;
    
    const tank = TANKS[sendForm.tank];
    const room = ROOMS[sendForm.room];
    isProcessing = true;
    
    try {
      showFeedback(`Sending ${tank.name} to ${room.name} - ${sendForm.gallons} gallons`, 'info');
      
      // Activate tank relay (4/5/6) and room relay (10/11/12)
      await apiCall(`/api/relays/${tank.tankRelay}/control`, 'POST', { state: true });
      await apiCall(`/api/relays/${room.relay}/control`, 'POST', { state: true });
      
      showFeedback(`${tank.name} is now sending to ${room.name}! Manually turn off relays when ${sendForm.gallons} gallons delivered.`, 'success', 8000);
      
    } catch (error) {
      showFeedback(`Error sending tank: ${error.message}`, 'error');
    } finally {
      isProcessing = false;
    }
  }

  // Mix Tank Operation
  async function mixTank() {
    if (isProcessing) return;
    
    const tank = TANKS[mixForm.tank];
    isProcessing = true;
    
    try {
      if (mixForm.mode === 'recipe') {
        // Recipe mode
        const recipe = RECIPES[mixForm.recipe];
        showFeedback(`Starting mix for ${tank.name} with ${mixForm.recipe} - ${mixForm.gallons} gallons`, 'info');
        
        // Activate mix relays
        for (const relay of tank.mixRelays) {
          await apiCall(`/api/relays/${relay}/control`, 'POST', { state: true });
        }
        
        // Calculate and dispense nutrients
        let nutrientActions = [];
        for (const [nutrient, mlPerGal] of Object.entries(recipe)) {
          const totalMl = mlPerGal * mixForm.gallons;
          nutrientActions.push(`${nutrient}: ${totalMl}ml`);
          
          // Find pump ID for this nutrient
          const pumpMap = { "Veg A": 1, "Veg B": 2, "Bloom A": 3, "Bloom B": 4, "Cake": 5, "PK Synergy": 6, "Runclean": 7, "pH Down": 8 };
          const pumpId = pumpMap[nutrient];
          
          if (pumpId) {
            await apiCall(`/api/pumps/${pumpId}/dispense`, 'POST', { volume_ml: totalMl });
          }
        }
        
        showFeedback(`${tank.name} mixing started! Nutrients dispensing: ${nutrientActions.join(', ')}. Manually turn off relays when mixing complete.`, 'success', 10000);
        
      } else {
        // Manual mode
        showFeedback(`Starting manual mix for ${tank.name} - ${mixForm.gallons} gallons`, 'info');
        
        // Activate mix relays
        for (const relay of tank.mixRelays) {
          await apiCall(`/api/relays/${relay}/control`, 'POST', { state: true });
        }
        
        // Dispense nutrients based on manual dosages
        let nutrientActions = [];
        for (const [pumpId, mlPerGal] of Object.entries(manualDosages)) {
          if (mlPerGal > 0) {
            const totalMl = mlPerGal * mixForm.gallons;
            const pumpName = PUMPS[pumpId];
            nutrientActions.push(`${pumpName}: ${totalMl}ml`);
            
            await apiCall(`/api/pumps/${pumpId}/dispense`, 'POST', { volume_ml: totalMl });
          }
        }
        
        if (nutrientActions.length > 0) {
          showFeedback(`${tank.name} manual mixing started! Nutrients dispensing: ${nutrientActions.join(', ')}. Manually turn off relays when mixing complete.`, 'success', 10000);
        } else {
          showFeedback(`${tank.name} mixing started with no nutrients (mix relays only). Manually turn off relays when mixing complete.`, 'warning', 8000);
        }
      }
      
    } catch (error) {
      showFeedback(`Error mixing tank: ${error.message}`, 'error');
    } finally {
      isProcessing = false;
    }
  }

  // Drain Tank Operation
  async function drainTank() {
    if (isProcessing) return;
    
    const tank = TANKS[drainForm.tank];
    isProcessing = true;
    
    try {
      showFeedback(`Starting drain for ${tank.name}`, 'info');
      
      // Activate tank relay (4/5/6) and drain relay (13)
      await apiCall(`/api/relays/${tank.tankRelay}/control`, 'POST', { state: true });
      await apiCall(`/api/relays/13/control`, 'POST', { state: true });
      
      showFeedback(`${tank.name} is now draining! Manually turn off relays when drain complete.`, 'warning', 8000);
      
    } catch (error) {
      showFeedback(`Error draining tank: ${error.message}`, 'error');
    } finally {
      isProcessing = false;
    }
  }

  // Emergency stop all relays
  async function emergencyStop() {
    try {
      showFeedback('Emergency stop activated - turning off all relays', 'warning');
      await apiCall('/api/relays/0/control', 'POST', { state: false });
      showFeedback('All relays turned off successfully', 'success');
    } catch (error) {
      showFeedback(`Error during emergency stop: ${error.message}`, 'error');
    }
  }
</script>

<div class="head-grower-container">
  <div class="page-header">
    <h1>Nutrient Operations Control</h1>
    <p>Production controls for head grower - manual monitoring required</p>
  </div>

  <!-- Feedback Display -->
  {#if feedback}
    <div class="feedback {feedbackClass}">
      <i class="fas {feedbackClass === 'success' ? 'fa-check-circle' : feedbackClass === 'error' ? 'fa-exclamation-triangle' : feedbackClass === 'warning' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
      <span>{feedback}</span>
    </div>
  {/if}

  <div class="operations-grid">
    
    <!-- Fill Tank Section -->
    <div class="operation-card">
      <div class="operation-header">
        <h2><i class="fas fa-tint"></i> Fill Tank</h2>
        <p>Fill selected tank with water - manual flow control</p>
      </div>
      
      <div class="operation-form">
        <div class="form-row">
          <label for="fill-tank">Tank:</label>
          <select id="fill-tank" bind:value={fillForm.tank}>
            {#each Object.entries(TANKS) as [id, tank]}
              <option value={Number(id)}>{tank.name}</option>
            {/each}
          </select>
        </div>
        
        <div class="form-row">
          <label for="fill-gallons">Gallons:</label>
          <input id="fill-gallons" type="number" bind:value={fillForm.gallons} min="1" max="100" />
        </div>
        
        <button 
          class="operation-btn fill-btn" 
          onclick={fillTank}
          disabled={isProcessing}
        >
          <i class="fas fa-play"></i>
          Start Fill
        </button>
        
        <div class="operation-details">
          <small>Activates: Fill Relay {TANKS[fillForm.tank].fillRelay}</small>
        </div>
      </div>
    </div>

    <!-- Send Tank Section -->
    <div class="operation-card">
      <div class="operation-header">
        <h2><i class="fas fa-arrow-right"></i> Send to Room</h2>
        <p>Send tank contents to grow room - manual flow control</p>
      </div>
      
      <div class="operation-form">
        <div class="form-row">
          <label for="send-tank">Tank:</label>
          <select id="send-tank" bind:value={sendForm.tank}>
            {#each Object.entries(TANKS) as [id, tank]}
              <option value={Number(id)}>{tank.name}</option>
            {/each}
          </select>
        </div>
        
        <div class="form-row">
          <label for="send-room">Room:</label>
          <select id="send-room" bind:value={sendForm.room}>
            {#each Object.entries(ROOMS) as [id, room]}
              <option value={Number(id)}>{room.name}</option>
            {/each}
          </select>
        </div>
        
        <div class="form-row">
          <label for="send-gallons">Gallons:</label>
          <input id="send-gallons" type="number" bind:value={sendForm.gallons} min="1" max="100" />
        </div>
        
        <button 
          class="operation-btn send-btn" 
          onclick={sendTankToRoom}
          disabled={isProcessing}
        >
          <i class="fas fa-share"></i>
          Send Tank
        </button>
        
        <div class="operation-details">
          <small>Activates: Tank Relay {TANKS[sendForm.tank].tankRelay}, Room Relay {ROOMS[sendForm.room].relay}</small>
        </div>
      </div>
    </div>

    <!-- Drain Tank Section -->
    <div class="operation-card">
      <div class="operation-header">
        <h2><i class="fas fa-drain"></i> Drain Tank</h2>
        <p>Drain selected tank completely</p>
      </div>
      
      <div class="operation-form">
        <div class="form-row">
          <label for="drain-tank">Tank:</label>
          <select id="drain-tank" bind:value={drainForm.tank}>
            {#each Object.entries(TANKS) as [id, tank]}
              <option value={Number(id)}>{tank.name}</option>
            {/each}
          </select>
        </div>
        
        <button 
          class="operation-btn drain-btn" 
          onclick={drainTank}
          disabled={isProcessing}
        >
          <i class="fas fa-tint-slash"></i>
          Start Drain
        </button>
        
        <div class="operation-details">
          <small>Activates: Tank Relay {TANKS[drainForm.tank].tankRelay}, Drain Relay 13</small>
        </div>
      </div>
    </div>

    <!-- Mix Tank Section -->
    <div class="operation-card mix-card">
      <div class="operation-header">
        <h2><i class="fas fa-flask"></i> Mix Nutrients</h2>
        <p>Mix nutrients into tank using recipe or manual dosages - manual timing control</p>
      </div>
      
      <div class="operation-form">
        <div class="form-row">
          <label for="mix-tank">Tank:</label>
          <select id="mix-tank" bind:value={mixForm.tank}>
            {#each Object.entries(TANKS) as [id, tank]}
              <option value={Number(id)}>{tank.name}</option>
            {/each}
          </select>
        </div>
        
        <div class="form-row">
          <label for="mix-gallons">Gallons:</label>
          <input id="mix-gallons" type="number" bind:value={mixForm.gallons} min="10" max="100" />
        </div>

        <!-- Mode Toggle -->
        <div class="mode-toggle">
          <label class="toggle-label">
            <input type="radio" bind:group={mixForm.mode} value="recipe" />
            <span>Recipe Mode</span>
          </label>
          <label class="toggle-label">
            <input type="radio" bind:group={mixForm.mode} value="manual" />
            <span>Manual Mode</span>
          </label>
        </div>
        
        {#if mixForm.mode === 'recipe'}
          <!-- Recipe Mode -->
          <div class="form-row">
            <label for="mix-recipe">Recipe:</label>
            <select id="mix-recipe" bind:value={mixForm.recipe}>
              {#each Object.keys(RECIPES) as recipe}
                <option value={recipe}>{recipe}</option>
              {/each}
            </select>
          </div>
        {:else}
          <!-- Manual Mode -->
          <div class="manual-dosages">
            <h4>Manual Dosages (ml/gallon):</h4>
            <div class="dosage-grid">
              {#each Object.entries(PUMPS) as [pumpId, pumpName]}
                <div class="dosage-row">
                  <label for="pump-{pumpId}">{pumpName}:</label>
                  <input 
                    id="pump-{pumpId}"
                    type="number" 
                    bind:value={manualDosages[pumpId]} 
                    min="0" 
                    max="10" 
                    step="0.1"
                    placeholder="0.0"
                  />
                  <span class="total-ml">
                    {manualDosages[pumpId] > 0 ? `= ${(manualDosages[pumpId] * mixForm.gallons).toFixed(1)} ml` : ''}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
        
        <button 
          class="operation-btn mix-btn" 
          onclick={mixTank}
          disabled={isProcessing}
        >
          <i class="fas fa-magic"></i>
          Start Mix
        </button>
        
        <div class="operation-details">
          <small>Activates: Mix Relays {TANKS[mixForm.tank].mixRelays.join(', ')} + Nutrient Pumps</small>
          
          {#if mixForm.mode === 'recipe'}
            <div class="recipe-details">
              <strong>Recipe Details:</strong>
              {#each Object.entries(RECIPES[mixForm.recipe]) as [nutrient, mlPerGal]}
                <div>{nutrient}: {mlPerGal} ml/gal × {mixForm.gallons} gal = {(mlPerGal * mixForm.gallons).toFixed(1)} ml</div>
              {/each}
            </div>
          {:else}
            <div class="manual-details">
              <strong>Manual Dosage Summary:</strong>
              {#each Object.entries(manualDosages) as [pumpId, mlPerGal]}
                {#if mlPerGal > 0}
                  <div>{PUMPS[pumpId]}: {mlPerGal} ml/gal × {mixForm.gallons} gal = {(mlPerGal * mixForm.gallons).toFixed(1)} ml</div>
                {/if}
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Emergency Controls -->
  <div class="emergency-section">
    <h3>Emergency Controls</h3>
    <button class="emergency-btn" onclick={emergencyStop} aria-label="Emergency stop - turn off all relays immediately">
      <i class="fas fa-stop" aria-hidden="true"></i>
      STOP ALL RELAYS
    </button>
  </div>
</div>

<style>
  .head-grower-container {
    padding: 2rem;
    background: #1a1a1a;
    color: white;
    min-height: 100vh;
  }

  .page-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .page-header h1 {
    color: #06b6d4;
    margin-bottom: 0.5rem;
    font-size: 2.5rem;
  }

  .page-header p {
    color: #94a3b8;
    font-size: 1.1rem;
  }

  .feedback {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
    font-weight: 500;
    font-size: 1.1rem;
  }

  .feedback.info {
    background: #0c4a6e;
    color: #7dd3fc;
    border: 1px solid #0284c7;
  }

  .feedback.success {
    background: #064e3b;
    color: #6ee7b7;
    border: 1px solid #059669;
  }

  .feedback.error {
    background: #7f1d1d;
    color: #fca5a5;
    border: 1px solid #dc2626;
  }

  .feedback.warning {
    background: #78350f;
    color: #fcd34d;
    border: 1px solid #d97706;
  }

  .operations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
  }

  .operation-card {
    background: #0f172a;
    border: 2px solid #334155;
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .mix-card {
    grid-column: 1 / -1;
    max-width: 800px;
    justify-self: center;
  }

  .operation-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .operation-header h2 {
    color: #e2e8f0;
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
  }

  .operation-header h2 i {
    margin-right: 0.5rem;
    color: #06b6d4;
  }

  .operation-header p {
    color: #94a3b8;
    font-size: 1rem;
  }

  .operation-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .form-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .form-row label {
    min-width: 80px;
    font-weight: 500;
    color: #e2e8f0;
    font-size: 1.1rem;
  }

  .form-row select,
  .form-row input {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid #475569;
    border-radius: 0.5rem;
    background: #1e293b;
    color: white;
    font-size: 1rem;
  }

  .form-row select:focus,
  .form-row input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .operation-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1.25rem 2rem;
    border: none;
    border-radius: 0.75rem;
    font-size: 1.2rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 1rem;
  }

  .fill-btn {
    background: #1e40af;
    color: white;
  }

  .fill-btn:hover:not(:disabled) {
    background: #1d4ed8;
    transform: translateY(-2px);
  }

  .send-btn {
    background: #059669;
    color: white;
  }

  .send-btn:hover:not(:disabled) {
    background: #047857;
    transform: translateY(-2px);
  }

  .mix-btn {
    background: #7c2d12;
    color: white;
  }

  .mix-btn:hover:not(:disabled) {
    background: #9a3412;
    transform: translateY(-2px);
  }

  .drain-btn {
    background: #7c2d12;
    color: white;
  }

  .drain-btn:hover:not(:disabled) {
    background: #92400e;
    transform: translateY(-2px);
  }

  .operation-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .operation-details {
    background: #1e293b;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #475569;
  }

  .operation-details small {
    color: #94a3b8;
    font-size: 0.9rem;
  }

  .recipe-details {
    margin-top: 0.5rem;
    font-size: 0.9rem;
  }

  .recipe-details strong {
    color: #e2e8f0;
    display: block;
    margin-bottom: 0.5rem;
  }

  .recipe-details div {
    color: #94a3b8;
    margin-left: 1rem;
  }

  .mode-toggle {
    display: flex;
    gap: 2rem;
    margin: 1rem 0;
    justify-content: center;
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: #e2e8f0;
    cursor: pointer;
    font-size: 1.1rem;
  }

  .toggle-label input[type="radio"] {
    width: 1.2rem;
    height: 1.2rem;
    accent-color: #06b6d4;
  }

  .manual-dosages {
    background: #1e293b;
    padding: 1.5rem;
    border-radius: 0.75rem;
    border: 2px solid #475569;
    margin: 1rem 0;
  }

  .manual-dosages h4 {
    color: #e2e8f0;
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    text-align: center;
  }

  .dosage-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .dosage-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #0f172a;
    padding: 0.75rem;
    border-radius: 0.5rem;
  }

  .dosage-row label {
    min-width: 80px;
    font-weight: 500;
    color: #94a3b8;
    font-size: 0.95rem;
  }

  .dosage-row input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
    width: 80px;
  }

  .dosage-row input:focus {
    outline: none;
    border-color: #06b6d4;
  }

  .total-ml {
    min-width: 80px;
    font-size: 0.85rem;
    color: #06b6d4;
    font-weight: 500;
  }

  .manual-details {
    margin-top: 0.5rem;
    font-size: 0.9rem;
  }

  .manual-details strong {
    color: #e2e8f0;
    display: block;
    margin-bottom: 0.5rem;
  }

  .manual-details div {
    color: #94a3b8;
    margin-left: 1rem;
  }

  .emergency-section {
    text-align: center;
    padding: 2rem;
    border: 2px solid #dc2626;
    border-radius: 1rem;
    background: #7f1d1d;
  }

  .emergency-section h3 {
    color: #fca5a5;
    margin-bottom: 1rem;
    font-size: 1.5rem;
  }

  .emergency-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1.25rem 3rem;
    border: none;
    border-radius: 0.75rem;
    background: #dc2626;
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    margin: 0 auto;
  }

  .emergency-btn:hover {
    background: #b91c1c;
    transform: scale(1.05);
  }

  /* Touch screen optimizations */
  @media (max-width: 1200px) {
    .operations-grid {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }
    
    .operation-btn,
    .emergency-btn {
      padding: 1.5rem 2rem;
      font-size: 1.3rem;
    }
    
    .form-row {
      flex-direction: column;
      align-items: stretch;
    }
    
    .form-row label {
      min-width: auto;
      margin-bottom: 0.5rem;
    }

    .dosage-grid {
      grid-template-columns: 1fr;
    }

    .dosage-row {
      flex-direction: column;
      align-items: stretch;
      gap: 0.5rem;
    }

    .dosage-row label {
      min-width: auto;
      text-align: center;
    }

    .total-ml {
      text-align: center;
      min-width: auto;
    }

    .mode-toggle {
      flex-direction: column;
      align-items: center;
      gap: 1rem;
    }
  }
</style>