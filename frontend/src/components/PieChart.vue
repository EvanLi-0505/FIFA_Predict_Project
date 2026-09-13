<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  segments: {
    // [{ label: 'Home Win', value: 12, color: '#3ec98b' }, ...]
    type: Array,
    required: true,
  },
  centerLabel: { type: String, default: '' },
})

const RADIUS = 60
const STROKE = 22
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

const total = computed(() => props.segments.reduce((sum, s) => sum + s.value, 0))

const animated = ref(false)
onMounted(() => {
  // Start all segments collapsed, then animate to full length on next frame
  // so the browser actually renders the 0-state first (donut "fills in").
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      animated.value = true
    })
  })
})

const arcs = computed(() => {
  if (total.value === 0) return []
  let offset = 0
  return props.segments.map((segment) => {
    const fraction = segment.value / total.value
    const length = fraction * CIRCUMFERENCE
    const arc = {
      ...segment,
      fraction,
      dasharray: `${length} ${CIRCUMFERENCE - length}`,
      dashoffset: -offset,
      percent: (fraction * 100).toFixed(1),
    }
    offset += length
    return arc
  })
})

const dominant = computed(() => {
  if (arcs.value.length === 0) return null
  return [...arcs.value].sort((a, b) => b.value - a.value)[0]
})
</script>

<template>
  <div class="pie-chart">
    <svg viewBox="0 0 150 150" class="pie-svg">
      <circle cx="75" cy="75" :r="RADIUS" fill="none" stroke="var(--color-surface-raised)" :stroke-width="STROKE" />
      <circle
        v-for="arc in arcs"
        :key="arc.label"
        cx="75"
        cy="75"
        :r="RADIUS"
        fill="none"
        :stroke="arc.color"
        :stroke-width="STROKE"
        :stroke-dasharray="animated ? arc.dasharray : `0 ${CIRCUMFERENCE}`"
        :stroke-dashoffset="arc.dashoffset"
        transform="rotate(-90 75 75)"
        class="pie-arc"
      />
      <text x="75" y="71" text-anchor="middle" class="pie-center-value">
        {{ dominant ? `${dominant.percent}%` : '—' }}
      </text>
      <text x="75" y="88" text-anchor="middle" class="pie-center-label">
        {{ centerLabel }}
      </text>
    </svg>

    <ul class="pie-legend">
      <li v-for="arc in arcs" :key="arc.label">
        <span class="dot" :style="{ background: arc.color }" />
        <span class="legend-label">{{ arc.label }}</span>
        <span class="legend-value">
          <template v-if="Number.isInteger(arc.value)">{{ arc.value }} ({{ arc.percent }}%)</template>
          <template v-else>{{ arc.percent }}%</template>
        </span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.pie-chart {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
}

.pie-svg {
  width: 170px;
  height: 170px;
  flex-shrink: 0;
}

.pie-arc {
  transition: stroke-dasharray 0.9s cubic-bezier(0.22, 1, 0.36, 1);
}

.pie-center-value {
  fill: var(--color-text);
  font-size: 1.15rem;
  font-weight: 700;
}

.pie-center-label {
  fill: var(--color-text-muted);
  font-size: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pie-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 180px;
}

.pie-legend li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  flex: 1;
}

.legend-value {
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
</style>
