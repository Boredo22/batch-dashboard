<script>
	import { Alert, AlertDescription, AlertTitle, Progress } from "../index.js";
	import { AlertCircle, CheckCircle, Info, AlertTriangle } from "@lucide/svelte";

	let progressValue = $state(65);
	let interval;

	function startProgressDemo() {
		if (interval) clearInterval(interval);
		progressValue = 0;
		interval = setInterval(() => {
			progressValue += 5;
			if (progressValue >= 100) {
				clearInterval(interval);
			}
		}, 200);
	}

	function onDestroy() {
		if (interval) clearInterval(interval);
	}
</script>

<div class="demo-container">
	<div class="section">
		<h3>Progress Components</h3>
		<div class="progress-demos">
			<div class="progress-demo">
				<p>Default Progress ({progressValue}%)</p>
				<Progress value={progressValue} />
			</div>
			
			<div class="progress-demo">
				<p>Success Progress (85%)</p>
				<Progress value={85} variant="success" />
			</div>
			
			<div class="progress-demo">
				<p>Purple Progress (45%)</p>
				<Progress value={45} variant="purple" />
			</div>
			
			<div class="progress-demo">
				<p>Green Progress (90%)</p>
				<Progress value={90} variant="green" />
			</div>
			
			<div class="progress-demo">
				<p>Large Warning Progress (75%)</p>
				<Progress value={75} variant="warning" size="lg" />
			</div>
			
			<div class="progress-demo">
				<p>Small Destructive Progress (30%)</p>
				<Progress value={30} variant="destructive" size="sm" />
			</div>
			
			<button onclick={startProgressDemo} class="demo-button">
				Start Progress Animation
			</button>
		</div>
	</div>

	<div class="section">
		<h3>Alert Components</h3>
		<div class="alert-demos">
			<Alert variant="default">
				<Info size={16} />
				<div>
					<AlertTitle>Default Alert</AlertTitle>
					<AlertDescription>
						This is a default alert with some information for the user.
					</AlertDescription>
				</div>
			</Alert>

			<Alert variant="success">
				<CheckCircle size={16} />
				<div>
					<AlertTitle>Success Alert</AlertTitle>
					<AlertDescription>
						Operation completed successfully! All systems are running normally.
					</AlertDescription>
				</div>
			</Alert>

			<Alert variant="warning">
				<AlertTriangle size={16} />
				<div>
					<AlertTitle>Warning Alert</AlertTitle>
					<AlertDescription>
						Pump pressure is slightly elevated. Monitor system performance.
					</AlertDescription>
				</div>
			</Alert>

			<Alert variant="destructive">
				<AlertCircle size={16} />
				<div>
					<AlertTitle>Error Alert</AlertTitle>
					<AlertDescription>
						Critical system error detected. Immediate attention required.
					</AlertDescription>
				</div>
			</Alert>

			<Alert variant="purple">
				<Info size={16} />
				<div>
					<AlertTitle>Purple Theme Alert</AlertTitle>
					<AlertDescription>
						This alert uses the purple theme color scheme.
					</AlertDescription>
				</div>
			</Alert>

			<Alert variant="green">
				<CheckCircle size={16} />
				<div>
					<AlertTitle>Green Theme Alert</AlertTitle>
					<AlertDescription>
						This alert uses the green theme color scheme for dashboard consistency.
					</AlertDescription>
				</div>
			</Alert>
		</div>
	</div>
</div>

<style>
	.demo-container {
		padding: 2rem;
		max-width: 800px;
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

	.progress-demos {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.progress-demo {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.progress-demo p {
		font-size: 0.875rem;
		color: hsl(var(--muted-foreground));
		margin: 0;
	}

	.alert-demos {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.demo-button {
		background-color: hsl(var(--primary));
		color: hsl(var(--primary-foreground));
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		border: none;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		transition: background-color 0.2s;
	}

	.demo-button:hover {
		background-color: hsl(var(--primary) / 0.9);
	}
</style>