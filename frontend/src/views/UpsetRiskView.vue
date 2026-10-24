<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../services/api'
import { usePredictionStore } from '../stores/predictionStore'
import PredictionForm from '../components/PredictionForm.vue'
import ProbabilityChart from '../components/ProbabilityChart.vue'
import UpsetRiskBadge from '../components/UpsetRiskBadge.vue'
import { RISK_LEVEL_LABELS, upsetSummary } from '../utils/upset'

const HISTORY_LIMIT = 20
const TIERS = [
  { level: 'low', range: '< 15%' },
  { level: 'medium', range: '15–30%' },
  { level: 'high', range: '> 30%' },
]

const predictionStore = usePredictionStore()

const assessing = ref(false)
const error = ref(null)
const result = ref(null)
const teamHistories = ref([]) // [{ team, loading, error, data }]
const prefill = ref(null)
const selectedHistoryId = ref('')

const summary = computed(() => (result.value ? upsetSummary(result.value) : null))

onMounted(() => {
  if (!predictionStore.teamsLoaded) predictionStore.loadTeams()
  predictionStore.loadHistory()
})

async function assess(payload) {
  assessing.value = true
  error.value = null
  try {
    result.value = await api.getUpsetRisk(payload)
  } catch (e) {
    error.value = e.message
    return
  } finally {
    assessing.value = false
  }
  loadTeamHistories([result.value.home_team, result.value.away_team])
}

function loadTeamHistories(teams) {
  teamHistories.value = teams.map((team) => ({ team, loading: true, error: null, data: null }))
  teamHistories.value.forEach(async (entry) => {
    try {
      entry.data = await api.getTeamUpsets(entry.team, HISTORY_LIMIT)
    } catch (e) {
      entry.error = e.message
    } finally {
      entry.loading = false
    }
  })
}

function useHistoryItem() {
  const item = predictionStore.history.find((h) => h.id === Number(selectedHistoryId.value))
  if (!item) return
  const values = {
    homeTeam: item.home_team,
    awayTeam: item.away_team,
    hostCountry: item.host_country,
    tournament: item.tournament,
  }
  prefill.value = values
  assess(values)
}

function percent(value) {
  return `${(value * 100).toFixed(1)}%`
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Upset Risk</h1>
      <p class="subtitle">爆冷风险 · 黑天鹅分析</p>
      <p class="muted">
        Upset risk is the probability that the underdog — the side the active model gives
        the lower win chance — wins outright (draws don't count). Matches above 30% are
        flagged as high-risk predictions. Historical upsets are matches the underdog won
        even though the model gave it less than 20% beforehand.
      </p>

      <div v-if="predictionStore.history.length" class="field history-picker">
        <label for="history-pick">Load from prediction history</label>
        <select id="history-pick" v-model="selectedHistoryId" @change="useHistoryItem">
          <option value="" disabled>Pick a past prediction…</option>
          <option v-for="item in predictionStore.history" :key="item.id" :value="item.id">
            {{ item.home_team }} vs {{ item.away_team }} · {{ item.tournament }} ·
            {{ new Date(item.created_at).toLocaleString() }}
          </option>
        </select>
      </div>

      <PredictionForm
        :teams="predictionStore.teams"
        :submitting="assessing"
        :prefill="prefill"
        submit-label="Assess upset risk"
        submitting-label="Assessing…"
        @submit="assess"
      />
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>

    <div v-if="result" class="card">
      <div class="result-header">
        <h3>{{ result.home_team }} vs {{ result.away_team }}</h3>
        <UpsetRiskBadge :probability="summary.probability" :level="summary.level" />
      </div>
      <p class="muted">
        Host: {{ result.host_country }} · Tournament: {{ result.tournament }}
        ({{ result.tournament_category }}) · {{ result.neutral ? 'Neutral venue' : 'Home venue' }}
      </p>

      <div v-if="summary.level === 'high'" class="high-risk-banner">
        <span>⚠</span>
        <div>
          HIGH-RISK PREDICTION / 高风险预测
          <small>The underdog has a better than 30% chance of winning outright.</small>
        </div>
      </div>

      <div class="headline">
        <div class="headline-number" :class="`risk-${summary.level}`">{{ percent(summary.probability) }}</div>
        <div>
          chance that <strong>{{ summary.underdogTeam }}</strong> (underdog) beats
          <strong>{{ summary.favoriteTeam }}</strong> (favorite)
        </div>
      </div>

      <div class="tiers">
        <div
          v-for="tier in TIERS"
          :key="tier.level"
          class="tier"
          :class="[`tier-${tier.level}`, { current: tier.level === summary.level }]"
        >
          {{ RISK_LEVEL_LABELS[tier.level] }} <span class="muted">{{ tier.range }}</span>
        </div>
      </div>

      <ProbabilityChart :probabilities="result.probabilities" :predicted-outcome="result.predicted_outcome" />
      <p class="muted">
        Model: <code>{{ result.model_version }}</code> · Dataset: <code>{{ result.dataset_version }}</code>
        · Not saved to prediction history.
      </p>
    </div>

    <div v-for="entry in teamHistories" :key="entry.team" class="card">
      <h3>{{ entry.team }} — historical upsets</h3>
      <p v-if="entry.loading" class="muted">Loading…</p>
      <p v-else-if="entry.error" class="error-text">{{ entry.error }}</p>
      <template v-else>
        <p class="muted">
          {{ entry.data.summary.matches.toLocaleString() }} matches in the dataset ·
          caused <strong>{{ entry.data.summary.upsets_caused }}</strong> upsets as the underdog ·
          suffered <strong>{{ entry.data.summary.upsets_suffered }}</strong> as the favorite
          <span v-if="entry.data.matches.length"> · most recent {{ entry.data.matches.length }} shown</span>
        </p>
        <p v-if="!entry.data.matches.length" class="muted">
          No upsets involving {{ entry.team }} below {{ percent(entry.data.max_probability) }} in the dataset.
        </p>
        <table v-else>
          <thead>
            <tr>
              <th>Date</th>
              <th>Match</th>
              <th>Score</th>
              <th>Tournament</th>
              <th>Pre-match upset chance</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="match in entry.data.matches" :key="`${match.date}-${match.home_team}-${match.away_team}`">
              <td class="nowrap">{{ match.date }}</td>
              <td>{{ match.home_team }} vs {{ match.away_team }}</td>
              <td class="nowrap">{{ match.home_score }}–{{ match.away_score }}</td>
              <td>{{ match.tournament }}</td>
              <td>{{ percent(match.upset_probability) }}</td>
              <td>
                <span class="badge" :class="match.role === 'caused' ? 'badge-active' : 'badge-invalid'">
                  {{ match.role === 'caused' ? 'Caused' : 'Suffered' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>
  </div>
</template>

<style scoped>
.subtitle {
  margin: -4px 0 8px;
  color: var(--color-text-muted);
}

.history-picker {
  margin-bottom: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-header h3 {
  margin: 0;
}

.headline {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 16px 0 12px;
}

.headline-number {
  font-size: 2.6rem;
  font-weight: 700;
  line-height: 1;
}

.risk-low { color: var(--color-success); }
.risk-medium { color: var(--color-warning); }
.risk-high { color: var(--color-danger); }

.tiers {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tier {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 0.85rem;
  opacity: 0.55;
}

.tier.current {
  opacity: 1;
  font-weight: 600;
}

.tier-low.current { border-color: var(--color-success); }
.tier-medium.current { border-color: var(--color-warning); }
.tier-high.current { border-color: var(--color-danger); }

.nowrap {
  white-space: nowrap;
}

code {
  background: var(--color-surface-raised);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}
</style>
