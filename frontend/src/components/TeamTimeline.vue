<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  matches: { type: Array, required: true }, // already most-recent-first
})

const PAGE_SIZE = 25
const visibleCount = ref(PAGE_SIZE)

const visibleMatches = computed(() => props.matches.slice(0, visibleCount.value))
const hasMore = computed(() => visibleCount.value < props.matches.length)

function showMore() {
  visibleCount.value += PAGE_SIZE
}

const OUTCOME_CLASS = {
  Win: 'badge-active',
  Draw: 'badge-inactive',
  Loss: 'badge-invalid',
}
</script>

<template>
  <div class="timeline">
    <p v-if="matches.length === 0" class="muted">No matches found for this team.</p>

    <div v-else class="timeline-track">
      <div v-for="match in visibleMatches" :key="`${match.date}-${match.opponent}`" class="timeline-item">
        <div class="timeline-dot" :class="OUTCOME_CLASS[match.outcome]" />
        <div class="timeline-content">
          <div class="timeline-header">
            <span class="timeline-date">{{ match.date }}</span>
            <span class="badge" :class="OUTCOME_CLASS[match.outcome]">{{ match.outcome }}</span>
          </div>
          <div class="timeline-body">
            <strong>{{ match.is_home ? 'vs' : '@' }} {{ match.opponent }}</strong>
            <span class="score">{{ match.team_score }} – {{ match.opponent_score }}</span>
          </div>
          <div class="muted timeline-meta">
            {{ match.tournament }}<span v-if="match.neutral"> · Neutral venue</span>
          </div>
        </div>
      </div>
    </div>

    <button v-if="hasMore" class="secondary" @click="showMore">
      Show more ({{ matches.length - visibleCount }} remaining)
    </button>
  </div>
</template>

<style scoped>
.timeline-track {
  position: relative;
  padding-left: 18px;
  border-left: 2px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 16px;
}

.timeline-item {
  position: relative;
}

.timeline-dot {
  position: absolute;
  left: -24px;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-text-muted);
}

.timeline-dot.badge-active { background: var(--color-success); }
.timeline-dot.badge-invalid { background: var(--color-danger); }
.timeline-dot.badge-inactive { background: var(--color-draw); }

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
}

.timeline-date {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.timeline-body {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.score {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.timeline-meta {
  font-size: 0.8rem;
  margin-top: 2px;
}
</style>
