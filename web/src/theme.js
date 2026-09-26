import { ref } from 'vue'

// Reactive dark-mode flag, so charts can re-read tokens when the OS theme changes.
const query = window.matchMedia('(prefers-color-scheme: dark)')
export const isDark = ref(query.matches)
query.addEventListener('change', (e) => (isDark.value = e.matches))

// Read chart colors from CSS custom properties (defined in style.css for both modes).
export function tokens() {
  void isDark.value // dependency for computed() callers
  const css = getComputedStyle(document.documentElement)
  const v = (name) => css.getPropertyValue(name).trim()
  return {
    surface: v('--viz-surface'),
    grid: v('--viz-grid'),
    axis: v('--viz-axis'),
    text: v('--text'),
    muted: v('--muted'),
    series: [v('--viz-series-1'), v('--viz-series-2'), v('--viz-series-3')],
    context: v('--viz-context'),
    reference: v('--viz-reference'),
    font: getComputedStyle(document.body).fontFamily,
  }
}
