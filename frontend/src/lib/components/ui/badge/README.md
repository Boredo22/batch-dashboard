# Badge Component

A flexible badge component built with Svelte 5 and Tailwind CSS, following shadcn design patterns.

## Features

- Svelte 5 compatibility with `$props()` destructuring
- Multiple variants: default, secondary, destructive, outline
- Dark theme optimized with CSS custom properties
- Tailwind class merging with `cn()` utility
- Custom class support for extended styling
- Accessible focus states and transitions

## Installation

The component is already installed at:
```
frontend/src/lib/components/ui/badge/
├── Badge.svelte          # Main component
├── index.js              # Exports and variant definitions
├── BadgeDemo.svelte      # Usage examples
└── README.md             # This documentation
```

## Usage

### Basic Import

```javascript
import { Badge } from "$lib/components/ui/badge";
// OR
import { Badge } from "$lib/components/ui";
```

### Basic Usage

```svelte
<Badge>Default Badge</Badge>
<Badge variant="secondary">Secondary Badge</Badge>
<Badge variant="destructive">Error Badge</Badge>
<Badge variant="outline">Outline Badge</Badge>
```

### Custom Styling

```svelte
<Badge class="bg-purple-900/20 text-purple-400 border-purple-900/30">
  Custom Purple Badge
</Badge>

<Badge variant="outline" class="border-green-600/50 text-green-400">
  Custom Green Outline
</Badge>
```

### Status Badges (Replacing existing status-badge classes)

Instead of:
```svelte
<div class="status-badge {systemStatus.toLowerCase()}">
  {systemStatus}
</div>
```

Use:
```svelte
<script>
  import { Badge } from "$lib/components/ui/badge";
  
  $: statusVariant = systemStatus === 'Connected' ? 'default' : 'destructive';
  $: statusClass = systemStatus === 'Connected' 
    ? 'bg-green-900/20 text-green-400 border-green-900/30 hover:bg-green-900/30'
    : 'bg-red-900/20 text-red-400 border-red-900/30 hover:bg-red-900/30';
</script>

<Badge variant={statusVariant} class={statusClass}>
  {systemStatus}
</Badge>
```

## Available Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| `default` | Primary badge with high contrast | Important status, active items |
| `secondary` | Muted background variant | Secondary information, tags |
| `destructive` | Error/danger styling | Errors, critical warnings |
| `outline` | Transparent with border | Subtle indicators, categories |

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `string` | `"default"` | Badge variant (default, secondary, destructive, outline) |
| `class` | `string` | `""` | Additional CSS classes |
| `children` | `snippet` | - | Badge content (text, icons, etc.) |

## Integration with Existing Status System

The badge component integrates seamlessly with your existing status classes defined in `app.css`:

```css
/* Existing classes in app.css */
.status-connected { @apply bg-green-900/20 text-green-400 border border-green-900/30; }
.status-disconnected { @apply bg-red-900/20 text-red-400 border border-red-900/30; }
.status-error { @apply bg-orange-900/20 text-orange-400 border border-orange-900/30; }
```

You can use these as class overrides:
```svelte
<Badge class="status-connected">Connected</Badge>
<Badge class="status-disconnected">Disconnected</Badge>
<Badge class="status-error">Error</Badge>
```

## Examples

### System Status Badge
```svelte
<script>
  let systemStatus = $state('Connected');
  
  $: getStatusBadgeProps = (status) => {
    switch(status.toLowerCase()) {
      case 'connected':
        return { 
          variant: 'default',
          class: 'bg-green-900/20 text-green-400 border-green-900/30 hover:bg-green-900/30'
        };
      case 'disconnected':
        return { 
          variant: 'destructive',
          class: 'bg-red-900/20 text-red-400 border-red-900/30 hover:bg-red-900/30'
        };
      case 'error':
        return { 
          variant: 'destructive',
          class: 'bg-orange-900/20 text-orange-400 border-orange-900/30 hover:bg-orange-900/30'
        };
      default:
        return { variant: 'secondary' };
    }
  };
</script>

<Badge {...getStatusBadgeProps(systemStatus)}>
  {systemStatus}
</Badge>
```

### Pump Status Badges
```svelte
{#each pumps as pump}
  <div class="pump-item">
    <span>{pump.name}</span>
    <Badge 
      variant={pump.status === 'running' ? 'default' : 'secondary'}
      class={pump.status === 'running' 
        ? 'bg-purple-900/20 text-purple-400 border-purple-900/30' 
        : ''}
    >
      {pump.status}
    </Badge>
  </div>
{/each}
```

## Dark Theme Integration

The component uses CSS custom properties from your `app.css`:
- `--primary` / `--primary-foreground`
- `--secondary` / `--secondary-foreground`  
- `--destructive` / `--destructive-foreground`
- `--border`, `--accent`, `--background`

This ensures consistent theming across your application.