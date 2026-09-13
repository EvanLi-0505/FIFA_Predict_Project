<script setup>
import { computed } from 'vue'

const props = defineProps({
  // [{ name: 'England', color: '#4f7cff', values: [winRate, drawRate, lossRate] }, ...]
  // 1 series = single-team view, 2 series = comparison view. Values are 0..1.
  series: { type: Array, required: true },
})

const CATEGORIES = ['Win rate', 'Draw rate', 'Loss rate']

const groups = computed(() =>
  CATEGORIES.map((category, categoryIndex) => ({
    category,
    bars: props.series.map((s) => ({
      name: s.name,
      color: s.color,
      value: s.values[categoryIndex],
    })),
  })),
)
</script>

<template>
  <div class="grouped-bars">
    <div v-if="series.length > 1" class="legend">
      <span v-for="s in series" :key="s.name" class="legend-item">
        <span class="dot" :style="{ background: s.color }" />
        {{ s.name }}
      </span>
    </div>

    <div class="chart">
      <div v-for="group in groups" :key="group.category" class="category">
        <div class="bars">
          <div v-for="bar in group.bars" :key="bar.name" class="bar-track">
            <div class="bar" :style="{ height: `${bar.value * 100}%`, background: bar.color }">
              <span class="bar-value">{{ (bar.value * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
        <span class="category-label">{{ group.category }}</span>
      </div>
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

.chart {
  display: flex;
  gap: 24px;
  align-items: flex-end;
  height: 180px;
  padding-top: 22px;
}

.category {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bars {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
}

.bar-track {
  flex: 1;
  max-width: 48px;
  height: 100%;
  display: flex;
  align-items: flex-end;
}

.bar {
  width: 100%;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
  position: relative;
  display: flex;
  justify-content: center;
  transition: height 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.bar-value {
  position: absolute;
  top: -18px;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.category-label {
  margin-top: 8px;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}
</style>
