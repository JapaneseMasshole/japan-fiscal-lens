<script setup>
// A tidy list of datasets being added next, with their official sources. No numbers.
defineProps({
  title: { type: String, required: true },
  intro: { type: String, default: '' },
  items: { type: Array, required: true }, // [[what, source], ...]
})
</script>

<template>
  <section class="coming">
    <h2>{{ title }}</h2>
    <p v-if="intro" class="muted">{{ intro }}</p>
    <ul>
      <li v-for="([what, source], i) in items" :key="i">
        <span class="dot" aria-hidden="true" />
        <span class="what">{{ what }}</span>
        <span class="source muted">{{ source }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.coming { border: 1px dashed var(--border); border-radius: var(--radius); padding: 20px; margin: 24px 0 48px; }
.coming h2 { margin-bottom: 4px; }
.coming > p { margin: 0 0 12px; font-size: 0.9rem; }
ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
li { display: grid; grid-template-columns: 12px 1fr; column-gap: 10px; align-items: baseline; }
.dot { width: 8px; height: 8px; border-radius: 50%; border: 2px solid var(--accent); display: inline-block; }
.what { font-weight: 600; }
.source { grid-column: 2; font-size: 0.85rem; }
</style>
