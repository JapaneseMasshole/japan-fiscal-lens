<script setup>
// A titled card holding one ECharts chart and its source line.
// With no `option`, it shows an empty state instead of a fake chart.
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import echarts from '../echarts.js'
import { t } from '../i18n.js'

const props = defineProps({
  title: { type: String, required: true },
  option: { type: Object, default: null },
  source: { type: Object, default: null }, // { id, publisher, title, url }
})

const el = ref(null)
let chart = null
let observer = null

function render() {
  if (!props.option || !el.value) return
  if (!chart) {
    chart = echarts.init(el.value)
    observer = new ResizeObserver(() => chart?.resize())
    observer.observe(el.value)
  }
  chart.setOption(props.option, true)
}

onMounted(render)
// flush: 'post' so the chart div exists when an option first arrives.
watch(() => props.option, render, { deep: true, flush: 'post' })
onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
})
</script>

<template>
  <section class="card">
    <h2>{{ title }}</h2>
    <div v-if="option" ref="el" class="chart" />
    <p v-else class="empty muted">{{ t('noData') }}</p>
    <p v-if="source" class="source muted">
      {{ t('source') }}: <a :href="source.url" target="_blank" rel="noopener">{{ source.publisher }}「{{ source.title }}」</a>
      （{{ t('processed') }}）
    </p>
  </section>
</template>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.chart { width: 100%; height: 320px; }
.empty { min-height: 120px; display: flex; align-items: center; font-size: 0.9rem; }
.source { font-size: 0.8rem; margin: 8px 0 0; }
</style>
