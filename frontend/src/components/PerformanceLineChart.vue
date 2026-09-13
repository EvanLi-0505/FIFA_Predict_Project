<script setup>
import { computed } from 'vue'

const props = defineProps({
  // [{ name: 'England', color: '#4f7cff', points: [{ label, value }, ...] }, ...]
  // points are chronological (oldest -> newest), value = per-match goal
  // difference (+goals scored, -goals conceded). 1 or 2 series supported.
  series: { type: Array, required: true },
})

const WIDTH = 600
const HEIGHT = 220
const PAD_X = 24
const PAD_Y = 20

const maxAbsValue = computed(() => {
  const all = props.series.flatMap((s) => s.points.map((p) => Math.abs(p.value)))
  return Math.max(1, ...all)
})

const maxPointCount = computed(() => Math.max(1, ...props.series.map((s) => s.points.length)))

function yFor(value) {
  const usable = (HEIGHT - PAD_Y * 2) / 2
  return HEIGHT / 2 - (value / maxAbsValue.value) * usable
}

function xFor(index, count) {
  if (count <= 1) return WIDTH / 2
  const usable = WIDTH - PAD_X * 2
  return PAD_X + (index / (count - 1)) * usable
}

const lines = computed(() =>
  props.series.map((s) => {
    const count = s.points.length
    const coords = s.points.map((p, i) => ({
      x: xFor(i, count),
      y: yFor(p.value),
      label: p.label,
      opponent: p.opponent,
      value: p.value,
    }))
    return {
      name: s.name,
      color: s.color,
      path: coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' '),
      coords,
    }
  }),
)

const zeroY = computed(() => yFor(0))
</script>

<template>
  <div class="performance-chart">
    <div v-if="series.length > 1" class="legend">
      <span v-for="s in series" :key="s.name" class="legend-item">
        <span class="dot" :style="{ background: s.color }" />
        {{ s.name }}
      </span>
    </div>

    <p v-if="maxPointCount <= 1" class="muted">Not enough recent matches to plot a trend.</p>

    <svg v-else :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="chart-svg" preserveAspectRatio="none">
      <line :x1="0" :x2="WIDTH" :y1="zeroY" :y2="zeroY" class="zero-line" />
      <text :x="4" :y="zeroY - 4" class="axis-label">0</text>
      <text :x="4" :y="PAD_Y" class="axis-label">+{{ maxAbsValue }}</text>
      <text :x="4" :y="HEIGHT - 6" class="axis-label">-{{ maxAbsValue }}</text>

      <g v-for="line in lines" :key="line.name">
        <path :d="line.path" fill="none" :stroke="line.color" stroke-width="2.5" class="line-path" />
        <circle
          v-for="(c, i) in line.coords"
          :key="i"
          :cx="c.x"
          :cy="c.y"
          r="3.5"
          :fill="line.color"
        >
          <title>{{ c.label }} vs {{ c.opponent }}: {{ c.value > 0 ? '+' : '' }}{{ c.value }}</title>
        </circle>
      </g>
    </svg>

    <div v-if="maxPointCount > 1" class="x-labels muted">
      <span>Oldest of last {{ maxPointCount }}</span>
      <span>Most recent</span>
    </div>
  </div>
</template>

<style scoped>
.legend {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.chart-svg {
  width: 100%;
  height: 220px;
  display: block;
}

.zero-line {
  stroke: var(--color-border);
  stroke-width: 1.5;
  stroke-dasharray: 4 4;
}

.axis-label {
  fill: var(--color-text-muted);
  font-size: 10px;
}

.line-path {
  transition: d 0.4s ease;
}

.x-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-top: 4px;
}
</style>
