<script>
  import { getContext } from 'svelte';

  const {
    class: className = '',
    children,
    ...restProps
  } = $props();

  const sidebar = getContext('sidebar');
</script>

<div
  class="sidebar-footer {className}"
  class:collapsed={!sidebar.isOpen}
  data-sidebar="footer"
  {...restProps}
>
  {@render children?.()}
</div>

<style>
  .sidebar-footer {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid var(--sidebar-border);
    background: var(--sidebar-background);
    margin-top: auto;
  }

  .sidebar-footer.collapsed {
    padding: 1rem 0.5rem;
    align-items: center;
  }

  /* User profile section */
  .sidebar-footer :global(.sidebar-user) {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem;
    border-radius: 0.375rem;
    transition: background-color 0.2s ease;
  }

  .sidebar-footer.collapsed :global(.sidebar-user) {
    justify-content: center;
    padding: 0.5rem;
  }

  .sidebar-footer :global(.sidebar-user:hover) {
    background: var(--sidebar-accent);
  }

  .sidebar-footer :global(.sidebar-user-avatar) {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: var(--sidebar-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--sidebar-primary-foreground);
  }

  .sidebar-footer :global(.sidebar-user-info) {
    flex: 1;
    min-width: 0;
  }

  .sidebar-footer.collapsed :global(.sidebar-user-info) {
    display: none;
  }

  .sidebar-footer :global(.sidebar-user-name) {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--sidebar-foreground);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sidebar-footer :global(.sidebar-user-email) {
    font-size: 0.75rem;
    color: hsl(215.4 16.3% 46.9%);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Footer actions */
  .sidebar-footer :global(.sidebar-footer-actions) {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-top: 0.5rem;
  }

  .sidebar-footer.collapsed :global(.sidebar-footer-actions) {
    flex-direction: column;
    margin-top: 0.5rem;
  }

  .sidebar-footer :global(.sidebar-footer-button) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border: none;
    border-radius: 0.25rem;
    background: transparent;
    color: var(--sidebar-foreground);
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease;
  }

  .sidebar-footer :global(.sidebar-footer-button:hover) {
    background: var(--sidebar-accent);
  }

  .sidebar-footer :global(.sidebar-footer-button:focus) {
    outline: none;
    box-shadow: 0 0 0 2px var(--sidebar-ring);
  }

  /* Status indicator */
  .sidebar-footer :global(.sidebar-status) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    font-size: 0.75rem;
    color: hsl(215.4 16.3% 46.9%);
  }

  .sidebar-footer.collapsed :global(.sidebar-status) {
    justify-content: center;
  }

  .sidebar-footer.collapsed :global(.sidebar-status-text) {
    display: none;
  }

  .sidebar-footer :global(.sidebar-status-indicator) {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: hsl(142.1 76.2% 36.3%);
    flex-shrink: 0;
  }

  .sidebar-footer :global(.sidebar-status-indicator.warning) {
    background: hsl(47.9 95.8% 53.1%);
  }

  .sidebar-footer :global(.sidebar-status-indicator.error) {
    background: hsl(0 84.2% 60.2%);
  }

  /* Divider */
  .sidebar-footer :global(.sidebar-divider) {
    height: 1px;
    background: var(--sidebar-border);
    margin: 0.5rem 0;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .sidebar-footer {
      padding: 1rem 0.5rem;
    }
  }
</style>