<script setup>
import { onMounted, ref } from 'vue'
import { usePredictionStore } from '../stores/predictionStore'
import { useModelStore } from '../stores/modelStore'
import { useDatasetStore } from '../stores/datasetStore'
import { downloadPredictionReportMarkdown, downloadPredictionReportPdf } from '../utils/report'
import { fetchTeamComparisonData } from '../utils/matchComparison'
import { fetchUpsetHistory, upsetSummary } from '../utils/upset'
import UpsetRiskBadge from '../components/UpsetRiskBadge.vue'

const predictionStore = usePredictionStore()
const modelStore = useModelStore()
const datasetStore = useDatasetStore()

const busyId = ref(null)
const downloadingKey = ref(null) // `${item.id}:${format}` while a download is in flight

onMounted(() => {
  predictionStore.loadHistory()
  modelStore.loadModels()
  datasetStore.loadDatasets()
})

function modelLabel(id) {
  return modelStore.models.find((m) => m.id === id)?.model_id ?? `#${id}`
}

function datasetLabel(id) {
  return datasetStore.datasets.find((d) => d.id === id)?.version_label ?? `#${id}`
}

function outcomeBadgeClass(outcome) {
  if (outcome === 'Home Win') return 'badge-active'
  if (outcome === 'Home Loss') return 'badge-invalid'
  return 'badge-inactive'
}

async function removeItem(item) {
  busyId.value = item.id
  try {
    await predictionStore.deleteHistoryItem(item.id)
  } finally {
    busyId.value = null
  }
}

async function clearAll() {
  if (!confirm('Delete all prediction history? This cannot be undone.')) return
  await predictionStore.clearHistory()
}

async function download(item, format) {
  const key = `${item.id}:${format}`
  downloadingKey.value = key

  // The comparison charts (histogram/line) are a nice-to-have addition to
  // the report — if fetching them fails for any reason, still download
  // the report with just the probability breakdown rather than blocking it.
  let comparison
  try {
    comparison = await fetchTeamComparisonData(item.home_team, item.away_team)
  } catch {
    comparison = undefined
  }
  let upsetHistory
  try {
    upsetHistory = await fetchUpsetHistory(item.home_team, item.away_team)
  } catch {
    upsetHistory = undefined
  }

  const payload = {
    homeTeam: item.home_team,
    awayTeam: item.away_team,
    hostCountry: item.host_country,
    tournament: item.tournament,
    neutral: item.neutral,
    probabilities: item.probabilities,
    predictedOutcome: item.predicted_outcome,
    confidence: item.confidence,
    modelVersion: modelLabel(item.model_version_id),
    datasetVersion: datasetLabel(item.dataset_id),
    timestamp: item.created_at,
    comparison,
    upset: { ...upsetSummary(item), history: upsetHistory },
  }

  try {
    if (format === 'md') downloadPredictionReportMarkdown(payload)
    else downloadPredictionReportPdf(payload)
  } finally {
    downloadingKey.value = null
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Prediction History</h1>
      <p class="muted">Every prediction ever made through this app, most recent first.</p>
      <button
        v-if="predictionStore.history.length"
        class="danger"
        @click="clearAll"
      >
        Clear all history
      </button>
      <p v-if="predictionStore.historyActionError" class="error-text">
        {{ predictionStore.historyActionError }}
      </p>
    </div>

    <div class="card">
      <p v-if="predictionStore.historyLoading" class="muted">Loading…</p>
      <p v-else-if="predictionStore.historyError" class="error-text">
        {{ predictionStore.historyError }}
      </p>
      <p v-else-if="predictionStore.history.length === 0" class="muted">
        No predictions yet — make one on the Predict page.
      </p>
      <div v-else class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Match</th>
            <th>Outcome</th>
            <th>Confidence</th>
            <th>Upset risk</th>
            <th>Model</th>
            <th>Dataset</th>
            <th>When</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in predictionStore.history" :key="item.id">
            <td>{{ item.home_team }} vs {{ item.away_team }}</td>
            <td><span class="badge" :class="outcomeBadgeClass(item.predicted_outcome)">{{ item.predicted_outcome }}</span></td>
            <td>{{ (item.confidence * 100).toFixed(1) }}%</td>
            <td><UpsetRiskBadge :probability="item.upset_probability" :level="item.upset_risk_level" compact /></td>
            <!-- zero-width spaces: long ids like logistic_regression_elo_v1 wrap at underscores -->
            <td>{{ modelLabel(item.model_version_id).replaceAll('_', '_​') }}</td>
            <td>{{ datasetLabel(item.dataset_id) }}</td>
            <td class="muted">{{ new Date(item.created_at).toLocaleString() }}</td>
            <td class="actions">
              <button
                class="secondary"
                :disabled="downloadingKey === `${item.id}:md`"
                @click="download(item, 'md')"
              >
                {{ downloadingKey === `${item.id}:md` ? 'Preparing…' : 'Markdown' }}
              </button>
              <button
                class="secondary"
                :disabled="downloadingKey === `${item.id}:pdf`"
                @click="download(item, 'pdf')"
              >
                {{ downloadingKey === `${item.id}:pdf` ? 'Preparing…' : 'PDF' }}
              </button>
              <button class="danger" :disabled="busyId === item.id" @click="removeItem(item)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-scroll {
  overflow-x: auto;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  white-space: nowrap;
}
</style>
