<script>
  import { API_BASE_URL } from '../config.js';

  let { nutrients = [] } = $props();

  // Predefined nutrients that are already in the system with default dosages
  const defaultNutrients = [
    { name: "Veg A", defaultDosage: 4.0 },
    { name: "Veg B", defaultDosage: 4.0 },
    { name: "Bloom A", defaultDosage: 4.0 },
    { name: "Bloom B", defaultDosage: 4.0 },
    { name: "Cake", defaultDosage: 2.0 },
    { name: "PK Synergy", defaultDosage: 2.0 },
    { name: "Runclean", defaultDosage: 1.0 },
    { name: "pH Down", defaultDosage: 0.5 }
  ];
  
  // Local state for managing nutrients
  let nutrientList = $state(Array.isArray(nutrients) && nutrients.length > 0 ? [...nutrients] : [...defaultNutrients]);
  let newNutrientName = $state('');
  let newNutrientDosage = $state(1.0);
  let editingIndex = $state(-1);
  let editingName = $state('');
  let editingDosage = $state(0);
  
  function addNutrient() {
    const trimmed = newNutrientName.trim();
    if (trimmed && !nutrientList.some(n => n.name === trimmed)) {
      nutrientList = [...nutrientList, { name: trimmed, defaultDosage: newNutrientDosage }];
      newNutrientName = '';
      newNutrientDosage = 1.0;
      emitChange();
    }
  }
  
  function removeNutrient(index) {
    nutrientList = nutrientList.filter((_, i) => i !== index);
    emitChange();
  }
  
  function startEdit(index) {
    editingIndex = index;
    editingName = nutrientList[index].name;
    editingDosage = nutrientList[index].defaultDosage;
  }
  
  function saveEdit() {
    const trimmed = editingName.trim();
    if (trimmed && editingDosage > 0) {
      // Check if name already exists (excluding current item)
      const exists = nutrientList.some((nutrient, index) => 
        index !== editingIndex && nutrient.name === trimmed
      );
      
      if (!exists) {
        nutrientList[editingIndex] = { name: trimmed, defaultDosage: editingDosage };
        nutrientList = [...nutrientList];
        emitChange();
      }
    }
    cancelEdit();
  }
  
  function cancelEdit() {
    editingIndex = -1;
    editingName = '';
    editingDosage = 0;
  }
  
  function resetToDefaults() {
    nutrientList = [...defaultNutrients];
    emitChange();
  }
  
  async function emitChange() {
    // Save to nutrients API
    try {
      const response = await fetch(`${API_BASE_URL}/api/nutrients`);
      if (response.ok) {
        const currentConfig = await response.json();
        
        // Update the available nutrients while preserving formulas
        const updatedConfig = {
          ...currentConfig,
          available_nutrients: nutrientList
        };
        
        // Save the updated configuration
        const saveResponse = await fetch(`${API_BASE_URL}/api/nutrients`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatedConfig)
        });
        
        if (saveResponse.ok) {
          console.log('Nutrients saved successfully');
        } else {
          console.error('Failed to save nutrients');
        }
      }
    } catch (error) {
      console.error('Error saving nutrients:', error);
    }
    
    // Also dispatch custom event to parent component for immediate UI updates
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('nutrients-updated', {
        detail: { nutrients: nutrientList }
      }));
    }
  }
  
  function handleKeyPress(event, action) {
    if (event.key === 'Enter') {
      event.preventDefault();
      if (action === 'add') {
        addNutrient();
      } else if (action === 'save') {
        saveEdit();
      }
    } else if (event.key === 'Escape' && action === 'save') {
      cancelEdit();
    }
  }
</script>

<div class="nutrients-container">
  <div class="nutrients-header">
    <h4><i class="fas fa-seedling"></i> Available Nutrients</h4>
    <p class="nutrients-description">
      Manage the list of available nutrients for pump mapping and recipes.
    </p>
  </div>
  
  <!-- Add New Nutrient -->
  <div class="add-nutrient">
    <div class="add-row">
      <input 
        type="text" 
        bind:value={newNutrientName}
        placeholder="Enter nutrient name..."
        onkeypress={(e) => handleKeyPress(e, 'add')}
      />
      <input 
        type="number" 
        bind:value={newNutrientDosage}
        placeholder="ml/gal"
        min="0.1"
        max="50"
        step="0.1"
        title="Default dosage in ml per gallon"
      />
      <button
        class="btn btn-primary"
        onclick={addNutrient}
        disabled={!newNutrientName.trim() || newNutrientDosage <= 0}
        aria-label="Add new nutrient to library"
      >
        <i class="fas fa-plus" aria-hidden="true"></i>
        Add Nutrient
      </button>
    </div>
  </div>
  
  <!-- Nutrients List -->
  <div class="nutrients-list">
    {#each nutrientList as nutrient, index}
      <div class="nutrient-item">
        {#if editingIndex === index}
          <div class="edit-inputs">
            <!-- svelte-ignore a11y_autofocus -->
            <input 
              type="text" 
              bind:value={editingName}
              class="edit-input edit-name"
              placeholder="Nutrient name"
              onkeypress={(e) => handleKeyPress(e, 'save')}
              autofocus
            />
            <input 
              type="number" 
              bind:value={editingDosage}
              class="edit-input edit-dosage"
              placeholder="ml/gal"
              min="0.1"
              max="50"
              step="0.1"
              onkeypress={(e) => handleKeyPress(e, 'save')}
            />
          </div>
          <div class="edit-actions">
            <button
              class="btn-save"
              onclick={saveEdit}
              disabled={!editingName.trim() || editingDosage <= 0}
              aria-label="Save nutrient changes"
            >
              <i class="fas fa-check" aria-hidden="true"></i>
            </button>
            <button
              class="btn-cancel"
              onclick={cancelEdit}
              aria-label="Cancel nutrient editing"
            >
              <i class="fas fa-times" aria-hidden="true"></i>
            </button>
          </div>
        {:else}
          <div class="nutrient-info">
            <span class="nutrient-name">{nutrient.name}</span>
            <span class="nutrient-dosage">{nutrient.defaultDosage} ml/gal</span>
          </div>
          <div class="nutrient-actions">
            <button
              class="btn-edit"
              onclick={() => startEdit(index)}
              aria-label="Edit {nutrient.name} nutrient"
            >
              <i class="fas fa-edit" aria-hidden="true"></i>
            </button>
            <button
              class="btn-remove"
              onclick={() => removeNutrient(index)}
              aria-label="Remove {nutrient.name} nutrient"
            >
              <i class="fas fa-trash" aria-hidden="true"></i>
            </button>
          </div>
        {/if}
      </div>
    {/each}
    
    {#if nutrientList.length === 0}
      <div class="no-nutrients">
        <i class="fas fa-info-circle"></i>
        No nutrients configured. Add some nutrients to get started.
      </div>
    {/if}
  </div>
  
  <!-- Actions -->
  <div class="nutrients-actions">
    <button
      class="btn btn-secondary"
      onclick={resetToDefaults}
      aria-label="Reset nutrients to default list"
    >
      <i class="fas fa-undo" aria-hidden="true"></i>
      Reset to Defaults
    </button>
    <div class="nutrient-count">
      {nutrientList.length} nutrient{nutrientList.length !== 1 ? 's' : ''}
    </div>
  </div>
  
  <!-- Usage Info -->
  <div class="usage-info">
    <h5><i class="fas fa-info-circle"></i> Usage</h5>
    <ul>
      <li>These nutrients will be available for pump mapping in pump configuration</li>
      <li>They'll also appear as options when creating VEG and BLOOM formulas</li>
      <li>Nutrient names should match your physical nutrient bottles/containers</li>
      <li>Changes are automatically saved to your configuration</li>
    </ul>
  </div>
</div>

<style>
  .nutrients-container {
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 0.5rem;
    padding: 1.5rem;
  }
  
  .nutrients-header {
    margin-bottom: 1.5rem;
  }
  
  .nutrients-header h4 {
    margin: 0 0 0.5rem 0;
    color: #06b6d4;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .nutrients-description {
    color: #94a3b8;
    margin: 0;
    font-size: 0.9rem;
  }
  
  .add-nutrient {
    margin-bottom: 1.5rem;
  }
  
  .add-row {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .add-row input[type="text"] {
    flex: 2;
    padding: 0.75rem;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
  }
  
  .add-row input[type="number"] {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #475569;
    border-radius: 0.375rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
    min-width: 80px;
  }
  
  .add-row input:focus {
    outline: none;
    border-color: #06b6d4;
  }
  
  .nutrients-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    max-height: 300px;
    overflow-y: auto;
  }
  
  .nutrient-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem;
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    transition: all 0.2s;
  }
  
  .nutrient-item:hover {
    border-color: #475569;
    background: #1e293b;
  }
  
  .nutrient-info {
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  
  .nutrient-name {
    color: #e2e8f0;
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  .nutrient-dosage {
    color: #94a3b8;
    font-size: 0.8rem;
    font-style: italic;
  }
  
  .nutrient-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .edit-inputs {
    display: flex;
    gap: 0.5rem;
    flex: 1;
    margin-right: 1rem;
  }
  
  .edit-name {
    flex: 2;
  }
  
  .edit-dosage {
    flex: 1;
    min-width: 80px;
  }
  
  .edit-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #06b6d4;
    border-radius: 0.25rem;
    background: #334155;
    color: white;
    font-size: 0.9rem;
    margin-right: 1rem;
  }
  
  .edit-input:focus {
    outline: none;
    border-color: #0891b2;
  }
  
  .edit-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .btn-edit, .btn-remove, .btn-save, .btn-cancel {
    padding: 0.5rem;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
  }
  
  .btn-edit {
    background: #475569;
    color: white;
  }
  
  .btn-edit:hover {
    background: #64748b;
  }
  
  .btn-remove {
    background: #dc2626;
    color: white;
  }
  
  .btn-remove:hover {
    background: #b91c1c;
  }
  
  .btn-save {
    background: #10b981;
    color: white;
  }
  
  .btn-save:hover:not(:disabled) {
    background: #059669;
  }
  
  .btn-cancel {
    background: #6b7280;
    color: white;
  }
  
  .btn-cancel:hover {
    background: #4b5563;
  }
  
  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .btn-primary {
    background: #06b6d4;
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: #0891b2;
  }
  
  .btn-secondary {
    background: #475569;
    color: white;
  }
  
  .btn-secondary:hover {
    background: #64748b;
  }
  
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .nutrients-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #334155;
  }
  
  .nutrient-count {
    color: #94a3b8;
    font-size: 0.9rem;
    font-style: italic;
  }
  
  .no-nutrients {
    text-align: center;
    padding: 2rem;
    color: #94a3b8;
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }
  
  .usage-info {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 0.375rem;
    padding: 1rem;
  }
  
  .usage-info h5 {
    margin: 0 0 0.75rem 0;
    color: #f59e0b;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  
  .usage-info ul {
    margin: 0;
    padding-left: 1.25rem;
  }
  
  .usage-info li {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
  }
  
  @media (max-width: 768px) {
    .add-row {
      flex-direction: column;
      gap: 0.75rem;
    }
    
    .add-row input {
      width: 100%;
      min-width: auto;
    }
    
    .edit-inputs {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .edit-name, .edit-dosage {
      flex: 1;
      min-width: auto;
    }
    
    .nutrients-actions {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    
    .nutrient-count {
      text-align: center;
    }
  }
</style>