<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { usePredictionStore } from '../stores/predictionStore'
import { fetchTeamComparisonData } from '../utils/matchComparison'
import PieChart from '../components/PieChart.vue'
import GroupedRateBars from '../components/GroupedRateBars.vue'
import PerformanceLineChart from '../components/PerformanceLineChart.vue'

const predictionStore = usePredictionStore()

const selectedPredictionId = ref('')
const comparison = ref(null)
const comparisonLoading = ref(false)
const comparisonError = ref(null)

onMounted(() => {
  predictionStore.loadHistory(200)
})

const selectedPrediction = computed(
  () => predictionStore.history.find((item) => item.id === Number(selectedPredictionId.value)) ?? null,
)

const OUTCOME_COLORS = {
  'Home Win': '#3ec98b',
  Draw: '#9a7bea',
  'Home Loss': '#f0576b',
}

const HOME_COLOR = '#4f7cff'
const AWAY_COLOR = '#f2b84b'

const outcomeSegments = computed(() => {
  if (!selectedPrediction.value) return []
  return Object.entries(selectedPrediction.value.probabilities).map(([label, value]) => ({
    label,
    value,
    color: OUTCOME_COLORS[label] ?? '#4f7cff',
  }))
})

const rateSeries = computed(() => {
  if (!comparison.value || !selectedPrediction.value) return []
  const { home, away } = comparison.value
  return [
    {
      name: selectedPrediction.value.home_team,
      color: HOME_COLOR,
      values: [home.stats.win_rate, home.stats.draw_rate, home.stats.loss_rate],
    },
    {
      name: selectedPrediction.value.away_team,
      color: AWAY_COLOR,
      values: [away.stats.win_rate, away.stats.draw_rate, away.stats.loss_rate],
    },
  ]
})

const formSeries = computed(() => {
  if (!comparison.value || !selectedPrediction.value) return []
  const { home, away } = comparison.value
  return [
    {
      name: selectedPrediction.value.home_team,
      color: HOME_COLOR,
      points: home.series.map((p) => ({ label: p.date, opponent: p.opponent, value: p.value })),
    },
    {
      name: selectedPrediction.value.away_team,
      color: AWAY_COLOR,
      points: away.series.map((p) => ({ label: p.date, opponent: p.opponent, value: p.value })),
    },
  ]
})

watch(selectedPrediction, async (prediction) => {
  comparison.value = null
  comparisonError.value = null
  if (!prediction) return

  comparisonLoading.value = true
  try {
    comparison.value = await fetchTeamComparisonData(prediction.home_team, prediction.away_team)
  } catch (error) {
    comparisonError.value = error.message
  } finally {
    comparisonLoading.value = false
  }
})
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Dashboard</h1>
      <p class="muted">
        Pick a prediction from your history to see its outcome breakdown alongside a
        head-to-head comparison of the two teams involved.
      </p>
    </div>

    <div class="card">
      <h3>Select a prediction</h3>
      <p v-if="predictionStore.historyLoading" class="muted">Loading history…</p>
      <p v-else-if="predictionStore.history.length === 0" class="muted">
        No predictions yet — make one on the Predict page.
      </p>
      <div v-else class="field">
        <label for="prediction-select">Prediction</label>
        <select id="prediction-select" v-model="selectedPredictionId">
          <option value="">Select a prediction…</option>
          <option v-for="item in predictionStore.history" :key="item.id" :value="item.id">
            {{ item.home_team }} vs {{ item.away_team }} — {{ item.predicted_outcome }}
            ({{ new Date(item.created_at).toLocaleString() }})
          </option>
        </select>
      </div>
    </div>

    <template v-if="selectedPrediction">
      <div class="card">
        <h3>Outcome probabilities</h3>
        <p class="muted">
          {{ selectedPrediction.home_team }} vs {{ selectedPrediction.away_team }}
        </p>
        <PieChart :segments="outcomeSegments" :center-label="selectedPrediction.predicted_outcome" />
      </div>

      <p v-if="comparisonLoading" class="muted">Loading team comparison…</p>
      <p v-else-if="comparisonError" class="error-text">{{ comparisonError }}</p>

      <template v-else-if="comparison">
        <div class="card">
          <h3>Head-to-head: lifetime record</h3>
          <p class="muted">
            {{ selectedPrediction.home_team }} vs {{ selectedPrediction.away_team }} — all-time
            win/draw/loss rate.
          </p>
          <GroupedRateBars :series="rateSeries" />
        </div>

        <div class="card">
          <h3>Head-to-head: recent form</h3>
          <p class="muted">
            Per-match goal difference over each team's last 20 matches.
          </p>
          <PerformanceLineChart :series="formSeries" />
        </div>
      </template>
    </template>
  </div>
</template>
