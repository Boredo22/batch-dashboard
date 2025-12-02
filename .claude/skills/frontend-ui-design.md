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
- **Avoid**: Inter, Roboto, Open Sans, system fonts
- **Use**: Distinctive typefaces that convey precision and industrial utility
  - Consider: JetBrains Mono (code/data), Space Grotesk (headings), Manrope (body)
  - Embrace monospace fonts for numerical data (tank levels, EC/pH readings)

**Typography Hierarchy**:
- **Extreme weight contrast**: Pair ultra-bold headings (700-900) with regular body text (400-500)
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
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
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

**Color Strategy**:
- **Commit fully**: Don't use timid, washed-out colors. Use saturated purples and vibrant greens
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

**Prioritize Orchestrated Page-Load Animations**:
- Stagger card entrances when loading dashboard
- Animate tank fill visualizations smoothly
- Sequence status updates to guide user attention

**Avoid Scattered Micro-Interactions**:
- Don't animate every button hover
- Skip gratuitous transitions on routine interactions
- Reserve animation for meaningful state changes

**High-Value Animations**:
1. **Tank fill progress**: Smooth vertical fill animation with gradient
2. **Pump dispensing**: Progress indicators with flow animation
3. **Page transitions**: Subtle slide/fade when switching between pages
4. **Status changes**: Color transitions when hardware state changes (relay on/off)
5. **Alert entries**: Slide-in for new alerts in activity log

**Implementation Pattern**:
```svelte
<script>
  import { fade, slide, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
</script>

<!-- Orchestrated card entrance -->
{#each tanks as tank, i}
  <div
    in:fade={{ delay: i * 100, duration: 400, easing: cubicOut }}
    class="tank-card"
  >
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

**Structure**:
- Clear header with icon and title
- Prominent status indicator (color-coded badge)
- Primary metric (large, monospace)
- Secondary controls (buttons, toggles)
- Compact footer with metadata

**Visual Hierarchy**:
1. Status (color + icon) - immediate recognition
2. Primary value (tank level, pump progress) - largest element
3. Label/context - smaller, uppercase, tracked
4. Actions - clearly separated, high contrast

### Control Interfaces

**Hardware Controls** (relays, pumps):
- Toggle states with clear ON/OFF visual distinction
- Use green for ON, gray for OFF (not red - reserve for errors)
- Include hardware ID and name prominently
- Show real-time status updates

**Forms & Inputs**:
- High contrast labels (uppercase, tracked spacing)
- Large touch targets (min 44px height for tablet use)
- Immediate validation feedback
- Clear error states with helpful messages

### Data Visualization

**Sensor Readings** (EC, pH, flow):
- Large numerical display (tabular monospace)
- Unit labels (smaller, adjacent)
- Trend indicators (arrows, sparklines)
- Historical context when relevant

**Progress Indicators**:
- Linear progress bars for pumps (0-100%)
- Circular/radial progress for tank fills
- Color-coded by operation type
- Show exact values, not just bars

## Responsive Design

**Breakpoints** (Tailwind defaults):
- `sm:` 640px - Small tablets portrait
- `md:` 768px - Tablets landscape, small laptops
- `lg:` 1024px - Desktops
- `xl:` 1280px - Large desktops

**Mobile-First Approach**:
```svelte
<!-- Stack on mobile, grid on tablet+ -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Cards -->
</div>

<!-- Full width controls on mobile, compact on desktop -->
<button class="w-full md:w-auto px-6 py-3">
  Dispense
</button>
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

## Resources & References

**Design System**:
- Tailwind CSS documentation: https://tailwindcss.com
- Lucide Icons: https://lucide.dev
- Svelte 5 Transitions: https://svelte.dev/docs/svelte-transition

**Inspiration** (industrial/operational UIs):
- Aviation cockpits (information density)
- Industrial SCADA systems (real-time monitoring)
- Financial trading terminals (data visualization)
- Professional audio/video equipment (hardware control)

---

**Remember**: This is an operational tool for professionals, not a consumer app. Prioritize clarity, speed, and reliability over aesthetic trends. Make decisions that help growers work efficiently in their grow rooms.
