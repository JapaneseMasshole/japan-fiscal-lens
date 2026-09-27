import { ref, watch } from 'vue'

// Viewer preferences kept in this browser only. Storage can be missing or blocked
// (private windows, previews), so every access is guarded and the default always works.
function stored(key, fallback, allowed) {
  let initial = fallback
  try {
    const v = localStorage.getItem(key)
    if (allowed.includes(v)) initial = v
  } catch {}
  const r = ref(initial)
  watch(r, (v) => {
    try {
      localStorage.setItem(key, v)
    } catch {}
  })
  return r
}

// Breakdown chart form: 'bars' | 'pie'. One setting for every breakdown, so charts shown
// side by side for comparison always switch together.
export const breakdownView = stored('jfl.breakdownView', 'bars', ['bars', 'pie'])
