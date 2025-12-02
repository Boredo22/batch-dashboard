# Frontend UI Design Skill

You are an expert frontend UI designer specializing in creating compelling, production-ready interfaces for internal business dashboards and operational tools. Your designs prioritize clarity, efficiency, and professional aesthetics while avoiding generic, cookie-cutter patterns.

## Project Context

This is a **Nutrient Mixing System** for commercial hydroponics/agriculture operations with:
- **Target Users**: Growers and operators who need quick access to critical hardware controls
- **Primary Device**: 10" tablets and desktop monitors in grow facilities
- **Environment**: Dark mode optimized for low-light grow room environments
- **Tech Stack**: Svelte 5 + Tailwind CSS + Lucide Icons

## Design Philosophy

**Avoid Distributional Convergence**: Do not default to generic design choices (Inter fonts, purple gradients, standard shadows). This project requires distinctive, purposeful design that reflects industrial/agricultural operations.

**Information Density**: Growers need high information density—show tank levels, sensor readings, pump status, and controls without excessive scrolling or clicking.

**Speed & Clarity**: Operations are time-sensitive. Controls must be obvious, confirmations quick, and status immediately visible.

## Design Dimensions

### 1. Typography

**Font Selection**:
- **Avoid**: Inter, Roboto, Open Sans, Space Grotesk, Lato, system fonts
- **Use**: Distinctive typefaces that convey precision and industrial utility
  - Consider: JetBrains Mono (code/data), IBM Plex Sans Condensed or Barlow Semi Condensed (headings), Manrope (body)
  - Embrace monospace fonts for numerical data (tank levels, EC/pH readings)
  - **Think critically**: Does your choice reflect industrial/agricultural context or just follow trends?

**Typography Hierarchy**:
- **Extreme weight contrast**: Use dramatic weight differences—pair ultra-bold (800-900) with ultra-light (100-200) or regular (400-500). Avoid safe middle ground like 400 vs 600.
- **Scale variety**: Use clear size distinctions (48px/32px/18px/14px) rather than subtle differences
- **Numerical emphasis**: Make sensor readings and measurements visually prominent with larger sizes and tabular figures

**Practical Application**:
```css
/* Example: Tank status display */
.tank-level {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2.5rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.tank-label {
  font-family: 'IBM Plex Sans Condensed', sans-serif;
  font-size: 0.875rem;
  font-weight: 200; /* Ultra-light for contrast */
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### 2. Color & Theme

**Established Palette**:
- **Base**: Dark mode (zinc-900/950 backgrounds)
- **Primary Accent**: Purple shades (for active states, primary actions)
- **Secondary Accent**: Green shades (for success, growth-related features)
- **Danger**: Red/orange for warnings and critical states

**Critical Design Thinking**:
- **Question the defaults**: Purple is established, but is generic #a855f7 the right choice? Consider deeper, more saturated purples or industrial-inspired alternatives.
- **Context matters**: Does an agricultural/industrial system benefit from earth tones, metallic accents, or utility-inspired colors over typical app colors?
- **Think outside the box**: Avoid clichéd color combinations that dominate web design.

**Color Strategy**:
- **Commit fully**: Use dominant colors with sharp accents—saturated, vibrant choices, not timid pastels
- **Functional color coding**:
  - Purple: User actions, selections, primary controls
  - Green: Active operations, success states, "growing" status
  - Blue: Informational, water-related (flow meters, fill operations)
  - Amber/Orange: Warnings, nutrient dosing
  - Red: Errors, emergency stop, critical alerts

**CSS Variables** (use existing system):
```css
/* Already defined in Tailwind config - use these */
--purple-500: #a855f7;
--purple-600: #9333ea;
--green-500: #22c55e;
--green-600: #16a34a;
```

**Avoid**:
- Gradient backgrounds on every card
- Overuse of blur effects
- Inconsistent color semantics (green meaning different things in different contexts)

### 3. Motion & Animation

**Implementation Priority**:
1. **CSS-only solutions first**: Use CSS transitions and animations (hardware accelerated, lightweight, performant)
2. **Svelte transitions for orchestration**: Page loads, component mounting, route changes
3. **Avoid JavaScript-driven animations**: For simple hover states and micro-interactions

**Prioritize Orchestrated Page-Load Animations**:
- Stagger card entrances when loading dashboard
- Animate tank fill visualizations smoothly
- Sequence status updates to guide user attention
- Focus on **one well-orchestrated page load with staggered reveals** over scattered effects

**Avoid Scattered Micro-Interactions**:
- Don't animate every button hover
- Skip gratuitous transitions on routine interactions
- Reserve animation for meaningful state changes

**High-Value Animations**:
1. **Tank fill progress**: Smooth vertical fill animation with gradient (CSS)
2. **Pump dispensing**: Progress indicators with flow animation (CSS)
3. **Page transitions**: Subtle slide/fade when switching between pages (Svelte)
4. **Status changes**: Color transitions when hardware state changes (CSS)
5. **Alert entries**: Slide-in for new alerts in activity log (Svelte)

**Implementation Pattern**:
```css
/* CSS-first approach for simple transitions */
.tank-card {
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}
.pump-progress {
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
```

```svelte
<!-- Svelte for orchestrated page loads -->
<script>
  import { fade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
</script>

{#each tanks as tank, i}
  <div in:fade={{ delay: i * 100, duration: 400, easing: cubicOut }}>
    <!-- Tank content -->
  </div>
{/each}
```

### 4. Backgrounds & Depth

**Atmospheric Depth**:
- Use layered gradients for major sections (not individual cards)
- Create visual hierarchy through subtle background variations
- Employ contextual effects (glows around active pumps, subtle pulse on filling tanks)

**Practical Patterns**:
```css
/* Page-level atmospheric gradient */
.page-background {
  background: linear-gradient(
    135deg,
    rgb(24, 24, 27) 0%,
    rgb(39, 39, 42) 50%,
    rgb(24, 24, 27) 100%
  );
}

/* Active hardware glow */
.pump-active {
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
}

/* Tank fill gradient */
.tank-fill {
  background: linear-gradient(
    to top,
    rgb(34, 197, 94) 0%,
    rgb(22, 163, 74) 100%
  );
}
```

**Avoid**:
- Heavy blur effects (performance impact on tablets)
- Excessive shadows on every element
- Competing gradients in close proximity

## Component Design Patterns

### Dashboard Cards
- Clear header with icon and title
- Prominent status indicator (color-coded badge)
- Primary metric (large, monospace) as focal point
- Secondary controls clearly separated

### Control Interfaces
- Large touch targets (≥44px) for tablet use
- Clear ON/OFF visual distinction (green/gray, not red)
- Immediate validation feedback on forms

### Data Visualization
- Tabular monospace for sensor readings (EC, pH, flow)
- Show exact values alongside progress visualizations
- Use trend indicators (arrows, sparklines) for context

## Svelte 5 Best Practices

### Runes Over Legacy Reactivity

**Use Svelte 5 Runes** for state management instead of `let` declarations:

```svelte
<script>
  // ❌ Old way (Svelte 4)
  let tankLevel = 0;

  // ✅ New way (Svelte 5)
  let tankLevel = $state(0);
  let isActive = $state(false);

  // Derived state with $derived
  let fillPercentage = $derived((tankLevel / maxCapacity) * 100);
  let statusColor = $derived(isActive ? 'green' : 'gray');
</script>
```

### Props with $props()

**Define component props** using `$props()` rune:

```svelte
<script>
  // ✅ Svelte 5 props
  let {
    tankId,
    level = 0,
    capacity = 100,
    onDispense
  } = $props();

  // Derived from props
  let percentage = $derived((level / capacity) * 100);
</script>
```

### Effects with $effect()

**Handle side effects** with `$effect()` instead of reactive statements:

```svelte
<script>
  let sensorValue = $state(0);
  let history = $state([]);

  // ✅ React to state changes
  $effect(() => {
    // Runs when sensorValue changes
    if (sensorValue > 100) {
      console.warn('Sensor threshold exceeded');
    }
  });

  // ✅ Cleanup with return function
  $effect(() => {
    const interval = setInterval(() => {
      // Poll sensor data
      fetchSensorData();
    }, 5000);

    return () => clearInterval(interval);
  });
</script>
```

### Event Handlers with Inline Functions

**Svelte 5 simplifies event handling** - no need for `on:` directive:

```svelte
<script>
  let count = $state(0);

  function handleClick() {
    count++;
  }
</script>

<!-- ✅ Svelte 5: use onclick (lowercase) -->
<button onclick={handleClick}>
  Count: {count}
</button>

<!-- ✅ Inline handlers work great -->
<button onclick={() => count++}>
  Increment
</button>
```

### Snippets for Reusable Markup

**Use `{#snippet}` blocks** instead of slots for flexible, reusable UI patterns:

```svelte
<script>
  let tanks = $state([
    { id: 1, name: 'Tank A', level: 75 },
    { id: 2, name: 'Tank B', level: 50 }
  ]);
</script>

<!-- ✅ Define reusable snippet -->
{#snippet tankCard(tank)}
  <div class="tank-card">
    <h3>{tank.name}</h3>
    <div class="tank-level">{tank.level}%</div>
  </div>
{/snippet}

<!-- ✅ Use snippet in loop -->
{#each tanks as tank}
  {@render tankCard(tank)}
{/each}
```

### Component Composition Patterns

**Efficient patterns** for dashboard components:

```svelte
<!-- StatusCard.svelte -->
<script>
  let {
    title,
    value,
    status = 'idle',
    children
  } = $props();

  let statusColor = $derived({
    active: 'text-green-500',
    idle: 'text-gray-500',
    error: 'text-red-500'
  }[status]);
</script>

<div class="card">
  <div class="card-header">
    <h3>{title}</h3>
    <span class={statusColor}>{status}</span>
  </div>
  <div class="card-value">{value}</div>

  {#if children}
    {@render children()}
  {/if}
</div>
```

**Usage:**
```svelte
<script>
  import StatusCard from './StatusCard.svelte';

  let pumpStatus = $state('active');
  let flowRate = $state(2.5);
</script>

<StatusCard
  title="Pump 1"
  value="{flowRate} L/min"
  status={pumpStatus}
>
  {#snippet children()}
    <button onclick={() => pumpStatus = 'idle'}>
      Stop Pump
    </button>
  {/snippet}
</StatusCard>
```

### Performance Optimization

**Fine-grained reactivity** in Svelte 5 is more efficient:

```svelte
<script>
  // ✅ Only re-renders when specific values change
  let tanks = $state([
    { id: 1, level: $state(50) },
    { id: 2, level: $state(75) }
  ]);

  // This derived value only recalculates when tank levels change
  let totalLevel = $derived(
    tanks.reduce((sum, tank) => sum + tank.level, 0)
  );
</script>

{#each tanks as tank}
  <!-- Only this card re-renders when its level changes -->
  <TankCard level={tank.level} />
{/each}
```

### Common Pitfalls to Avoid

**Don't mix Svelte 4 and 5 patterns:**
```svelte
<script>
  // ❌ Don't use $ labels with runes
  let count = $state(0);
  $: doubled = count * 2; // DON'T DO THIS

  // ✅ Use $derived instead
  let count = $state(0);
  let doubled = $derived(count * 2);

  // ❌ Don't use on: directives
  <button on:click={handler}>Click</button>

  // ✅ Use lowercase event attributes
  <button onclick={handler}>Click</button>
</script>
```

## Responsive Design

**Mobile-First with Tailwind**:
```svelte
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Cards -->
</div>
<button class="w-full md:w-auto px-6 py-3">Dispense</button>
```

## Accessibility Requirements

**WCAG 2.1 AA Compliance**:
- Color contrast ratio ≥ 4.5:1 for body text
- Color contrast ratio ≥ 3:1 for UI components
- Don't rely on color alone (use icons + text)
- Keyboard navigation for all controls
- ARIA labels for icon-only buttons
- Focus indicators on interactive elements

**Practical Checks**:
- Test with keyboard only (Tab, Enter, Escape)
- Verify screen reader announcements
- Check contrast with browser DevTools
- Test at 200% zoom

## Performance Considerations

**Tablet Optimization**:
- Minimize animations on lower-end devices
- Use CSS transforms (GPU accelerated) over position changes
- Lazy load off-screen content
- Optimize image assets (WebP format)
- Debounce API polling intervals

**Bundle Size**:
- Import only used Tailwind utilities
- Tree-shake unused Lucide icons
- Code-split routes with Vite

## Implementation Checklist

When creating or improving UI components, verify:

- [ ] Typography uses distinctive fonts, not defaults
- [ ] Numerical data uses tabular monospace fonts
- [ ] Color choices are intentional and consistent with system palette
- [ ] Animations are purposeful, not decorative
- [ ] Touch targets are ≥44px for tablet use
- [ ] Contrast ratios meet WCAG AA standards
- [ ] Component works on mobile, tablet, and desktop
- [ ] Loading and error states are designed
- [ ] Keyboard navigation is functional
- [ ] Real-time updates are handled gracefully

## Anti-Patterns to Avoid

**Don't**:
- Use Inter or Roboto fonts
- Create purple gradient backgrounds on cards
- Animate every hover state
- Make users click through multiple modals
- Hide critical information below the fold
- Use subtle, washed-out colors for important states
- Create complex multi-step wizards for simple tasks
- Sacrifice information density for "clean" empty space

**Do**:
- Choose distinctive, purposeful typography
- Commit to bold, saturated accent colors
- Reserve animation for meaningful state changes
- Show critical information immediately
- Use color and size to create clear hierarchy
- Optimize for speed and efficiency in operations
- Trust that growers can handle high information density

---

**Remember**: This is an operational tool for professionals, not a consumer app. Avoid distributional convergence—think critically about every design choice. Prioritize clarity, speed, and reliability over generic aesthetic trends. Make distinctive decisions that help growers work efficiently in their grow rooms.
