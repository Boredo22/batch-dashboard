<script>
	import { Switch } from "../switch/index.js";
	import { TabsRoot, TabsList, TabsTrigger, TabsContent } from "../tabs/index.js";
	import { Textarea } from "../textarea/index.js";

	let switchChecked = $state(false);
	let tabValue = $state("tab1");
	let textareaValue = $state("Enter your text here...");
</script>

<div class="demo-container">
	<div class="section">
		<h3>Switch Component</h3>
		<div class="switch-demo">
			<label class="flex items-center gap-2">
				<Switch bind:checked={switchChecked} />
				<span>Enable notifications ({switchChecked ? 'ON' : 'OFF'})</span>
			</label>
		</div>
	</div>

	<div class="section">
		<h3>Tabs Component</h3>
		<TabsRoot bind:value={tabValue} class="w-full">
			<TabsList class="grid w-full grid-cols-3">
				<TabsTrigger value="tab1">General</TabsTrigger>
				<TabsTrigger value="tab2">Security</TabsTrigger>
				<TabsTrigger value="tab3">Advanced</TabsTrigger>
			</TabsList>
			<TabsContent value="tab1" class="mt-4">
				<div class="p-4 border rounded-md bg-card">
					<h4 class="text-sm font-medium mb-2">General Settings</h4>
					<p class="text-sm text-muted-foreground">Configure general application settings and preferences.</p>
				</div>
			</TabsContent>
			<TabsContent value="tab2" class="mt-4">
				<div class="p-4 border rounded-md bg-card">
					<h4 class="text-sm font-medium mb-2">Security Settings</h4>
					<p class="text-sm text-muted-foreground">Manage security options and access controls.</p>
				</div>
			</TabsContent>
			<TabsContent value="tab3" class="mt-4">
				<div class="p-4 border rounded-md bg-card">
					<h4 class="text-sm font-medium mb-2">Advanced Settings</h4>
					<p class="text-sm text-muted-foreground">Configure advanced system parameters and debugging options.</p>
				</div>
			</TabsContent>
		</TabsRoot>
	</div>

	<div class="section">
		<h3>Textarea Component</h3>
		<div class="textarea-demo">
			<label class="text-sm font-medium">Description:</label>
			<Textarea 
				bind:value={textareaValue} 
				placeholder="Enter a detailed description..."
				rows={4}
				class="mt-2"
			/>
			<p class="text-xs text-muted-foreground mt-2">
				Character count: {textareaValue.length}
			</p>
		</div>
	</div>
</div>

<style>
	.demo-container {
		padding: 2rem;
		max-width: 600px;
		margin: 0 auto;
		color: hsl(var(--foreground));
	}

	.section {
		margin-bottom: 3rem;
	}

	.section h3 {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 1.5rem;
		color: hsl(var(--foreground));
	}

	.switch-demo {
		padding: 1rem;
		border: 1px solid hsl(var(--border));
		border-radius: 0.5rem;
		background-color: hsl(var(--card));
	}

	.switch-demo label {
		cursor: pointer;
		font-size: 0.875rem;
	}

	.textarea-demo {
		display: flex;
		flex-direction: column;
	}

	.textarea-demo label {
		font-size: 0.875rem;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}
</style>