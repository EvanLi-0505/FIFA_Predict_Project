<script setup>
import { computed, onMounted } from 'vue'
import { useTeamStatsStore, MAX_COMPARE_TEAMS } from '../stores/teamStatsStore'
import TeamTimeline from '../components/TeamTimeline.vue'
import GroupedRateBars from '../components/GroupedRateBars.vue'
import PerformanceLineChart from '../components/PerformanceLineChart.vue'
import { computeGoalDiffSeries, FORM_CHART_MATCH_COUNT } from '../utils/teamForm'

const store = useTeamStatsStore()

onMounted(() => {
  if (!store.allTeamsLoaded) store.loadAllTeams()
})

function selectTeam(event) {
  const team = event.target.value
  if (team) store.loadTeamDetail(team)
}

const rateSeries = computed(() => {
  if (!store.stats) return []
  return [
    {
      name: store.stats.team_name,
      color: 'var(--color-primary)',
      values: [store.stats.win_rate, store.stats.draw_rate, store.stats.loss_rate],
    },
  ]
})

const formSeries = computed(() => {
  if (!store.stats) return []
  const points = computeGoalDiffSeries(store.matches, FORM_CHART_MATCH_COUNT).map((p) => ({
    label: p.date,
    opponent: p.opponent,
    value: p.value,
  }))
  return [{ name: store.stats.team_name, color: 'var(--color-primary)', points }]
})

const recentFormLabel = computed(() => (store.stats ? store.stats.recent_form.join(' · ') : ''))

function toggleCompare(team) {
  store.toggleCompareSelection(team)
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Team Explorer</h1>
      <p class="muted">
        Browse a team's full match history and lifetime record, or compare up to
        {{ MAX_COMPARE_TEAMS }} teams side by side using a composite power rating.
        Ratings are an illustrative in-app metric, not an official FIFA ranking.
      </p>
    </div>

    <div class="card">
      <h3>Browse a team</h3>
      <div class="field">
        <label for="team-select">Team</label>
        <select id="team-select" @change="selectTeam">
          <option value="">Select a team…</option>
          <option v-for="team in store.allTeams" :key="team" :value="team">{{ team }}</option>
        </select>
      </div>
      <p v-if="store.allTeamsError" class="error-text">{{ store.allTeamsError }}</p>
    </div>

    <template v-if="store.selectedTeam">
      <p v-if="store.detailLoading" class="muted">Loading {{ store.selectedTeam }}…</p>
      <p v-else-if="store.detailError" class="error-text">{{ store.detailError }}</p>

      <template v-else-if="store.stats">
        <div class="card">
          <div class="team-header">
            <h3>{{ store.stats.team_name }}</h3>
            <span v-if="store.stats.small_sample" class="badge badge-inactive">Small sample</span>
          </div>
          <div class="rating-display">
            <span class="rating-number">{{ store.stats.rating }}</span>
            <span class="rating-caption">Power rating<br /><span class="muted">(illustrative, not official)</span></span>
          </div>
          <p class="muted">
            {{ store.stats.matches_played }} matches · {{ store.stats.wins }}W
            {{ store.stats.draws }}D {{ store.stats.losses }}L · Goals
            {{ store.stats.goals_for }}–{{ store.stats.goals_against }}
            (avg diff {{ store.stats.goal_diff_avg.toFixed(2) }}/game)
          </p>
          <p class="muted">Recent form (most recent first): {{ recentFormLabel || '—' }}</p>
          <GroupedRateBars :series="rateSeries" />
        </div>

        <div class="card">
          <h3>Recent performance trend</h3>
          <p class="muted">
            Per-match goal difference (goal scored = +1, goal conceded = -1) over the
            last {{ FORM_CHART_MATCH_COUNT }} matches.
          </p>
          <PerformanceLineChart :series="formSeries" />
        </div>

        <div class="card">
          <h3>Match history</h3>
          <TeamTimeline :matches="store.matches" />
        </div>
      </template>
    </template>

    <div class="card">
      <h3>Compare teams</h3>
      <p class="muted">
        Pick up to {{ MAX_COMPARE_TEAMS }} teams, then click Compare.
      </p>
      <div class="compare-picker">
        <label
          v-for="team in store.allTeams"
          :key="team"
          class="compare-chip"
          :class="{ selected: store.compareSelection.includes(team) }"
        >
          <input
            type="checkbox"
            :checked="store.compareSelection.includes(team)"
            :disabled="
              !store.compareSelection.includes(team) &&
              store.compareSelection.length >= MAX_COMPARE_TEAMS
            "
            @change="toggleCompare(team)"
          />
          {{ team }}
        </label>
      </div>

      <div class="compare-actions">
        <button :disabled="store.compareSelection.length === 0 || store.comparing" @click="store.runComparison">
          {{ store.comparing ? 'Comparing…' : `Compare (${store.compareSelection.length})` }}
        </button>
        <button class="secondary" :disabled="store.compareSelection.length === 0" @click="store.clearCompareSelection">
          Clear
        </button>
      </div>
      <p v-if="store.compareError" class="error-text">{{ store.compareError }}</p>

      <table v-if="store.compareResults.length" class="compare-table">
        <thead>
          <tr>
            <th>Team</th>
            <th>Rating</th>
            <th>Record</th>
            <th>Win %</th>
            <th>Goal diff/game</th>
            <th>Recent form</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(result, index) in store.compareResults" :key="result.team_name">
            <td><strong>#{{ index + 1 }}</strong> {{ result.team_name }}</td>
            <td>{{ result.rating }}</td>
            <td>{{ result.wins }}W {{ result.draws }}D {{ result.losses }}L</td>
            <td>{{ (result.win_rate * 100).toFixed(1) }}%</td>
            <td>{{ result.goal_diff_avg.toFixed(2) }}</td>
            <td class="muted">{{ result.recent_form.join(' · ') || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.team-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.team-header h3 {
  margin: 0;
}

.rating-display {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 8px 0 14px;
}

.rating-number {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.rating-caption {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  line-height: 1.3;
}

.compare-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding: 4px 0 16px;
}

.compare-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  font-size: 0.82rem;
  cursor: pointer;
}

.compare-chip.selected {
  border-color: var(--color-primary);
  background: rgba(79, 124, 255, 0.12);
}

.compare-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.compare-table {
  margin-top: 8px;
}
</style>
