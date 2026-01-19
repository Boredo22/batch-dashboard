<script>
  let {
    steps = [],
    currentStepIndex = -1,
    completedSteps = [],
    workflowPhase = 'idle',
    onStepClick = null,
    isTestingMode = false
  } = $props();

  // Group steps by phase
  let fillSteps = $derived(steps.filter(s => s.phase === 'fill'));
  let mixSteps = $derived(steps.filter(s => s.phase === 'mix'));
  let sendSteps = $derived(steps.filter(s => s.phase === 'send'));

  function getStepStatus(step) {
    const stepIndex = steps.findIndex(s => s.id === step.id);
    if (completedSteps.includes(step.id)) return 'completed';
    if (stepIndex === currentStepIndex) return 'active';
    if (step.error) return 'error';
    if (step.skipped) return 'skipped';
    return 'pending';
  }

  function getPhaseStatus(phase) {
    const phaseSteps = steps.filter(s => s.phase === phase);
    const completed = phaseSteps.every(s => completedSteps.includes(s.id));
    const hasActive = phaseSteps.some(s => steps.findIndex(st => st.id === s.id) === currentStepIndex);
    const hasError = phaseSteps.some(s => s.error);

    if (hasError) return 'error';
    if (completed) return 'completed';
    if (hasActive) return 'active';
    return 'pending';
  }

  function handleStepClick(step) {
    if (isTestingMode && onStepClick) {
      onStepClick(step);
    }
  }

  // Expanded step state
  let expandedSteps = $state(new Set());

  function toggleExpand(stepId) {
    if (expandedSteps.has(stepId)) {
      expandedSteps.delete(stepId);
      expandedSteps = new Set(expandedSteps);
    } else {
      expandedSteps.add(stepId);
      expandedSteps = new Set(expandedSteps);
    }
  }
</script>

<div class="flowchart">
  <!-- Fill Phase -->
  {#if fillSteps.length > 0}
    <div class="phase-section">
      <div class="phase-header {getPhaseStatus('fill')}">
        <div class="phase-indicator">
          {#if getPhaseStatus('fill') === 'completed'}
            <i class="fas fa-check-circle"></i>
          {:else if getPhaseStatus('fill') === 'active'}
            <i class="fas fa-circle-notch fa-spin"></i>
          {:else if getPhaseStatus('fill') === 'error'}
            <i class="fas fa-exclamation-circle"></i>
          {:else}
            <i class="fas fa-circle"></i>
          {/if}
        </div>
        <span class="phase-title">Fill Phase</span>
        <span class="phase-count">{fillSteps.filter(s => completedSteps.includes(s.id)).length}/{fillSteps.length}</span>
      </div>

      <div class="steps-container">
        {#each fillSteps as step, i}
          {@const status = getStepStatus(step)}
          {@const isExpanded = expandedSteps.has(step.id)}
          <div class="step-wrapper">
            {#if i > 0}
              <div class="step-connector {status === 'completed' || completedSteps.includes(fillSteps[i-1]?.id) ? 'completed' : ''}"></div>
            {/if}
            <button
              class="step-item {status}"
              class:clickable={isTestingMode}
              class:expanded={isExpanded}
              onclick={() => toggleExpand(step.id)}
              disabled={!isTestingMode && status === 'pending'}
            >
              <div class="step-indicator">
                {#if status === 'completed'}
                  <i class="fas fa-check"></i>
                {:else if status === 'active'}
                  <i class="fas fa-spinner fa-spin"></i>
                {:else if status === 'error'}
                  <i class="fas fa-times"></i>
                {:else if status === 'skipped'}
                  <i class="fas fa-forward"></i>
                {:else}
                  <span class="step-number">{i + 1}</span>
                {/if}
              </div>
              <div class="step-content">
                <div class="step-name">{step.name}</div>
                <div class="step-description">{step.description}</div>
              </div>
              {#if step.commands?.length > 0 || step.waitCondition}
                <div class="expand-icon">
                  <i class="fas fa-chevron-{isExpanded ? 'up' : 'down'}"></i>
                </div>
              {/if}
            </button>

            {#if isExpanded && (step.commands?.length > 0 || step.waitCondition)}
              <div class="step-details">
                {#if step.commands?.length > 0}
                  <div class="detail-section">
                    <div class="detail-label">Commands:</div>
                    {#each step.commands as cmd}
                      <code class="command-code">{cmd}</code>
                    {/each}
                  </div>
                {/if}
                {#if step.waitCondition}
                  <div class="detail-section">
                    <div class="detail-label">Wait:</div>
                    <span class="wait-condition">{step.waitCondition.type === 'delay' ? `${step.waitCondition.duration / 1000}s delay` : step.waitCondition.type}</span>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Phase Connector -->
  {#if fillSteps.length > 0 && mixSteps.length > 0}
    <div class="phase-connector {getPhaseStatus('fill') === 'completed' ? 'completed' : ''}"></div>
  {/if}

  <!-- Mix Phase -->
  {#if mixSteps.length > 0}
    <div class="phase-section">
      <div class="phase-header {getPhaseStatus('mix')}">
        <div class="phase-indicator">
          {#if getPhaseStatus('mix') === 'completed'}
            <i class="fas fa-check-circle"></i>
          {:else if getPhaseStatus('mix') === 'active'}
            <i class="fas fa-circle-notch fa-spin"></i>
          {:else if getPhaseStatus('mix') === 'error'}
            <i class="fas fa-exclamation-circle"></i>
          {:else}
            <i class="fas fa-circle"></i>
          {/if}
        </div>
        <span class="phase-title">Mix Phase</span>
        <span class="phase-count">{mixSteps.filter(s => completedSteps.includes(s.id)).length}/{mixSteps.length}</span>
      </div>

      <div class="steps-container">
        {#each mixSteps as step, i}
          {@const status = getStepStatus(step)}
          {@const isExpanded = expandedSteps.has(step.id)}
          {@const globalIndex = fillSteps.length + i}
          <div class="step-wrapper">
            {#if i > 0}
              <div class="step-connector {status === 'completed' || completedSteps.includes(mixSteps[i-1]?.id) ? 'completed' : ''}"></div>
            {/if}
            <button
              class="step-item {status}"
              class:clickable={isTestingMode}
              class:expanded={isExpanded}
              onclick={() => toggleExpand(step.id)}
              disabled={!isTestingMode && status === 'pending'}
            >
              <div class="step-indicator">
                {#if status === 'completed'}
                  <i class="fas fa-check"></i>
                {:else if status === 'active'}
                  <i class="fas fa-spinner fa-spin"></i>
                {:else if status === 'error'}
                  <i class="fas fa-times"></i>
                {:else if status === 'skipped'}
                  <i class="fas fa-forward"></i>
                {:else}
                  <span class="step-number">{globalIndex + 1}</span>
                {/if}
              </div>
              <div class="step-content">
                <div class="step-name">{step.name}</div>
                <div class="step-description">{step.description}</div>
              </div>
              {#if step.commands?.length > 0 || step.waitCondition}
                <div class="expand-icon">
                  <i class="fas fa-chevron-{isExpanded ? 'up' : 'down'}"></i>
                </div>
              {/if}
            </button>

            {#if isExpanded && (step.commands?.length > 0 || step.waitCondition)}
              <div class="step-details">
                {#if step.commands?.length > 0}
                  <div class="detail-section">
                    <div class="detail-label">Commands:</div>
                    {#each step.commands as cmd}
                      <code class="command-code">{cmd}</code>
                    {/each}
                  </div>
                {/if}
                {#if step.waitCondition}
                  <div class="detail-section">
                    <div class="detail-label">Wait:</div>
                    <span class="wait-condition">{step.waitCondition.type === 'delay' ? `${step.waitCondition.duration / 1000}s delay` : step.waitCondition.type}</span>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Phase Connector -->
  {#if mixSteps.length > 0 && sendSteps.length > 0}
    <div class="phase-connector {getPhaseStatus('mix') === 'completed' ? 'completed' : ''}"></div>
  {/if}

  <!-- Send Phase -->
  {#if sendSteps.length > 0}
    <div class="phase-section">
      <div class="phase-header {getPhaseStatus('send')}">
        <div class="phase-indicator">
          {#if getPhaseStatus('send') === 'completed'}
            <i class="fas fa-check-circle"></i>
          {:else if getPhaseStatus('send') === 'active'}
            <i class="fas fa-circle-notch fa-spin"></i>
          {:else if getPhaseStatus('send') === 'error'}
            <i class="fas fa-exclamation-circle"></i>
          {:else}
            <i class="fas fa-circle"></i>
          {/if}
        </div>
        <span class="phase-title">Send Phase</span>
        <span class="phase-count">{sendSteps.filter(s => completedSteps.includes(s.id)).length}/{sendSteps.length}</span>
      </div>

      <div class="steps-container">
        {#each sendSteps as step, i}
          {@const status = getStepStatus(step)}
          {@const isExpanded = expandedSteps.has(step.id)}
          {@const globalIndex = fillSteps.length + mixSteps.length + i}
          <div class="step-wrapper">
            {#if i > 0}
              <div class="step-connector {status === 'completed' || completedSteps.includes(sendSteps[i-1]?.id) ? 'completed' : ''}"></div>
            {/if}
            <button
              class="step-item {status}"
              class:clickable={isTestingMode}
              class:expanded={isExpanded}
              onclick={() => toggleExpand(step.id)}
              disabled={!isTestingMode && status === 'pending'}
            >
              <div class="step-indicator">
                {#if status === 'completed'}
                  <i class="fas fa-check"></i>
                {:else if status === 'active'}
                  <i class="fas fa-spinner fa-spin"></i>
                {:else if status === 'error'}
                  <i class="fas fa-times"></i>
                {:else if status === 'skipped'}
                  <i class="fas fa-forward"></i>
                {:else}
                  <span class="step-number">{globalIndex + 1}</span>
                {/if}
              </div>
              <div class="step-content">
                <div class="step-name">{step.name}</div>
                <div class="step-description">{step.description}</div>
              </div>
              {#if step.commands?.length > 0 || step.waitCondition}
                <div class="expand-icon">
                  <i class="fas fa-chevron-{isExpanded ? 'up' : 'down'}"></i>
                </div>
              {/if}
            </button>

            {#if isExpanded && (step.commands?.length > 0 || step.waitCondition)}
              <div class="step-details">
                {#if step.commands?.length > 0}
                  <div class="detail-section">
                    <div class="detail-label">Commands:</div>
                    {#each step.commands as cmd}
                      <code class="command-code">{cmd}</code>
                    {/each}
                  </div>
                {/if}
                {#if step.waitCondition}
                  <div class="detail-section">
                    <div class="detail-label">Wait:</div>
                    <span class="wait-condition">{step.waitCondition.type === 'delay' ? `${step.waitCondition.duration / 1000}s delay` : step.waitCondition.type}</span>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .flowchart {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    height: 100%;
    overflow-y: auto;
  }

  .phase-section {
    background: #1a202c;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #4a5568;
  }

  .phase-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid #4a5568;
  }

  .phase-header.completed .phase-indicator {
    color: #22c55e;
  }

  .phase-header.active .phase-indicator {
    color: #3b82f6;
  }

  .phase-header.error .phase-indicator {
    color: #ef4444;
  }

  .phase-header.pending .phase-indicator {
    color: #6b7280;
  }

  .phase-indicator {
    font-size: 1.2rem;
  }

  .phase-title {
    font-weight: 600;
    font-size: 1rem;
    color: #e2e8f0;
    flex: 1;
  }

  .phase-count {
    font-size: 0.85rem;
    color: #a0aec0;
    background: #2d3748;
    padding: 4px 10px;
    border-radius: 12px;
  }

  .phase-connector {
    height: 24px;
    width: 2px;
    background: #4a5568;
    margin: 0 auto;
    transition: background 0.3s;
  }

  .phase-connector.completed {
    background: #22c55e;
  }

  .steps-container {
    display: flex;
    flex-direction: column;
  }

  .step-wrapper {
    display: flex;
    flex-direction: column;
  }

  .step-connector {
    width: 2px;
    height: 16px;
    background: #4a5568;
    margin-left: 19px;
    transition: background 0.3s;
  }

  .step-connector.completed {
    background: #22c55e;
  }

  .step-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 8px;
    cursor: default;
    transition: all 0.2s;
    width: 100%;
    text-align: left;
  }

  .step-item.clickable {
    cursor: pointer;
  }

  .step-item.clickable:hover {
    background: #374151;
    border-color: #6b7280;
  }

  .step-item.pending {
    opacity: 0.6;
  }

  .step-item.active {
    background: #1e3a5f;
    border-color: #3b82f6;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
  }

  .step-item.completed {
    background: #1a2e1a;
    border-color: #22c55e;
  }

  .step-item.error {
    background: #2d1a1a;
    border-color: #ef4444;
  }

  .step-item.skipped {
    background: #2d2a1a;
    border-color: #f59e0b;
    opacity: 0.7;
  }

  .step-indicator {
    width: 28px;
    height: 28px;
    min-width: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 0.85rem;
    background: #4a5568;
    color: #e2e8f0;
  }

  .step-item.completed .step-indicator {
    background: #22c55e;
    color: white;
  }

  .step-item.active .step-indicator {
    background: #3b82f6;
    color: white;
  }

  .step-item.error .step-indicator {
    background: #ef4444;
    color: white;
  }

  .step-item.skipped .step-indicator {
    background: #f59e0b;
    color: white;
  }

  .step-number {
    font-weight: 600;
    font-size: 0.75rem;
  }

  .step-content {
    flex: 1;
    min-width: 0;
  }

  .step-name {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.9rem;
    margin-bottom: 2px;
  }

  .step-description {
    font-size: 0.8rem;
    color: #a0aec0;
    line-height: 1.3;
  }

  .expand-icon {
    color: #6b7280;
    font-size: 0.75rem;
    padding: 4px;
  }

  .step-details {
    margin-left: 40px;
    margin-top: 8px;
    padding: 12px;
    background: #0f172a;
    border-radius: 6px;
    border: 1px solid #374151;
  }

  .detail-section {
    margin-bottom: 8px;
  }

  .detail-section:last-child {
    margin-bottom: 0;
  }

  .detail-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 4px;
  }

  .command-code {
    display: block;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.75rem;
    background: #1e293b;
    color: #fbbf24;
    padding: 6px 10px;
    border-radius: 4px;
    margin-bottom: 4px;
    border-left: 3px solid #f59e0b;
  }

  .wait-condition {
    font-size: 0.8rem;
    color: #60a5fa;
  }

  @media (max-width: 768px) {
    .phase-header {
      flex-wrap: wrap;
    }

    .step-item {
      padding: 10px;
    }

    .step-indicator {
      width: 24px;
      height: 24px;
      min-width: 24px;
      font-size: 0.75rem;
    }

    .step-details {
      margin-left: 36px;
    }
  }
</style>
