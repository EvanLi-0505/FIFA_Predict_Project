<script setup>
import { computed } from 'vue'

const props = defineProps({
  // [{ range_label: '40-50%', count: 3 }, ...]
  buckets: { type: Array, required: true },
  color: { type: String, default: 'var(--color-primary)' },
})

const maxCount = computed(() => Math.max(1, ...props.buckets.map((b) => b.count)))
</script>

<template>
  <div class="histogram">
    <div v-for="bucket in buckets" :key="bucket.range_label" class="hist-col">
      <div class="hist-bar-track">
        <div
          class="hist-bar"
          :style="{ height: `${(bucket.count / maxCount) * 100}%`, background: color }"
        >
          <span v-if="bucket.count > 0" class="hist-count">{{ bucket.count }}</span>
        </div>
      </div>
      <span class="hist-label">{{ bucket.range_label }}</span>
    </div>
  </div>
</template>

<style scoped>
.histogram {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 180px;
  padding-top: 20px;
}

.hist-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.hist-bar-track {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.hist-bar {
  width: 70%;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
  transition: height 0.6s cubic-bezier(0.22, 1, 0.36, 1);
  position: relative;
  display: flex;
  justify-content: center;
}

.hist-count {
  position: absolute;
  top: -18px;
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.hist-label {
  margin-top: 8px;
  font-size: 0.68rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  transform: rotate(-40deg);
  transform-origin: top center;
}
</style>
