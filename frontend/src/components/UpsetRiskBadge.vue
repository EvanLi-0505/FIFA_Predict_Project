<script setup>
import { RISK_LEVEL_LABELS } from '../utils/upset'

const COMPACT_LABELS = { low: 'Low', medium: 'Medium', high: 'High' }

defineProps({
  probability: { type: Number, required: true },
  level: { type: String, required: true },
  // Short form for tables: "33.8% · High"
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <span
    class="badge upset-badge"
    :class="`badge-risk-${level}`"
    title="Probability that the underdog wins outright"
  >
    <template v-if="compact">{{ (probability * 100).toFixed(1) }}% · {{ COMPACT_LABELS[level] }}</template>
    <template v-else>Upset {{ (probability * 100).toFixed(1) }}% · {{ RISK_LEVEL_LABELS[level] }}</template>
  </span>
</template>

<style scoped>
.upset-badge {
  white-space: nowrap;
}
</style>
