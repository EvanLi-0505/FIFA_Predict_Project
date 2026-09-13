<script setup>
import { computed } from 'vue'

const props = defineProps({
  probabilities: { type: Object, required: true },
  predictedOutcome: { type: String, default: '' },
})

// Fixed display order regardless of the dict's key order in the response.
const ORDER = ['Home Win', 'Draw', 'Home Loss']

const rows = computed(() =>
  ORDER.filter((outcome) => outcome in props.probabilities).map((outcome) => ({
    outcome,
    value: props.probabilities[outcome],
    className: outcome.toLowerCase().replace(' ', '-'),
  })),
)
</script>

<template>
  <div class="probability-chart">
    <div v-for="row in rows" :key="row.outcome" class="prob-row">
      <div class="prob-label">
        <span>{{ row.outcome }}</span>
        <span class="prob-value">{{ (row.value * 100).toFixed(1) }}%</span>
      </div>
      <div class="prob-track">
        <div
          class="prob-fill"
          :class="[row.className, { winner: row.outcome === predictedOutcome }]"
          :style="{ width: `${row.value * 100}%` }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.probability-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prob-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  margin-bottom: 4px;
}

.prob-value {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.prob-track {
  background: var(--color-surface-raised);
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
  opacity: 0.55;
}

.prob-fill.winner {
  opacity: 1;
}

.prob-fill.home-win { background: var(--color-home-win); }
.prob-fill.draw { background: var(--color-draw); }
.prob-fill.home-loss { background: var(--color-home-loss); }
</style>
